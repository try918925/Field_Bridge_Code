from pathlib import Path
import sys
import os
os.environ['KMP_DUPLICATE_LIB_OK']='True'

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]  # YOLOv5 root directory
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative


from global_info import *
from initializers import *
from workers import *

import logging
import socket
import threading
import time
import zmq

def set_midlock(midlock_value:int):
    '''
    midlock_value: 11-中锁缩运动  10-中锁缩停止，
           21-中锁伸运动  20-中锁伸停止
    '''
    import uuid
    send_msg = get_global('CT001') 
    send_msg["timestamp"] = int(time.time() * 1000)
    send_msg["msg_uid"] = str(uuid.uuid1())
    send_msg["data"] = [ {"cmd": "spreader_mid_lock", "value": midlock_value}, ]
    set_global('CT001', send_msg)
    send_msg = json.dumps(send_msg, ensure_ascii=False)
    CT2MC_pub.send_msg(send_msg)
    print("at time {} send msg to MC:\n{}\n".format(time.asctime(time.localtime()), send_msg))  

def test_cmd( ):
    '''
    控制系统速度清零, 请求切手动
    '''
    for i in range(10):
        time.sleep(0.1)
        set_midlock(21)
    set_midlock(20)

def main():
    refresh_MC001 = recv_plc()
    process_MC2CT = recv_MC2CT()
    heartbeat = CT_heartbeat(refresh_MC001, process_MC2CT)
    safe_monitor = ctrl_monitor()
    anti_swing = thread_anti_swing()
    # cal_relative_pos_thread = cal_relative_pos()
    # cal_midlock_thread = cal_midlock()

    refresh_MC001.start()
    process_MC2CT.start()
    safe_monitor.start()
    heartbeat.start()
    anti_swing.start()
    # cal_relative_pos_thread.start()
    # cal_midlock_thread.start()

    
if __name__ == '__main__':
    main()
