from pathlib import Path
import sys
import os

FILE = Path(__file__).resolve()
ROOT = FILE.parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative

import zmq
import json
import time
import uuid
import cv2
import os
import numpy as np
import socket
import threading
import traceback
import copy
from cam_utils.camsdk import hksdk as camera_sdk
from configs import config_det_guid
from configs.lane_info import LANE_INFO
from algorithms.yolov5.predictor.det_predictor import YOLOv5Detector
from global_info import *
from initializers import *
from configs.cam_info import CAMERA_DICT


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


class PreProcessImg:
    def calculate_M(trapezoid):
        rectangle = np.array([[0, 0], [1600, 0], [0, 1800], [1600, 1800]], dtype=np.float32)
        return cv2.getPerspectiveTransform(trapezoid, rectangle)

    cam_params = {
        '119': {
            'distortion_coeffs': np.array(
                [-2.17041889e+00, -9.59734151e+01, 2.68401705e-02, 2.63032028e-03, -4.07008640e+02]),
            'camera_matrix': np.array([[2.13243587e+04, 0.00000000e+00, 1.64599216e+03],
                                       [0.00000000e+00, 9.88544217e+03, 1.06588013e+03],
                                       [0.00000000e+00, 0.00000000e+00, 1.00000000e+00]]),
            'trapezoid': np.array([[1880, 435], [2950, 520], [1716, 1780], [3030, 1830]], dtype=np.float32),
            'M': calculate_M(np.array([[1880, 435], [2950, 520], [1716, 1780], [3030, 1830]], dtype=np.float32))
        },
        '115': {
            'distortion_coeffs': np.array(
                [-5.17041889e+00, -3.89734151e+01, 3.37001705e-01, 5.60032028e-03, -5.07000000e+02]),
            'camera_matrix': np.array([[2.13243587e+04, 0.00000000e+00, 1.64599216e+03],
                                       [0.00000000e+00, 9.88544217e+03, 1.06588013e+03],
                                       [0.00000000e+00, 0.00000000e+00, 1.00000000e+00]]),
            'trapezoid': np.array([[1633, 331], [2775, 328], [1573, 1868], [2801, 1830]], dtype=np.float32),
            'M': calculate_M(np.array([[1633, 331], [2775, 328], [1573, 1868], [2801, 1830]], dtype=np.float32))
        }
    }

    def __call__(self, img, cam):
        h, w = img.shape[:2]

        if cam not in self.cam_params:
            raise ValueError(f"错误相机：'{cam}'")

        params = self.cam_params[cam]

        new_camera_matrix, roi = cv2.getOptimalNewCameraMatrix(params['camera_matrix'],
                                                               params['distortion_coeffs'], (w, h), 0, (w, h))
        undistorted_img = cv2.undistort(img, params['camera_matrix'], params['distortion_coeffs'],
                                        None, new_camera_matrix)
        res_img = cv2.warpPerspective(undistorted_img, params['M'], (1600, 1800))

        return res_img


def truck_head_dis_judge(pos_dict):
    if pos_dict['car_front'] is None:
        pass
    else:
        if pos_dict['center'] is not None:
            dis = abs(pos_dict['car_front'][0][0] - pos_dict['center'][0])
            if dis < 350:
                Ep = {
                    "exception_code": 'E206',  # int,异常代码
                    "detail": f"catch center will attack truck head",  # string,具体信息描述
                    "happen_time": str(int(time.time())),  # long, 时间戳,单位毫秒
                    "has_solved": False,  # bool,是否已解决
                    "solve_time": None  # long, 时间戳,单位毫秒
                }
                set_VI003(Ep)


def renew_VI008(lane_id, car_target_x=25.15, car_target_y=0.3):
    # todo 引导任务对应完成后 需要更新这个字段
    VI008 = get_global('VI008')
    VI008["msg_uid"] = str(uuid.uuid1())
    VI008["timestamp"] = int(time.time() * 1000)
    VI008["data"]["lane_id"] = str(lane_id)
    VI008["data"]["has_car"] = True
    VI008["data"]["car_target_x"] = car_target_x
    VI008["data"]["car_target_y"] = car_target_y
    set_global('VI008', VI008)
    send_msg = str(json.dumps(VI008, ensure_ascii=False))
    VI2MC_pub.send_msg(send_msg)
    key_logger.info(f'Truck-Guide:  sendVI008:{VI008}')


def renew_VI007(lane_id, guide_state, truck_distance, truck_move_dir):
    MC001 = get_global('MC001')
    trolley_pos = MC001['data']['trolley_pos']

    no_renew = [0]

    if LANE_INFO['lane_6']['center'] - 2.3 < trolley_pos < LANE_INFO['lane_6']['center'] + 2.3:
        no_renew = [6]
    elif LANE_INFO['lane_5']['center'] - 2.3 < trolley_pos < LANE_INFO['lane_5']['center'] + 2.3:
        no_renew = [5]
    elif LANE_INFO['lane_4']['center'] - 2.3 < trolley_pos < LANE_INFO['lane_4']['center'] + 2.3:
        no_renew = [4]
    elif LANE_INFO['lane_1']['center'] - 2.3 < trolley_pos < LANE_INFO['lane_1']['center'] + 4.5:
        no_renew = [3, 2, 1]
    elif LANE_INFO['lane_2']['center'] - 2.3 < trolley_pos < LANE_INFO['lane_2']['center'] + 2.3:
        no_renew = [3, 2, 1]
    elif LANE_INFO['lane_3']['center'] - 2.3 < trolley_pos < LANE_INFO['lane_3']['center'] + 2.3:
        no_renew = [3, 2, 1]

    # # 如果小车进入陆侧3车道了，就不更新引导值
    # if LANE_INFO['lane_3']['center'] - 2.3 < trolley_pos < LANE_INFO['lane_3']['center'] + 2.3:
    #     no_renew = [3, 4, 5, 6]

    if int(lane_id) not in no_renew:
        GuideStatus = {
            "lane_id": str(lane_id),
            "guide_state": guide_state,  # 0=未引导 1=引导中 2=引导到位
            "truck_distance": truck_distance,  # 集卡距离作业位置行驶距离
            "truck_move_dir": truck_move_dir,  # 0=到位,1=面海向右,2=面海向左,3=不在视野中
            "has_truck": int(1)  # 0 无, 1有
        }

        # VI007 反馈引导状态
        VI007 = get_global('VI007')
        VI007["msg_uid"] = str(uuid.uuid1())
        VI007["timestamp"] = int(time.time() * 1000)
        VI007["data"]["lane_guide_status"][int(lane_id) - 1] = GuideStatus
        send_msg = str(json.dumps(VI007, ensure_ascii=False))
        VI2MC_pub.send_msg(send_msg)
        # key_logger.info(f'Truck-Guide:  sendVI007:{VI007}')
        set_global('VI007', VI007)


def renew_VI002(TruckRecognizeResultLst):
    MC001 = get_global('MC001')
    trolley_pos = MC001['data']['trolley_pos']

    no_renew = [0]

    if LANE_INFO['lane_6']['center'] - 2.3 < trolley_pos < LANE_INFO['lane_6']['center'] + 2.3:
        no_renew = [6]
    elif LANE_INFO['lane_5']['center'] - 2.3 < trolley_pos < LANE_INFO['lane_5']['center'] + 2.3:
        no_renew = [5]
    elif LANE_INFO['lane_4']['center'] - 2.3 < trolley_pos < LANE_INFO['lane_4']['center'] + 2.3:
        no_renew = [4]
    elif LANE_INFO['lane_2']['center'] - 2.3 < trolley_pos < LANE_INFO['lane_2']['center'] + 2.3:
        no_renew = [3, 2, 1]
    elif LANE_INFO['lane_3']['center'] - 2.3 < trolley_pos < LANE_INFO['lane_3']['center'] + 2.3:
        no_renew = [3, 2, 1]
    elif LANE_INFO['lane_1']['center'] - 2.3 < trolley_pos < LANE_INFO['lane_1']['center'] + 4.5:
        no_renew = [3, 2, 1]

    VI002 = get_global('VI002')

    if VI002['data']['truck_recognize_results'] is None:
        VI002['data']['truck_recognize_results'] = [None] * 6

    for i in range(len(VI002['data']['truck_recognize_results'])):
        if VI002['data']['truck_recognize_results'][i]['recognizeResults'] is None or \
                len(VI002['data']['truck_recognize_results'][i]['recognizeResults']) == 0:
            VI002['data']['truck_recognize_results'][i]['recognizeResults'] = [None] * 8

    VI002['msg_uid'] = str(uuid.uuid1())
    VI002["timestamp"] = int(time.time() * 1000)
    need_send = False
    # 为空：初始化一个VI002
    if len(TruckRecognizeResultLst) > 0:
        for TruckRecognizeResult in TruckRecognizeResultLst:
            for item in VI002['data']['truck_recognize_results']:
                if int(item['lane_id']) in no_renew:
                    continue
                else:
                    if int(item['lane_id']) == int(TruckRecognizeResult['lane_id']):

                        if item['recognizeResults'][1] is not None:
                            if (item['recognizeResults'][1]['result'] != TruckRecognizeResult['recognizeResults'][0][
                                'result']):
                                item['recognizeResults'][1] = TruckRecognizeResult['recognizeResults'][0]
                                need_send = True
                        else:
                            item['recognizeResults'][1] = TruckRecognizeResult['recognizeResults'][0]
                            need_send = True

                        if item['recognizeResults'][3] is not None:
                            if (item['recognizeResults'][3]['result'] != TruckRecognizeResult['recognizeResults'][2][
                                'result']):
                                item['recognizeResults'][3] = TruckRecognizeResult['recognizeResults'][2]
                                need_send = True
                        else:
                            item['recognizeResults'][3] = TruckRecognizeResult['recognizeResults'][2]
                            need_send = True
                        if item['recognizeResults'][4] is not None:
                            if (item['recognizeResults'][4]['result'] != TruckRecognizeResult['recognizeResults'][1][
                                'result']):
                                item['recognizeResults'][4] = TruckRecognizeResult['recognizeResults'][1]
                                need_send = True
                        else:
                            item['recognizeResults'][4] = TruckRecognizeResult['recognizeResults'][1]
                            need_send = True

    else:
        for item in VI002['data']['truck_recognize_results']:
            if int(item['lane_id']) in no_renew:
                continue
            else:
                if item['recognizeResults'][1] is not None or item['recognizeResults'][3] is not None or \
                        item['recognizeResults'][4] is not None:
                    item['recognizeResults'] = [None] * 8
                    need_send = True
                # item['recognizeResults'][3] = None
                # item['recognizeResults'][4] = None
    if need_send:
        print('------------------------guid Send------------------------')
        VI2MC_pub.send_msg(json.dumps(VI002))
        # key_logger.info(f'sendVI002:{VI002}')
        set_global('VI002', VI002)


def create_recognize_result(item, result, save_name, save_time):
    if result == -1:
        result_str = ""
    else:
        result_str = str(result)

    images = [{
        "image": os.path.relpath(save_name + ".jpg", '/home/root123'),
        "datetime": int(save_time)
    }]

    recognize_result = {
        "item": item,
        "state": 1,
        "result": result_str,
        "images": images
    }

    return recognize_result


# 单个车道的
def create_TruckRecognizeResult(recognize_result_lst, lane_id):
    TruckRecognizeResult = {
        "lane_id": str(lane_id),
        "recognizeResults": recognize_result_lst[:]  # 取所有元素
    }

    return TruckRecognizeResult


class det_guid(threading.Thread):
    def __init__(self, config: config_det_guid):
        super().__init__()
        self.det = YOLOv5Detector.from_config(config)
        self.result = None
        # True/False
        self.debug = config.DEBUG
        self.logdir = config.LOG_DIR
        if not os.path.exists(self.logdir):
            os.makedirs(self.logdir)
        self.cam_pre_process = PreProcessImg()

        self.cams_dict = {
            'cam_119': None,  # cam device
            'cam_115': None,
        }

        self.init_cams()

        self.device_119 = self.cams_dict['cam_119']
        self.device_115 = self.cams_dict['cam_115']

        self.save_cnt = 20

        self.lane_lst = ['lane_1', 'lane_2', 'lane_3', 'lane_4', 'lane_5', 'lane_6']

        # 119车道范围
        self.lanes_119 = {
            'lane_1': (121, 273),
            'lane_2': (360, 543),
            'lane_3': (595, 786),
            'lane_4': (740, 1020),
            'lane_5': (1280, 1500),
            'lane_6': (1540, 1700)
        }

        # 115车道范围
        self.lanes_115 = {
            'lane_1': (1550, 1720),
            'lane_2': (1300, 1500),
            'lane_3': (1000, 1300),
            'lane_4': (830, 1020),
            'lane_5': (300, 570),
            'lane_6': (100, 300)
        }

        # 初始化变量

        self.offside_pos = 0

        self.TruckRecognizeResult_lst = []

        # 0=未引导 1=引导中 2=引导到位
        self.guide_state = 0

        # 是否有任务下发
        self.no_task = True

        # 任务id
        self.msg_uid = "msg_uid_1234567890"

        # debug时存储记录信息(VI002)
        self.save_name, self.save_time = '', 0
        self.lane_index = 0

        self.truck_direction, self.truck_load_state, self.truck_height = -1, '', 0

        # 引导目标位于集卡位置 1=前, 2=中, 3=后, 0=自动判断 (无任务：-1)
        self.truck_pos = -1

        # truck_distance 引导移动距离
        # truck_move_dir 0=到位，1=面海向右，2=面海向左，3=不在视野中 (无任务:-1)
        (self.truck_distance, self.truck_move_dir) = 9999, -1

        self.guide_state_count = 0

        self.pos_dict = {
            "car": [],
            "car_front": [],
            "car_board": [],
            "target": [],
            "20_container": [],
            "40_container": [],
            "center": None,  # cx, cy, 抓/放位置
            "road_num": None,  # 车道
            "has_car": None,  # 是否有车
        }

        # 119相机所有检测结果
        self.all_obj_lst_119 = None

        # 115相机所有检测结果
        self.all_obj_lst_115 = None

        # 初始化119相机下车道检测到目标信息
        self.lane_obj_119 = {
            'lane_1': [],
            'lane_2': [],
            'lane_3': [],
            'lane_4': [],
            'lane_5': [],
            'lane_6': [],
            'frame': None
        }
        # 初始化115相机下车道检测到目标信息
        self.lane_obj_115 = {
            'lane_1': [],
            'lane_2': [],
            'lane_3': [],
            'lane_4': [],
            'lane_5': [],
            'lane_6': [],
            'frame': None
        }

        self.params = {
            '1': {
                'LOAD': {
                    'guid_c': 0,
                    'trolley_c': 0,
                },
                'DSCH': {
                    'guid_c': 0,
                    'trolley_c': 0,
                }
            },
            '2': {
                'LOAD': {
                    'guid_c': 725,
                    'trolley_c': 1380,
                },
                'DSCH': {
                    'guid_c': 752,
                    'trolley_c': 1383,
                },
                'trolley': 42.8,
            },
            '3': {
                'LOAD': {
                    'guid_c': 715,
                    'trolley_c': 1135,
                },
                'DSCH': {
                    'guid_c': 730,
                    'trolley_c': 1138,
                },
                'trolley': 38.40,
            },
            '4': {
                'LOAD': {
                    'guid_c': 680,
                    'trolley_c': 868,
                },
                'DSCH': {
                    'guid_c': 685,
                    'trolley_c': 877,
                },
                'trolley': 34.21,
            },
            '5': {
                'LOAD': {
                    'guid_c': 682,
                    'trolley_c': 1384,
                },
                'DSCH': {
                    'guid_c': 713,
                    'trolley_c': 1402,
                },
                'trolley': 25.12,
            },
            '6': {
                'LOAD': {
                    'guid_c': 686,
                    'trolley_c': 1647,
                },
                'DSCH': {
                    'guid_c': 691,
                    'trolley_c': 1654,
                },
                'trolley': 21.48,
            },

        }

    # 刷新pos_dict
    def refresh_pos_dict(self):
        self.pos_dict = {
            "car": [],
            "car_front": [],
            "car_board": [],
            "target": [],
            "20_container": [],
            "40_container": [],
            "center": None,  # cx, cy, 抓/放位置
            "road_num": None,  # 车道
            "has_car": None,  # 是否有车
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

    # 得到一条车道上的pos_dict
    def get_lane_pos_dict(self, obj_lst):
        # 刷新pos_dict，确保没有别的信息干扰
        self.pos_dict = {
            "car": [],
            "car_front": [],
            "car_board": [],
            "target": [],
            "20_container": [],
            "40_container": [],
            "center": None,  # cx, cy, 抓/放位置
            "road_num": None,  # 车道
            "has_car": None,  # 是否有车
            "f_container": [],
            "r_container": []
        }

        for _, class_name, _, _, oxywh in obj_lst:
            if class_name in self.pos_dict:
                self.pos_dict[class_name].append(oxywh)

    def select_truck_head(self):
        TruckHeadRecognizeResult = get_global('TruckHeadRecognizeResult')
        obj119 = copy.deepcopy(self.lane_obj_119)
        obj115 = copy.deepcopy(self.lane_obj_115)
        for lane, obj_lst in obj119.items():
            if lane != 'frame':
                if int(lane.split('lane_')[-1]) > 3:
                    TruckHeadRecognizeResult[lane.split('lane_')[-1]] = obj_lst

        for lane, obj_lst in obj115.items():
            if lane != 'frame':
                if int(lane.split('lane_')[-1]) < 4:
                    TruckHeadRecognizeResult[lane.split('lane_')[-1]] = obj_lst

        set_global('TruckHeadRecognizeResult', TruckHeadRecognizeResult)

    # 得到按车道划分对应的obj:
    # lane_obj_119['lane_5'] = obj_lane5_list
    def get_road_obj(self, img_lst):
        inference_results = self.det.infer(img_lst)
        self.all_obj_lst_119 = copy.deepcopy(inference_results[0])
        self.all_obj_lst_115 = copy.deepcopy(inference_results[1])
        # print(self.all_obj_lst_115)
        for cam, obj_lst in [('119', self.all_obj_lst_119), ('115', self.all_obj_lst_115)]:
            self.check_laneid(obj_lst, cam, img_lst)

        self.select_truck_head()

    # 根据车道划分检测结果
    def check_laneid(self, obj_lst, cam, img_lst):
        if cam == '119':
            self.lane_obj_119['frame'] = img_lst[0]
            lanes = self.lanes_119
            lane_obj = self.lane_obj_119
        elif cam == '115':
            self.lane_obj_115['frame'] = img_lst[1]
            lanes = self.lanes_115
            lane_obj = self.lane_obj_115
        else:
            return

        for obj in obj_lst:
            class_id, class_name, score, p1p2, oxywh = obj
            bbox_y = oxywh[1]

            for lane, (min_y, max_y) in lanes.items():
                if min_y < bbox_y < max_y:
                    lane_obj[lane].append((obj))
                    break

        ##########################
        # 得到每个车道对应的车头的obj
        # 传给车头防砸线程，

        # print(self.lane_obj_115)
        # print(self.lane_obj_119)

    # 车道上是否有车判断
    # 车道上是否有目标车辆的判断：
    # 如果识别到car —— 车道上有车
    # 如果没识别到car，但识别到了car_front和别的（车板或者车厢） —— 车道上有车
    # 如果没识别到car，没识别到car_front（单箱吊后箱可能车头会出视野）但识别到了车板或者target或者container↓
    # 根据任务判断 —— 单箱吊后箱：车道上有车，其他：没车
    def lane_has_car(self, obj_lst, lane):
        # 得到这个车道的pos_dict
        self.get_lane_pos_dict(obj_lst)
        # print('=============================')
        # print(lane, obj_lst, self.truck_pos)
        # print('=============================')
        if len(self.pos_dict['car']) > 0 or len(self.pos_dict['car_front']) > 0:
            self.pos_dict['has_car'] = True
        else:
            if len(self.pos_dict['car_front']) > 0 and (
                    len(self.pos_dict['car_board']) > 0 or
                    len(self.pos_dict['20_container']) > 0 or
                    len(self.pos_dict['40_container']) > 0 or
                    len(self.pos_dict['target']) > 0):
                self.pos_dict['has_car'] = True
            # 如果没识别到车头和车身，且当前任务是后箱作业：
            elif len(self.pos_dict['car_front']) < 1 and self.truck_pos == 3:
                if len(self.pos_dict['20_container']) > 0 or \
                        len(self.pos_dict['car_board']) > 0 or \
                        len(self.pos_dict['target']) > 0 or \
                        len(self.pos_dict['40_container']) > 0:
                    self.pos_dict['has_car'] = True

            else:
                self.pos_dict['has_car'] = False

        if not self.pos_dict['has_car'] and not self.no_task:
            self.truck_move_dir = 3

        elif self.pos_dict['has_car']:
            if self.debug:  # 视野内有车时, 对应图片存档
                save_dir = os.path.join(self.logdir, self.msg_uid)
                if not os.path.exists(save_dir):
                    os.makedirs(save_dir)

                self.save_time = int(time.time() * 1000)
                self.save_name = os.path.join(save_dir, f"{self.save_time}")
                if self.pos_dict['car_front'] is not None and len(self.pos_dict['car_front']) > 0:
                    if int(self.lane_lst.index(lane)) < 3:
                        cv2.imwrite(self.save_name + ".jpg", self.lane_obj_115['frame'])
                        with open(self.save_name + ".txt", "a", encoding='utf-8') as f:
                            f.write(str(self.all_obj_lst_115))
                    else:
                        cv2.imwrite(self.save_name + ".jpg", self.lane_obj_119['frame'])
                        with open(self.save_name + ".txt", "a", encoding='utf-8') as f:
                            f.write(str(self.all_obj_lst_119))

    # 先判断车道是否有车，如果有车则进行这一步
    # 判断车头朝向, 输入一个车道的obj_lst
    def get_car_front_dir(self):

        # 0-底端（面海向左）1-高端（面海向右）
        truck_direction = -1

        if len(self.pos_dict['car_front']) > 0:
            car_front_x = self.pos_dict['car_front'][0][0]

            # 检测车、20尺箱子、40尺箱子和车板的x坐标
            entities = ['20_container', '40_container', 'car_board', 'target', 'car']
            entity_x_coords = {entity: self.pos_dict[entity][0][0] for entity in entities if
                               len(self.pos_dict[entity]) > 0}

            # 根据优先级依次检查各个实体的x坐标
            for entity in entities:
                if entity in entity_x_coords:
                    truck_direction = 1 if car_front_x > entity_x_coords[entity] else 0
                    break
        # 得到带箱状态和车头朝向
        truck_load_state, truck_height = self.get_truck_load_state()

        return truck_direction, truck_load_state, truck_height

    # 判断集卡带箱状态, 在得到车头朝向之后判断，和车头朝向共用pos_dict
    def get_truck_load_state(self):
        truck_height, truck_load_state = None, None
        # 000=无箱 100=前20尺 001=后20尺 010=中20尺 111=大箱40尺 121=大箱45尺  101=双箱
        # 5尺 大约 95pix 左右
        if len(self.pos_dict['40_container']) > 0:
            if self.pos_dict['40_container'][0][2] > 880:
                truck_load_state = '121'  # 大箱45尺
            else:
                truck_load_state = '111'  # 大箱40尺

        elif len(self.pos_dict['20_container']) == 0 and len(self.pos_dict['40_container']) == 0:
            truck_load_state = '000'  # 无箱

        elif len(self.pos_dict['20_container']) == 1:
            if self.pos_dict['car_front'] is not None and len(self.pos_dict['car_front']) > 0:
                if abs(self.pos_dict['20_container'][0][0] - self.pos_dict['car_front'][0][0]) < 600:
                    truck_load_state = '100'  # 前20尺
                else:
                    truck_load_state = '001'
            else:
                if self.pos_dict['20_container'][0][2] < 600:
                    truck_load_state = '001'  # 后20尺
                else:
                    if self.pos_dict['20_container'][0][2] > 880:
                        truck_load_state = '121'
                    else:
                        truck_load_state = '111'
        else:
            truck_load_state = '101'  # 双箱

        truck_height = 1.5 if truck_load_state == '000' else 4.5

        return truck_load_state, truck_height

    # 小车移动到目标位置上方0.5m内进行切换相机判断是否移动
    def convert_cam(self, lane_id):
        MC001 = get_global('MC001')
        trolley_pos = MC001['data']['trolley_pos']
        trolley_height = MC001['data']['hoist_height']
        # trolley_v = MC001['data']['rope_vel']
        if LANE_INFO[f'lane_{int(lane_id)}']['center'] - 2.3 < trolley_pos < LANE_INFO[f'lane_{int(lane_id)}'][
            'center'] + 2.3 and trolley_height < 10.0:
            # 根据 lane_id 的不同选择不同的车道
            if int(lane_id) < 4:
                offside_obj_lst = copy.deepcopy(self.lane_obj_119[f'lane_{lane_id}'])
            else:
                offside_obj_lst = copy.deepcopy(self.lane_obj_115[f'lane_{lane_id}'])

            # 提取车道对象列表中的位置信息

            temp_offside_pos = 0
            for _, class_name, _, _, oxywh in offside_obj_lst:
                if class_name == 'car_front':
                    temp_offside_pos = oxywh[0]

            if temp_offside_pos == 0:
                return

            # 如果 self.offside_pos 为空，则将 temp_offside_pos 赋值给它
            if self.offside_pos == 0:
                self.offside_pos = copy.deepcopy(temp_offside_pos)
            else:
                # 计算当前车头位置和上次位置之间的偏移量
                offset = abs(self.offside_pos - temp_offside_pos)
                # 如果最大偏移量大于80，则视为移动
                # print('=============================')
                # print(self.offside_pos, temp_offside_pos)
                # print(offset)
                # print('=============================')
                if offset > 150:
                    # print('11111111111111111111111111')
                    # 感知抛个VI003的异常
                    E206 = {
                        "exception_code": 'E206',  # int,异常代码
                        # 引导到位，集卡发生移动
                        "detail": f"guide finished but truck move",  # string,具体信息描述
                        "happen_time": str(int(time.time() * 1000)),  # long, 时间戳,单位毫秒
                        "has_solved": False,  # bool,是否已解决
                        "solve_time": None  # long, 时间戳,单位毫秒
                    }
                    # 吊具低于一定高度时有防砸车头风险/砸集装箱
                    set_VI003(E206)
        else:
            self.offside_pos = 0

    def judge_f_r_container(self, lane_id):
        now_pos_dict = copy.deepcopy(self.pos_dict)

        # 4, 5, 6 ----- 119
        if lane_id > 3:
            if self.truck_direction == 0:
                if now_pos_dict['20_container'][0][0] > now_pos_dict['20_container'][1][0]:
                    self.pos_dict['f_container'] = now_pos_dict['20_container'][1]
                    self.pos_dict['r_container'] = now_pos_dict['20_container'][0]
                else:
                    self.pos_dict['f_container'] = now_pos_dict['20_container'][0]
                    self.pos_dict['r_container'] = now_pos_dict['20_container'][1]

            elif self.truck_direction == 1:
                if now_pos_dict['20_container'][0][0] > now_pos_dict['20_container'][1][0]:
                    self.pos_dict['f_container'] = now_pos_dict['20_container'][0]
                    self.pos_dict['r_container'] = now_pos_dict['20_container'][1]
                else:
                    self.pos_dict['f_container'] = now_pos_dict['20_container'][1]
                    self.pos_dict['r_container'] = now_pos_dict['20_container'][0]
        else:
            if self.truck_direction == 0:
                if now_pos_dict['20_container'][0][0] > now_pos_dict['20_container'][1][0]:
                    self.pos_dict['f_container'] = now_pos_dict['20_container'][0]
                    self.pos_dict['r_container'] = now_pos_dict['20_container'][1]
                else:
                    self.pos_dict['f_container'] = now_pos_dict['20_container'][1]
                    self.pos_dict['r_container'] = now_pos_dict['20_container'][0]

            elif self.truck_direction == 1:
                if now_pos_dict['20_container'][0][0] > now_pos_dict['20_container'][1][0]:
                    self.pos_dict['f_container'] = now_pos_dict['20_container'][1]
                    self.pos_dict['r_container'] = now_pos_dict['20_container'][0]
                else:
                    self.pos_dict['f_container'] = now_pos_dict['20_container'][0]
                    self.pos_dict['r_container'] = now_pos_dict['20_container'][1]

    def get_center_box(self, workflow, work_type):
        now_pos_dict = copy.deepcopy(self.pos_dict)
        # "work_type"  作业类型, LOAD-装船, DSCH-卸船
        # "workflow"   作业工艺 int类型 0:单箱吊; 1: 双箱吊;
        # 如果是单箱

        target_bbox = None
        x, y = now_pos_dict["center"]
        if workflow == 0:
            # 箱子
            if len(now_pos_dict["20_container"]) == 1 and now_pos_dict["20_container"][0][2] > 600:
                now_pos_dict['40_container'] = now_pos_dict['20_container']
            if work_type == 'LOAD':
                # oxywh
                if now_pos_dict["20_container"] is not None and len(now_pos_dict["20_container"]) > 0:
                    w, h = now_pos_dict["20_container"][0][2:]
                    target_bbox = (x, y, w, h)
                elif now_pos_dict["40_container"] is not None and len(now_pos_dict["40_container"]) > 0:
                    w, h = now_pos_dict["40_container"][0][2:]
                    target_bbox = (x, y, w, h)
            # 车板
            else:
                if now_pos_dict["car_board"] is not None and len(now_pos_dict["car_board"]) > 0:
                    h = now_pos_dict["car_board"][0][3]
                    w = now_pos_dict["car_board"][0][2] / 2
                    target_bbox = (x, y, w, h)
        # 双箱
        else:
            if work_type == 'LOAD':
                # oxywh
                if now_pos_dict["20_container"] is not None and len(now_pos_dict["20_container"]) > 1:
                    w = now_pos_dict["20_container"][0][2] * 2
                    h = now_pos_dict["20_container"][0][3]
                    target_bbox = (x, y, w, h)
            else:
                if now_pos_dict["car_board"] is not None and len(now_pos_dict["car_board"]) > 0:
                    w, h = now_pos_dict["car_board"][0][2:]
                    target_bbox = (x, y, w, h)
        return target_bbox

    # 抓放的计算部分
    def calc_center_part(self, truck_pos, work_type, workflow, lane_id, worksize):
        # 2-3车道情况下，暂时未在115相机下测试抓放，后续可能需要根据2-3车道下抓放时的视角进行一些补充

        # "truck_pos"  引导目标位于集卡位置 1=前, 2=中, 3=后, 0=自动判断
        # "work_type"  作业类型, LOAD-装船, DSCH-卸船
        # "workflow"   作业工艺 int类型 0:单箱吊; 1: 双箱吊;
        # "worksize"   作业箱尺寸 20,40

        # calc_parame[lane_id][truck_pos]

        calc_parame = {
            1: {
                0: {
                    'LOAD': {'left': {'has_other': 0, 'no_other': 0}, 'right': {'has_other': 0, 'no_other': 0}},
                    'DSCH': {'left': {'has_other': 0, 'no_other': 0}, 'right': {'has_other': 0, 'no_other': 0}}
                },
                1: {
                    'LOAD': {'left': {'has_other': 0, 'no_other': 0}, 'right': {'has_other': 0, 'no_other': 0}},
                    'DSCH': {'left': {'has_other': 0, 'no_other': 0}, 'right': {'has_other': 0, 'no_other': 0}}
                },
                2: {
                    'LOAD': {'left': {'has_other': 0, 'no_other': 0}, 'right': {'has_other': 0, 'no_other': 0}},
                    'DSCH': {'left': {'has_other': 0, 'no_other': 0}, 'right': {'has_other': 0, 'no_other': 0}}
                },
                3: {
                    'LOAD': {'left': {'has_other': 0, 'no_other': 0}, 'right': {'has_other': 0, 'no_other': 0}},
                    'DSCH': {'left': {'has_other': 0, 'no_other': 0}, 'right': {'has_other': 0, 'no_other': 0}}
                }
            },
            2: {
                0: {
                    'LOAD': {'left': {'has_other': 0, 'no_other': 0}, 'right': {'has_other': 0, 'no_other': 0}},
                    'DSCH': {'left': {'has_other': 0, 'no_other': 0}, 'right': {'has_other': 0, 'no_other': 0}}
                },
                1: {
                    'LOAD': {'left': {'has_other': 0, 'no_other': -8}, 'right': {'has_other': 0, 'no_other': 6}},
                    'DSCH': {'left': {'has_other': 0, 'no_other': 234}, 'right': {'has_other': 0, 'no_other': -135}}
                },
                2: {
                    'LOAD': {'left': {'has_other': 0, 'no_other': 2}, 'right': {'has_other': 0, 'no_other': 2}},
                    'DSCH': {'left': {'has_other': 0, 'no_other': 20}, 'right': {'has_other': 0, 'no_other': 50}}
                },
                3: {
                    'LOAD': {'left': {'has_other': 0, 'no_other': -8}, 'right': {'has_other': 0, 'no_other': -8}},
                    'DSCH': {'left': {'has_other': 2, 'no_other': -180}, 'right': {'has_other': -2, 'no_other': 212}}
                }
            },
            3: {
                0: {
                    'LOAD': {'left': {'has_other': 0, 'no_other': 0}, 'right': {'has_other': 0, 'no_other': 0}},
                    'DSCH': {'left': {'has_other': 0, 'no_other': 0}, 'right': {'has_other': 0, 'no_other': 0}}
                },
                1: {
                    'LOAD': {'left': {'has_other': 0, 'no_other': -12}, 'right': {'has_other': 0, 'no_other': 2}},
                    'DSCH': {'left': {'has_other': 0, 'no_other': 220}, 'right': {'has_other': 0, 'no_other': -160}}
                },
                2: {
                    'LOAD': {'left': {'has_other': 0, 'no_other': 5}, 'right': {'has_other': 0, 'no_other': 5}},
                    'DSCH': {'left': {'has_other': 0, 'no_other': -2}, 'right': {'has_other': 0, 'no_other': 24}}
                },
                3: {
                    'LOAD': {'left': {'has_other': 0, 'no_other': -12}, 'right': {'has_other': 0, 'no_other': -4}},
                    'DSCH': {'left': {'has_other': -4, 'no_other': -135}, 'right': {'has_other': 4, 'no_other': 224}}
                }
            },
            4: {
                0: {
                    'LOAD': {'left': {'has_other': 0, 'no_other': 0}, 'right': {'has_other': 0, 'no_other': 0}},
                    'DSCH': {'left': {'has_other': 0, 'no_other': 0}, 'right': {'has_other': 0, 'no_other': 0}}
                },
                1: {
                    'LOAD': {'left': {'has_other': 0, 'no_other': -12}, 'right': {'has_other': 0, 'no_other': 12}},
                    'DSCH': {'left': {'has_other': 0, 'no_other': -148}, 'right': {'has_other': 0, 'no_other': 210}}
                },
                2: {
                    'LOAD': {'left': {'has_other': 0, 'no_other': 16}, 'right': {'has_other': 0, 'no_other': 16}},
                    'DSCH': {'left': {'has_other': 0, 'no_other': 50}, 'right': {'has_other': 0, 'no_other': 24}}
                },
                3: {
                    'LOAD': {'left': {'has_other': 0, 'no_other': 10}, 'right': {'has_other': 0, 'no_other': 10}},
                    'DSCH': {'left': {'has_other': 2, 'no_other': 242}, 'right': {'has_other': -2, 'no_other': -120}}
                }
            },
            5: {
                0: {
                    'LOAD': {'left': {'has_other': 0, 'no_other': 0}, 'right': {'has_other': 0, 'no_other': 0}},
                    'DSCH': {'left': {'has_other': 0, 'no_other': 0}, 'right': {'has_other': 0, 'no_other': 0}}
                },
                1: {
                    'LOAD': {'left': {'has_other': 0, 'no_other': 0}, 'right': {'has_other': 0, 'no_other': 0}},
                    'DSCH': {'left': {'has_other': 0, 'no_other': -120}, 'right': {'has_other': 0, 'no_other': 210}}
                },
                2: {
                    'LOAD': {'left': {'has_other': 0, 'no_other': -5}, 'right': {'has_other': 0, 'no_other': -5}},
                    'DSCH': {'left': {'has_other': 0, 'no_other': 75}, 'right': {'has_other': 0, 'no_other': 24}}
                },
                3: {
                    'LOAD': {'left': {'has_other': 0, 'no_other': 0}, 'right': {'has_other': 5, 'no_other': 0}},
                    'DSCH': {'left': {'has_other': 2, 'no_other': 242}, 'right': {'has_other': 6, 'no_other': -120}}
                }
            },
            6: {
                0: {
                    'LOAD': {'left': {'has_other': 0, 'no_other': 0}, 'right': {'has_other': 0, 'no_other': 0}},
                    'DSCH': {'left': {'has_other': 0, 'no_other': 0}, 'right': {'has_other': 0, 'no_other': 0}}
                },
                1: {
                    'LOAD': {'left': {'has_other': 0, 'no_other': 0}, 'right': {'has_other': 0, 'no_other': 0}},
                    'DSCH': {'left': {'has_other': 0, 'no_other': 0}, 'right': {'has_other': 0, 'no_other': 0}}
                },
                2: {
                    'LOAD': {'left': {'has_other': 0, 'no_other': 0}, 'right': {'has_other': 0, 'no_other': 0}},
                    'DSCH': {'left': {'has_other': 0, 'no_other': 0}, 'right': {'has_other': 0, 'no_other': 0}}
                },
                3: {
                    'LOAD': {'left': {'has_other': 0, 'no_other': 0}, 'right': {'has_other': 0, 'no_other': 0}},
                    'DSCH': {'left': {'has_other': 0, 'no_other': 0}, 'right': {'has_other': 0, 'no_other': 0}}
                }
            }
        }

        # 0-底端（面海向左）1-高端（面海向右）
        # 前1后0
        try:
            if truck_pos == 0:
                if workflow == 0 and work_type == "LOAD":  # 装船-单箱吊, 中心为第一个识别到的20尺/40尺集装装箱
                    # 如果两个箱子？
                    if len(self.pos_dict["20_container"]) > 1:
                        pass
                    elif len(self.pos_dict["20_container"]) == 1:
                        self.pos_dict["center"] = [self.pos_dict["20_container"][0][0],
                                                   self.pos_dict["20_container"][0][1]]

                # 单箱部分待讨论。
                elif workflow == 0 and work_type == "DSCH":  # 卸船-单箱吊, 中心为标靶数量大
                    now_pos = self.pos_dict["car"]

                elif workflow == 1 and work_type == "LOAD":  # 装船-双箱吊, 中心为
                    if len(self.pos_dict["20_container"]) > 1:
                        self.pos_dict["center"] = [
                            0.5 * (self.pos_dict["20_container"][0][0] + self.pos_dict["20_container"][1][0]) + 1, \
                            0.5 * (self.pos_dict["20_container"][0][1] + self.pos_dict["20_container"][1][1]) - 5]

                elif workflow == 1 and work_type == "DSCH":  # 卸船-双箱吊,
                    if len(self.pos_dict['car_board']) > 0:
                        board_x, board_y, car_w, car_h = self.pos_dict["car_board"][0]
                        # p = 1 if front_x > car_x else -1
                        p = calc_parame[lane_id][truck_pos][0][0] if self.truck_direction == 1 else \
                            calc_parame[lane_id][truck_pos][0][1]
                        self.pos_dict["center"] = [board_x + p, board_y]

            elif truck_pos == 1:  # 前箱
                if work_type == "LOAD":
                    if len(self.pos_dict["20_container"]) > 1:
                        self.judge_f_r_container(lane_id)
                        self.pos_dict["center"] = [self.pos_dict["f_container"][0], self.pos_dict["f_container"][1] + \
                                                   calc_parame[lane_id][truck_pos]['LOAD']['right']['has_other']]
                    else:
                        self.pos_dict["center"] = [self.pos_dict["20_container"][0][0],
                                                   self.pos_dict["20_container"][0][1] + \
                                                   calc_parame[lane_id][truck_pos]['LOAD']['right']['no_other']]
                else:
                    if len(self.pos_dict["car_board"]) > 0 and len(self.pos_dict["20_container"]) < 1:
                        board_x, board_y, _, _ = self.pos_dict["car_board"][0]
                        # p = 1 if front_x > board_x else -1
                        p = calc_parame[lane_id][truck_pos]['DSCH']['right'][
                            'no_other'] if self.truck_direction == 1 else \
                            calc_parame[lane_id][truck_pos]['DSCH']['left']['no_other']
                        self.pos_dict["center"] = [board_x + p, board_y]
                    elif len(self.pos_dict["car_board"]) > 0 and len(self.pos_dict["20_container"]) == 1:
                        self.pos_dict["center"] = [self.pos_dict["car_board"][0][0], self.pos_dict["car_board"][0][1]]


            elif truck_pos == 2:  # 引导位置放在中间位置
                if work_type == 'LOAD':
                    if len(self.pos_dict["20_container"]) > 1 and worksize == 20:
                        self.pos_dict["center"] = [
                            0.5 * (self.pos_dict["20_container"][0][0] + self.pos_dict["20_container"][1][0]), \
                            0.5 * (self.pos_dict["20_container"][0][1] + self.pos_dict["20_container"][1][1]) + \
                            calc_parame[lane_id][truck_pos]['LOAD']['right']['no_other']]
                        # 五车道
                        # self.pos_dict["center"] = [
                        #     0.5 * (self.pos_dict["20_container"][0][0] + self.pos_dict["20_container"][1][0]) + 1, \
                        #     0.5 * (self.pos_dict["20_container"][0][1] - 10 + self.pos_dict["20_container"][1][1]) - 10]

                        # 四车道
                        # self.pos_dict["center"] = [
                        #     0.5 * (self.pos_dict["20_container"][0][0] + self.pos_dict["20_container"][1][0]) + 1, \
                        #     0.5 * (self.pos_dict["20_container"][0][1] + 2 + self.pos_dict["20_container"][1][1]) + 5]

                        # 三
                        # self.pos_dict["center"] = [
                        #     0.5 * (self.pos_dict["20_container"][0][0] + self.pos_dict["20_container"][1][0]) + 1, \
                        #     0.5 * (self.pos_dict["20_container"][0][1] + self.pos_dict["20_container"][1][1]) + 5]

                        # 二
                        # self.pos_dict["center"] = [
                        #     0.5 * (self.pos_dict["20_container"][0][0] + self.pos_dict["20_container"][1][0]) + 1, \
                        #     0.5 * (self.pos_dict["20_container"][0][1] + self.pos_dict["20_container"][1][1]) + 2]

                    elif len(self.pos_dict["20_container"]) == 1 and worksize == 20:
                        self.pos_dict["center"] = [self.pos_dict["20_container"][0][0],
                                                   self.pos_dict["20_container"][0][1]]
                    elif len(self.pos_dict["40_container"]) == 1 and worksize != 20:
                        self.pos_dict["center"] = [self.pos_dict["40_container"][0][0],
                                                   self.pos_dict["40_container"][0][1] + \
                                                   calc_parame[lane_id][truck_pos]['LOAD']['right']['no_other']]
                else:
                    if len(self.pos_dict['car_board']) > 0:
                        board_x, board_y, car_w, car_h = self.pos_dict["car_board"][0]
                        # p = 1 if front_x > car_x else -1
                        p = calc_parame[lane_id][truck_pos]['DSCH']['right'][
                            'no_other'] if self.truck_direction == 1 else \
                            calc_parame[lane_id][truck_pos]['DSCH']['left']['no_other']
                        self.pos_dict["center"] = [board_x + p, board_y]


            elif truck_pos == 3:  # 引导位置放在后箱位置
                if work_type == "LOAD":
                    # print('=========================================')
                    # print(self.truck_direction)
                    # print('=========================================')
                    # print(self.pos_dict)
                    if len(self.pos_dict['20_container']) > 1:
                        board_x = (self.pos_dict['20_container'][0][0] + self.pos_dict['20_container'][1][0]) / 2
                        if self.truck_direction != 0 and self.truck_direction != 1:
                            if board_x < 710 and lane_id > 3:
                                self.truck_direction = 0
                            elif board_x < 710 and lane_id < 4:
                                self.truck_direction = 1
                        self.judge_f_r_container(lane_id)

                        self.pos_dict["center"] = [self.pos_dict["r_container"][0], self.pos_dict["r_container"][1] \
                                                   + calc_parame[lane_id][truck_pos]['LOAD']['right']['has_other']]

                    else:
                        self.pos_dict["center"] = [self.pos_dict["20_container"][0][0],
                                                   self.pos_dict["20_container"][0][1] + \
                                                   calc_parame[lane_id][truck_pos]['LOAD']['right']['no_other']]
                        if len(self.pos_dict['car_board']) > 0:
                            board_x, board_y, car_w, car_h = self.pos_dict["car_board"][0]

                            if self.truck_direction != 0 and self.truck_direction != 1:
                                if board_x < 710:
                                    if lane_id > 3:
                                        self.truck_direction = 0
                                    elif lane_id < 4:
                                        self.truck_direction = 1

                            # print(self.truck_direction)

                else:
                    if len(self.pos_dict['20_container']) == 0:
                        if len(self.pos_dict['car_board']) > 0:
                            board_x, board_y, car_w, car_h = self.pos_dict["car_board"][0]
                            if self.truck_direction != 0 and self.truck_direction != 1:

                                if board_x < 710 and lane_id > 3:
                                    self.truck_direction = 0
                                elif board_x < 710 and lane_id < 4:
                                    self.truck_direction = 1

                            p = calc_parame[lane_id][truck_pos]['DSCH']['right'][
                                'no_other'] if self.truck_direction == 1 else \
                                calc_parame[lane_id][truck_pos]['DSCH']['left']['no_other']
                            self.pos_dict['center'] = [board_x + p, board_y]
                    else:
                        board_x, board_y, car_w, car_h = self.pos_dict["car_board"][0]
                        if self.truck_direction != 0 and self.truck_direction != 1:
                            if self.pos_dict['20_container'][0][0] > board_x and lane_id > 3:
                                self.truck_direction = 1
                            elif self.pos_dict['20_container'][0][0] > board_x and lane_id < 4:
                                self.truck_direction = 0

                        p = calc_parame[lane_id][truck_pos]['DSCH']['right'][
                            'has_other'] if self.truck_direction == 1 else \
                            calc_parame[lane_id][truck_pos]['DSCH']['left']['has_other']
                        # pos_dict["center"] = [car_x - p * 265, board_y]
                        # pos_dict["center"] = [car_x - p * 571, board_y]
                        self.pos_dict["center"] = [board_x + p, board_y]
        except Exception as error:
            error_logger.error(f'calc {error}')

    # 计算引导距离，集卡引导移动方向，目标位置
    def calc_guide_part(self, work_type, lane):

        if self.pos_dict['center'] is not None:
            c_x, c_y = copy.deepcopy(self.pos_dict['center'])

            guid_c = self.params[lane][work_type]['guid_c']
            trolley_c = self.params[lane][work_type]['trolley_c']

            if c_x < guid_c:
                self.truck_move_dir = 1  # =移动方向：面海向右
            elif c_x > guid_c:
                self.truck_move_dir = 2  # =移动方向：面海向左
            else:
                self.truck_move_dir = 0  #
            self.truck_distance = 0.01 * 1.24 * abs(c_x - guid_c)
            plane = 1 if int(lane) >= 4 else -1
            car_target_y = self.params[lane]['trolley'] - plane * 0.01 * 1.7 * (c_y - trolley_c)

            if int(lane) < 4:
                # self.truck_distance = -1 * self.truck_distance

                if self.truck_move_dir == 1:
                    self.truck_move_dir = 2

                elif self.truck_move_dir == 2:
                    self.truck_move_dir = 1

            self.result = (self.truck_distance, self.truck_move_dir, car_target_y)
            print(self.result)

    # 有作业任务部分
    # 也要做一遍无作业任务的部分，给VI002所有检测结果的一些信息
    def rec_dis(self, msg_uid="msg_uid_1234567890", lane_id=5, truck_pos=1, work_type="LOAD", workflow=1, worksize=20):
        self.truck_pos = truck_pos
        self.msg_uid = msg_uid
        # 得到对应任务车道的pos_dict
        if int(lane_id) < 4:
            self.process_lane(self.lane_obj_115[f'lane_{lane_id}'], f'lane_{lane_id}')
        else:
            self.process_lane(self.lane_obj_119[f'lane_{lane_id}'], f'lane_{lane_id}')

        # 是否要切换相机判断集卡是否移动
        self.convert_cam(lane_id)

        try:
            if not self.pos_dict['has_car']:
                renew_VI007(lane_id, 0, 9999, 3)
            else:
                # 得到pos_dict['center']
                self.guide_state = 1
                self.calc_center_part(truck_pos, work_type, workflow, int(lane_id), worksize)
                self.calc_guide_part(work_type, lane_id)

                if (self.guide_state == 1) and (self.truck_distance < 0.05):
                    self.guide_state_count += 1
                    if self.guide_state_count >= 6:
                        self.guide_state = 2
                        renew_VI008(lane_id, self.result[2], self.truck_distance)
                        # truck_head_dis_judge(copy.deepcopy(self.pos_dict))
                        center_box = self.get_center_box(workflow=workflow, work_type=work_type)
                        # print('=============center_box===================')
                        # print(center_box)
                        # print('=============center_box===================')

                # 如果引导到位了且距离变化更大了
                # (到位之后小车移动过来的过程中会有相机画面抖动，导致偏移变大)
                if self.guide_state_count >= 10:
                    if self.truck_distance < 0.1:
                        self.guide_state = 2
                        self.guide_state_count += 1
                    else:
                        self.guide_state = 1
                        self.guide_state_count = 0
                # 没引导到位时
                # if (self.truck_distance > 0.07) and (self.guide_state_count < 5): # 0.05 超過7cm才變化狀態
                #     self.guide_state = 1
                #     self.guide_state_count = 0

                renew_VI007(lane_id=lane_id, guide_state=self.guide_state, truck_distance=self.truck_distance,
                            truck_move_dir=self.truck_move_dir)

        except Exception as error:
            exception_traceback = traceback.format_exc()
            error_logger.error(f'{type(error).__name__}: {error}\n detail: {exception_traceback}')

        # print(self.guide_state, self.truck_distance, self.truck_move_dir)
        # 当前画面中所有车道的信息
        self.update_VI002(int(lane_id))

    def no_task_part(self):
        # 没有任务，车道默认-1（全部都更新）
        self.update_VI002(-1)

    def update_all_VI007(self, laneID):
        result = {
            'lane_1': 0,
            'lane_2': 0,
            'lane_3': 0,
            'lane_4': 0,
            'lane_5': 0,
            'lane_6': 0
        }

        def has_car(obj_lst):
            if_has = 0
            if len(obj_lst) > 0:
                for _, class_name, _, _, oxywh in obj_lst:
                    if class_name == 'car_front' or class_name == 'car':
                        if_has = 1
            return if_has

        for lane in self.lane_lst[:3]:
            now_lane_obj = copy.deepcopy(self.lane_obj_115[lane])
            result[lane] = has_car(now_lane_obj)
        for lane in self.lane_lst[3:]:
            now_lane_obj = copy.deepcopy(self.lane_obj_119[lane])
            result[lane] = has_car(now_lane_obj)

        VI007 = get_global('VI007')
        for i in range(6):
            if int(laneID) - 1 == i:
                continue
            GuideStatus = {
                "lane_id": str(i + 1),
                "guide_state": 0,  # 0=未引导 1=引导中 2=引导到位
                "truck_distance": 9999,  # 集卡距离作业位置行驶距离
                "truck_move_dir": 3,  # 0=到位,1=面海向右,2=面海向左,3=不在视野中
                "has_truck": result[f'lane_{i + 1}']  # 0 无, 1有
            }
            VI007["data"]["lane_guide_status"][i] = GuideStatus
        set_global('VI007', VI007)

    # 更新VI002部分
    def update_VI002(self, lane_id):
        for lane in self.lane_lst[:3]:
            try:
                if f'lane_{lane_id}' == lane:
                    for item in self.TruckRecognizeResult_lst:
                        if int(item['lane_id']) == int(lane_id):
                            item['recognizeResults'][0]['result'] = copy.deepcopy(self.truck_direction)
                    continue
                self.process_lane(self.lane_obj_115[lane], lane)
            except Exception as error:
                continue

        for lane in self.lane_lst[3:]:
            try:
                if f'lane_{lane_id}' == lane:
                    for item in self.TruckRecognizeResult_lst:
                        if int(item['lane_id']) == int(lane_id):
                            item['recognizeResults'][0]['result'] = copy.deepcopy(self.truck_direction)
                    continue
                self.process_lane(self.lane_obj_119[lane], lane)
            except Exception as error:
                continue

    def process_lane(self, lane_obj, lane):
        # 检查车道是否有车辆
        self.lane_has_car(lane_obj, lane)
        # print('==========================')
        # print(lane)
        # print(lane_obj)
        # print('==========================')

        if self.pos_dict['has_car']:
            # recognize_result_lst = []
            # 获取车辆前方信息：车辆方向、载货状态、高度
            self.truck_direction, self.truck_load_state, self.truck_height = self.get_car_front_dir()

            if self.lane_lst.index(lane) < 3:

                # 如果是1——3车道，车头朝向要取反(相机115)
                if self.truck_direction == 0:
                    self.truck_direction = 1
                elif self.truck_direction == 1:
                    self.truck_direction = 0
                else:
                    self.truck_direction = -1

            # 获取车道在列表中的索引
            self.lane_index = self.lane_lst.index(lane)

            self.add_TruckRecognizeResult()

    def add_TruckRecognizeResult(self, ):
        recognize_result_lst = []
        recognize_result_lst.append(
            create_recognize_result('truck_direction', self.truck_direction, self.save_name, self.save_time))
        recognize_result_lst.append(
            create_recognize_result('truck_load_state', self.truck_load_state, self.save_name, self.save_time))
        recognize_result_lst.append(
            create_recognize_result('truck_height', self.truck_height, self.save_name, self.save_time))

        TruckRecognizeResult = create_TruckRecognizeResult(recognize_result_lst, int(self.lane_index + 1))

        self.TruckRecognizeResult_lst.append(TruckRecognizeResult)

    def reset_variables(self):
        self.refresh_pos_dict()
        self.TruckRecognizeResult_lst = []
        self.guide_state = 0
        self.no_task = True
        self.msg_uid = "msg_uid_1234567890"
        self.save_name = ''
        self.save_time = 0
        self.lane_index = 0
        self.truck_direction = -1
        self.truck_load_state = ''
        self.truck_height = 0
        self.truck_pos = -1
        self.truck_distance = 9999
        self.truck_move_dir = -1
        self.all_obj_lst_119 = None
        self.all_obj_lst_115 = None
        self.lane_obj_119 = {
            'lane_1': [],
            'lane_2': [],
            'lane_3': [],
            'lane_4': [],
            'lane_5': [],
            'lane_6': [],
            'frame': None
        }
        self.lane_obj_115 = {
            'lane_1': [],
            'lane_2': [],
            'lane_3': [],
            'lane_4': [],
            'lane_5': [],
            'lane_6': [],
            'frame': None
        }

    def run(self):
        # 任务判断
        no_task = False
        last_time = time.time()
        while True:
            try:
                time.sleep(0.04)
                ret_119, frame_119 = self.device_119.read()
                if not ret_119:
                    continue
                if frame_119.shape[:2] != (2160, 3840):
                    frame_119 = cv2.resize(frame_119, (3840, 2160))
                crop_img_119 = self.cam_pre_process(frame_119, '119')

                ret_115, frame_115 = self.device_115.read()
                if not ret_115:
                    continue
                if frame_115.shape[:2] != (2160, 3840):
                    frame_115 = cv2.resize(frame_115, (3840, 2160))
                crop_img_115 = self.cam_pre_process(frame_115, '115')

                now_time = time.time()
                if now_time - last_time >= 300:
                    last_time = now_time
                    check_res_115 = check_img_cam(self.device_115, 'cam_115', frame_115)
                    check_res_119 = check_img_cam(self.device_119, 'cam_119', frame_119)
                    if check_res_115 != 0:
                        set_VI003(check_res_115)
                    if check_res_119 != 0:
                        set_VI003(check_res_119)
                # 得到检测结果，对应到每条车道的结果
                # self.lane_obj_119, self.lane_obj_115
                self.get_road_obj([crop_img_119, crop_img_115])

                # 判断是否收到任务
                # 如果没有任务，得到车道上VI002需要的信息，返回即可
                Has_task = get_global('Has_task')
                # print(Has_task)
                # for i in range(6):
                #     if Has_task[i]['has_task'] is True:
                #         no_task = False
                if no_task:
                    self.no_task_part()
                else:
                    MC301 = get_global('MC301')
                    # if abs(MC301["timestamp"] - int(time.time() * 1000)) < 1000:
                    if True:
                        self.update_all_VI007(MC301['data']['guide_mission']['lane_id'])
                        self.rec_dis(msg_uid=MC301['msg_uid'],
                                     lane_id=MC301['data']['guide_mission']['lane_id'],
                                     truck_pos=MC301['data']['guide_mission']['truck_pos'],
                                     work_type=MC301['data']['guide_mission']['work_type'],
                                     workflow=MC301['data']['guide_mission']['workflow'],
                                     worksize=MC301['data']['guide_mission']['work_size'])
                    else:
                        self.no_task_part()
                # print('-------------------')
                # print(self.TruckRecognizeResult_lst)
                # 有车的时候会更新这个列表，没车的时候为空
                if len(self.TruckRecognizeResult_lst) >= 0:
                    renew_VI002(self.TruckRecognizeResult_lst)
                # else:
                #     renew_VI002()
                self.reset_variables()
            except Exception as error:
                exception_traceback = traceback.format_exc()
                error_logger.error(f'{type(error).__name__}: {error}\n detail: {exception_traceback}')
                continue


if __name__ == '__main__':
    a = det_guid(config_det_guid)
    a.run()
