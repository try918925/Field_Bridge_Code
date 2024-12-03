import time
import uuid
import zmq
import json
import math
import socket
from pathlib import Path
import sys
import os
import threading
import cv2
import numpy as np

FILE = Path(__file__).resolve()
ROOT = FILE.parents[1]  # 上一级目录
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative

from global_info import *
from initializers import *
from algorithms.yolov5.predictor.det_predictor import YOLOv5Detector
from configs import config_det_target
from cam_utils.camsdk import hksdk as camera_sdk


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

SpreaderPositionStatus = { 
    "has_spreader": True,#True-目标下有吊具,False-目标下无吊具
    "spreader_target_x": 20.5, #float 型,目标吊具小车方向位置,单位：m
    "spreader_target_z": 1.5, #float 型,目标吊具高度,单位：m
    "spreader_target_y": 0.3, #float 型,目标吊具大车方向位置,单位：m
    "spreader_target_theta": 0.01, #float 型,目标吊具摆角,单位rad
    "spreader_target_zeta": 0.01, #float 型,目标吊具扭角,单位rad
    "spreader_cntr_num": 1,#吊具当前抓起的箱子,0-无箱子,1-一个箱子,2-两个箱子
    "spreader_code":0,#备用
}

VI004 = {
    "msg_uid":"1234567890",#string,消息序号
    "msg_name":"VI004",#string,消息名称
    "sender":"VI",#string,发送方
    "timestamp":16879546201,#long, 时间戳,单位毫秒
    "receiver":"MC", #string,接收方
    "craneId":"404-1", #string, 设备号
    "data":SpreaderPositionStatus #SpreaderPositionStatus,吊具位置状态
}

class det_target():
    '''
        输入相机原图 - 返回标靶中心像素坐标与旋转角度
    '''
    def __init__(self, config: config_det_target):
        self.p1p2 = config.DET_ROI
        self.det = YOLOv5Detector.from_config(config)
        self.result = None
        self.debug = config.DEUBG
        self.logdir = config.LOG_DIR
        if not os.path.exists(self.logdir):
            os.makedirs(self.logdir)

    def rec_angle(self, img):
        has_target = False # 判断是否有吊具
        # crop center area
        oh, ow = img.shape[:2]
        img_roi = img[self.p1p2[0][1] : self.p1p2[1][1], 
                      self.p1p2[0][0] : self.p1p2[1][0]]
        cv2.imwrite("rec.png", img_roi)
        # obj det: [target / center]
        obj_list = self.det.infer([img_roi])[0]
        # print(obj_list)
        try:
            sorted_o = sorted(obj_list, key=lambda x: x[-1][0])
            lock_elements = [item for item in sorted_o if item[1] == 'lock']
            left_lock = sorted(lock_elements[:2], key=lambda x: x[-1][1])
            x1, y1 = left_lock[0][-1][-0], left_lock[0][-1][1]
            x2, y2 = left_lock[1][-1][-0], left_lock[1][-1][1]
            angle = math.atan2(x2 - x1, y2 - y1)
            if abs(angle) > 0.785:
                angle = 0.01 * ((angle * 100) % 157 )
        except:
            # angle = 0.0
            (cx, cy), (width, height), angle, has_target = self.get_result()
            # pass

        for class_id, class_name, score, p1p2, oxywh in obj_list:
            if class_name == "target":
                has_target = True
                x1, y1, x2, y2 = map(int, p1p2)
                xo, yo, w, h = oxywh
                
                # rec center / angle
                rec_img = img_roi[int(y1 + 0.1 * h) : int(y2 - 0.1 * h), int(x1 + 0.1 * w) : int(x2 - 0.1 * w)]
                
                img_gray = cv2.cvtColor(rec_img, cv2.COLOR_BGR2GRAY)
                adaptive_threshold_img = cv2.adaptiveThreshold(img_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 151, 5)
                # kernel_erode = np.ones((5, 5), np.uint8)
                # kernel_dilate = np.ones((9, 9), np.uint8)
                kernel_erode = np.ones((3, 3), np.uint8)
                kernel_dilate = np.ones((3, 3), np.uint8)
                img_erode = cv2.erode(adaptive_threshold_img, kernel_erode, iterations = 1)
                img_dilate = cv2.dilate(img_erode, kernel_dilate, iterations = 1)
                img_dilate = cv2.bitwise_not(img_dilate)
                
                cv2.imwrite("res.png", img_dilate)
                
                cnts = cv2.findContours(img_dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                cnts = cnts[0] if len(cnts) == 2 else cnts[1]

                # Find the contour with the largest area
                max_area = 0
                max_cnt = None
                for cnt in cnts:
                    area = cv2.contourArea(cnt)
                    if area > max_area:
                        max_area = area
                        max_cnt = cnt

                # Get the minimum enclosing rectangle of the largest contour
                rect = cv2.minAreaRect(max_cnt)
                (cx, cy), (width, height), _ = rect
    
                # if not (-45 < angle < 45):
                #     angle = angle % 90 # 一般不会旋转超过45° 异常值被修正
                # angle = angle*3.14/180.0# 角度变成弧度

                self.result = ((cx+x1+0.1*w+self.p1p2[0][0], cy+y1+0.1*h+self.p1p2[0][1]), (width, height), angle, has_target)
                
                # renew det area
                self.p1p2 =[[max(int(self.result[0][0]-800), 0), max(int(self.result[0][1]-800), 0)], \
                             [min(int(self.result[0][0]+800), ow), max(int(self.result[0][1]+800), oh)]] # LU, RD

        # if self.debug: # todo 目前准确率足够，暂时先不存图
        #     if len(obj_list) == 0:
        #         cv2.imwrite(os.path.join(self.logdir, f"{time.time()}.jpg"), img)

    def get_result(self, ):
        '''
            返回标靶识别信息| 中心坐标、长宽、扭角
        '''
        return self.result

def cal_angle(x, y, l):
    '''
        输入标靶在图像中坐标、绳长
        输出偏移量、摆角
    '''
    camera_matrix = np.array([
            [1299.0407965871414, 0.0, 1200.7271079791833],
            [0.0, 1294.9708145469992, 834.771341853078],
            [0.0, 0.0, 1.0]
        ])
    dist_coeffs = np.array([-0.24878210429638445, 0.026090261203760866,
                -0.0227401823103362, 0.007351272805341688,
                0.026012259428508197
        ])    
    
    X_norm = (x - camera_matrix[0, 2]) / camera_matrix[0, 0]
    Y_norm = -(y - camera_matrix[1, 2]) / camera_matrix[1, 1]
	# 校正归一化平面坐标中的径向畸变
    r2 = X_norm * X_norm + Y_norm * Y_norm
    radial_correction = 1.0 + dist_coeffs[0] * r2 + dist_coeffs[1] * r2**2 + dist_coeffs[4] * r2**3
    tangential_correction_x = 2.0 * dist_coeffs[2] * X_norm * Y_norm + dist_coeffs[3] * (r2 + 2.0 * X_norm**2)
    tangential_correction_y = dist_coeffs[2] * (r2 + 2.0 * Y_norm**2) + 2.0 * dist_coeffs[3] * X_norm * Y_norm
    X_norm_corrected = X_norm * radial_correction + tangential_correction_x
    Y_norm_corrected = Y_norm * radial_correction + tangential_correction_y	
    X_norm_corrected += -0.1
    Y_norm_corrected += 0.01
    # print(X_norm_corrected, Y_norm_corrected)
    
    h = l / math.sqrt(1 + X_norm_corrected**2 + Y_norm_corrected**2)
    X_cam, Y_cam = X_norm_corrected * h , Y_norm_corrected * h
    # X_cam = (X_norm_corrected - 0.0733) * h - 1.5873  # 大车方向偏移量
    # Y_cam = (Y_norm_corrected + 0.0933) * h - 0.1130  # 小车方向偏移量
    
    theta = math.atan(Y_cam / h) - 0.08# 小车方向摆角

    return X_cam, Y_cam, theta

def renew_VI004(has_target, X_cam, Y_cam, theta, angle, trolley_pos, rope_pos, lock_state, spreader_double_state):
    spreader_cntr_num = 0
    if lock_state == 0:
        spreader_cntr_num = 0
    elif spreader_double_state == 0:
        spreader_cntr_num = 1
    elif spreader_double_state == 0:
        spreader_cntr_num = 2
    
    SpreaderPositionStatus = { 
        "has_spreader": has_target,#True-目标下有吊具,False-目标下无吊具
        "spreader_target_x": Y_cam + trolley_pos, #float 型,目标吊具小车方向位置,单位：m
        "spreader_target_z": rope_pos, #float 型,目标吊具高度,单位：m
        "spreader_target_y": -X_cam, #float 型,目标吊具大车方向位置,单位：m
        "spreader_target_theta": theta, #float 型,目标吊具摆角,单位rad
        "spreader_target_zeta": angle, #float 型,目标吊具扭角,单位rad
        "spreader_cntr_num": spreader_cntr_num,#吊具当前抓起的箱子,0-无箱子,1-一个箱子,2-两个箱子
        "spreader_code":0,#备用
    }

    VI004 = {
        "msg_uid":str(uuid.uuid1()),#string,消息序号
        "msg_name":"VI004",#string,消息名称
        "sender":"VI",#string,发送方
        "timestamp":int(time.time()*1000),#long, 时间戳,单位毫秒
        "receiver":"MC", #string,接收方
        "craneId":"404-1", #string, 设备号
        "data":SpreaderPositionStatus #SpreaderPositionStatus,吊具位置状态
    }

    return VI004

class spreader_pos(threading.Thread):
    def __init__(self, ):
        super().__init__()
        # todo !!! add to config
        # device = cv2.VideoCapture("./test_data/145.mkv")
        cap_101 = camera_sdk.Device('101', '10.141.1.101', 8000, 'admin', 'Dnt@QC2023', (2560, 1400))

        ret_flag, error_code = cap_101.login()
        if not ret_flag:
            print("登录失败:", error_code)
            exit()
        flag, stutas = cap_101.open()
        print(flag, stutas)        
        self.device = cap_101
        self.target_process = det_target(config_det_target)

    def run(self, ):
        last_time = time.time()
        a = 0
        # while a < 10:
        while True:
            # a += 1
            MC001 = get_global('MC001')
            trolley_pos = MC001["data"]["trolley_pos"] #float,小车位置,单位m 
            hoist_height = MC001["data"]["hoist_height"]  
            rope_pos = MC001["data"]["rope_pos"]  # float,起升绳长值,单位m
            lock_state = MC001["data"]["lock_state"]  #int,闭锁状态, 0-闭锁灯灭,1-闭锁灯亮
            spreader_double_state = MC001["data"]["spreader_double_state"]  
            
            ret_flag, frame = self.device.read()
            now_time = time.time()
            if now_time - last_time >= 300:
                last_time = now_time
                check_res = check_img_cam(self.device, 'cam_101', frame)
                if check_res != 0:
                    set_VI003(check_res)
            if ret_flag:
                self.target_process.rec_angle(frame)  
                (cx, cy), (width, height), angle, has_target = self.target_process.get_result()  
                X_cam, Y_cam, theta = cal_angle(cx, cy, 46-hoist_height)
                spreader_cntr_num = 0
                if lock_state == 0:
                    spreader_cntr_num = 0
                elif spreader_double_state == 0:
                    spreader_cntr_num = 1
                elif spreader_double_state == 1:
                    spreader_cntr_num = 2

                VI004 = get_global('VI004')
                tik = VI004['timestamp']
                # old_theta = VI004['data']['spreader_target_theta']
                # if abs(theta - old_theta) > 0.1:
                #     theta = old_theta todo
                SpreaderPositionStatus = {
                    "has_spreader": has_target,#True-目标下有吊具,False-目标下无吊具
                    "spreader_target_x": Y_cam + trolley_pos, #float 型,目标吊具小车方向位置,单位：m
                    "spreader_target_z": 46-hoist_height, #float 型,目标吊具高度,单位：m
                    "spreader_target_y": -X_cam, #float 型,目标吊具大车方向位置,单位：m
                    "spreader_target_theta": theta, #float 型,目标吊具摆角,单位rad
                    "spreader_target_zeta": angle, #float 型,目标吊具扭角,单位rad
                    "spreader_cntr_num": spreader_cntr_num,#吊具当前抓起的箱子,0-无箱子,1-一个箱子,2-两个箱子
                    "spreader_code":0,#备用
                }      
                VI004 = {
                    "msg_uid":str(uuid.uuid1()),#string,消息序号
                    "msg_name":"VI004",#string,消息名称
                    "sender":"VI",#string,发送方
                    "timestamp":int(time.time()*1000),#long, 时间戳,单位毫秒
                    "receiver":"MC", #string,接收方
                    "craneId":"404-1", #string, 设备号
                    "data":SpreaderPositionStatus #SpreaderPositionStatus,吊具位置状态
                }
                # time.sleep(0.001 * abs(120-(int(VI004['timestamp']) - int(tik))))
                time.sleep(0.02)
                set_global('VI004', VI004)
                # print(VI004)
                VI2MC_pub.send_msg(json.dumps(VI004))


if __name__ == "__main__":
    spread_pos_thread = spreader_pos()
    spread_pos_thread.start()

#     import cv2
#     import numpy as np
#     import time

#     target_process = det_target(config_det_target)
    
#     ## ==== ##  
#     from cam_utils.camsdk import hksdk as camera_sdk
#     cap_101 = camera_sdk.Device('101', '10.141.1.101', 8000, 'admin', 'Dnt@QC2023', (2560, 1400))

#     ret_flag, error_code = cap_101.login()
#     if not ret_flag:
#         print("登录失败:", error_code)
#         exit()
#     flag, stutas = cap_101.open()
#     print(flag, stutas)

#     client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     server_address = ("127.0.0.1", 10001)    
#     while True:
#         flag, trolley_pos, hoist_height, lock_state, spreader_double_state = recv_plc()
#         time1 = time.time()
#         ret_flag, frame = cap_101.read()
#         if ret_flag:
#             print(int(time.time()*1000))
#             target_process.rec_angle(frame)  
#             print(int(time.time()*1000))
#             (cx, cy), (width, height), angle, has_target = target_process.get_result()           
#             print(int(time.time()*1000))
#             # box = cv2.boxPoints(((cx, cy), (width, height), angle))
#             # box = np.intp(box)
#             # cv2.drawContours(frame, [box], 0, (0, 255, 0), 2)
#             # cv2.imwrite("res1.png", frame)      
#             print(int(time.time()*1000))
#             X_cam, Y_cam, theta = cal_angle(cx, cy, 46-hoist_height)
#             print(int(time.time()*1000))
#             VI004 = renew_VI004(has_target, X_cam, Y_cam, theta, angle, trolley_pos, 46-hoist_height, lock_state, spreader_double_state)
            
#             send_msg = str(json.dumps(VI004, ensure_ascii=False))
#             client_socket.sendto(send_msg.encode(), server_address)  
#             print(int(time.time()*1000))          
#             print(send_msg)
    
#     ## ==== ##  
#     img_path = "E:\\workspace\\tianji\\test_3\\VI\\test_data\\target\\picture20240408_164240835.jpeg"
#     img = cv2.imread(img_path)
    
#     def process(img, test_process: det_target):
#         test_process.rec_angle(img)
#         (cx, cy), (width, height), angle = test_process.get_result()
#         print(test_process.get_result())
#         box = cv2.boxPoints(test_process.get_result())
#         box = np.intp(box)
#         cv2.drawContours(img, [box], 0, (0, 255, 0), 2)
#         cv2.imwrite("res.png", img)

#     process(img, target_process)

#     ## ==== ##  
#     vedio_path = "E:\\workspace\\tianji\\test_3\\VI\\test_data\\target\\ch0001_20240401T144048Z_20240401T150443Z_X00000010402000000.mp4"
#     cap = cv2.VideoCapture(vedio_path)
#     kp = 0
#     while True:
#         # flag, trolley_pos, rope_pos, lock_state, spreader_double_state = recv_plc()
#         ret = cap.grab()
#         kp += 1
#         if kp % 61 == 0:
#             kp = 0
#             ret, img = cap.retrieve()          
            
#             target_process.rec_angle(img)  
#             (cx, cy), (width, height), angle, has_target = target_process.get_result()
                      
#             # X_cam, Y_cam, theta = cal_angle(cx, cy, rope_pos)

#             print(cal_angle(cx, cy, 15))

#             box = cv2.boxPoints(target_process.get_result())
#             box = np.intp(box)
#             cv2.drawContours(img, [box], 0, (0, 255, 0), 2)
#             cv2.imwrite("res.png", img)

#             time.sleep(0.03)

