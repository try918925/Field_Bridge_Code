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
from cam_utils.camsdk import hksdk as camera_sdk

if __name__ == '__main__':
    import time
    cap = camera_sdk.Device('', '10.141.1.159', 8000, 'admin', 'Dnt@QC2023')
    ret_flag, error_code = cap.login()
    if not ret_flag:
        print("登录失败:", error_code)
        exit()
    # time.sleep(1)
    cap.open()
    # time.sleep(1)
    # while True:
    #     ret_flag, error_code, (p, t, z) = cap.get_ptz()
    #     if ret_flag:
    #         print((p, t, z))
    #     time.sleep(1)
    while True:
        time.sleep(0.1)
        time1 = time.time()
        ret_flag, frame = cap.read()
        time2 = time.time()
        print(time2-time1)
        if ret_flag:
            cv2.imwrite("./frame.jpg", frame)
            print('has frame')
        else:
            time.sleep(0.1)
            print('???')