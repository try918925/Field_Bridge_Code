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

from cam_utils.camsdk import hksdk as camera_sdk
from configs.cam_info import CAMERA_DICT
from configs import config_fog_cls
from algorithms.yolov5.predictor.cls_predictor import YOLOv5Classifier

import traceback
import threading
import time
import numpy as np
import uuid
import cv2
import json


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

def renew_VI011(result):
    VI011 = get_global('VI011')
    VI011["msg_uid"] = str(uuid.uuid1())
    VI011["timestamp"] = int(time.time() * 1000)
    VI011["data"]["fog_level"] = int(result)
    set_global('VI011', VI011)
    send_msg = str(json.dumps(VI011, ensure_ascii=False))
    VI2MC_pub.send_msg(send_msg)
    key_logger.info(f'Fog-Cls:  sendVI011:{VI011}')


class FogDetect(threading.Thread):
    def __init__(self, ):
        super().__init__()
        self.fog_cls = YOLOv5Classifier.from_config(config_fog_cls)
        self.result = 0  # 0无，1有，99失败

        self.cams_dict = {
            'cam_107': None,  # cam device
        }

        self.init_cams()

        self.device_107 = self.cams_dict['cam_107']
        renew_VI011(self.result)

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

    def run(self):
        while True:
            try:
                # blank = np.zeros((1080, 1920, 3), dtype=np.uint8)
                # 五分钟检测一次
                time.sleep(300)
                ret_107, frame_107 = self.device_107.read()
                if not ret_107:
                    continue

                if frame_107.shape[:2] != (1080, 1920):
                    frame_107 = cv2.resize(frame_107, (1080, 1920))

                check_res_107 = check_img_cam(self.device_107, 'cam_107', frame_107)
                if check_res_107 != 0:
                    set_VI003(check_res_107)
                now_result = self.fog_cls.infer([frame_107])

                if now_result[0][0][1] == 'fog':
                    self.result = 1
                else:
                    self.result = 0
                # self.result = 1
                renew_VI011(self.result)



            except Exception as error:
                exception_traceback = traceback.format_exc()
                error_logger.error(f'{type(error).__name__}: {error}\n detail: {exception_traceback}')
                continue
