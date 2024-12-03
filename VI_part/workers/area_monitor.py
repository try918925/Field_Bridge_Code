'''
    小车方向: 100/104 - 反馈VI005
    大车方向: 158/168 159/169 - 反馈VI009
    !!! todo: 增加设置项交互MC306 MC307
'''
import copy
from pathlib import Path
import sys
import os

FILE = Path(__file__).resolve()
ROOT = FILE.parents[1]  # 
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative

from shapely.geometry import Point, Polygon
from global_info import *
from initializers import *
import configs.config_det_pedestrain as config_det_pedestrain
import configs.config_det_qc as config_det_qc
from algorithms.yolov5.predictor.det_predictor import YOLOv5Detector
from cam_utils.camsdk import hksdk as camera_sdk
from configs.cam_info import CAMERA_DICT
from configs import road_polygon

import traceback
import threading
import time
import numpy as np
import uuid
import cv2

global area_code_lock# 联系梁上相机同时赋值时的保护
area_code_lock = threading.Lock()


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


def renew_VI009(result):
    VI009 = get_global('VI009')
    VI009['msg_uid'] = str(uuid.uuid1())  # string,消息序号
    VI009['timestamp'] = str(int(time.time() * 1000))

    # 距离可能要每个相机对应一个（暂时先用同一个验证
    if result['area_code'] < 5:
        VI009['data']['object_distance'] = float(
            0.01 * (-99.19370180305047 * result['max_y'] ** (1 / 3) + 1255.0348889725458))
    else:
        VI009['data']['object_distance'] = result['object_distance']
    VI009['data']['has_person'] = result['has_person']
    VI009['data']['has_object'] = result['has_object']
    VI009['data']['object_type'] = result['object_type']
    VI009['data']['person_num'] = result['person_num']
    VI009['data']['person_target_x'] = result['person_target_x']
    VI009['data']['person_target_y'] = result['person_target_y']
    VI009['data']['area_code'] = result['area_code']
    VI009['data']['cam_code_list'] = result['cam_code_list']
    set_global('VI009', VI009)
    VI2MC_pub.send_msg(json.dumps(VI009))


def renew_VI005(result):
    VI005 = get_global('VI005')
    VI005['msg_uid'] = str(uuid.uuid1())  # string,消息序号
    VI005['timestamp'] = str(int(time.time() * 1000))

    VI005['data']['has_person'] = result['has_person']
    VI005['data']['person_num'] = result['person_num']
    VI005['data']['person_target_x'] = result['person_target_x']
    VI005['data']['person_target_y'] = result['person_target_y']
    VI005['data']['cam_code'] = result['cam_code_list']
    set_global('VI005', VI005)
    VI2MC_pub.send_msg(json.dumps(VI005))

class gantry_monitor(threading.Thread):
    def __init__(self, ):
        super().__init__()
        self.qc_detector = YOLOv5Detector.from_config(config_det_qc)

        self.cams_dict = {
            'cam_158': None,  # cam device
            'cam_168': None,
            'cam_159': None,
            'cam_169': None,
        }

        self.init_cams()

        self.device_158 = self.cams_dict['cam_158']
        self.device_168 = self.cams_dict['cam_168']
        self.device_159 = self.cams_dict['cam_159']
        self.device_169 = self.cams_dict['cam_169']

        self.cams_result = {
            'cam_158': [],
            'cam_168': [],
            'cam_159': [],
            'cam_169': [],
        }

        # “area_code”: int 区域编号 
        # 1=海左大车轨道 2=海右大车轨道 3=陆左大车轨道 4=陆右大车轨道 5=海侧关路 6=陆侧关路
        self.now_result = {
            'area_code': 0,
            'cam_code_list': [],
            'has_object': False,
            'object_distance': None,
            'object_type': None,
            'has_person': False,
            'person_target_x': None,
            'person_target_y': None,
            'person_num': 0,
            'max_y': 0,
            'frame': []
        }

        global area_code_lock
        with area_code_lock:
            VI010 = get_global('VI010')
            VI010['msg_uid'] = str(uuid.uuid1())  # string,消息序号
            VI010['timestamp'] = str(int(time.time() * 1000))  # long, 时间戳,单位毫秒
            if VI010['data']['on_area_list'] is None or len(VI010['data']['on_area_list']) == 0:
                VI010['data']['on_area_list'] = [1, 2, 3, 4]
            else:
                for i in [1, 2, 3, 4]:
                    if i not in VI010['data']['on_area_list']:
                        VI010['data']['on_area_list'].extend(i)
            set_global('VI010', VI010)
        VI2MC_pub.send_msg(json.dumps(VI010))

    def refresh_cam_obj(self):
        self.cams_result = {
            'cam_158': [],
            'cam_168': [],
            'cam_159': [],
            'cam_169': [],
        }

    def renew_now_result(self):
        self.now_result = {
            'area_code': 0,
            'cam_code_list': [],
            'has_object': False,
            'object_distance': None,
            'object_type': None,
            'has_person': False,
            'person_target_x': None,
            'person_target_y': None,
            'person_num': 0,
            'max_y': 0,
            'frame': []
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

    def area_judge(self, point, cam_name):
        in_area = False
        if cam_name == 'cam_168':
            pt = road_polygon.road_left
            polygon = Polygon(pt)
            point = Point(point)
            if polygon.contains(point):
                in_area = True
        elif cam_name == 'cam_169':
            pt = road_polygon.road_right
            polygon = Polygon(pt)
            point = Point(point)
            if polygon.contains(point):
                in_area = True
        elif cam_name == 'cam_158':
            pt = road_polygon.sea_left
            polygon = Polygon(pt)
            point = Point(point)
            if polygon.contains(point):
                in_area = True
        elif cam_name == 'cam_159':
            pt = road_polygon.sea_right
            polygon = Polygon(pt)
            point = Point(point)
            if polygon.contains(point):
                in_area = True

        return in_area


    def get_all_result(self):
        area_code = {
            'cam_158': [1, 158],
            'cam_159': [2, 159],
            'cam_168': [3, 168],
            'cam_169': [4, 169]
        }
        # file = open('./dache.txt', 'a+')
        for key, item in self.cams_result.items():
            # print(key, item)
            # print(len(item))
            self.now_result['area_code'] = area_code[key][0]
            self.now_result['cam_code_list'] = [area_code[key][1]]
            if len(item[0]) > 0:

                self.now_result['has_object'] = True
                # print(item, file=file)
                for class_id, class_name, score, p1p2, oxywh in item[0]:
                    obj_in_area = self.area_judge(oxywh[:2], key)
                    if not obj_in_area:
                        continue

                    x1, y1, x2, y2 = map(int, p1p2)
                    xo, yo, w, h = oxywh
                    datatime = int(time.time() * 1000)
                    if y1 > y2:
                        if y1 > self.now_result['max_y']:
                            self.now_result['max_y'] = y1
                    else:
                        if y2 > self.now_result['max_y']:
                            self.now_result['max_y'] = y2
                    if class_name == 'person':
                        self.now_result['has_person'] = True
                        datetime = int(time.time() * 1000)
                        cv2.imwrite(os.path.join(config_det_qc.RESULT_DIR, f"pedestrain_{datetime}.jpg"), item[1])
                        if self.now_result['object_type'] is None or len(self.now_result['object_type']) == 0:
                            self.now_result['object_type'] = 'person'
                        else:
                            self.now_result['object_type'] += ',person'
                        self.now_result['person_num'] += 0

                        if self.now_result['person_target_x'] is None or len(self.now_result['person_target_x']) == 0:
                            self.now_result['person_target_x'] = str(xo)
                            self.now_result['person_target_y'] = str(yo)
                        else:
                            self.now_result['person_target_x'] += f',{str(xo)}'
                            self.now_result['person_target_x'] += f',{str(yo)}'

                    elif class_name == 'big_car':
                        if self.now_result['object_type'] is None or len(self.now_result['object_type']) == 0:
                            self.now_result['object_type'] = 'qc'
                        else:
                            self.now_result['object_type'] += ',qc'
                    elif class_name == 'truck':
                        if self.now_result['object_type'] is None or len(self.now_result['object_type']) == 0:
                            self.now_result['object_type'] = 'truck'
                        else:
                            self.now_result['object_type'] += ',truck'
                    else:
                        if self.now_result['object_type'] is None or len(self.now_result['object_type']) == 0:
                            self.now_result['object_type'] = 'other'
                        else:
                            self.now_result['object_type'] += ',other'

            renew_VI009(self.now_result)
            self.renew_now_result()


    def get_all_obj(self, img_lst):
        # 对所有图像进行推断
        inference_results = self.qc_detector.infer(img_lst)
        # print('=============================')
        # print(inference_results)
        # print('=============================')
        camera_ids = ['cam_158', 'cam_159', 'cam_168', 'cam_169']
        for index, cam_id in enumerate(camera_ids):
            # print(index, cam_id)
            # print(inference_results[index])
            # [obj_lst]
            self.cams_result[cam_id] = copy.deepcopy([inference_results[index], img_lst[index]])
        self.get_all_result()

    def run(self):
        try:
            last_time = time.time()
            while True:
                MC001 = get_global('MC001')
                # if abs(MC001['data']['gantry_vel']) > 0.0:
                if True:
                    time.sleep(0.04)
                    ret_158, frame_158 = self.device_158.read()
                    if not ret_158:
                        continue
                    if frame_158.shape[:2] != (1440, 2560):
                        frame_158 = cv2.resize(frame_158, (2560, 1440))

                    ret_168, frame_168 = self.device_168.read()
                    if not ret_168:
                        continue
                    if frame_168.shape[:2] != (1440, 2560):
                        frame_168 = cv2.resize(frame_168, (2560, 1440))

                    ret_159, frame_159 = self.device_159.read()
                    if not ret_159:
                        continue
                    if frame_159.shape[:2] != (1440, 2560):
                        frame_159 = cv2.resize(frame_159, (2560, 1440))

                    ret_169, frame_169 = self.device_169.read()
                    if not ret_169:
                        continue
                    if frame_169.shape[:2] != (1440, 2560):
                        frame_169 = cv2.resize(frame_169, (2560, 1440))

                    now_time = time.time()
                    if now_time - last_time >= 300:
                        last_time = now_time
                        check_res_158 = check_img_cam(self.device_158, 'cam_158', frame_158)
                        check_res_159 = check_img_cam(self.device_159, 'cam_159', frame_159)
                        check_res_168 = check_img_cam(self.device_168, 'cam_168', frame_168)
                        check_res_169 = check_img_cam(self.device_169, 'cam_169', frame_169)
                        if check_res_158 != 0:
                            set_VI003(check_res_158)
                        if check_res_159 != 0:
                            set_VI003(check_res_159)
                        if check_res_168 != 0:
                            set_VI003(check_res_168)
                        if check_res_169 != 0:
                            set_VI003(check_res_169)

                    self.get_all_obj([frame_158, frame_159, frame_168, frame_169])
                    self.refresh_cam_obj()
        except Exception as error:
            exception_traceback = traceback.format_exc()
            error_logger.error(f'{type(error).__name__}: {error}\n detail: {exception_traceback}')

            # todo !!! 根据开启状态启动对应检测


class trolley_monitor(threading.Thread):
    def __init__(self, ):
        super().__init__()
        self.ped_detector = YOLOv5Detector.from_config(config_det_pedestrain)


        self.cams_dict = {
            'cam_100': None,  # cam device
            'cam_104': None,
        }

        self.init_cams()

        self.device_100 = self.cams_dict['cam_100']
        self.device_104 = self.cams_dict['cam_104']

        self.cams_result = {
            'cam_100': [],
            'cam_104': []
        }

        self.now_result = {
            'area_code': 0,
            'cam_code_list': [],
            'has_object': False,
            'object_distance': None,
            'object_type': None,
            'has_person': False,
            'person_target_x': None,
            'person_target_y': None,
            'person_num': 0,
            'max_y': 0,
            'frame': []
        }

        self.renew_cnt = 0

        self.roi_100= [[0.147, 0.261], [0.147, 0.812], [0.82, 0.812], [0.82, 0.261]] #LU LD RD RU
        
        self.roi_104 = [[0.135, 0.35], [0.135, 0.868], [0.84, 0.868], [0.84, 0.35]] #LU LD RD RU

        self.min_y = 432
        self.max_y = 1782
        self.middle_y = 648

        global area_code_lock
        with area_code_lock:
            VI010 = get_global('VI010')
            VI010['msg_uid'] = str(uuid.uuid1())  # string,消息序号
            VI010['timestamp'] = str(int(time.time() * 1000))  # long, 时间戳,单位毫秒
            if VI010['data']['on_area_list'] is None or len(VI010['data']['on_area_list']) == 0:
                VI010['data']['on_area_list'] = [5, 6]
            else:
                for i in [5, 6]:
                    if i not in VI010['data']['on_area_list']:
                        VI010['data']['on_area_list'].extend(i)
            set_global('VI010', VI010)
        VI2MC_pub.send_msg(json.dumps(VI010))
        

    def renew_now_result(self):
        self.now_result = {
            'area_code': 0,
            'cam_code_list': [],
            'has_object': False,
            'object_distance': None,
            'object_type': None,
            'has_person': False,
            'person_target_x': None,
            'person_target_y': None,
            'person_num': 0,
            'max_y': 0,
            'frame': []
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

    def setup_roi_polygon(self, roi_polygon_points):
        # 每行按位相乘
        roi_polygon_points = np.array(roi_polygon_points) * \
            np.array([3840, 2160])[:, np.newaxis].T
        ret_flag, roi_polygon = init_roi_polygon(roi_polygon_points.astype(np.int32))
        if not ret_flag:
            print("setup roi failed")
        return roi_polygon


    def get_result(self):
        area_code = {
            'cam_100': [5, 100, self.roi_100],
            'cam_104': [6, 104, self.roi_104],
        }
        # item [obj_lst, frame]
        for key, item in self.cams_result.items():
            self.checker = self.setup_roi_polygon(area_code[key][2])
            MC001 = get_global('MC001')
            trolley_pos = MC001["data"]["trolley_pos"] #float,小车位置,单位m
            self.now_result['area_code'] = 6 if trolley_pos < 52 else 5
             # area_code[key][0] # todo judge pos
            self.now_result['cam_code_list'] = [area_code[key][1]]
            if len(item[0]) > 0:
                self.now_result['person_target_x'] = ''
                self.now_result['person_target_y'] = ''
                self.now_result['person_num'] = 0
                self.now_result['has_object'] = True
                # print(item, file=file)
                for class_id, class_name, score, p1p2, oxywh in item[0]:
                    x1, y1, x2, y2 = map(int, p1p2)
                    xo, yo, w, h = oxywh
                    if self.checker.is_intersects_by_p1p2(p1p2):
                        if class_name == 'pedestrian':
                            datetime = int(time.time() * 1000)

                            cv2.imwrite(os.path.join(config_det_qc.RESULT_DIR, f"pedestrain_{datetime}.jpg"), item[1])
                            self.now_result['has_person'] = True
                            if self.now_result['person_target_x'] is None or len(self.now_result['person_target_x']) == 0:
                                self.now_result['person_target_x'] = str(0.01*abs(xo))
                                self.now_result['person_target_y'] = str(0.01*abs(yo))
                            else:
                                self.now_result['person_target_x'] += f',{str(0.01*abs(xo))}'
                                self.now_result['person_target_x'] += f',{str(0.01*abs(yo))}'
                            
                            self.now_result['person_num'] += 1

                            # 目标在偏下面的位置：
                            if yo >= self.middle_y:
                                off = self.max_y - yo
                            else:
                                off = yo - self.min_y
                            # off越小，离大车越近
                            if off < self.now_result['max_y']:
                                self.now_result['max_y'] = off

                            self.now_result['object_distance'] = float(0.01*(self.now_result['max_y']))

            else:
                self.now_result['person_target_x'] = ''
                self.now_result['person_target_y'] = ''
                self.now_result['person_num'] = 0
                self.renew_cnt += 1
            renew_VI009(self.now_result)
            # renew_VI005(self.now_result)
            if self.renew_cnt > 25:
                self.renew_cnt = 0
                self.renew_now_result()


    def process_imgs(self, img_lst):
        inference_results = self.ped_detector.infer(img_lst)
        camera_ids = ['cam_100', 'cam_104']
        print('=====================')
        print(inference_results)
        for index, cam_id in enumerate(camera_ids):
            self.cams_result[cam_id] = copy.deepcopy([inference_results[index], img_lst[index]])

        self.get_result()
    


    def run(self):
        last_time = time.time()
        while True:
            blank = np.zeros((2160, 3840), dtype=np.uint8)
            try:
                # time.sleep(0.04)
                MC001 = get_global('MC001')
                trolley_pos = MC001["data"]["trolley_pos"]
                hoist_height = MC001["data"]["hoist_height"]
                # if hoist_height > 15 and trolley_pos < 52:
                #     continue

                ret_100, frame_100 = self.device_100.read()
                if not ret_100:
                    time.sleep(0.04)
                    continue
                if frame_100.shape[:2] != (2160, 3840):
                    frame_100 = cv2.resize(frame_100, (3840, 2160))

                ret_104, frame_104 = self.device_104.read()
                if not ret_104:
                    time.sleep(0.04)
                    continue
                if frame_104.shape[:2] != (2160, 3840):
                    frame_104 = cv2.resize(frame_104, (3840, 2160))

                now_time = time.time()
                if now_time - last_time >= 300:
                    last_time = now_time
                    check_res_100 = check_img_cam(self.device_100, 'cam_100', frame_100)
                    check_res_104 = check_img_cam(self.device_104, 'cam_104', frame_104)
                    if check_res_100 != 0:
                        set_VI003(check_res_100)
                    if check_res_104 != 0:
                        set_VI003(check_res_104)

                self.process_imgs([frame_100, frame_104])

            except Exception as error:
                exception_traceback = traceback.format_exc()
                error_logger.error(f'{type(error).__name__}: {error}\n detail: {exception_traceback}')
