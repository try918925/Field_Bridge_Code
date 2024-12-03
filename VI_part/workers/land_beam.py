import time
import uuid
import zmq
import json
import math
import cv2
import numpy as np
import time
import socket
import threading
import traceback
from pathlib import Path
import sys
import os
import copy

FILE = Path(__file__).resolve()
ROOT = FILE.parents[1]  # YOLOv5 root directory
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative
from global_info import *
from initializers import *
from configs import config_det_cemian
from algorithms.yolov5.predictor.det_predictor import YOLOv5Detector
from algorithms.ppocr.infer_det_rec import OCR_process
from cam_utils.camsdk import hksdk as camera_sdk
from configs.cam_info import CAMERA_DICT

has_time = time.time()
no_time = time.time()

def set_VI003(Ep):
    '''

    Ep = {
            "exception_code": 'E202',#int,异常代码
            "detail":f"{item}", #string,具体信息描述
            "happen_time": VI003['timestamp'], #long, 时间戳,单位毫秒
            "has_solved": False, #bool,是否已解决
            "solve_time": None #long, 时间戳,单位毫秒
    }
    '''
    VI003 = get_global('VI003')
    VI003['msg_uid'] = str(uuid.uuid1())
    VI003['timestamp'] = str(int(time.time() * 1000))  # long, 时间戳,单位毫秒
    VI003['data'] = Ep
    set_global('VI003', VI003)
    send_msg = json.dumps(VI003, ensure_ascii=False)
    VI2MC_pub.send_msg(send_msg)

def renew_VI002(result, need_det_cam):
    _lane_cam = {
        'lane_2': 'cam_151',
        'lane_3': 'cam_153',
        'lane_4': ['cam_155', 'cam_163'],
        'lane_5': 'cam_165',
        'lane_6': 'cam_161'
    }
    VI002 = get_global('VI002')
    if VI002['data']['truck_recognize_results'] is None:
        VI002['data']['truck_recognize_results'] = [None] * 6  # 6

    for i in range(len(VI002['data']['truck_recognize_results'])):

        if VI002['data']['truck_recognize_results'][i]['recognizeResults'] is None or \
                len(VI002['data']['truck_recognize_results'][i]['recognizeResults']) == 0:
            VI002['data']['truck_recognize_results'][i]['recognizeResults'] = [None] * 8  # 8组识别结果

        # 没有带箱子
        if VI002['data']['truck_recognize_results'][i]['recognizeResults'][4] is None or i == 0:
            continue
        else:
            if i + 1 == 4:
                if 'cam_163' in need_det_cam:
                    cam = _lane_cam[f'lane_{i + 1}'][1]
                elif 'cam_155' in need_det_cam:
                    cam = _lane_cam[f'lane_{i + 1}'][0]
                else:
                    cam = _lane_cam[f'lane_{i + 1}'][1]
            else:
                cam = _lane_cam[f'lane_{i + 1}']

            # 1: dir 0zuo 1you
            if result[cam]["front"]["container_info"] is not None:
                datetime = result[cam]["front"]["timestamp"]
                VI002["data"]["truck_recognize_results"][i]["recognizeResults"][5] = \
                    {
                        "item": "container_id_front",
                        "state": 1,
                        "result": result[cam]["front"]["container_info"][0],
                        "images": [
                            {
                                "image": os.path.relpath(f"./log/cemian_result/frame_{datetime}.jpg",
                                                         '/home/root123'),
                                "datetime": datetime
                            }
                        ]
                    }
            if result[cam]["center"]["container_info"] is not None:
                datetime = result[cam]["center"]["timestamp"]
                VI002["data"]["truck_recognize_results"][i]["recognizeResults"][6] = \
                    {
                        "item": "container_id_center",
                        "state": 1,
                        "result": result[cam]["center"]["container_info"][0],
                        "images": [
                            {
                                "image": os.path.relpath(f"./log/cemian_result/frame_{datetime}.jpg", '/home/root123'),
                                "datetime": datetime
                            }
                        ]
                    }
            if result[cam]["rear"]["container_info"] is not None:
                datetime = result[cam]["rear"]["timestamp"]
                VI002["data"]["truck_recognize_results"][i]["recognizeResults"][7] = \
                    {
                        "item": "container_id_rear",
                        "state": 1,
                        "result": result[cam]["rear"]["container_info"][0],
                        "images": [
                            {
                                "image": os.path.relpath(f"./log/cemian_result/frame_{datetime}.jpg",
                                                         '/home/root123'),
                                "datetime": datetime
                            }
                        ]
                    }

    set_global('VI002', VI002)
    send_msg = str(json.dumps(VI002, ensure_ascii=False))
    VI2MC_pub.send_msg(send_msg)
    return VI002


class cemian_ocr(threading.Thread):
    def __init__(self) -> None:
        super().__init__()

        self.cemian_detector = YOLOv5Detector.from_config(config_det_cemian)
        config_dict = {
            "ocr_det_config": "./configs/cemian_container_num_det_r50_db++_td_tr.yml",
            "ocr_rec_config": "./configs/cemian_container_num_rec_en_PP-OCRv3.yml"
        }
        self.cemian_ocr_process = OCR_process(config_dict)

        # 165相机：陆侧看5车道
        # 155相机：海侧看4车道
        # 153相机：海侧看3车道
        # 151相机：海侧看2车道
        # 163相机：陆侧看4车道
        # 161相机：陆侧看6车道

        self.cams_dict = {
            'cam_165': None,  # cam device
            'cam_155': None,
            'cam_153': None,
            'cam_151': None,
            'cam_163': None,
            'cam_161': None
        }

        # 相机对应车道
        self.cam_lane = {
            'cam_151': 'lane_2',
            'cam_153': 'lane_3',
            'cam_155': 'lane_4',
            'cam_163': 'lane_4',
            'cam_165': 'lane_5',
            'cam_161': 'lane_6'
        }

        # 车道对应相机
        self.lane_cam = {
            'lane_2': 'cam_151',
            'lane_3': 'cam_153',
            'lane_4': ['cam_155', 'cam_163'],
            # 'lane_4': 'cam_155',
            'lane_5': 'cam_165',
            'lane_6': 'cam_161'
        }

        self.init_cams()

        self.device_165 = self.cams_dict['cam_165']
        self.device_155 = self.cams_dict['cam_155']
        self.device_153 = self.cams_dict['cam_153']
        self.device_151 = self.cams_dict['cam_151']
        self.device_163 = self.cams_dict['cam_163']
        self.device_161 = self.cams_dict['cam_161']

        self.cams_obj_lst = {
            'cam_165': {
                "front": {
                    "area": 0,
                    "oxy": [0, 0],
                    "need_rec": 0,
                    "keyframe": None,
                    "crop_img": None,
                    "timestamp": None,
                    "container_info": None,
                    "container_score": [0.0, 0.0],

                },
                "center": {
                    "area": 0,
                    "oxy": [0, 0],
                    "need_rec": 0,
                    "keyframe": None,
                    "crop_img": None,
                    "timestamp": None,
                    "container_info": None,
                    "container_score": [0.0, 0.0],
                },
                "rear": {
                    "area": 0,
                    "oxy": [0, 0],
                    "need_rec": 0,
                    "keyframe": None,
                    "crop_img": None,
                    "timestamp": None,
                    "container_info": None,
                    "container_score": [0.0, 0.0],
                }
            },
            'cam_155': {
                "front": {
                    "area": 0,
                    "oxy": [0, 0],
                    "need_rec": 0,
                    "keyframe": None,
                    "crop_img": None,
                    "timestamp": None,
                    "container_info": None,
                    "container_score": [0.0, 0.0],
                },
                "center": {
                    "area": 0,
                    "oxy": [0, 0],
                    "need_rec": 0,
                    "keyframe": None,
                    "crop_img": None,
                    "timestamp": None,
                    "container_info": None,
                    "container_score": [0.0, 0.0],
                },
                "rear": {
                    "area": 0,
                    "oxy": [0, 0],
                    "need_rec": 0,
                    "keyframe": None,
                    "crop_img": None,
                    "timestamp": None,
                    "container_info": None,
                    "container_score": [0.0, 0.0],
                }
            },
            'cam_153': {
                "front": {
                    "area": 0,
                    "oxy": [0, 0],
                    "need_rec": 0,
                    "keyframe": None,
                    "crop_img": None,
                    "timestamp": None,
                    "container_info": None,
                    "container_score": [0.0, 0.0],
                },
                "center": {
                    "area": 0,
                    "oxy": [0, 0],
                    "need_rec": 0,
                    "keyframe": None,
                    "crop_img": None,
                    "timestamp": None,
                    "container_info": None,
                    "container_score": [0.0, 0.0],
                },
                "rear": {
                    "area": 0,
                    "oxy": [0, 0],
                    "need_rec": 0,
                    "keyframe": None,
                    "crop_img": None,
                    "timestamp": None,
                    "container_info": None,
                    "container_score": [0.0, 0.0],
                }
            },
            'cam_151': {
                "front": {
                    "area": 0,
                    "oxy": [0, 0],
                    "need_rec": 0,
                    "keyframe": None,
                    "crop_img": None,
                    "timestamp": None,
                    "container_info": None,
                    "container_score": [0.0, 0.0],
                },
                "center": {
                    "area": 0,
                    "oxy": [0, 0],
                    "need_rec": 0,
                    "keyframe": None,
                    "crop_img": None,
                    "timestamp": None,
                    "container_info": None,
                    "container_score": [0.0, 0.0],
                },
                "rear": {
                    "area": 0,
                    "oxy": [0, 0],
                    "need_rec": 0,
                    "keyframe": None,
                    "crop_img": None,
                    "timestamp": None,
                    "container_info": None,
                    "container_score": [0.0, 0.0],
                }
            },
            'cam_163': {
                "front": {
                    "area": 0,
                    "oxy": [0, 0],
                    "need_rec": 0,
                    "keyframe": None,
                    "crop_img": None,
                    "timestamp": None,
                    "container_info": None,
                    "container_score": [0.0, 0.0],
                },
                "center": {
                    "area": 0,
                    "oxy": [0, 0],
                    "need_rec": 0,
                    "keyframe": None,
                    "crop_img": None,
                    "timestamp": None,
                    "container_info": None,
                    "container_score": [0.0, 0.0],
                },
                "rear": {
                    "area": 0,
                    "oxy": [0, 0],
                    "need_rec": 0,
                    "keyframe": None,
                    "crop_img": None,
                    "timestamp": None,
                    "container_info": None,
                    "container_score": [0.0, 0.0],
                }
            },
            'cam_161': {
                "front": {
                    "area": 0,
                    "oxy": [0, 0],
                    "need_rec": 0,
                    "keyframe": None,
                    "crop_img": None,
                    "timestamp": None,
                    "container_info": None,
                    "container_score": [0.0, 0.0],
                },
                "center": {
                    "area": 0,
                    "oxy": [0, 0],
                    "need_rec": 0,
                    "keyframe": None,
                    "crop_img": None,
                    "timestamp": None,
                    "container_info": None,
                    "container_score": [0.0, 0.0],
                },
                "rear": {
                    "area": 0,
                    "oxy": [0, 0],
                    "need_rec": 0,
                    "keyframe": None,
                    "crop_img": None,
                    "timestamp": None,
                    "container_info": None,
                    "container_score": [0.0, 0.0],
                }
            }
        }

        self.cams_results = {
            'cam_165': [],
            'cam_155': [],
            'cam_153': [],
            'cam_151': [],
            'cam_163': [],
            'cam_161': []
        }

        self.need_det_cam = []

        self.need_det_frame = []

        self.nowTime = time.time()

    def refresh_cams_obj_lst(self):
        self.cams_obj_lst = {
            'cam_165': {
                "front": {
                    "area": 0,
                    "oxy": [0, 0],
                    "need_rec": 0,
                    "keyframe": None,
                    "crop_img": None,
                    "timestamp": None,
                    "container_info": None,
                    "container_score": [0.0, 0.0],
                },
                "center": {
                    "area": 0,
                    "oxy": [0, 0],
                    "need_rec": 0,
                    "keyframe": None,
                    "crop_img": None,
                    "timestamp": None,
                    "container_info": None,
                    "container_score": [0.0, 0.0],
                },
                "rear": {
                    "area": 0,
                    "oxy": [0, 0],
                    "need_rec": 0,
                    "keyframe": None,
                    "crop_img": None,
                    "timestamp": None,
                    "container_info": None,
                    "container_score": [0.0, 0.0],
                }
            },
            'cam_155': {
                "front": {
                    "area": 0,
                    "oxy": [0, 0],
                    "need_rec": 0,
                    "keyframe": None,
                    "crop_img": None,
                    "timestamp": None,
                    "container_info": None,
                    "container_score": [0.0, 0.0],
                },
                "center": {
                    "area": 0,
                    "oxy": [0, 0],
                    "need_rec": 0,
                    "keyframe": None,
                    "crop_img": None,
                    "timestamp": None,
                    "container_info": None,
                    "container_score": [0.0, 0.0],
                },
                "rear": {
                    "area": 0,
                    "oxy": [0, 0],
                    "need_rec": 0,
                    "keyframe": None,
                    "crop_img": None,
                    "timestamp": None,
                    "container_info": None,
                    "container_score": [0.0, 0.0],
                }
            },
            'cam_153': {
                "front": {
                    "area": 0,
                    "oxy": [0, 0],
                    "need_rec": 0,
                    "keyframe": None,
                    "crop_img": None,
                    "timestamp": None,
                    "container_info": None,
                    "container_score": [0.0, 0.0],
                },
                "center": {
                    "area": 0,
                    "oxy": [0, 0],
                    "need_rec": 0,
                    "keyframe": None,
                    "crop_img": None,
                    "timestamp": None,
                    "container_info": None,
                    "container_score": [0.0, 0.0],
                },
                "rear": {
                    "area": 0,
                    "oxy": [0, 0],
                    "need_rec": 0,
                    "keyframe": None,
                    "crop_img": None,
                    "timestamp": None,
                    "container_info": None,
                    "container_score": [0.0, 0.0],
                }
            },
            'cam_151': {
                "front": {
                    "area": 0,
                    "oxy": [0, 0],
                    "need_rec": 0,
                    "keyframe": None,
                    "crop_img": None,
                    "timestamp": None,
                    "container_info": None,
                    "container_score": [0.0, 0.0],
                },
                "center": {
                    "area": 0,
                    "oxy": [0, 0],
                    "need_rec": 0,
                    "keyframe": None,
                    "crop_img": None,
                    "timestamp": None,
                    "container_info": None,
                    "container_score": [0.0, 0.0],
                },
                "rear": {
                    "area": 0,
                    "oxy": [0, 0],
                    "need_rec": 0,
                    "keyframe": None,
                    "crop_img": None,
                    "timestamp": None,
                    "container_info": None,
                    "container_score": [0.0, 0.0],
                }
            },
            'cam_163': {
                "front": {
                    "area": 0,
                    "oxy": [0, 0],
                    "need_rec": 0,
                    "keyframe": None,
                    "crop_img": None,
                    "timestamp": None,
                    "container_info": None,
                    "container_score": [0.0, 0.0],
                },
                "center": {
                    "area": 0,
                    "oxy": [0, 0],
                    "need_rec": 0,
                    "keyframe": None,
                    "crop_img": None,
                    "timestamp": None,
                    "container_info": None,
                    "container_score": [0.0, 0.0],
                },
                "rear": {
                    "area": 0,
                    "oxy": [0, 0],
                    "need_rec": 0,
                    "keyframe": None,
                    "crop_img": None,
                    "timestamp": None,
                    "container_info": None,
                    "container_score": [0.0, 0.0],
                }
            },
            'cam_161': {
                "front": {
                    "area": 0,
                    "oxy": [0, 0],
                    "need_rec": 0,
                    "keyframe": None,
                    "crop_img": None,
                    "timestamp": None,
                    "container_info": None,
                    "container_score": [0.0, 0.0],
                },
                "center": {
                    "area": 0,
                    "oxy": [0, 0],
                    "need_rec": 0,
                    "keyframe": None,
                    "crop_img": None,
                    "timestamp": None,
                    "container_info": None,
                    "container_score": [0.0, 0.0],
                },
                "rear": {
                    "area": 0,
                    "oxy": [0, 0],
                    "need_rec": 0,
                    "keyframe": None,
                    "crop_img": None,
                    "timestamp": None,
                    "container_info": None,
                    "container_score": [0.0, 0.0],
                }
            }
        }

    def init_cams(self, ):
        '''
            初始化所有相机
        '''
        for item in self.cams_dict.keys():
            ret, self.cams_dict[item] = init_camera(CAMERA_DICT[item], key_logger)
            if not ret:
                # VI003 E202
                Ep = {
                    "exception_code": 'E202',  # int,异常代码
                    "detail": f"{item}",  # string,具体信息描述
                    "happen_time": str(int(time.time())),  # long, 时间戳,单位毫秒
                    "has_solved": False,  # bool,是否已解决
                    "solve_time": None  # long, 时间戳,单位毫秒
                }
                set_VI003(Ep)
                error_logger.error(f'failed to init {item}')

    # 该功能测试31种排列组合无误
    def judge_which_cam_det(self):
        lane_has_car = []
        min_lane = -1
        max_lane = -1

        VI002 = get_global('VI002')

        if VI002['data']['truck_recognize_results'] is None:
            VI002['data']['truck_recognize_results'] = [None] * 6

        # 2-6车道
        for i in range(5):
            if VI002['data']['truck_recognize_results'][i + 1]['recognizeResults'] is None or \
                    len(VI002['data']['truck_recognize_results'][i + 1]['recognizeResults']) == 0:
                VI002['data']['truck_recognize_results'][i + 1]['recognizeResults'] = [None] * 8
                # 车道上没有车（去掉1车道）
            if VI002['data']['truck_recognize_results'][i + 1]['recognizeResults'][1] is None:
                continue
            else:
                lane = int(i + 2)
                lane_has_car.append(lane)

        if len(lane_has_car) > 0:
            min_lane = min(lane_has_car)
            max_lane = max(lane_has_car)

        # 车道只有一个车的情况：
        if min_lane > 0 and max_lane > 0:
            if min_lane == max_lane:
                # cam = self.lane_cam[f'lane_{min_lane}']
                # self.need_det_cam.append(cam)
                if min_lane != 4:
                    cam = self.lane_cam[f'lane_{min_lane}']
                    self.need_det_cam.append(cam)
                else:
                    cam = self.lane_cam[f'lane_{min_lane}'][1]
                    self.need_det_cam.append(cam)
                #     # 看是否可以做4车道两个相机的结果融合
                #     # 155
                #     cam1 = self.lane_cam[f'lane_{min_lane}'][0]
                #     self.need_det_cam.append(cam1)
                #     # 163
                #     cam2 = self.lane_cam[f'lane_{min_lane}'][1]
                #     self.need_det_cam.append(cam2)

            else:
                # 车道车辆数大于1的情况：
                # 先根据有车的车道区分陆侧海侧（23，56）（4车道海侧和陆侧都有相机可以看）
                sea_lst = [number for number in lane_has_car if number < 4]
                road_lst = [number for number in lane_has_car if number > 4]
                if len(sea_lst) > 0:
                    min_lane = min(sea_lst)

                if len(road_lst) > 0:
                    max_lane = max(road_lst)

                if min_lane < 4:
                    cam = self.lane_cam[f'lane_{min_lane}']
                    self.need_det_cam.append(cam)
                if max_lane > 4:
                    cam = self.lane_cam[f'lane_{max_lane}']
                    self.need_det_cam.append(cam)

                if max_lane == 4:
                    cam = self.lane_cam[f'lane_{max_lane}'][1]
                    self.need_det_cam.append(cam)

                if min_lane == 4:
                    cam = self.lane_cam[f'lane_{min_lane}'][0]
                    self.need_det_cam.append(cam)

                # if min_lane == 4:
                #     cam = self.lane_cam[f'lane_{min_lane}'][0]
                #     self.need_det_cam.append(cam)

                # if max_lane == 4:
                #     cam = self.lane_cam[f'lane_{max_lane}'][1]
                #     self.need_det_cam.append(cam)

    def judge_cam_rec(self, cam, obj_lst, frame, last_result):
        def update_result(section, area, xo, yo, y1, y2, x1, x2):
            temp_result[section]["need_rec"] = 1
            temp_result[section]["area"] = area
            temp_result[section]["oxy"] = [xo, yo]
            temp_result[section]["keyframe"] = frame
            temp_result[section]["crop_img"] = frame[y1: y2, x1: x2]
            temp_result[section]["timestamp"] = int(time.time() * 1000)

        temp_result = {
            "front": {
                "area": 0,
                "oxy": [0, 0],
                "need_rec": 0,
                "keyframe": None,
                "crop_img": None,
                "timestamp": None,
                "container_info": None,
                'container_score': [0.0, 0.0]
            },
            "center": {
                "area": 0,
                "oxy": [0, 0],
                "need_rec": 0,
                "keyframe": None,
                "crop_img": None,
                "timestamp": None,
                "container_info": None,
                'container_score': [0.0, 0.0]
            },
            "rear": {
                "area": 0,
                "oxy": [0, 0],
                "need_rec": 0,
                "keyframe": None,
                "crop_img": None,
                "timestamp": None,
                "container_info": None,
                'container_score': [0.0, 0.0]
            },
        }

        if len(obj_lst) > 0:
            cam_conditions = {
                'cam_165': {'20': 200000, '40': 400000},
                'cam_163': {'20': 150000, '40': 300000},
                'cam_155': {'20': 150000, '40': 360000},
                'cam_153': {'20': 100000, '40': 300000},
                'cam_151': {'20': 100000, '40': 300000}
            }

            if cam in cam_conditions:
                for class_id, class_name, score, p1p2, oxywh in obj_lst:
                    x1, y1, x2, y2 = map(int, p1p2)
                    xo, yo, w, h = oxywh
                    area = w * h
                    if class_name in cam_conditions[cam]:
                        area_threshold = cam_conditions[cam][class_name]
                        if (area > area_threshold) and (600 < yo < 2000):
                            if class_name == "20":
                                if xo < 1920 and area >= last_result["front"]["area"] - 200:
                                    update_result("front", area, xo, yo, y1, y2, x1, x2)
                                elif xo > 1920 and area >= last_result["rear"]["area"] - 200:
                                    update_result("rear", area, xo, yo, y1, y2, x1, x2)
                            elif class_name == "40":
                                update_result("center", area, xo, yo, y1, y2, x1, x2)

        return temp_result

    def get_cam_obj(self, cam_f_dt):
        key_lst = []
        frame_lst = []
        for key, frame in cam_f_dt.items():
            key_lst.append(key)
            frame_lst.append(frame)

        inference_results = self.cemian_detector.infer(frame_lst)
        for i in range(len(key_lst)):
            obj_lst = inference_results[i]
            last_result = copy.deepcopy(self.cams_obj_lst[key_lst[i]])

            now_result = self.judge_cam_rec(key_lst[i], obj_lst, frame_lst[i], last_result)
            # print(now_result)

            for pos, item in now_result.items():
                # print(key_lst[i], pos, last_result[pos]['need_rec'])
                # print(key_lst[i], pos, now_result[pos]['need_rec'])
                if now_result[pos]['need_rec'] > 0:
                    self.cams_obj_lst[key_lst[i]][pos] = now_result[pos]
                    self.cams_obj_lst[key_lst[i]][pos]['need_rec'] = last_result[pos]['need_rec'] + 1

    def get_lane_result(self, lane):
        need_det_cam = copy.deepcopy(self.need_det_cam)
        VI002 = get_global('VI002')
        if VI002['data']['truck_recognize_results'][lane - 1]['recognizeResults'][4] is not None:
            state = VI002['data']['truck_recognize_results'][lane - 1]['recognizeResults'][4]['result']
        else:
            return None

        if lane == 4:
            if 'cam_163' in need_det_cam:
                cam = self.lane_cam[f'lane_{lane}'][1]
            elif 'cam_155' in need_det_cam:
                cam = self.lane_cam[f'lane_{lane}'][0]
            else:
                cam = self.lane_cam[f'lane_{lane}'][1]
        else:
            cam = self.lane_cam[f'lane_{lane}']
        renew_result = copy.deepcopy(self.cams_obj_lst)
        cam_result = copy.deepcopy(self.cams_obj_lst[cam])
        if state != '101' and state != '000':
            if cam_result['front']['timestamp'] is not None:
                container_num_dict = cam_result["front"]
            elif cam_result['center']['timestamp'] is not None:
                container_num_dict = cam_result["center"]
            elif cam_result['rear']['timestamp'] is not None:
                container_num_dict = cam_result["rear"]
            else:
                container_num_dict = None

            if state == '121' or state == '111':
                renew_result[cam]['center'] = container_num_dict
            elif state == '100':
                renew_result[cam]['front'] = container_num_dict
            elif state == '001':
                renew_result[cam]['rear'] = container_num_dict
        # 双箱
        else:
            if VI002['data']['truck_recognize_results'][lane - 1]['recognizeResults'][1] is not None:
                truck_dir = VI002['data']['truck_recognize_results'][lane - 1]['recognizeResults'][1]['result']
                # dir 0左 1右
                # 交换
                if truck_dir == '1' or lane < 4:
                    # print('===================================')
                    # print(truck_dir)
                    # print(self.cams_obj_lst[cam]['front']['container_info'])
                    # print(self.cams_obj_lst[cam]['rear']['container_info'])

                    temp_front = copy.deepcopy(renew_result[cam]['front'])
                    temp_rear = copy.deepcopy(renew_result[cam]['rear'])
                    renew_result[cam]['front'] = temp_rear
                    renew_result[cam]['rear'] = temp_front

        return renew_result

    def save_container(self, lane, final_result):
        need_det_cam = copy.deepcopy(self.need_det_cam)
        if lane == 4:
            if 'cam_163' in need_det_cam:
                cam = self.lane_cam[f'lane_{lane}'][1]
            elif 'cam_155' in need_det_cam:
                cam = self.lane_cam[f'lane_{lane}'][0]
            else:
                cam = self.lane_cam[f'lane_{lane}'][1]
        else:
            cam = self.lane_cam[f'lane_{lane}']

        cam_result = copy.deepcopy(final_result[cam])
        Container_INFO = get_global('Container_INFO')
        Container_INFO['container_num_center'] = cam_result['center']['container_info']
        Container_INFO['thresh_center'] = cam_result['center']['container_score']

        VI002 = get_global('VI002')
        if VI002['data']['truck_recognize_results'][lane - 1]['recognizeResults'][1] is not None:
            truck_dir = VI002['data']['truck_recognize_results'][lane - 1]['recognizeResults'][1]['result']
            if cam == 'cam_155':
                if (truck_dir == '1' and lane > 4) or (truck_dir == '0' and lane <= 4):
                    if cam_result['rear']['container_info'] is not None:
                        Container_INFO['container_num_front'] = cam_result['rear']['container_info']
                        Container_INFO['thresh_front'] = cam_result['rear']['container_score']

                    if cam_result['front']['container_info'] is not None:
                        Container_INFO['container_num_rear'] = cam_result['front']['container_info']
                        Container_INFO['thresh_rear'] = cam_result['front']['container_score']
                else:
                    if cam_result['front']['container_info'] is not None:
                        Container_INFO['container_num_front'] = cam_result['front']['container_info']
                        Container_INFO['thresh_front'] = cam_result['front']['container_score']
                    if cam_result['rear']['container_info'] is not None:
                        Container_INFO['container_num_rear'] = cam_result['rear']['container_info']
                        Container_INFO['thresh_rear'] = cam_result['rear']['container_score']
            else:
                if (truck_dir == '1' and lane >= 4) or (truck_dir == '0' and lane < 4):
                    if cam_result['rear']['container_info'] is not None:
                        Container_INFO['container_num_front'] = cam_result['rear']['container_info']
                        Container_INFO['thresh_front'] = cam_result['rear']['container_score']
                    if cam_result['front']['container_info'] is not None:
                        Container_INFO['container_num_rear'] = cam_result['front']['container_info']
                        Container_INFO['thresh_rear'] = cam_result['front']['container_score']
                else:
                    if cam_result['front']['container_info'] is not None:
                        Container_INFO['container_num_front'] = cam_result['front']['container_info']
                        Container_INFO['thresh_front'] = cam_result['front']['container_score']
                    if cam_result['rear']['container_info'] is not None:
                        Container_INFO['container_num_rear'] = cam_result['rear']['container_info']
                        Container_INFO['thresh_rear'] = cam_result['rear']['container_score']
        else:
            Container_INFO['container_num_front'] = []
            Container_INFO['thresh_front'] = 0.0
            Container_INFO['container_num_rear'] = []
            Container_INFO['thresh_rear'] = 0.0
            Container_INFO['container_num_center'] = []
            Container_INFO['thresh_center'] = 0.0
        print('============================')
        print(Container_INFO)
        set_global('Container_INFO', Container_INFO)

    def if_cam_do_rec(self):
        judge_dict = copy.deepcopy(self.cams_obj_lst)
        need_renewVI002 = False
        for cam, cam_result in judge_dict.items():
            for pos, pos_result in cam_result.items():
                if pos_result['need_rec'] > 4:
                    containernum, iso, score = self.cemian_ocr_process.process_imgs([pos_result["crop_img"]])
                    print(containernum, iso, score, pos)
                    if score is None:
                        score = [0.0, 0.0]
                    # 置信度高的
                    if float(score[0]) > float(pos_result["container_score"][0]):
                        pos_result["container_info"] = [containernum, iso]
                        pos_result["container_score"] = score
                        need_renewVI002 = True

                    # if pos_result["container_info"] is not None:
                    #     _temp = None
                    #     if pos == 'front' and cam_result['rear']['container_info'] is not None:
                    #         _temp = cam_result['rear']['container_info'][0]
                    #     elif pos == 'rear' and cam_result['front']['container_info'] is not None:
                    #         _temp = cam_result['front']['container_info'][0]

                    #     if _temp is not None:
                    #         # 如果前后箱号相等，本次全部更新
                    #         if _temp == containernum:
                    #             pos_result["container_info"] = [containernum, iso]
                    #             pos_result["container_score"] = float(score[0])
                    #             need_renewVI002 = True

                    # 需要更新的时候进行一次保存
                    if need_renewVI002:
                        # print(containernum, iso, score)
                        datetime = pos_result["timestamp"]
                        cv2.imwrite(os.path.join(config_det_cemian.RESULT_DIR, f"frame_{datetime}.jpg"), \
                                    pos_result["keyframe"])
                        cv2.imwrite(
                            os.path.join(config_det_cemian.RESULT_DIR,
                                         f"{pos}_crop_{datetime}_{containernum}_{iso}.jpg"), \
                            pos_result["crop_img"])

        self.cams_obj_lst = copy.deepcopy(judge_dict)

        return need_renewVI002

    def run(self):
        guide_count = 0
        last_time = time.time()
        while True:
            try:
                time.sleep(0.03)
                blank = np.zeros((2160, 3840), dtype=np.uint8)
                ret_165, frame_165 = self.device_165.read()
                if not ret_165:
                    frame_165 = blank

                if frame_165.shape[:2] != (2160, 3840):
                    frame_165 = cv2.resize(frame_165, (3840, 2160))

                ret_155, frame_155 = self.device_155.read()
                if not ret_155:
                    frame_155 = blank
                if frame_155.shape[:2] != (2160, 3840):
                    frame_155 = cv2.resize(frame_155, (3840, 2160))

                ret_153, frame_153 = self.device_153.read()
                if not ret_153:
                    frame_153 = blank
                if frame_153.shape[:2] != (2160, 3840):
                    frame_153 = cv2.resize(frame_153, (3840, 2160))

                ret_151, frame_151 = self.device_151.read()
                if not ret_151:
                    frame_151 = blank
                if frame_151.shape[:2] != (2160, 3840):
                    frame_151 = cv2.resize(frame_151, (3840, 2160))

                ret_163, frame_163 = self.device_163.read()
                if not ret_163:
                    frame_163 = blank
                if frame_163.shape[:2] != (2160, 3840):
                    frame_163 = cv2.resize(frame_163, (3840, 2160))

                ret_161, frame_161 = self.device_161.read()
                if not ret_161:
                    frame_161 = blank
                if frame_161.shape[:2] != (2160, 3840):
                    frame_161 = cv2.resize(frame_161, (3840, 2160))

                now_time = time.time()
                if now_time - last_time >= 300:
                    last_time = now_time
                    check_res_165 = check_img_cam(self.device_165, 'cam_165', frame_165)
                    check_res_163 = check_img_cam(self.device_163, 'cam_163', frame_163)
                    check_res_161 = check_img_cam(self.device_161, 'cam_161', frame_161)
                    check_res_155 = check_img_cam(self.device_155, 'cam_155', frame_155)
                    check_res_153 = check_img_cam(self.device_153, 'cam_153', frame_153)
                    check_res_151 = check_img_cam(self.device_151, 'cam_151', frame_151)
                    if check_res_165 != 0:
                        set_VI003(check_res_165)
                    if check_res_163 != 0:
                        set_VI003(check_res_163)
                    if check_res_161 != 0:
                        set_VI003(check_res_161)
                    if check_res_155 != 0:
                        set_VI003(check_res_155)
                    if check_res_153 != 0:
                        set_VI003(check_res_153)
                    if check_res_151 != 0:
                        set_VI003(check_res_151)

                cam_frame = {
                    'cam_165': frame_165,
                    'cam_155': frame_155,
                    'cam_153': frame_153,
                    'cam_151': frame_151,
                    'cam_163': frame_163,
                    'cam_161': frame_161
                }

                # 根据引导任务的车道有车情况来判断用哪个相机来进行侧面箱号识别
                self.judge_which_cam_det()

                need_det_frame = {}

                # 相机和帧对应上，后续侧面的判断逻辑要对应专门的相机分开写
                # print(self.need_det_cam)
                if len(self.need_det_cam) < 1:
                    self.need_det_cam = ['cam_165']
                for cam in self.need_det_cam:
                    need_det_frame[cam] = cam_frame[cam]

                self.get_cam_obj(need_det_frame)

                MC301 = get_global('MC301')
                lane_id = int(MC301['data']['guide_mission']['lane_id'])

                VI007 = get_global('VI007')
                guide_state = int(VI007["data"]["lane_guide_status"][lane_id - 1]['guide_state'])

                if self.if_cam_do_rec():
                    renew_result = self.get_lane_result(lane_id)
                    if renew_result is not None:
                        need_det_cam = copy.deepcopy(self.need_det_cam)
                        renew_VI002(renew_result, need_det_cam)
                        self.save_container(lane_id, renew_result)

                self.need_det_cam = []
                MC001 = get_global('MC001')
                if MC001['data']['lock_state'] == 1:
                    self.refresh_cams_obj_lst()

                # 第一次引导到位，强制刷新一次
                if guide_state == 2:
                    guide_count += 1
                    if guide_count == 1:
                        self.refresh_cams_obj_lst()
                else:
                    guide_count = 0

            except Exception as error:
                exception_traceback = traceback.format_exc()
                error_logger.error(f'{type(error).__name__}: {error}\n detail: {exception_traceback}')
                continue


if __name__ == '__main__':
    det_test = cemian_ocr()
    det_test.run()
