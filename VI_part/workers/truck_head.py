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
import socket
import threading
import traceback
import copy
from configs.lane_info import LANE_INFO
from global_info import *
from initializers import *


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


class car_head_detect(threading.Thread):
    def __init__(self, ):
        super().__init__()
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
                    'trolley_c': 1388,
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

    def truck_head_detect(self, trolley_pos, lock_state, now_spreader):
        lane = None
        now_x = -1
        TruckHeadRecognizeResult = get_global('TruckHeadRecognizeResult')
        if LANE_INFO['lane_6']['center'] - 2.3 < trolley_pos < LANE_INFO['lane_6']['center'] + 2.3:
            lane = '6'
        elif LANE_INFO['lane_5']['center'] - 2.3 < trolley_pos < LANE_INFO['lane_5']['center'] + 2.3:
            lane = '5'
        elif LANE_INFO['lane_4']['center'] - 2.3 < trolley_pos < LANE_INFO['lane_4']['center'] + 2.3:
            lane = '4'
        elif LANE_INFO['lane_3']['center'] - 2.3 < trolley_pos < LANE_INFO['lane_3']['center'] + 2.3:
            lane = '3'
        elif LANE_INFO['lane_2']['center'] - 2.3 < trolley_pos < LANE_INFO['lane_2']['center'] + 2.3:
            lane = '2'

        if lane is not None:
            # oxywh
            truck_head_obj = TruckHeadRecognizeResult[lane]
            for _, class_name, _, _, oxywh in truck_head_obj:
                if class_name == 'car_front':
                    now_x = oxywh[0]
            # 开锁：抓箱
            if lock_state != 1:
                now_state = 'LOAD'
            else:
                now_state = 'DSCH'



            now_center = self.params[lane][now_state]['guid_c']
            if now_spreader == '20':
                min_x = now_center - 200
                max_x = now_center + 200
            elif now_spreader == '40':
                min_x = now_center - 400
                max_x = now_center + 400
            else:
                min_x = now_center - 440
                max_x = now_center + 440

            if len(truck_head_obj) > 0 and now_x > 0:
                # print('=========truckhead==============')
                # print(now_x, min_x, max_x)
                if min_x - 100 < now_x < max_x + 100:
                    Ep = {
                        "exception_code": 'E206',  # int,异常代码
                        "detail": f"catch center will attack truck head",  # string,具体信息描述
                        "happen_time": str(int(time.time())),  # long, 时间戳,单位毫秒
                        "has_solved": False,  # bool,是否已解决
                        "solve_time": None  # long, 时间戳,单位毫秒
                    }
                    set_VI003(Ep)

    def run(self):
        try:
            while True:
                time.sleep(0.04)
                now_spreader = '20'
                MC001 = get_global('MC001')
                trolley_height = MC001['data']['hoist_height']
                trolley_pos = MC001['data']['trolley_pos']
                rope_vel = MC001['data']['rope_vel']
                lock_state = MC001['data']['lock_state']
                spreader_20 = MC001['data']['spreader_20f']
                spreader_40 = MC001['data']['spreader_40f']
                spreader_45 = MC001['data']['spreader_45f']

                if spreader_20 == 1:
                    now_spreader = '20'
                elif spreader_40 == 1:
                    now_spreader = '40'
                elif spreader_45 == 1:
                    now_spreader = '45'
                if trolley_height < 10 and rope_vel < 0:
                    self.truck_head_detect(trolley_pos, lock_state, now_spreader)

        except Exception as error:
            exception_traceback = traceback.format_exc()
            error_logger.error(f'{type(error).__name__}: {error}\n detail: {exception_traceback}')

if __name__ == '__main__':
    a = car_head_detect()
    a.run()
