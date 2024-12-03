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

import traceback

from pathlib import Path
import sys
import os

FILE = Path(__file__).resolve()
ROOT = FILE.parents[1]  # YOLOv5 root directory
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative
from algorithms.yolov5.predictor.det_predictor import YOLOv5Detector

from global_info import * 
# from initializers import * 
# 感知的CAMERA_DICT
from config.cam_info import CAMERA_DICT
############################################
from cam_utils.camsdk import hksdk as camera_sdk
from config import config_det_midlock
from initializers import *

class cal_midlock(threading.Thread):
    def __init__(self) -> None:
        super().__init__()    

        self.cams_dict = {
            'cam_165': None,  # cam device
            'cam_163': None,
            'cam_153': None,
            'cam_151': None,
        }

        self.init_cams()

        self.device_165 = self.cams_dict['cam_165']
        self.device_155 = self.cams_dict['cam_163']
        self.device_153 = self.cams_dict['cam_153']
        self.device_151 = self.cams_dict['cam_151']
        

        self.det_midlock = YOLOv5Detector.from_config(config_det_midlock)


    def init_cams(self, ):
        '''
            初始化所有相机
        '''
        for item in self.cams_dict.keys():
            try:
                device  = camera_sdk.Device(
                        camera_id=CAMERA_DICT[item]["comment"],
                        host=CAMERA_DICT[item]["ip"],
                        port=8000,
                        user=CAMERA_DICT[item]["username"],
                        passwd=CAMERA_DICT[item]["password"],
                        resolution=CAMERA_DICT[item]["resolution"],
                        gpu_id=CAMERA_DICT[item]["gpu_id"]
                    )
                
                ret_flag, error_code = device.login()
                if not ret_flag:
                    key_logger.debug(f"Failed to login camera - {device.id} ({device.host}): '{error_code}'")
                ret_flag, error_code = device.open()
                if not ret_flag:
                    key_logger.debug(f"Failed to open camera - {device.id} ({device.host}): '{error_code}'")
                # ------------------------------
                key_logger.info(f"Success to init cameras - {device.id} ({device.host}):")
                ret, self.cams_dict[item] = True, device
            # ----------------------------------------
            except Exception as error:
                logger.error(f"Failed to init cameras: '{type(error).__name__}: {error}'")
                ret, self.cams_dict[item] = False, None
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


    def select_cam(self):
        lane_cam = {
            'lane_2': self.device_151, # 'cam_151',
            'lane_3': self.device_153, # 'cam_153',
            # 'lane_4': ['cam_163', 'cam_163'],
            'lane_4': self.device_155, #'cam_163',
            'lane_5': self.device_165, # 'cam_165',
            # 'lane_6': 'cam_161'
        }
        MC108 = get_global('MC108')
        lane_id = int(MC108['data']['lane_id'])
        ret, frame  = lane_cam[f'lane_{lane_id}'].read()
        return ret, frame 
        
        # if not ret:
        #     time.sleep(0.04)
        #     return 
        # if frame_155.shape[:2] != (2160, 3840):
        #     frame_155 = cv2.resize(frame_155, (3840, 2160))
        # # print(use_cam)
        # cam_frame = {
        #         'cam_165': frame_165,
        #         'cam_163': frame_155,
        #         'cam_153': frame_153,
        #         'cam_151': frame_151
        # }

        # ret_165, frame_165 = self.device_165.read()
        # if not ret_165:
        #     time.sleep(0.04)
        #     continue
        # if frame_165.shape[:2] != (2160, 3840):
        #     frame_165 = cv2.resize(frame_165, (3840, 2160))

        # ret_155, frame_155 = self.device_155.read()
        # if not ret_155:
        #     time.sleep(0.04)
        #     continue
        # if frame_155.shape[:2] != (2160, 3840):
        #     frame_155 = cv2.resize(frame_155, (3840, 2160))

        # ret_151, frame_151 = self.device_151.read()
        # if not ret_151:
        #     time.sleep(0.04)
        #     continue
        # if frame_151.shape[:2] != (2160, 3840):
        #     frame_151 = cv2.resize(frame_151, (3840, 2160))

        # ret_153, frame_153 = self.device_153.read()
        # if not ret_153:
        #     time.sleep(0.04)
        #     continue
        # if frame_153.shape[:2] != (2160, 3840):
        #     frame_153 = cv2.resize(frame_153, (3840, 2160))

        # return lane_cam[f'lane_{lane_id}']

    def run(self, ):
        while True:
            MC001 = get_global('MC001')
            # 当起升低于8m时开始做位置的更新
            trolley_pos, hoist_height  = MC001['data']['trolley_pos'], MC001['data']['hoist_height']
            if hoist_height > 7.5 or trolley_pos > 52 or trolley_pos < 21:
                time.sleep(0.1)
                continue
            MC101 = get_global('MC101')
            spreader_size = MC101["data"]["currentAction"]["spreaderSize"] if 'spreaderSize' in MC101["data"]["currentAction"].keys() else None
            if spreader_size != 'D20f':
                time.sleep(0.1)
                continue
            
            ret, use_cam_frame = self.select_cam()
            if not ret:
                time.sleep(0.04)
                continue
            if use_cam_frame.shape[:2] != (2160, 3840):
                use_cam_frame = cv2.resize(use_cam_frame, (3840, 2160))                
            
            obj_list = self.det_midlock.infer([use_cam_frame])[0]
            # print(obj_list)
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
            except :
                erro_info = traceback.format_exc()
                error_logger.error(erro_info)