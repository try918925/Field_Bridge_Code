from global_info import * 
import threading
import zmq
import json

class recv_plc(threading.Thread):
    '''
        收取主控广播消息 更新PLC状态MC001
    '''
    def __init__(self, ):
        super().__init__()
        MCPUB_url = 'tcp://10.142.1.200:9000'
        MCPUB_sub_context = zmq.Context()
        self.MCPUB_sub_socket = MCPUB_sub_context.socket(zmq.SUB)
        self.MCPUB_sub_socket.setsockopt(zmq.SUBSCRIBE, b'')
        self.MCPUB_sub_socket.setsockopt(zmq.LINGER, 0)
        self.MCPUB_sub_socket.setsockopt(zmq.CONFLATE, 1)
        self.MCPUB_sub_socket.connect(MCPUB_url)

        self.logcnt = 0 # int
    
    def run(self, ):
        while True:
            MCPUB_msg = json.loads(self.MCPUB_sub_socket.recv_string())
            if MCPUB_msg['msg_name'] == 'MC001':
                set_global('MC001', MCPUB_msg)
            else:
                print('erro info \t', json.dumps(MCPUB_msg))
                error_logger.info(f'erro info \t {json.dumps(MCPUB_msg)}')
            ## 间隔50 * 20 ms 输出一次
            self.logcnt += 1
            if self.logcnt > 50 and MCPUB_msg['msg_name'] == 'MC001':
                self.logcnt = self.logcnt % 50
                MC001 = get_global('MC001')
                # key_logger.info(json.dumps(MC001))
                now_y, now_z = MC001['data']['trolley_pos'], MC001['data']['hoist_height']
                now_vy, now_vz = MC001['data']['trolley_vel'], MC001['data']['rope_vel']
                print(now_y, now_z, now_vy, now_vz)
        
