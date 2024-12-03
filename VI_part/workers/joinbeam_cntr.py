'''
    更新VI001字段, 识别内容包括左右箱号/iso号/箱门朝向/锁钮/铅封
    结合plc位置做识别: 在不同范围内调用不同相机, 1车道 47.41 | 2车道 42.9 | 3车道 38.4 |
                                             4车道小车33.82 | 5车道 25.32 | 6车道小车21.11
    左联系梁刷新第一个集装箱识别结果, 右联系梁刷新第二个识别结果
'''

import time
import uuid
import zmq
import json
import math
import threading
import cv2
import traceback
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
import configs.config_det_door as config_det_door
from configs.cam_info import CAMERA_DICT
from configs.lane_info import LANE_INFO
from algorithms.yolov5.predictor.det_predictor import YOLOv5Detector
from algorithms.ppocr.infer_det_rec import OCR_process
from cam_utils.camsdk import hksdk as camera_sdk
from configs import config_qf_cls
from algorithms.yolov5.predictor.cls_predictor import YOLOv5Classifier

global joinbeam_cntr_lock  # 联系梁上相机同时赋值时的保护
joinbeam_cntr_lock = threading.Lock()


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


def select_best_num(container_num, score, isLeft):
    container_info = get_global('Container_INFO')
    left_num = container_info.get('container_num_front')
    center_num = container_info.get('container_num_center')
    right_num = container_info.get('container_num_rear')
    left_score = container_info.get('thresh_front')
    center_score = container_info.get('thresh_center')
    rear_score = container_info.get('thresh_rear')

    MC301 = get_global('MC301')
    if MC301['data']['guide_mission']['work_type'] != 'LOAD':
        return container_num
    else:
        lane_id = MC301['data']['guide_mission']['lane_id']
        VI002 = get_global('VI002')
        recognize_results = VI002['data']['truck_recognize_results']
        result_info = recognize_results[int(lane_id) - 1]['recognizeResults'][4]

        final_num = []
        final_score = []
        last_number = []
        last_score = []

        if container_num is None:
            container_num = ['None']

        if result_info is not None:
            state = result_info.get('result')

            if state not in ('101', '000'):

                last_number = left_num or right_num or center_num
                last_score = left_score or rear_score or center_score

                if last_number is None:
                    last_number = ['', '']

                if len(container_num) > 0 and len(last_number) > 0:
                    if score[0] > last_score[0] and container_num[0] != last_number[0]:
                        final_num.append(container_num[0])
                        final_score.append(score[0])
                    else:
                        final_num.append(last_number[0])
                        final_score.append(last_score[0])

                    if score[1] > last_score[1] and container_num[1] != last_number[1]:
                        final_num.append(container_num[1])
                        final_score.append(score[1])
                    else:
                        final_num.append(last_number[1])
                        final_score.append(last_score[1])

                elif len(container_num) == 0 and len(last_number) > 0:
                    final_num = last_number
                    final_score = last_score

                elif len(container_num) > 0 and len(last_number) == 0:
                    final_num = container_num
                    final_score = score

                container_info['container_num_front'] = final_num
                container_info['thresh_front'] = final_score
                container_info['container_num_center'] = final_num
                container_info['thresh_center'] = final_score
                container_info['container_num_rear'] = final_num
                container_info['thresh_rear'] = final_score
                set_global('Container_INFO', container_info)
            else:
                last_number = [left_num, right_num]
                last_score = [left_score, rear_score]
                # print('==========================')
                # print('==========================')
                # print('==========================')
                # print(last_score)
                # print(left_score, rear_score)
                # print('==========================')


                if isLeft:
                    if last_number[0] is None:
                        last_number[0] = ['', '']
                    if len(container_num) > 0 and len(last_number[0]) > 0:
                        if score[0] > last_score[0][0] and container_num[0] != last_number[0][0]:
                            final_num.append(container_num[0])
                            final_score.append(score[0])
                        else:
                            final_num.append(last_number[0][0])
                            final_score.append(last_score[0][0])

                        if score[1] > last_score[0][1] and container_num[1] != last_number[0][1]:
                            final_num.append(container_num[1])
                            final_score.append(score[1])
                        else:
                            final_num.append(last_number[0][1])
                            final_score.append(last_score[0][1])

                    elif len(container_num) == 0 and len(last_number[0]) > 0:
                        final_num = last_number[0]
                        final_score = last_score[0]

                    elif len(container_num) > 0 and len(last_number[0]) == 0:
                        final_num = container_num
                        final_score = score

                    container_info['container_num_front'] = final_num
                    container_info['thresh_front'] = final_score

                else:
                    if last_number[1] is None:
                        last_number[1] = ['', '']
                    if len(container_num) > 0 and len(last_number[1]) > 0:
                        if score[0] > last_score[1][0] and container_num[0] != last_number[1][0]:
                            final_num.append(container_num[0])
                            final_score.append(score[0])
                        else:
                            final_num.append(last_number[1][0])
                            final_score.append(last_score[1][0])

                        if score[1] > last_score[1][1] and container_num[1] != last_number[1][1]:
                            final_num.append(container_num[1])
                            final_score.append(score[1])
                        else:
                            final_num.append(last_number[1][1])
                            final_score.append(last_score[1][1])

                    elif len(container_num) == 0 and len(last_number[1]) > 0:
                        final_num = last_number[1]
                        final_score = last_score[1]

                    elif len(container_num) > 0 and len(last_number[1]) == 0:
                        final_num = container_num
                        final_score = score

                    container_info['container_num_rear'] = final_num
                    container_info['thresh_rear'] = final_score
                set_global('Container_INFO', container_info)

        return final_num


def VI002_renew_VI001(container_info, state):
    VI001 = get_global('VI001')
    VI001['msg_uid'] = str(uuid.uuid1())  # string,消息序号
    VI001['timestamp'] = str(int(time.time() * 1000))  # long, 时间戳,单位毫秒
    datetime = int(time.time() * 1000)
    if not state:
        VI001['data']['container2'] = {}
        VI001['data']['container1'] = {"recognizeResults": [None] * 5}
        VI001["data"]['container1']["recognizeResults"][0] = {
            "item": "container_code",
            "state": 1,
            "result": str(container_info[0]),
            "images": [
                {
                    "image": '',
                    "datetime": datetime
                }
            ]
        }

        VI001["data"]['container1']["recognizeResults"][1] = {
            "item": "container_iso",
            "state": 1,
            "result": str(container_info[1]),
            "images": [
                {
                    "image": '',
                    "datetime": datetime
                }
            ]
        }
    else:
        VI001['data']['container1'] = {"recognizeResults": [None] * 5}
        VI001["data"]['container1']["recognizeResults"][0] = {
            "item": "container_code",
            "state": 1,
            "result": str(container_info[0][0]),
            "images": [
                {
                    "image": '',
                    "datetime": datetime
                }
            ]
        }

        VI001["data"]['container1']["recognizeResults"][1] = {
            "item": "container_iso",
            "state": 1,
            "result": str(container_info[0][1]),
            "images": [
                {
                    "image": '',
                    "datetime": datetime
                }
            ]
        }
        VI001['data']['container2'] = {"recognizeResults": [None] * 5}
        VI001["data"]['container2']["recognizeResults"][0] = {
            "item": "container_code",
            "state": 1,
            "result": str(container_info[1][0]),
            "images": [
                {
                    "image": '',
                    "datetime": datetime
                }
            ]
        }

        VI001["data"]['container2']["recognizeResults"][1] = {
            "item": "container_iso",
            "state": 1,
            "result": str(container_info[1][1]),
            "images": [
                {
                    "image": '',
                    "datetime": datetime
                }
            ]
        }

    set_global('VI001', VI001)
    VI2MC_pub.send_msg(json.dumps(VI001))


def VI002_VI001():
    """
    在抓箱闭锁时，将 VI002 的箱号赋给 VI001
    """
    # 获取全局变量 Container_INFO
    container_info = get_global('Container_INFO')
    left_num = container_info.get('container_num_front')
    center_num = container_info.get('container_num_center')
    right_num = container_info.get('container_num_rear')

    print('============================')
    print(container_info)
    print([left_num, right_num])
    print('============================')

    # 获取全局变量 MC301 和 VI002
    MC301 = get_global('MC301')
    lane_id = MC301['data']['guide_mission']['lane_id']  # 获取当前车道ID
    VI002 = get_global('VI002')

    recognize_results = VI002['data']['truck_recognize_results']
    if recognize_results[int(lane_id) - 1] is not None:
        try:
            result_info = recognize_results[int(lane_id) - 1]['recognizeResults'][4]

            if result_info is not None:
                state = result_info.get('result')

                if state not in ('101', '000'):
                    container_number = left_num or right_num or center_num
                    VI002_renew_VI001(container_number, False)
                else:
                    VI002_renew_VI001([left_num, right_num], True)
        except Exception as error:
            pass


class left_joinbeam(threading.Thread):
    def __init__(self, ):
        super().__init__()
        self.qf_cls = YOLOv5Classifier.from_config(config_qf_cls)
        self.door_detector = YOLOv5Detector.from_config(config_det_door)
        config_dict = {
            "ocr_det_config": "./configs/door_container_num_det_r50_db++_td_tr.yml",
            "ocr_rec_config": "./configs/door_container_num_rec_en_PP-OCRv3.yml"
        }
        self.door_ocr_process = OCR_process(config_dict)
        self.cams_dict = {
            'cam_132': None,  # cam device
            'cam_133': None,
            'cam_134': None,
            'cam_135': None,
            'cam_136': None,
        }
        self.init_cams()
        self.result = {
            "area": 0,
            "need_rec": 0,  # 初始为0, 有箱门面为1，开始无箱门面+=1, 至三帧无结果后传出一次
            "keyframe": None,  # 箱门面
            "crop_img": None,
            "timestamp": None,
            "container_info": None,  # 箱号
            "container_score": 0.0,
            "container_door_dir": None,
            "container_lock": None,
            "container_seal": 0,  # 0无，1有
        }

    def run(self, ):
        need_renew = False
        count = 0
        last_time = time.time()
        while True:
            time.sleep(0.04)
            try:
                MC301 = get_global('MC301')
                work_type = MC301['data']['guide_mission']['work_type']
                MC001 = get_global('MC001')
                # 如果吊具上无集装箱, 不进行后续
                if MC001['data']['lock_state'] != 1:
                    count = 0
                    continue

                count += 1
                if count == 1 and work_type == 'LOAD':
                    VI002_VI001()
                    # pass
                # 不在对应区域不做识别, 且
                if not ((19.0 < MC001['data']['trolley_pos'] < 50.0) and \
                        (7.5 < MC001['data']['hoist_height'] < 14.5)):  # todo ！!
                    if need_renew:  # 更新一次识别结果
                        self.renew_VI001()
                        key_logger.info('trolley_pos-{} hoist_height-{} renew_VI001-{}' \
                                        .format(MC001['data']['trolley_pos'], MC001['data']['hoist_height'],
                                                get_global('VI001')))
                        need_renew = False
                        # 清空result
                        self.result = {
                            "area": 0,
                            "need_rec": 0,  # 初始为0, 有箱门面为1，开始无箱门面+=1, 至三帧无结果后传出一次
                            "keyframe": None,  # 箱门面
                            "crop_img": None,
                            "timestamp": None,
                            "container_info": None,  # 箱号
                            "container_score": 0.0,
                            "container_door_dir": None,
                            "container_lock": None,
                            "container_seal": 0,  # 0无，1有
                        }
                    continue  # 超出范围后不做后续识别

                # if self.result['need_rec'] == 3:
                #     # 连续有三次需要识别的, 传出一次识别结果
                #     self.renew_VI001()
                #     key_logger.info('count need_rec renew_VI001-{}'.format(get_global('VI001')))

                ret, frame, device, cam_name = self.select_cam(MC001['data']['trolley_pos'])
                if not ret:
                    # error_logger.warning('not get frame')
                    continue

                now_time = time.time()
                if now_time - last_time >= 300:
                    last_time = now_time
                    check_res = check_img_cam(device, cam_name, frame)
                    if check_res != 0:
                        set_VI003(check_res)

                obj_list = self.door_detector.infer([frame])[0]

                if len(obj_list) > 0:  # 如果检测到视野内目标
                    for class_id, class_name, score, p1p2, oxywh in obj_list:
                        x1, y1, x2, y2 = map(int, p1p2)
                        xo, yo, w, h = oxywh
                        area = w * h
                        if class_name == "BD" or class_name == "FD":
                            # 箱门面用面积筛选关键帧
                            # 面积大于 800 * 1000 todo: 确认拍摄完整箱门的条件
                            if (area > 300000) and (area > self.result["area"]) and (700 < xo < 3140) and (
                                    500 < yo < 1660):
                                need_renew = True  # 第一次有识别结果，记录需要刷新一次
                                if self.result["need_rec"] == 0:
                                    self.result["need_rec"] = 1
                                else:
                                    self.result["need_rec"] += 1

                                # key_logger.info(f'left joinbeam cam {class_id}, {class_name}, {score}, {p1p2}, {oxywh}')
                                self.result["area"] = area
                                self.result["keyframe"] = frame
                                self.result["crop_img"] = frame[y1: y2, x1: x2]
                                self.result["timestamp"] = int(time.time() * 1000)

                                if class_name == "BD":
                                    self.result["container_door_dir"] = 0  # 0-面海向左 1-面海向右
                                elif class_name == "FD":
                                    self.result["container_door_dir"] = 1  # 0-面海向左 1-面海向右
                        else:
                            crop_img = frame[y1: y2, x1: x2]
                            seal_result = self.qf_cls.infer([crop_img])
                            if seal_result[0][0][0] == 0:
                                self.result["container_seal"] += 1



            except Exception as error:
                exception_traceback = traceback.format_exc()
                error_logger.error(f'{type(error).__name__}: {error}\n detail: {exception_traceback}')

                # todo: set Vi003 E202

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

    def select_cam(self, trolley_pos):
        '''
        根据小车位置, 反馈要识别的图像
        车道中心 +- 2.3m调用对应相机, 单个吊具上只可能出现在一个车道
        '''
        cam = ''
        device, ret, frame = None, False, None
        if LANE_INFO['lane_6']['center'] - 2.3 < trolley_pos < LANE_INFO['lane_6']['center'] + 2.3:
            device = self.cams_dict['cam_136']
            cam = 'cam_136'
        elif LANE_INFO['lane_5']['center'] - 2.3 < trolley_pos < LANE_INFO['lane_5']['center'] + 2.3:
            device = self.cams_dict['cam_135']
            cam = 'cam_135'
        elif LANE_INFO['lane_4']['center'] - 2.3 < trolley_pos < LANE_INFO['lane_4']['center'] + 2.3:
            device = self.cams_dict['cam_134']
            cam = 'cam_134'
        elif LANE_INFO['lane_3']['center'] - 2.3 < trolley_pos < LANE_INFO['lane_3']['center'] + 2.3:
            device = self.cams_dict['cam_133']
            cam = 'cam_133'
        elif LANE_INFO['lane_2']['center'] - 2.3 < trolley_pos < LANE_INFO['lane_2']['center'] + 2.3:
            device = self.cams_dict['cam_132']
            cam = 'cam_132'
        if device is not None:
            ret, frame = device.read()
        return ret, frame, device, cam

    def renew_VI001(self, ):
        '''
        左联系梁将result更新到VI001
        '''

        if self.result["container_seal"] > 0:
            self.result["container_seal"] = 1
        containernum, iso, score = self.door_ocr_process.process_imgs([self.result["crop_img"]])
        if len(score) <= 1:
            score = score.append(0.0)
        container_info = select_best_num([containernum, iso], score, True)
        if len(container_info) < 1:
            container_info = ['', '']
        containernum, iso = container_info[0], container_info[1]

        self.result["container_info"] = [containernum, iso]
        self.result["container_score"] = score
        datetime = self.result["timestamp"]
        save_name = os.path.join(config_det_door.RESULT_DIR, f"left_frame_{datetime}_{containernum}_{iso}.jpg")
        cv2.imwrite(os.path.join(config_det_door.RESULT_DIR, f"left_frame_{datetime}_{containernum}_{iso}.jpg"), \
                    self.result["keyframe"])
        cv2.imwrite(os.path.join(config_det_door.RESULT_DIR, f"left_crop_{datetime}_{containernum}_{iso}.jpg"), \
                    self.result["crop_img"])
        global joinbeam_cntr_lock
        with joinbeam_cntr_lock:
            VI001 = get_global('VI001')
            VI001['msg_uid'] = str(uuid.uuid1())  # string,消息序号
            VI001['timestamp'] = str(int(time.time() * 1000))  # long, 时间戳,单位毫秒

            VI001['data']['container1'] = {"recognizeResults": [None] * 5}
            VI001["data"]['container1']["recognizeResults"][0] = {
                "item": "container_code",
                "state": 1,
                "result": str(containernum),
                "images": [
                    {
                        "image": os.path.relpath(save_name, '/home/root123'),
                        "datetime": datetime
                    }
                ]
            }

            VI001["data"]['container1']["recognizeResults"][1] = {
                "item": "container_iso",
                "state": 1,
                "result": str(iso),
                "images": [
                    {
                        "image": os.path.relpath(save_name, '/home/root123'),
                        "datetime": datetime
                    }
                ]
            }

            VI001["data"]['container1']["recognizeResults"][2] = {
                "item": "container_door_dir",
                "state": 1,
                "result": str(self.result['container_door_dir']),
                "images": [
                    {
                        "image": os.path.relpath(save_name, '/home/root123'),
                        "datetime": datetime
                    }
                ]
            }
            if self.result['container_door_dir'] != 1:
                VI001["data"]['container1']["recognizeResults"][4] = {
                    "item": "container_seal",
                    "state": 1,
                    "result": self.result['container_seal'],
                    "images": [
                        {
                            "image": os.path.relpath(save_name, '/home/root123'),
                            "datetime": datetime
                        }
                    ]
                }

            set_global('VI001', VI001)
        VI2MC_pub.send_msg(json.dumps(VI001))


class right_joinbeam(threading.Thread):
    def __init__(self, ):
        super().__init__()
        self.qf_cls = YOLOv5Classifier.from_config(config_qf_cls)
        self.door_detector = YOLOv5Detector.from_config(config_det_door)
        config_dict = {
            "ocr_det_config": "./configs/door_container_num_det_r50_db++_td_tr.yml",
            "ocr_rec_config": "./configs/door_container_num_rec_en_PP-OCRv3.yml"
        }
        self.door_ocr_process = OCR_process(config_dict)
        self.cams_dict = {
            'cam_142': None,  # cam device
            'cam_143': None,
            'cam_144': None,
            'cam_145': None,
            'cam_146': None,
        }
        self.init_cams()
        self.result = {
            "area": 0,
            "need_rec": 0,  # 初始为0, 有箱门面为1，开始无箱门面+=1, 至三帧无结果后传出一次
            "keyframe": None,  # 箱门面
            "crop_img": None,
            "timestamp": None,
            "container_info": None,  # 箱号
            "container_score": 0.0,
            "container_door_dir": None,
            "container_lock": None,
            "container_seal": 0,  # 0无，1有
        }

    def run(self, ):
        need_renew = False
        count = 0
        last_time = time.time()
        while True:
            time.sleep(0.05)
            try:
                MC001 = get_global('MC001')
                MC301 = get_global('MC301')
                work_type = MC301['data']['guide_mission']['work_type']
                Container_INFO = get_global('Container_INFO')

                # 如果吊具上无集装箱, 不进行后续
                if MC001['data']['lock_state'] != 1:
                    count += 1
                    # 开锁之后刷新这个值
                    if count == 1 and work_type == 'LOAD':
                        Container_INFO['container_num_front'] = []
                        Container_INFO['thresh_front'] = 0.0
                        Container_INFO['container_num_rear'] = []
                        Container_INFO['thresh_rear'] = 0.0
                        Container_INFO['container_num_center'] = []
                        Container_INFO['thresh_center'] = 0.0
                        set_global('Container_INFO', Container_INFO)
                    continue

                count = 0
                # 不在对应区域不做识别, 且
                if not ((19.0 < MC001['data']['trolley_pos'] < 50.0) and \
                        (7.0 < MC001['data']['hoist_height'] < 15)):
                    if need_renew:  # 更新一次识别结果
                        self.renew_VI001()
                        key_logger.info('trolley_pos-{} hoist_height-{} renew_VI001-{}' \
                                        .format(MC001['data']['trolley_pos'], MC001['data']['hoist_height'],
                                                get_global('VI001')))
                        need_renew = False
                        # 清空result
                        self.result = {
                            "area": 0,
                            "need_rec": 0,  # 初始为0, 有箱门面为1，开始无箱门面+=1, 至三帧无结果后传出一次
                            "keyframe": None,  # 箱门面
                            "crop_img": None,
                            "timestamp": None,
                            "container_info": None,  # 箱号
                            "container_score": 0.0,
                            "container_door_dir": None,
                            "container_lock": None,
                            "container_seal": 0,  # 0无，1有
                        }
                    continue  # 超出范围后不做后续识别

                # if self.result['need_rec'] == 3:
                #     # 连续有三次需要识别的, 传出一次识别结果
                #     self.renew_VI001()
                #     key_logger.info('count need_rec renew_VI001-{}'.format(get_global('VI001')))

                ret, frame, device, cam_name = self.select_cam(MC001['data']['trolley_pos'])
                if not ret:
                    # error_logger.warning('not get frame')
                    continue

                now_time = time.time()
                if now_time - last_time >= 300:
                    last_time = now_time
                    check_res = check_img_cam(device, cam_name, frame)
                    if check_res != 0:
                        set_VI003(check_res)

                obj_list = self.door_detector.infer([frame])[0]
                # print(obj_list)
                if len(obj_list) > 0:  # 如果检测到视野内目标
                    for class_id, class_name, score, p1p2, oxywh in obj_list:
                        x1, y1, x2, y2 = map(int, p1p2)
                        xo, yo, w, h = oxywh
                        area = w * h
                        if class_name == "BD" or class_name == "FD":
                            # 箱门面用面积筛选关键帧
                            # 面积大于 800 * 1000 todo: 确认拍摄完整箱门的条件
                            if (area > 300000) and (area > self.result["area"]) and (700 < xo < 3140) and (
                                    500 < yo < 1660):
                                # if (area > 300000 ) and (area > self.result["area"]) and (700 < xo < 3180 ) and (500 < yo < 1660 ) and (w/h<1.8):
                                need_renew = True  # 第一次有识别结果，记录需要刷新一次
                                if self.result["need_rec"] == 0:
                                    self.result["need_rec"] = 1
                                else:
                                    self.result["need_rec"] += 1

                                # key_logger.info(f'left joinbeam cam {class_id}, {class_name}, {score}, {p1p2}, {oxywh}')
                                self.result["area"] = area
                                self.result["keyframe"] = frame
                                self.result["crop_img"] = frame[y1: y2, x1: x2]
                                self.result["timestamp"] = int(time.time() * 1000)

                                if class_name == "BD":
                                    self.result["container_door_dir"] = 1  # 0-面海向左 1-面海向右
                                elif class_name == "FD":
                                    self.result["container_door_dir"] = 0  # 0-面海向左 1-面海向右
                        else:
                            crop_img = frame[y1: y2, x1: x2]
                            seal_result = self.qf_cls.infer([crop_img])
                            if seal_result[0][0][0] == 0:
                                self.result["container_seal"] += 1

            except Exception as error:
                exception_traceback = traceback.format_exc()
                error_logger.error(f'{type(error).__name__}: {error}\n detail: {exception_traceback}')
                # todo: set Vi003 E202

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

    def select_cam(self, trolley_pos):
        '''
        根据小车位置, 反馈要识别的图像
        车道中心 +- 2.3m调用对应相机, 单个吊具上只可能出现在一个车道
        '''
        cam = ''
        device, ret, frame = None, False, None
        if LANE_INFO['lane_6']['center'] - 2.0 < trolley_pos < LANE_INFO['lane_6']['center'] + 2.0:
            device = self.cams_dict['cam_146']
            cam = 'cam_146'
        elif LANE_INFO['lane_5']['center'] - 2.3 < trolley_pos < LANE_INFO['lane_5']['center'] + 2.3:
            device = self.cams_dict['cam_145']
            cam = 'cam_145'
        elif LANE_INFO['lane_4']['center'] - 2.3 < trolley_pos < LANE_INFO['lane_4']['center'] + 2.3:
            device = self.cams_dict['cam_144']
            cam = 'cam_144'
        elif LANE_INFO['lane_3']['center'] - 2.3 < trolley_pos < LANE_INFO['lane_3']['center'] + 2.3:
            device = self.cams_dict['cam_143']
            cam = 'cam_143'
        elif LANE_INFO['lane_2']['center'] - 2.3 < trolley_pos < LANE_INFO['lane_2']['center'] + 2.3:
            device = self.cams_dict['cam_142']
            cam = 'cam_142'
        if device is not None:
            ret, frame = device.read()
        # print(trolley_pos, device, ret, type(frame))
        return ret, frame, device, cam

    def renew_VI001(self, ):
        '''
        右联系梁将result更新到VI002
        '''
        if self.result["container_seal"] > 0:
            self.result["container_seal"] = 1
        containernum, iso, score = self.door_ocr_process.process_imgs([self.result["crop_img"]])
        if len(score) <= 1:
            score.append(0.0)
        container_info = select_best_num([containernum, iso], score, False)
        if len(container_info) == 0:
            container_info = ['', '']
        containernum, iso = container_info[0], container_info[1]
        self.result["container_info"] = [containernum, iso]
        self.result["container_score"] = score
        datetime = self.result["timestamp"]
        save_name = os.path.join(config_det_door.RESULT_DIR, f"right_frame_{datetime}_{containernum}_{iso}.jpg")
        cv2.imwrite(os.path.join(config_det_door.RESULT_DIR, f"right_frame_{datetime}_{containernum}_{iso}.jpg"), \
                    self.result["keyframe"])
        cv2.imwrite(os.path.join(config_det_door.RESULT_DIR, f"right_crop_{datetime}_{containernum}_{iso}.jpg"), \
                    self.result["crop_img"])

        global joinbeam_cntr_lock
        with joinbeam_cntr_lock:
            VI001 = get_global('VI001')
            VI001['msg_uid'] = str(uuid.uuid1())  # string,消息序号
            VI001['timestamp'] = str(int(time.time() * 1000))  # long, 时间戳,单位毫秒
            # VI001['data']['container1'] = {"recognizeResults": [None] * 5}
            MC001 = get_global('MC001')
            if MC001['data']['spreader_single_state'] == 1:
                VI001['data']['container2'] = {}
                # 单箱模式更新container1中更对的部分
                if VI001['data']['container1']["recognizeResults"][0] is None \
                        and containernum is not None:
                    VI001['data']['container1']["recognizeResults"][0] = {
                        "item": "container_code",
                        "state": 1,
                        "result": str(containernum),
                        "images": [
                            {
                                "image": os.path.relpath(save_name, '/home/root123'),
                                "datetime": datetime
                            }
                        ]
                    }
                elif len(VI001['data']['container1']["recognizeResults"][0]["result"]) != 11 \
                        and len(containernum) == 11:
                    VI001['data']['container1']["recognizeResults"][0] = {
                        "item": "container_code",
                        "state": 1,
                        "result": str(containernum),
                        "images": [
                            {
                                "image": os.path.relpath(save_name, '/home/root123'),
                                "datetime": datetime
                            }
                        ]
                    }

                if VI001['data']['container1']["recognizeResults"][1] is None \
                        and iso is not None:
                    VI001['data']['container1']["recognizeResults"][1] = {
                        "item": "container_iso",
                        "state": 1,
                        "result": str(iso),
                        "images": [
                            {
                                "image": os.path.relpath(save_name, '/home/root123'),
                                "datetime": datetime
                            }
                        ]
                    }
                elif len(VI001['data']['container1']["recognizeResults"][1]["result"]) != 4 \
                        and len(iso) == 4:
                    VI001['data']['container1']["recognizeResults"][1] = {
                        "item": "container_iso",
                        "state": 1,
                        "result": str(iso),
                        "images": [
                            {
                                "image": os.path.relpath(save_name, '/home/root123'),
                                "datetime": datetime
                            }
                        ]
                    }

                if self.result['container_seal'] != 0:
                    VI001['data']['container1']["recognizeResults"][4] = {
                        "item": "container_seal",
                        "state": 1,
                        "result": self.result['container_seal'],
                        "images": [
                            {
                                "image": os.path.relpath(save_name, '/home/root123'),
                                "datetime": datetime
                            }
                        ]
                    }

            elif MC001['data']['spreader_double_state'] == 1:  # 双箱模式更新container2
                VI001['data']['container2'] = {"recognizeResults": [None] * 5}
                VI001["data"]['container2']["recognizeResults"][0] = {
                    "item": "container_code",
                    "state": 1,
                    "result": str(containernum),
                    "images": [
                        {
                            "image": os.path.relpath(save_name, '/home/root123'),
                            "datetime": datetime
                        }
                    ]
                }

                VI001["data"]['container2']["recognizeResults"][1] = {
                    "item": "container_iso",
                    "state": 1,
                    "result": str(iso),
                    "images": [
                        {
                            "image": os.path.relpath(save_name, '/home/root123'),
                            "datetime": datetime
                        }
                    ]
                }

                VI001["data"]['container2']["recognizeResults"][2] = {
                    "item": "container_door_dir",
                    "state": 1,
                    "result": str(self.result['container_door_dir']),
                    "images": [
                        {
                            "image": os.path.relpath(save_name, '/home/root123'),
                            "datetime": datetime
                        }
                    ]
                }
                if self.result['container_door_dir'] != 0:
                    VI001["data"]['container2']["recognizeResults"][4] = {
                        "item": "container_seal",
                        "state": 1,
                        "result": str(self.result['container_seal']),
                        "images": [
                            {
                                "image": os.path.relpath(save_name, '/home/root123'),
                                "datetime": datetime
                            }
                        ]
                    }

            set_global('VI001', VI001)
        VI2MC_pub.send_msg(json.dumps(VI001))
