import time
import uuid
# import zmq
import json
import math
import cv2
import numpy as np
import time
import socket
import threading
from pathlib import Path
import sys
import os

FILE = Path(__file__).resolve()
ROOT = FILE.parents[1]  #
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative
from global_info import * 
# from initializers import * 
from algorithms.yolov5.predictor.det_predictor import YOLOv5Detector
from cam_utils.camsdk import hksdk as camera_sdk
from config import config_det_guid, config_det_target

class pre_process_119():
    def __init__(self) -> None:
        self._distortion_coeffs = np.array([-2.17041889e+00, -9.59734151e+01, 2.68401705e-02, \
                                            2.63032028e-03, -4.07008640e+02])
        # 相机的内参矩阵 [fx 0 cx; 0 fy cy; 0 0 1]
        self._camera_matrix = np.array([[2.13243587e+04, 0.00000000e+00, 1.64599216e+03],
                                        [0.00000000e+00, 9.88544217e+03, 1.06588013e+03],
                                        [0.00000000e+00, 0.00000000e+00, 1.00000000e+00]])

        self._trapezoid = np.array([[1880, 435], [2950, 520], [1716, 1780], [3030, 1830]], dtype=np.float32)
        self._rectangle = np.array([[0, 0], [1600, 0], [0, 1800], [1600, 1800]], dtype=np.float32)
        # 计算透视变换矩阵
        self._M = cv2.getPerspectiveTransform(self._trapezoid, self._rectangle)

    def __call__(self, img):
        h, w = img.shape[:2]
        new_camera_matrix, roi = cv2.getOptimalNewCameraMatrix(self._camera_matrix, self._distortion_coeffs, (w, h), 0,
                                                               (w, h))
        undistorted_img = cv2.undistort(img, self._camera_matrix, self._distortion_coeffs, None, new_camera_matrix)
        # undistorted_img = img
        # undistorted_img = cv2.remap(img, self._map1, self._map2, cv2.INTER_LINEAR)
        res_img = cv2.warpPerspective(undistorted_img, self._M, (1600, 1800))  # 只留下矫正的部分
        cv2.imwrite("./119_res_img.jpg", res_img)
        return res_img

class cal_relative_pos(threading.Thread):
    '''
        侧面相机能拿到箱号信息：
        20尺箱子前后
        40尺箱中间
    '''
    def __init__(self) -> None:
        super().__init__()
        self.cap_119 = camera_sdk.Device('陆侧集卡引导', '10.141.1.115', 8000, 'admin', 'Dnt@QC2023', (3840, 2160))
        ret_flag, error_code = self.cap_119.login()
        if not ret_flag:
            print("登录失败:", error_code)
            exit()
        flag, stutas = self.cap_119.open()
        if not flag:
            print("登录失败:", )
        self.cam119_pre_process = pre_process_119()
        self.det_guid = YOLOv5Detector.from_config(config_det_guid)
        self.det_target = YOLOv5Detector.from_config(config_det_target)

    def run(self, ):
        guide_state = 1
        has_car = False
        while True:
            try:
                MC001 = get_global('MC001')
                # 当起升低于8m时开始做位置的更新
                trolley_pos, hoist_height  = MC001['data']['trolley_pos'], MC001['data']['hoist_height']
                if hoist_height > 8 or trolley_pos > 52 or trolley_pos < 21:
                    time.sleep(0.1)
                    continue
                ret, frame = self.cap_119.read()
                if not ret:
                    time.sleep(0.04)
                    continue    
                crop_img = self.cam119_pre_process(frame)
                obj_list = self.det_target.infer([crop_img])[0]
                for class_id, class_name, score, p1p2, oxywh in obj_list:
                    if class_name == 'hanger':
                        TEMP = get_global('TEMP')
                        TEMP['hanger_pos']['timestamp'] = int(time.time()*1000)
                        TEMP['hanger_pos']['bbox'] = oxywh
                        set_global("TEMP", TEMP)
                        continue
            except:
                pass    
            

    def cal_target(self, ):
        '''
        收到作业任务后识别一次
        更新目标位置bbox-oxywh
        '''
        pos_dict = {
            "car": None,
            "car_front": None,
            "car_board": None,
            "target": None,
            "20_container": [],
            "40_container": None,
            "f_container": None,
            "m_container": None,
            "r_container": None,
            "center": None, # cx, cy, 抓/放位置
            "road_num":None # 车道
        }
        MC101 = get_global('MC101')
        actionType = MC101["data"]["currentAction"]["actionType"] if "actionType" in MC101["data"]["currentAction"].keys() else None
        work_type = MC101["data"]["currentAction"]["work_type"] if "work_type" in MC101["data"]["currentAction"].keys() else None
        work_lane = MC101["data"]["currentAction"]["work_lane"] if "work_lane" in MC101["data"]["currentAction"].keys() else None
        # 根据work_lane切换相机
        while True and work_type != None and actionType != 1:
            try:
                ret, frame = self.cap_119.read()
                if not ret:
                    time.sleep(0.04)
                    continue    
                crop_img = self.cam119_pre_process(frame)
                obj_list = self.det_guid.infer([crop_img])[0]

                for class_id, class_name, score, p1p2, oxywh in obj_list:
                    xo, yo, w, h = oxywh
                    if not pos_dict[class_name]: # 判断是否为None
                        pos_dict[class_name] = []
                    if 800 < yo < 1520:
                        pos_dict[class_name].append(oxywh)   

                bbox = None
                if work_type == 'LOAD' and actionType == 2: # 装船抓箱
                    truck_pos = MC101["data"]["currentAction"]['targetPosition']['truckPos']
                    if (truck_pos == 'rear') and (work_type == "LOAD") and (pos_dict["car"] is None) and (len(pos_dict["20_container"]) > 0):  # 引导位置放在后箱位置
                        import copy
                        pos_dict["car"] = [copy.deepcopy(pos_dict["20_container"][0])]
                        p =list(pos_dict["car"][0])
                        if p[0] > 800:
                            p[0] = 1600-180
                        else:
                            p[0] = 0+180
                        pos_dict["car"][0] = tuple(p)


                    if (truck_pos == 'rear') and (work_type == "DSCH") and (pos_dict["car"] is None) and (pos_dict["car_board"] is not None):  # 引导位置放在后箱位置
                        import copy
                        pos_dict["car"] = copy.deepcopy(pos_dict["car_board"])
                        p =list(pos_dict["car"][0])
                        if p[0] > 800:
                            p[0] += 80
                        else:
                            p[0] -= 80
                        pos_dict["car"][0] = tuple(p)

                    # todo 解决车头不在视野内的问题
                    if (pos_dict["car"] is not None) and (pos_dict["car_front"] is None):
                        import copy
                        pos_dict["car_front"] = copy.deepcopy(pos_dict["car"])
                        p =list(pos_dict["car"][0])
                        if p[0] > 800:
                            p[0] = 1600
                        else:
                            p[0] = 0
                        pos_dict["car_front"][0] = tuple(p)

                    if truck_pos == 'front': # 
                        bbox = list(pos_dict["20_container"][0])
                    elif truck_pos == 'center':
                        bbox = [None] * 4
                        for i in range(4):
                            bbox[i] = 0.5*(pos_dict["20_container"][0][i] + pos_dict["20_container"][1][i])
                        bbox[2] = bbox[2] * 2 # 宽度为两个集装箱
                    elif truck_pos == 'rear':
                        bbox = list(pos_dict["20_container"][0])
                elif work_type == 'DSCH' and actionType == 3: # 卸船放箱
                    truck_pos = MC101["data"]["currentAction"]['targetPosition']['truckPos']

                    if (truck_pos == 'rear') and (work_type == "LOAD") and (pos_dict["car"] is None) and (len(pos_dict["20_container"]) > 0):  # 引导位置放在后箱位置
                        import copy
                        pos_dict["car"] = [copy.deepcopy(pos_dict["20_container"][0])]
                        p =list(pos_dict["car"][0])
                        if p[0] > 800:
                            p[0] = 1600-180
                        else:
                            p[0] = 0+180
                        pos_dict["car"][0] = tuple(p)


                    if (truck_pos == 'rear') and (work_type == "DSCH") and (pos_dict["car"] is None) and (pos_dict["car_board"] is not None):  # 引导位置放在后箱位置
                        import copy
                        pos_dict["car"] = copy.deepcopy(pos_dict["car_board"])
                        p =list(pos_dict["car"][0])
                        if p[0] > 800:
                            p[0] += 80
                        else:
                            p[0] -= 80
                        pos_dict["car"][0] = tuple(p)

                    # todo 解决车头不在视野内的问题
                    if (pos_dict["car"] is not None) and (pos_dict["car_front"] is None):
                        import copy
                        pos_dict["car_front"] = copy.deepcopy(pos_dict["car"])
                        p =list(pos_dict["car"][0])
                        if p[0] > 800:
                            p[0] = 1600
                        else:
                            p[0] = 0
                        pos_dict["car_front"][0] = tuple(p)

                    if truck_pos == 'front':
                        bbox = list(pos_dict["car_board"][0])
                        bbox[2] = bbox[2] * 0.5 # 宽度为半个车板
                        front_x, front_y, _, _ = pos_dict["car_front"][0]
                        car_x, car_y, car_w, car_h = pos_dict["car"][0]
                        p = 104 if front_x > car_x else -0
                        bbox[0] = car_x + p
                    elif truck_pos == 'center':
                        bbox = list(pos_dict["car_board"][0])
                        front_x, front_y, _, _ = pos_dict["car_front"][0]
                        car_x, car_y, car_w, car_h =pos_dict["car"][0]
                        board_x, board_y, car_w, car_h = pos_dict["car_board"][0]
                        p = 24 if front_x > car_x else 50
                        bbox[0] = board_x + p
                    elif truck_pos == 'rear':
                        bbox = list(pos_dict["car_board"][0])
                        if len(pos_dict["20_container"]) == 0:
                            bbox[2] = bbox[2] * 0.5 # 宽度为半个车板
                            front_x, front_y, _, _ = pos_dict["car_front"][0]
                            car_x, car_y, car_w, car_h =pos_dict["car"][0]
                            board_x, board_y, car_w, car_h = pos_dict["car_board"][0]
                            p = -120 if front_x > car_x else 242
                            bbox[0] = board_x + p
                        else:
                            front_x, front_y, _, _ = pos_dict["car_front"][0]
                            car_x, car_y, car_w, car_h =pos_dict["car"][0]
                            board_x, board_y, car_w, car_h = pos_dict["car_board"][0]
                            # p = -120 if front_x > car_x else -242
                            p = -2 if front_x > car_x else 2
                            bbox[0] = board_x + p

                TEMP = get_global('TEMP')
                TEMP['target_pos']['timestamp'] = int(time.time()*1000)
                TEMP['target_pos']['bbox'] = bbox
                set_global("TEMP", TEMP)
                print(TEMP)
                break # 计算完一次就结束
 
            except Exception as error: # 无指令则全升起
                print(error)
                break

