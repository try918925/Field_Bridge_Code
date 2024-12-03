import time
import uuid
import json
import cv2
from global_info import *


def check_img_corrupted(img, threshold):
    re_img = cv2.resize(img, (512, 512))
    if img.ndim != 3:
        img2gray = re_img
    else:
        img2gray = cv2.cvtColor(re_img, cv2.COLOR_BGR2GRAY)
    score = cv2.Laplacian(img2gray, cv2.CV_64F).var()
    return score < threshold


key_cam = ['cam_115', 'cam_119', 'cam_101', 'cam_100', 'cam_104', 'cam_158', 'cam_159', 'cam_168', 'cam_169']


def check_img_cam(device, cam_name, frame):
    if cam_name in key_cam:
        if not device.is_open:
            E201 = {
                "exception_code": 'E201',  # int,异常代码
                "detail": f"{cam_name} is not opened",  # string,具体信息描述
                "happen_time": str(int(time.time() * 1000)),  # long, 时间戳,单位毫秒
                "has_solved": False,  # bool,是否已解决
                "solve_time": None  # long, 时间戳,单位毫秒
            }
            # 吊具低于一定高度时有防砸车头风险/砸集装箱
            return E201
        if check_img_corrupted(frame, 200):
            pic_name = cam_name.replace('cam', 'pic')
            E213 = {
                "exception_code": 'E213',  # int,异常代码
                "detail": f"{pic_name} is not clear",  # string,具体信息描述
                "happen_time": str(int(time.time() * 1000)),  # long, 时间戳,单位毫秒
                "has_solved": False,  # bool,是否已解决
                "solve_time": None  # long, 时间戳,单位毫秒
            }
            return E213
        else:
            return 0
    else:
        if not device.is_open:
            E202 = {
                "exception_code": 'E202',  # int,异常代码
                "detail": f"{cam_name} is not opened",  # string,具体信息描述
                "happen_time": str(int(time.time() * 1000)),  # long, 时间戳,单位毫秒
                "has_solved": False,  # bool,是否已解决
                "solve_time": None  # long, 时间戳,单位毫秒
            }
            # 吊具低于一定高度时有防砸车头风险/砸集装箱
            return E202
        if check_img_corrupted(frame, 200):
            pic_name = cam_name.replace('cam', 'pic')
            E214 = {
                "exception_code": 'E214',  # int,异常代码
                "detail": f"{pic_name} is not clear",  # string,具体信息描述
                "happen_time": str(int(time.time() * 1000)),  # long, 时间戳,单位毫秒
                "has_solved": False,  # bool,是否已解决
                "solve_time": None  # long, 时间戳,单位毫秒
            }
            return E214
        else:
            return 0
