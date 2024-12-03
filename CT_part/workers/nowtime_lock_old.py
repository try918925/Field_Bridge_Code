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
ROOT = FILE.parents[1]  # YOLOv5 root directory
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative
from global_info import * 
# from initializers import * 
from algorithms.yolov5.predictor.det_predictor import YOLOv5Detector
from cam_utils.camsdk import hksdk as camera_sdk
from config import config_det_midlock

class cal_midlock(threading.Thread):
    def __init__(self) -> None:
        super().__init__()    
        self.cap_165 = camera_sdk.Device('陆侧集卡引导', '10.141.1.165', 8000, 'admin', 'Dnt@QC2023', (3840, 2160))
        ret_flag, error_code = self.cap_165.login()
        if not ret_flag:
            print("登录失败:", error_code)
            exit()
        flag, stutas = self.cap_165.open()
        if not flag:
            print("登录失败:", stutas)

        self.det_midlock = YOLOv5Detector.from_config(config_det_midlock)

    def run(self, ):
        guide_state = 1
        has_car = False
        while True:
            MC001 = get_global('MC001')
            # 当起升低于8m时开始做位置的更新
            trolley_pos, hoist_height  = MC001['data']['trolley_pos'], MC001['data']['hoist_height']
            if hoist_height > 8 or trolley_pos > 52 or trolley_pos < 21:
                time.sleep(0.1)
                continue
            # MC101 = get_global('MC101')
            # actionType = MC101["data"]["currentAction"]["actionType"] if "actionType" in MC101["data"]["currentAction"].keys() else None
            # work_type = MC101["data"]["currentAction"]["work_type"] if "work_type" in MC101["data"]["currentAction"].keys() else None
            # work_lane = MC101["data"]["currentAction"]["work_lane"] if "work_lane" in MC101["data"]["currentAction"].keys() else None
            # # 根据work_lane切换相机
            # while True and work_type != None and actionType != 1:
            ret, frame = self.cap_165.read()
            if not ret:
                time.sleep(0.04)
                continue    
            obj_list = self.det_midlock.infer([frame])[0]
            latch_lst = []
            target_lst = []
            try:
                for class_id, class_name, score, p1p2, oxywh in obj_list:
                    if class_name == 'target':
                        target_lst.append(oxywh[0])
                    elif class_name == 'latch':
                        if 1000 < oxywh[0] < 2500:
                            latch_lst.append(oxywh[0])

                latch_dis = abs(latch_lst[0] - latch_lst[1])
                lock_dis = abs(target_lst[0] - target_lst[1])

                ratio = latch_dis / lock_dis            

                TEMP = get_global('TEMP')
                TEMP['lock_dis']['timestamp'] = int(time.time()*1000)
                TEMP['lock_dis']['ratio'] = ratio
                TEMP['lock_dis']['latch_dis'] = latch_dis
                # print(TEMP)
                set_global("TEMP", TEMP)
            except:
                pass