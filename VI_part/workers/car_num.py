from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from pathlib import Path
import sys
import os
from shapely.geometry import Point, Polygon
from configs.cam_info import CAMERA_DICT

os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'

import traceback
import time
import uuid
import numpy as np
import cv2
import yaml
import os
import sys
import json
import socket
import threading

FILE = Path(__file__).resolve()
ROOT = FILE.parents[1]  # YOLOv5 root directory
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative

import copy
from cam_utils.camsdk import hksdk as camera_sdk
from algorithms.yolov5.predictor.det_predictor import YOLOv5Detector
from algorithms.ppocr.infer_rec import OCR_rec
from configs import config_det_carnum, road_polygon
from configs.lane_info import LANE_INFO
from global_info import *
from initializers import *



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


class InitLaneResult:
    def __init__(self):
        self.result = {
            'cam138': self.initialize_lanes(),
            'cam139': self.initialize_lanes(),
            'cam148': self.initialize_lanes(),
            'cam149': self.initialize_lanes()
        }

    def initialize_lane(self):
        return {
            "area": 0,
            "need_rec": 0,  # 初始为0, 有车号为1，开始无车号+=1, 至连续三帧无结果，
            "do_rec": False,  # 是否做了识别
            "keyframe": None,
            "crop_img": None,
            "crop_thresh": 0.0,
            "timestamp": 0,  # 毫秒
            "truck_id": None,
            "id_thresh": None,
            "has_car": False,
            "save_name": ''
        }

    def initialize_lanes(self):
        lanes = {}
        for i in range(1, 4):
            lanes[f'lane{i}'] = self.initialize_lane()
        return lanes


class car_num(threading.Thread):
    def __init__(self):
        super().__init__()

        self.det_carnum = YOLOv5Detector.from_config(config_det_carnum)
        self.rec_carnum = OCR_rec("./configs/carnum_en_PP-OCRv4_rec.yml")
        self.rec_carnum.load_checkpoint()

        self.cams_dict = {
            'cam_139': None,  # cam device
            'cam_149': None,
            'cam_138': None,
            'cam_148': None,
        }

        self.init_cams()

        self.device_139 = self.cams_dict['cam_139']
        self.device_138 = self.cams_dict['cam_138']
        self.device_149 = self.cams_dict['cam_149']
        self.device_148 = self.cams_dict['cam_148']

        self.cams_result = {
            'cam_139': [],
            'cam_149': [],
            'cam_138': [],
            'cam_148': [],
        }

        self.concat_result = {
            'lane1': {'area': 0, 'need_rec': 0, 'do_rec': False, 'keyframe': None, 'crop_img': None, 'crop_thresh': 0.0,
                      'timestamp': 0, 'truck_id': None, 'id_thresh': None, 'has_car': False, 'save_name': ''},
            'lane2': {'area': 0, 'need_rec': 0, 'do_rec': False, 'keyframe': None, 'crop_img': None, 'crop_thresh': 0.0,
                      'timestamp': 0, 'truck_id': None, 'id_thresh': None, 'has_car': False, 'save_name': ''},
            'lane3': {'area': 0, 'need_rec': 0, 'do_rec': False, 'keyframe': None, 'crop_img': None, 'crop_thresh': 0.0,
                      'timestamp': 0, 'truck_id': None, 'id_thresh': None, 'has_car': False, 'save_name': ''},
            'lane4': {'area': 0, 'need_rec': 0, 'do_rec': False, 'keyframe': None, 'crop_img': None, 'crop_thresh': 0.0,
                      'timestamp': 0, 'truck_id': None, 'id_thresh': None, 'has_car': False, 'save_name': ''},
            'lane5': {'area': 0, 'need_rec': 0, 'do_rec': False, 'keyframe': None, 'crop_img': None, 'crop_thresh': 0.0,
                      'timestamp': 0, 'truck_id': None, 'id_thresh': None, 'has_car': False, 'save_name': ''},
            'lane6': {'area': 0, 'need_rec': 0, 'do_rec': False, 'keyframe': None, 'crop_img': None, 'crop_thresh': 0.0,
                      'timestamp': 0, 'truck_id': None, 'id_thresh': None, 'has_car': False, 'save_name': ''}
        }

        self.TruckRecognizeResult_lst = []
        self.result = InitLaneResult().result

        self.cam_lane_lst = ['lane1', 'lane2', 'lane3']
        self.cam_lst = ['cam138', 'cam139', 'cam148', 'cam149']

    def if_refresh_lane_result(self):
        _lane_ = {
            'lane1': {
                'cam138': 'lane3',
                'cam148': 'lane3'
            },
            'lane2': {
                'cam138': 'lane2',
                'cam148': 'lane2'
            },
            'lane3': {
                'cam138': 'lane1',
                'cam148': 'lane1'
            },
            'lane4': {
                'cam139': 'lane1',
                'cam149': 'lane1'
            },
            'lane5': {
                'cam139': 'lane2',
                'cam149': 'lane2'
            },
            'lane6': {
                'cam139': 'lane3',
                'cam149': 'lane3'
            }
        }

        VI002 = get_global('VI002')
        if VI002['data']['truck_recognize_results'] is None:
            VI002['data']['truck_recognize_results'] = [None] * 6

        for i in range(len(VI002['data']['truck_recognize_results'])):
            # str
            # print(i, VI002['data']['truck_recognize_results'][i])
            if VI002['data']['truck_recognize_results'][i]['recognizeResults'] is None or \
                    len(VI002['data']['truck_recognize_results'][i]['recognizeResults']) == 0:
                VI002['data']['truck_recognize_results'][i]['recognizeResults'] = [None] * 8  # 8组识别结果

            # 车道上没有车
            # print(VI002['data']['truck_recognize_results'][i]['recognizeResults'][1])
            if VI002['data']['truck_recognize_results'][i]['recognizeResults'][1] is None or \
                    len(VI002['data']['truck_recognize_results'][i]['recognizeResults'][1]) < 1:
                # print('qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq')
                cam_dict = _lane_[f'lane{i + 1}']

                for cam, cam_lane in cam_dict.items():
                    self.result[cam][cam_lane] = {
                        "area": 0,
                        "need_rec": 0,  # 初始为0, 有车号为1，开始无车号+=1, 至连续三帧无结果，
                        "do_rec": False,  # 是否做了识别
                        "keyframe": None,
                        "crop_img": None,
                        "crop_thresh": 0.0,
                        "timestamp": 0,  # 毫秒
                        "truck_id": None,
                        "id_thresh": None,
                        "has_car": False,
                        "save_name": ''
                    }

    def refresh_concat(self, lane):
        self.concat_result[f'lane{lane}'] = {'area': 0, 'need_rec': 0, 'do_rec': False, 'keyframe': None,
                                             'crop_img': None, 'crop_thresh': 0.0,
                                             'timestamp': 0, 'truck_id': None, 'id_thresh': None, 'has_car': False,
                                             'save_name': ''}

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

    def lane_judge(self, point, cam_name):
        final_lane = 0

        if cam_name == '139':
            lane_56_l = road_polygon.car_num_56_left
            for i in range(3):
                pt = lane_56_l[f'{i + 4}']
                polygon = Polygon(pt)
                point = Point(point)
                if polygon.contains(point):
                    final_lane = i + 4
        elif cam_name == '149':
            lane_56_r = road_polygon.car_num_56_right
            for i in range(3):
                pt = lane_56_r[f'{i + 4}']
                polygon = Polygon(pt)
                point = Point(point)
                if polygon.contains(point):
                    final_lane = i + 4
        elif cam_name == '138':
            lane_12_l = road_polygon.car_num_12_left
            for i in range(3):
                pt = lane_12_l[f'{i + 1}']
                polygon = Polygon(pt)
                point = Point(point)
                if polygon.contains(point):
                    final_lane = i + 1
        elif cam_name == '148':
            lane_12_r = road_polygon.car_num_12_right
            for i in range(3):
                pt = lane_12_r[f'{i + 1}']
                polygon = Polygon(pt)
                point = Point(point)
                if polygon.contains(point):
                    final_lane = i + 1

        return final_lane

    def refresh_cams_result(self):
        self.cams_result = {
            'cam_139': [],
            'cam_149': [],
            'cam_138': [],
            'cam_148': [],
        }

    def get_wagon_obj(self, img_lst):
        # 对所有图像进行推断
        inference_results = self.det_carnum.infer(img_lst)
        camera_ids = ['cam_138', 'cam_139', 'cam_148', 'cam_149']
        for index, cam_id in enumerate(camera_ids):
            # [obj_lst, frame]
            self.cams_result[cam_id].extend([inference_results[index], img_lst[index]])
        self.all_cam_has_car()

    # 四个相机的检测结果，是否在目标区域内结果，如果有，记录下来
    def all_cam_has_car(self):
        for key, item in self.cams_result.items():
            self.get_det_result(key.split('_')[-1], item)
        self.refresh_cams_result()

    # 整理每个车道的结果并记录
    def get_det_result(self, cam, item):
        y_range = {
            '138': [10, 2000],
            '139': [10, 2000],
            '148': [10, 2000],
            '149': [10, 2000]
        }

        obj_lst = item[0]
        frame = item[1]

        # print('==============================')
        # print(cam, obj_lst)
        # print('==============================')
        if len(obj_lst) > 0:
            for class_id, class_name, score, p1p2, oxywh in obj_lst:
                if class_name == 'wagon-number':
                    x1, y1, x2, y2 = map(int, p1p2)
                    xo, yo, w, h = oxywh
                    area = w * h
                    now_lane = self.lane_judge(oxywh[:2], cam)

                    if now_lane > 3:
                        now_lane = now_lane - 3
                    if now_lane == 0:
                        break

                    # 取置信度更高的，面积较大的
                    if (area > 400) and (area >= self.result[f'cam{cam}'][f'lane{now_lane}']["area"]) \
                            and (score >= self.result[f'cam{cam}'][f'lane{now_lane}']['crop_thresh']) \
                            and (y_range[cam][0] < yo < y_range[cam][1]) and (3840 > xo > 0):
                        self.result[f'cam{cam}'][f'lane{now_lane}']['has_car'] = True
                        self.result[f'cam{cam}'][f'lane{now_lane}']["need_rec"] += 1
                        self.result[f'cam{cam}'][f'lane{now_lane}']["area"] = area

                        self.result[f'cam{cam}'][f'lane{now_lane}']["keyframe"] = frame
                        self.result[f'cam{cam}'][f'lane{now_lane}']["crop_img"] = frame[y1:y2, x1:x2]
                        self.result[f'cam{cam}'][f'lane{now_lane}']["crop_thresh"] = score
                        self.result[f'cam{cam}'][f'lane{now_lane}']["timestamp"] = int(time.time() * 1000)

    # 判断每个车道的结果是否要做ocr
    def need_ocr(self):
        for cam in self.cam_lst:
            for lane in self.cam_lane_lst:
                lane_dict = copy.deepcopy(self.result[cam][lane])

                if lane_dict['need_rec'] >= 3 and lane_dict['do_rec'] is False:
                    if len(lane_dict['crop_img']) > 0:
                        predict_use = lane_dict['crop_img']
                        ocr_str, score_str = self.rec_carnum.predict([predict_use])
                        flip_img = cv2.flip(predict_use, -1)
                        ocr_str1, score_str1 = self.rec_carnum.predict([flip_img])

                        if float(score_str1) > float(score_str):
                            ocr_str = ocr_str1
                            self.result[cam][lane]["truck_id"] = ocr_str
                            self.result[cam][lane]["id_thresh"] = score_str1
                        self.result[cam][lane]["truck_id"] = ocr_str
                        self.result[cam][lane]["id_thresh"] = score_str

                        print('-----------------------------------')
                        print(lane)
                        print(ocr_str)
                        print('-----------------------------------')

                        self.result[cam][lane]["do_rec"] = True
                        datatime = int(time.time() * 1000)
                        self.result[cam][lane]["timestamp"] = datatime

                        save_pth = os.path.join(config_det_carnum.RESULT_DIR, f"frame_{datatime}_{ocr_str}.jpg")
                        self.result[cam][lane]["save_name"] = save_pth

                        cv2.imwrite(os.path.join(config_det_carnum.RESULT_DIR, f"frame_{datatime}_{ocr_str}.jpg"), \
                                    self.result[cam][lane]["keyframe"])

                        cv2.imwrite(os.path.join(config_det_carnum.RESULT_DIR, f"crop_{datatime}_{ocr_str}.jpg"), \
                                    self.result[cam][lane]["crop_img"])

    def get_final_result(self):
        _lane_ = {
            'lane1': {
                'cam138': 'lane3',
                'cam148': 'lane3'
            },
            'lane2': {
                'cam138': 'lane2',
                'cam148': 'lane2'
            },
            'lane3': {
                'cam138': 'lane1',
                'cam148': 'lane1'
            },
            'lane4': {
                'cam139': 'lane1',
                'cam149': 'lane1'
            },
            'lane5': {
                'cam139': 'lane2',
                'cam149': 'lane2'
            },
            'lane6': {
                'cam139': 'lane3',
                'cam149': 'lane3'
            }
        }

        tmp_result = {
            'lane1': None,
            'lane2': None,
            'lane3': None,
            'lane4': None,
            'lane5': None,
            'lane6': None,
        }

        for key, item in _lane_.items():
            item_keys = list(item.keys())
            item_values = list(item.values())
            result1 = copy.deepcopy(self.result[item_keys[0]][item_values[0]])
            result2 = copy.deepcopy(self.result[item_keys[1]][item_values[1]])

            tmp_result[key] = self.two_result_concate(result1, result2)

        return tmp_result

    def two_result_concate(self, result1, result2):
        truck_id1 = result1['truck_id']
        truck_id2 = result2['truck_id']
        # print(truck_id1, truck_id2)
        if truck_id1 == truck_id2:
            return result1
        elif truck_id1 is None and truck_id2 is not None:
            return result2
        elif truck_id1 is not None and truck_id2 is None:

            return result1
        else:
            if float(result1['id_thresh']) > float(result2['id_thresh']):
                return result1
            else:
                return result2

    def compare_dicts(self, dict1):
        result = {}
        for lane in dict1.keys():
            if lane in self.concat_result:
                # print(lane, dict1[lane]['truck_id'], self.concat_result[lane]['truck_id'])
                if dict1[lane]['truck_id'] == self.concat_result[lane]['truck_id']:
                    result[lane] = True
                else:
                    id_thresh1 = dict1[lane]['id_thresh']
                    id_thresh2 = copy.deepcopy(self.concat_result[lane]['id_thresh'])
                    if id_thresh1 is not None and id_thresh2 is not None:
                        if dict1[lane]['id_thresh'] >= self.concat_result[lane]['id_thresh'] or \
                                dict1[lane]['area'] >= self.concat_result[lane]['area']:
                            result[lane] = False
                    elif id_thresh1 is not None and id_thresh2 is None:
                        result[lane] = False
                    else:
                        result[lane] = True

        self.concat_result = copy.deepcopy(dict1)

        # print(result)
        return result

    def run(self, ):
        last_time = time.time()
        while True:
            time.sleep(0.04)
            try:
                blank = np.zeros((2160, 3840), dtype=np.uint8)
                ret_138, frame_138 = self.device_138.read()
                if not ret_138:
                    # continue
                    frame_138 = blank
                if frame_138.shape[:2] != (2160, 3840):
                    frame_138 = cv2.resize(frame_138, (3840, 2160))

                ret_139, frame_139 = self.device_139.read()
                if not ret_139:
                    # print('Not get 139')
                    frame_139 = blank
                    # continue
                if frame_139.shape[:2] != (2160, 3840):
                    frame_139 = cv2.resize(frame_139, (3840, 2160))

                ret_148, frame_148 = self.device_148.read()
                if not ret_148:
                    frame_148 = blank
                    # continue
                if frame_148.shape[:2] != (2160, 3840):
                    frame_148 = cv2.resize(frame_148, (3840, 2160))

                ret_149, frame_149 = self.device_149.read()
                if not ret_149:
                    # print('Not get 149')
                    # continue
                    frame_149 = blank
                if frame_149.shape[:2] != (2160, 3840):
                    frame_149 = cv2.resize(frame_149, (3840, 2160))


                now_time = time.time()
                if now_time - last_time >= 300:
                    last_time = now_time
                    check_res_138 = check_img_cam(self.device_138, 'cam_138', frame_138)
                    check_res_139 = check_img_cam(self.device_139, 'cam_139', frame_139)
                    check_res_148 = check_img_cam(self.device_148, 'cam_148', frame_148)
                    check_res_149 = check_img_cam(self.device_149, 'cam_149', frame_149)
                    if check_res_138 != 0:
                        set_VI003(check_res_138)
                    if check_res_139 != 0:
                        set_VI003(check_res_139)
                    if check_res_148 != 0:
                        set_VI003(check_res_148)
                    if check_res_149 != 0:
                        set_VI003(check_res_149)

                self.get_wagon_obj([frame_138, frame_139, frame_148, frame_149])
                self.need_ocr()
                now_result = self.get_final_result()

                compare_res = self.compare_dicts(now_result)

                self.if_refresh_lane_result()

                # 如果有不同数据出现
                if False in compare_res.values():
                    # 车道上集卡识别结果需要更新
                    VI002 = get_global('VI002')
                    if VI002['data']['truck_recognize_results'] is None:
                        VI002['data']['truck_recognize_results'] = [None] * 6  # 6

                    need_renew = True
                    for i in range(len(VI002['data']['truck_recognize_results'])):
                        truck_lane_id = VI002['data']['truck_recognize_results'][i]['lane_id']  # str
                        # print(i, VI002['data']['truck_recognize_results'][i])
                        if VI002['data']['truck_recognize_results'][i]['recognizeResults'] is None or \
                                len(VI002['data']['truck_recognize_results'][i]['recognizeResults']) == 0:
                            VI002['data']['truck_recognize_results'][i]['recognizeResults'] = [None] * 8  # 8组识别结果

                        lane_result = now_result[f'lane{i + 1}']
                        print(now_result[f'lane{i + 1}']['truck_id'], i + 1)
                        # 车道上没有车

                        if VI002['data']['truck_recognize_results'][i]['recognizeResults'][1] is None:
                            VI002['data']['truck_recognize_results'][i]['recognizeResults'][0] = None
                            VI002['data']['truck_recognize_results'][i]['recognizeResults'][2] = None
                            # lane_result['truck_id'] = None
                            self.refresh_concat(i + 1)

                        # trurck_id 赋值
                        # try:
                        #     if VI002['data']['truck_recognize_results'][i]['recognizeResults'][0] is None and \
                        #             lane_result['truck_id'] is not None:
                        #         need_renew = True
                        #     if VI002['data']['truck_recognize_results'][i]['recognizeResults'][0]["result"] is not None \
                        #             and lane_result['truck_id'] is not None:
                        #         if VI002['data']['truck_recognize_results'][i]['recognizeResults'][0]["result"] != \
                        #                 lane_result['truck_id']:
                        #             need_renew = True
                        # except Exception as error:
                        #     exception_traceback = traceback.format_exc()
                        #     error_logger.error(f'{type(error).__name__}: {error}\n detail: {exception_traceback}')


                        if lane_result['truck_id'] is not None:
                            VI002['data']['truck_recognize_results'][i]['recognizeResults'][0] = {
                                "item": "truck_id",
                                "state": 1,
                                "result": lane_result['truck_id'],
                                "images": [
                                    {
                                        "image": os.path.relpath(lane_result['save_name'], '/home/root123'),
                                        "datetime": lane_result['timestamp']
                                    }
                                ]
                            }
                            # trurck_type 赋值 目前只有内集卡, 其他项目可能需要增加内外集卡的分类
                            VI002['data']['truck_recognize_results'][i]['recognizeResults'][2] = {
                                "item": "truck_type",
                                "state": 1,
                                "result": "ITK",  # ITK内集卡，OTK外集卡，AIV无人集卡
                                "images": [
                                    {
                                        "image": os.path.relpath(lane_result['save_name'], '/home/root123'),
                                        "datetime": lane_result['timestamp']
                                    }
                                ]
                            }
                    # 更新VI002
                    VI002['msg_uid'] = str(uuid.uuid1())
                    VI002["timestamp"] = int(time.time() * 1000)
                    if need_renew:
                        VI2MC_pub.send_msg(json.dumps(VI002))
                        key_logger.info(f'Wagon-Number:  sendVI002:{VI002}')
                        set_global('VI002', VI002)

                    self.TruckRecognizeResult_lst = []
            except Exception as error:
                exception_traceback = traceback.format_exc()
                error_logger.error(f'{type(error).__name__}: {error}\n detail: {exception_traceback}')
                continue


if __name__ == '__main__':
    det_test = car_num()
    det_test.run()
