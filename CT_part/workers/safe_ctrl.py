from global_info import *
from initializers import *
from ctrl_utils import *
import threading
import zmq
import time 

class ctrl_monitor(threading.Thread):

    def __init__(self) -> None:
        '''
        监控当前plc状态的线程:
        如果plc状态时间与控制服务器时间不一致, 速度清零、反馈CT007-E101、请求切手动
        如果到达禁行区域,  速度清零、反馈CT007-E103、请求切手动
        todo: 监控当前执行任务 如果当前位置
        '''
        super().__init__() 
        self.stop_flag = False # 持续执行
    
    def run(self, ):
        time.sleep(3) # 等待消息线程启动并同步信息
        aver_filter = AverageFilter(100)
        while True:
            time.sleep(0.05) # 控制频率
            try: # 用try
                MC001 = get_global('MC001')
                # 非自动模式下不需要校验
                if MC001['data']['ctr_mod_auto'] == 0:
                    continue
                # check time
                plc_time = MC001['timestamp']
                ctrl_time = int(time.time()*1000) # ms
                # if abs(ctrl_time - plc_time) > 1000:
                #     error_logger.error(f"time erro ctrl_time:{ctrl_time} - plc_time {plc_time}")
                #     Ep = {
                #         "exception_code": 'E101',#int,异常代码
                #         "detail":f"{ctrl_time}|{plc_time}", #string,具体信息描述
                #         "happen_time": ctrl_time, #long, 时间戳,单位毫秒
                #         "has_solved": False, #bool,是否已解决
                #         "solve_time": None #long, 时间戳,单位毫秒
                #     }
                #     self.ctrl_stop()
                #     time.sleep(0.001) # 增加延迟控制收发顺序
                #     self.set_CT007(Ep)
                    
                    
                
                # check pos
                # 边界区域：起升高度: < 4.5m  > 45m； 小车方向：< 5m  > 110m
                # 陆侧横梁区域：( 起升  < 10.0m)  (12.0m < 小车方向 < 21.6m)
                # 海侧横梁区域：( 起升  < 10.0m)  (46.8m < 小车方向 < 55.8m)
                trolley_pos, hoist_height = MC001['data']['trolley_pos'], MC001['data']['hoist_height']
                if (trolley_pos < 5.0 or  trolley_pos > 110.0 or hoist_height < 4.5 or hoist_height > 45.0 ) \
                or ((11.0 < trolley_pos < 22.6) and ( hoist_height < 15.0)) \
                or ((45.8 < trolley_pos < 56.8) and ( hoist_height < 15.0)):
                    error_logger.error(f"in danger erea trolley_pos:{trolley_pos} | hoist_height:{hoist_height}")
                    Ep = {
                        "exception_code": 'E103',# str,异常代码
                        "detail":f'{trolley_pos}|{hoist_height}', #string,具体信息描述
                        "happen_time": plc_time, #long, 时间戳,单位毫秒
                        "has_solved": False, #bool,是否已解决
                        "solve_time": None #long, 时间戳,单位毫秒
                    }
                    self.ctrl_stop()
                    time.sleep(0.001) 
                    self.set_CT007(Ep)   

                # 风速                    
                wind_speed = MC001['data']['wind']
                wind_speed = aver_filter.get_value(wind_speed)               
                if wind_speed > 15.0:
                    error_logger.error(f" danger wind_speed:{wind_speed}")
                    Ep = {
                        "exception_code": 'E127',# str,异常代码
                        "detail":f'{wind_speed}', #string,具体信息描述
                        "happen_time": plc_time, #long, 时间戳,单位毫秒
                        "has_solved": False, #bool,是否已解决
                        "solve_time": None #long, 时间戳,单位毫秒
                    }
                    self.ctrl_stop()
                    time.sleep(0.001) 
                    self.set_CT007(Ep)   
                
                # MC114 = get_global('MC114')
                # # check time
                # MC114_time = MC114['timestamp']
                # ctrl_time = int(time.time()*1000) # ms
                # if abs(ctrl_time - plc_time) > 1000:
                #     error_logger.error(f"time erro ctrl_time:{ctrl_time} - MC114_time {MC114_time}")
                #     Ep = {
                #         "exception_code": 'E102',#int,异常代码
                #         "detail":f"{ctrl_time}|{MC114_time}", #string,具体信息描述
                #         "happen_time": ctrl_time, #long, 时间戳,单位毫秒
                #         "has_solved": False, #bool,是否已解决
                #         "solve_time": None #long, 时间戳,单位毫秒
                #     }
                #     self.ctrl_stop()
                #     time.sleep(0.001) # 增加延迟控制收发顺序
                #     self.set_CT007(Ep)
                
                # check theta
                theta = MC114['data']['spreader_target_theta']
                if theta > 0.6: # 30deg
                    error_logger.error(f"spreader theta:{theta}")
                    Ep = {
                        "exception_code": 'E126',#int,异常代码
                        "detail":f"{theta}", #string,具体信息描述
                        "happen_time": ctrl_time, #long, 时间戳,单位毫秒
                        "has_solved": False, #bool,是否已解决
                        "solve_time": None #long, 时间戳,单位毫秒
                    }
                    self.ctrl_stop()
                    time.sleep(0.001) # 增加延迟控制收发顺序
                    self.set_CT007(Ep)

            except Exception as error: # 无指令则全升起
                error_logger.error(f'ctrl_monitor {error}')

    def stop(self, ):
        self.stop_flag = True 
    
    def set_CT007(self, Ep = None):
        '''
            Ep = {
                "exception_code":1000,#int,异常代码
                "detail":"xxxx", #string,具体信息描述
                "happen_time":16879546201,#long, 时间戳,单位毫秒
                "has_solved":False, #bool,是否已解决
                "solve_time":0#long, 时间戳,单位毫秒
            }
        '''
        CT007 = get_global('CT007')
        CT007['msg_uid'] = str(uuid.uuid1())
        CT007['timestamp'] = int(time.time()*1000)
        CT007['data'] = Ep
        set_global('CT007', CT007)
        send_msg = json.dumps(CT007, ensure_ascii=False)
        CT2MC_pub.send_msg(send_msg)
    
    def ctrl_stop(self, ):
        '''
        控制系统速度清零, 请求切手动
        '''
        send_msg = get_global('CT001')
        send_msg["msg_uid"] = str(uuid.uuid1())
        send_msg["timestamp"] = int(time.time() * 1000)
        send_msg["data"] = [
                            {"cmd": "trolley_velocity", "value":0.0},
                            {"cmd": "hoist_velocity", "value":0.0},
                        ]
        set_global('CT001', send_msg)
        send_msg = json.dumps(send_msg, ensure_ascii=False)
        CT2MC_pub.send_msg(send_msg)
        
        # time.sleep(0.001)
        # send_msg = get_global('CT003')
        # send_msg["timestamp"] = int(time.time()*1000)
        # send_msg["msg_uid"] = str(uuid.uuid1())   
        # send_msg["data"]["task_id"] = None
        # send_msg["data"]["request_mode"] = "manual"
        # send_msg["data"]["request_reason"] = 'ctrl monitor dangerous event'
        # set_global('CT003', send_msg)
        # send_msg = json.dumps(send_msg, ensure_ascii=False)
        # CT2MC_pub.send_msg(send_msg)        

if __name__ == "__main__":
    thread_monitor = ctrl_monitor()
    thread_monitor.start()
