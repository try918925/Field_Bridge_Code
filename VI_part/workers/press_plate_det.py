import copy
from pathlib import Path
import sys
import os

FILE = Path(__file__).resolve()
ROOT = FILE.parents[1]  # 
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative

from global_info import *
from initializers import *
import configs.config_det_plate as config_det_press_plate
from algorithms.yolov5.predictor.det_predictor import YOLOv5Detector
from configs.cam_info import CAMERA_DICT
from configs.lane_info import LANE_INFO
import traceback
import threading
import time
import cv2
import json
import uuid

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

class press_plate(threading.Thread):
    def __init__(self, ):
        super().__init__()
        self.press_plate_detector = YOLOv5Detector.from_config(config_det_press_plate)

        self.cams_dict = {
            'cam_100': None,  # cam device
            'cam_104': None
        }

        self.init_cams()

        self.device_100 = self.cams_dict['cam_100']
        self.device_104 = self.cams_dict['cam_104']

        self.cams_result = {
            'cam_100': [],
            'cam_104': []
        }

        self.used_result = {
            'cam_100': {'now_count': 0, 'frame_count': 0},
            'cam_104': {'now_count': 0, 'frame_count': 0}
        }

    def refresh_used_result(self):
        self.used_result = {
            'cam_100': {'now_count': 0, 'frame_count': 0},
            'cam_104': {'now_count': 0, 'frame_count': 0}
        }

    def refresh_cam_obj(self):
        self.cams_result = {
            'cam_100': [],
            'cam_104': []
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

    def process_result(self):
        cam_100_lst = []
        cam_100_center = 0
        cam_104_lst = []
        cam_104_center = 0
        for key, item in self.cams_result.items():
            if len(item[0]) > 0:
                for class_id, class_name, score, p1p2, oxywh in item[0]:
                    if class_name == 'hanger':
                        if key == 'cam_100':
                            cam_100_center = oxywh[1]
                        else:
                            cam_104_center = oxywh[1]
                    if class_name == 'target':
                        if key == 'cam_100':
                            cam_100_lst.append(oxywh[1])
                        else:
                            cam_104_lst.append(oxywh[1])

        for i in cam_100_lst:
            if i > cam_100_center:
                self.used_result['cam_100']['now_count'] += 1

        for i in cam_104_lst:
            if i < cam_104_center:
                self.used_result['cam_104']['now_count'] += 1

    def get_all_obj(self, img_lst):
        # 对所有图像进行推断
        inference_results = self.press_plate_detector.infer(img_lst)
        camera_ids = ['cam_100', 'cam_104']
        for index, cam_id in enumerate(camera_ids):
            self.cams_result[cam_id] = copy.deepcopy([inference_results[index], img_lst[index]])
        self.process_result()

    def judge_result(self):
        temp_result = copy.deepcopy(self.used_result)
        # print(temp_result)
        for key, item in temp_result.items():
            # print('================daobandaoban================')
            # print(key, temp_result[key]['now_count'])
            if temp_result[key]['now_count'] < 3:
                temp_result[key]['frame_count'] += 1
            else:
                temp_result[key]['frame_count'] = 0
            temp_result[key]['now_count'] = 0

            # print(temp_result[key]['frame_count'])
            # print('================daobandaoban================')
            if temp_result[key]['frame_count'] > 200:
                Ep = {
                    "exception_code": 'E206',  # int,异常代码
                    "detail": "Container will attack plate",  # string,具体信息描述
                    "happen_time": str(int(time.time() * 1000)),  # long, 时间戳,单位毫秒
                    "has_solved": False,  # bool,是否已解决
                    "solve_time": None  # long, 时间戳,单位毫秒
                }
                set_VI003(Ep)
        self.used_result = temp_result

    def run(self):
        try:
            while True:
                time.sleep(0.04)
                MC001 = get_global('MC001')
                MC301 = get_global('MC301')
                trolley_pos = MC001['data']['trolley_pos']
                trolley_height = MC001['data']['hoist_height']
                work_type = MC301['data']['guide_mission']['work_type']
                lane_id = MC301['data']['guide_mission']['lane_id']
                if LANE_INFO[f'lane_{int(lane_id)}']['center'] - 2.3 < trolley_pos < LANE_INFO[f'lane_{int(lane_id)}'][
                    'center'] + 2.3 and trolley_height < 10.0 and work_type == 'DSCH':
                # if True:
                    ret_100, frame_100 = self.device_100.read()
                    if not ret_100:
                        continue
                    if frame_100.shape[:2] != (2160, 3840):
                        frame_100 = cv2.resize(frame_100, (3840, 2160))

                    ret_104, frame_104 = self.device_104.read()
                    if not ret_104:
                        continue
                    if frame_104.shape[:2] != (2160, 3840):
                        frame_104 = cv2.resize(frame_104, (3840, 2160))

                    self.get_all_obj([frame_100, frame_104])
                    self.judge_result()
                    self.refresh_cam_obj()
                else:
                    self.refresh_used_result()
                    continue
        except Exception as error:
            exception_traceback = traceback.format_exc()
            error_logger.error(f'{type(error).__name__}: {error}\n detail: {exception_traceback}')
