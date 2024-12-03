from global_info import * 
import threading
import zmq
import traceback
import json
from initializers import *

def process_MC201():
    '''
    请求陆侧箱信息，
    按车道号return VI001
    '''
    msg = json.dumps(get_global('VI001'))
    VI2MC_pub.send_msg(msg)
    key_logger.info(f'process_MC201 send msg {msg}')


def process_MC202():
    '''
    请求车道集卡识别结果
    按车道号反馈 VI002
    '''
    msg = json.dumps(get_global('VI002'))
    VI2MC_pub.send_msg(msg)
    key_logger.info(f'process_MC202 send msg {msg}')

def process_MC204():
    '''
    感知车道开启/关闭: 把对应车道结果记录置为None
    '''
    key_logger.info(f'process_MC204')

def process_MC205():
    '''
    请求吊具姿态与位置
    return VI004
    '''
    msg = json.dumps(get_global('VI004'))
    VI2MC_pub.send_msg(msg)
    key_logger.info(f'process_MC205 - send msg {msg}')

def process_MC206():
    '''
    人员安全触发, 按相机
    '''
    key_logger.info(f'process_MC206')

def process_MC207():
    '''
    请求图片与视频流信息
    return VI006
    '''
    msg = json.dumps(get_global('VI006'))
    VI2MC_pub.send_msg(msg)
    key_logger.info(f'process_MC207 - send msg {msg}')


def process_MC301():
    '''
    发送引导任务
    '''
    MC301 = get_global('MC301')
    Has_task = get_global('Has_task')
    lane_id = MC301['data']['guide_mission']['lane_id']
    for i in range(6):
        if int(Has_task[i]['lane']) == int(lane_id):
            Has_task[i]['has_task'] = True
    set_global('Has_task', Has_task)
    key_logger.info(f'process_MC301')

def process_MC302():
    '''
    结束引导任务
    '''
    MC302 = get_global('MC302')
    lane_id = MC302['data']['lane_id']
    Has_task = get_global('Has_task')
    print('================================')
    print('lanelanelane')
    print(lane_id)
    print('lanelanelane')
    for i in range(6):
        if int(Has_task[i]['lane']) == int(lane_id):
            Has_task[i]['has_task'] = False
    set_global('Has_task', Has_task)
    key_logger.info(f'process_MC302')

def process_MC303():
    '''
    请求引导状态
    反馈VI007
    '''
    import copy
    MC303 = get_global('MC303')
    lanid = MC303['lane_id']

    VI007 = get_global('VI007')
    msg = copy.deepcopy(VI007)
    msg['data']['lane_guide_status'] = [msg['data']['lane_guide_status'][int(lanid)-1]]
    VI2MC_pub.send_msg(msg)
    key_logger.info(f'process_MC303 - send msg {msg}')

def process_MC304():
    '''
    请求集卡和集装箱位置
    反馈VI008
    '''
    import copy
    MC304 = get_global('MC304')
    lanid = MC304['data']['lane_id']

    VI008 = get_global('VI008')
    msg = copy.deepcopy(VI008)

    VI2MC_pub.send_msg(json.dumps(msg))
    key_logger.info(f'process_MC304 - send msg {msg}')


def process_MC305():
    '''
    集卡引导车道开启关闭
    '''
    import copy
    MC305 = get_global('MC305')
    VI007 = get_global('VI007')
    WorkLaneSetting = MC305['data']['lane_settings']
    for item in WorkLaneSetting:
        lane_id, activate = item['lane_id'], item['activate']
        if activate:
            VI007['data']['lane_guide_status'][int(lane_id)-1] = {}
        else:
            VI007['data']['lane_guide_status'][int(lane_id)-1] = None
    set_global('VI007', VI007)
    msg = json.dumps(VI007)
    VI2MC_pub.send_msg(msg)
    key_logger.info(f'process_MC304 - send msg {msg}')

def process_MC306():
    '''
    关路安全检测设置
    '''
    key_logger.info(f'process_MC306')


def process_MC307():
    '''
    开启关闭大车轨道障碍检测
    '''
    key_logger.info(f'process_MC307')


def process_MC308():
    '''
    开启关闭大车轨道障碍检测
    反馈障碍物开启关闭状态VI010
    '''
    msg = json.dumps(get_global('VI010'))
    VI2MC_pub.send_msg(msg)
    key_logger.info(f'process_MC308 send msg {msg}')

def process_MC309():
    '''
    查询雾天状态
    反馈雾天检测结果VI011
    '''
    msg = json.dumps(get_global('VI011'))
    VI2MC_pub.send_msg(msg)
    key_logger.info(f'process_MC309 send msg {msg}')

process_VI_dict = {
    # MC -> VI
    "MC201": process_MC201,
    "MC202": process_MC202,
    # "MC203": process_MC203,
    "MC204": process_MC204,
    "MC205": process_MC205,
    "MC206": process_MC206,
    "MC207": process_MC207,

    "MC301": process_MC301,
    "MC302": process_MC302,
    "MC303": process_MC303,
    "MC304": process_MC304,
    "MC305": process_MC305,
    "MC308": process_MC308,
}


class process_MC2VI(threading.Thread):
    '''

    '''
    def __init__(self, ):
        super().__init__()
        MC2VI_url = 'tcp://10.142.1.200:9003'
        MC2VI_sub_context = zmq.Context()
        self.MC2VI_sub_socket = MC2VI_sub_context.socket(zmq.SUB)
        self.MC2VI_sub_socket.setsockopt(zmq.SUBSCRIBE, b'')
        self.MC2VI_sub_socket.setsockopt(zmq.LINGER, 0)
        self.MC2VI_sub_socket.setsockopt(zmq.CONFLATE, 1)
        self.MC2VI_sub_socket.connect(MC2VI_url)
        self.logcnt = 0 # int
    
    def run(self, ):
        while True:
            msg_str = self.MC2VI_sub_socket.recv_string()
            key_logger.info(f"recv {msg_str}:.")
            MC2VI_msg = json.loads(msg_str)
            # key_logger.info(f"recv dict {MC2VI_msg}: {MC2VI_msg['msg_name'] in VI_msg_dict.keys()}.:{VI_msg_dict.keys()}")
            if MC2VI_msg['msg_name'] in VI_msg_dict.keys():
                try:
                    key_logger.info(f"start process {(MC2VI_msg)}:.")
                    set_global(MC2VI_msg['msg_name'], MC2VI_msg)
                    # process_VI_dict[MC2VI_msg['msg_name']]()
                    p = threading.Thread(target =process_VI_dict[MC2VI_msg['msg_name']]())
                    p.start()
                except Exception as error:
                    exception_traceback = traceback.format_exc()
                    error_logger.error(f"Failed process {MC2VI_msg['msg_name']}: \n'{type(error).__name__}: {error}"
                                       f"'detail: {exception_traceback}")
                # process_dict[MC2CT_msg['msg_name']]() 用函数处理会阻塞
            else:
                print('erro info \t', json.dumps(MC2VI_msg))
                error_logger.error('erro info \t', (MC2VI_msg))
            ## 间隔50 * 20 ms 输出一次

