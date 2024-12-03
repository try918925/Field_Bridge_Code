from initializers import *
from global_info import *
# --------------------------------------------------
import threading
import time
import uuid
import json

class CT_heartbeat(threading.Thread):

    def __init__(self, MCPUB_msg_thread: threading.Thread, MC2CT_msg_thread: threading.Thread, ):
        super().__init__()
        self.logger = error_logger
        self._CT2MC_pub = CT2MC_pub
        self._MCPUB_msg_thread = MCPUB_msg_thread
        self._MC2CT_msg_thread = MC2CT_msg_thread
        
    def run(self, ):
        time.sleep(3) # 等待5s所有线程启动
        while True:
            time.sleep(0.2)
            if not self._MCPUB_msg_thread.is_alive():
                error_logger.info("_MCPUB_msg_thread is closesd")
                # todo 发送异常 
                continue
            if not self._MC2CT_msg_thread.is_alive():
                error_logger.info("_MC2CT_msg_thread is closesd")
                # todo 发送异常 
                continue

            CT000 = get_global('CT000')
            CT000["msg_uid"] = str(uuid.uuid1())
            CT000["timestamp"] = int(time.time() * 1000)
            CT000["data"]['heartbeat'] += 1 # 1 -9999
            if CT000["data"]['heartbeat'] > 9999:
                CT000["data"]['heartbeat'] -= 9999
            # if CT000["data"]['heartbeat'] % 100 == 0:
            #     save_global()
            set_global('CT000', CT000)
            CT2MC_pub.send_msg(json.dumps(CT000))  
            
