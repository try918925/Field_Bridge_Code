
from global_info import *
from initializers import *
from ctrl_utils import *
import threading
import zmq
import time 
import uuid
import copy
from math import sin
from relative_pos import cal_relative_pos
from nowtime_lock import cal_midlock

class thread_MC101(threading.Thread):
    def __init__(self, ):
        super().__init__() 
        self.stop_flag = True # 初始状态不执行任务
        self.MC101_processing = get_global('MC101')

    def run(self, ):      
        while True: # 每个循环为收取到任务
            if self.stop_flag: # 停止时仍然循环, 等待收取新的作业任务
                time.sleep(0.1)
                continue
            # todo set CT004

            # 更新状态
            change_CT002_state(self.MC101_processing, "received", False, False)        
            time.sleep(0.01)
            if not self.check_MC101():
                stop()
                Ep = {
                        "exception_code": 'E106',#int,异常代码
                        "detail":f"", #string,具体信息描述
                        "happen_time": int(time.time()*1000), #long, 时间戳,单位毫秒
                        "has_solved": False, #bool,是否已解决
                        "solve_time": None #long, 时间戳,单位毫秒
                    }
                CT007 = get_global('CT007')
                CT007['msg_uid'] = str(uuid.uuid1())
                CT007['timestamp'] = int(time.time()*1000)
                CT007['data'] = Ep
                set_global('CT007', CT007)
                send_msg = json.dumps(CT007, ensure_ascii=False)
                CT2MC_pub.send_msg(send_msg)
                error_logger.error(f"erro task")
                change_CT002_state(self.MC101_processing, "abort", False, False, reject_reason=f'erro task') 

                return 
            
            change_CT002_state( self.MC101_processing, "running", False, False)
            target_json = self.MC101_processing["data"]["currentAction"]["targetPosition"]
            actionType = self.MC101_processing["data"]["currentAction"]["actionType"] if "actionType" in self.MC101_processing["data"]["currentAction"].keys() else None
            work_type = self.MC101_processing["data"]["currentAction"]["work_type"] if "work_type" in self.MC101_processing["data"]["currentAction"].keys() else None
            task_id = self.MC101_processing["data"]["currentAction"]["task_id"] if "task_id" in self.MC101_processing["data"]["currentAction"].keys() else None
            workflow = self.MC101_processing["data"]["currentAction"]["workflow"] if "workflow" in self.MC101_processing["data"]["currentAction"].keys() else None
            
            #//动作类型，1=停车 2=抓箱 3=放箱 # //作业类型,LOAD-装船 DSCH-卸船
            seaSideSafeHeight = 16 if not ("seaSideSafetyHeight" in self.MC101_processing["data"]["currentAction"]) \
                else self.MC101_processing["data"]["currentAction"]["seaSideSafetyHeight"]
            landSideSafeHeight = 16 if not "landSideSafetyHeight" in self.MC101_processing["data"]["currentAction"] \
                else self.MC101_processing["data"]["currentAction"]["landSideSafetyHeight"]  
            container_h = 3 # 带箱时，安全高度补偿箱高3m 
            
            if actionType == 3: # 放箱时 陆侧安全高度加箱高 todo 带箱状态时
                landSideSafeHeight += container_h
                seaSideSafeHeight  += container_h

            # 获取目标位置, 如果是抓放任务, 从感知信息获取
            target_y, target_z = target_json["trolleyPos"], target_json["hoistHeight"]
            if (actionType == 2 and work_type == "LOAD") or (actionType == 3 and work_type == "DSCH"):      
                MC108 = get_global('MC108')
                print(MC108) # todo check MC108
                target_y = MC108['data']['car_target_x']
                # target_y = 25.15
                target_z = 5.1
                
            if target_y > 52 and target_z < seaSideSafeHeight: # 海侧停止在安全高度以上
                target_z = seaSideSafeHeight
           
            MC001 = get_global('MC001')
            y_start, z_start = MC001['data']['trolley_pos'], MC001['data']['hoist_height'] 
            if MC001['data']['ctr_mod_auto'] == 0:
                stop() # 切手动后任务失败
                change_CT002_state(self.MC101_processing, "abort", False, False, reject_reason='auto change to manual') 
                self.stop_flag = True # 完成之后等待接收新任务  
                continue      

            # 起升阶段
            key_logger.info(f'MC101 from ({y_start}, {z_start}) to ({target_y}, {target_z}), task:{self.MC101_processing }')
            if z_start < 15: # 先拉去安全高度以上才允许动小车
                key_logger.info(f'fast_hosit up to safe height 15m')
                self.fast_hosit(2.5, 15, False, self.MC101_processing)
                # self.hoist_control(15, self.MC101_processing)
            
            # 装船 - 放箱时需要升导板
            if (work_type == "LOAD") and (actionType == 3):
                set_flip('up', [1, 2, 3, 4]) # 全升起
            
            # 卸船 - 放箱时需要升导板
            if (work_type == "DSCH") and (actionType == 3):
                try:
                    down_list = self.MC101_processing['data']["currentAction"]['flipperDownList']
                except Exception as error: # 无指令则全升起
                    print(error)
                    down_list = [1, 2, 3 ,4]
                set_flip('up', down_list)

            # 起升与小车联动阶段
            MC001 = get_global('MC001')
            y_start, z_start = MC001['data']['trolley_pos'], MC001['data']['hoist_height'] 
            if target_z > 15:
                print(target_y, max(z_start, 20, target_z), target_z)
                key_logger.info('anti_swing_mv to {}, {}, {})'.format(target_y, max(z_start, 20, target_z), target_z))
                self.anti_swing_mv(target_y, max(z_start, 20, target_z), target_z, self.MC101_processing)
            else:
                print(target_y, 30, 20)
                key_logger.info('anti_swing_mv to {}, {}, 15)'.format(target_y, max(z_start, 20)))
                self.anti_swing_mv(target_y, max(z_start, 20), 15, self.MC101_processing)

            MC001 = get_global('MC001')
            y_start, z_start = MC001['data']['trolley_pos'], MC001['data']['hoist_height'] 
            if MC001['data']['ctr_mod_auto'] == 0:
                stop() # 切手动后任务失败
                change_CT002_state(self.MC101_processing, "abort", False, False, reject_reason='auto change to manual') 
                self.stop_flag = True # 完成之后等待接收新任务  
                continue               
            if check_new_task(self.MC101_processing) or self.stop_flag:
                self.stop_flag = True
                change_CT002_state(self.MC101_processing, "abort", False, False, reject_reason=f'recv new task') 
                return # 每次控制前都判断一次是否有新任务收到
            
            # !! todo 与运动过程中同时启动
            if actionType == 2: # 抓箱时需要判断吊具尺寸
                print('set_spreader')
                set_spreader(self.MC101_processing["data"]["currentAction"]["workflow"], \
                            self.MC101_processing["data"]["currentAction"]["spreaderSize"])
            
            # 装船 - 抓箱时需要放导板
            if (work_type == "LOAD") and (actionType == 2):
                try:
                    down_list = self.MC101_processing['data']['currentAction']['flipperDownList']
                except Exception as error: # 无指令则全升起
                    print(error)
                    down_list = [1, 2, 3 ,4]
                key_logger.info('set_flip down_list:{}'.format(down_list))
                set_flip('down', down_list)
            
            MC001 = get_global('MC001')
            y_start, z_start = MC001['data']['trolley_pos'], MC001['data']['hoist_height']        
            # print(target_y, 0.5 * (z_start + target_z), target_z)
            if MC001['data']['ctr_mod_auto'] == 0:
                stop() # 切手动后任务失败
                change_CT002_state(self.MC101_processing ,"abort", False, False, reject_reason='auto change to manual') 
                self.stop_flag = True # 完成之后等待接收新任务  
                continue    

            if ((work_type == "LOAD") and (actionType == 2)) or ((work_type == "DSCH") and (actionType == 3)):
                key_logger.info(f'start land ctrl, target_y:{target_y} - target_z:{target_z}')
                self.land_cntr(target_y, target_z, self.MC101_processing)
            else:
                key_logger.info(f'start hoist_control - target_z:{target_z}') 
                self.hoist_control(target_z, self.MC101_processing)           
            stop() # 停止 todo 后续流畅动作时需要去除这部分

            if target_y > 52: # 海侧作业请求切手动
                request_manual_mode(self.MC101_processing)
                change_CT002_state( self.MC101_processing, "complete", True, False) 
                stop()
                key_logger.info(f'end process {self.MC101_processing }')
                self.stop_flag = True # 完成之后等待接收新任务
            
            #//动作类型，1=停车 2=抓箱 3=放箱 # //作业类型,LOAD-装船，DSCH-卸船
            # 装船 - 抓箱时 有着箱信号 则自动闭锁, 否则请求切手动
            if actionType == 2 and self.MC101_processing["data"]["currentAction"]["work_type"] == "LOAD":
                sleep_cnt = 0
                while True:
                    if check_new_task(self.MC101_processing) or self.stop_flag:
                        self.stop_flag = True
                        change_CT002_state( self.MC101_processing, "abort", False, False, reject_reason=f'recv new task') 
                        return # 每次控制前都判断一次是否有新任务收到
                    
                    MC001 = get_global('MC001')
                    land_state = MC001['data']['land_state']
                    if land_state == 1: # int,着箱状态， 0-着箱灯灭，1-着箱灯亮
                        twist_lock(1)
                    time.sleep(1.0)
                    sleep_cnt += 1
                    
                    if MC001['data']['lock_state'] == 1:
                        # 拉起一小段判断是否有危险
                        key_logger.info(f'up to judge safe, {self.MC101_processing }')
                        # self.hoist_control(MC001['data']['hoist_height']+0.3, self.MC101_processing) 
                        self.fast_hosit(0.8, MC001['data']['hoist_height']+0.3, False, self.MC101_processing)
                        # ！！！ todo check 是否安全
                        time.sleep(1.0)

                        key_logger.info(f'up to compete height, {self.MC101_processing }')
                        # self.hoist_control(15.1, self.MC101_processing) # 起升拉高之后在结束
                        self.fast_hosit(2.5, 20.0, True, self.MC101_processing) # 15m时发送任务完成 20m时停止
                        change_CT002_state( self.MC101_processing, "complete", True, False) # 冗余的20m任务完成
                        stop()
                        self.stop_flag = True # 完成之后等待接收新任务
                        break
                    if sleep_cnt > 10:
                        change_CT002_state( self.MC101_processing, "abort", True, False, reject_reason='lock state timeout') 
                        request_manual_mode(self.MC101_processing)
                        break      
            # 卸船放箱完成时, 有着箱信号开锁，无着箱型号时请求且手动，并且任务中断
            elif actionType == 3 and self.MC101_processing["data"]["currentAction"]["work_type"] == "DSCH":  
                sleep_cnt = 0
                while True:
                    if check_new_task(self.MC101_processing) or self.stop_flag:
                        self.stop_flag = True
                        change_CT002_state( self.MC101_processing, "abort", False, False, reject_reason=f'recv new task') 
                        return # 每次控制前都判断一次是否有新任务收到
                    MC001 = get_global('MC001')
                    land_state = MC001['data']['land_state']
                    if land_state == 1: # int,着箱状态， 0-着箱灯灭，1-着箱灯亮
                        time.sleep(5.0)
                        # !!! todo dudge true land
                        twist_lock(0)
                        time.sleep(1.0)
                        key_logger.info(f'up to judge safe, {self.MC101_processing }')
                        # self.hoist_control(MC001['data']['hoist_height'] + 0.3, self.MC101_processing) 
                        self.fast_hosit(0.8, MC001['data']['hoist_height']+0.3, False, self.MC101_processing)
                        # ！！！ todo check 是否安全
                        time.sleep(1.0)

                        key_logger.info(f'up to compete height, {self.MC101_processing }')
                        # self.hoist_control(15.1, self.MC101_processing) # 起升拉高之后在结束
                        self.fast_hosit(2.5, 20.0, True, self.MC101_processing) # 15m时发送任务完成 20m时停止
                        change_CT002_state(self.MC101_processing, "complete", False, True) # 冗余的到20m任务完成
                        stop()
                        self.stop_flag = True # 完成之后等待接收新任务

                    time.sleep(0.5)
                    sleep_cnt += 1
                    if MC001['data']['unlock_state'] == 1:
                        break
                    if sleep_cnt > 10 or MC001['data']['unlock_state'] == 1:
                        change_CT002_state( self.MC101_processing, "abort", False, False) 
                        request_manual_mode(self.MC101_processing) 
                        break
            
            elif actionType == 1: 
                change_CT002_state( self.MC101_processing, "complete", False, False) 
                stop()
                self.stop_flag = True # 完成之后等待接收新任务               
                  
            time.sleep(0.2)

    def stop(self, ):
        self.stop_flag = True
        # key_logger.info(f'stop process {self.MC101_processing}')
        time.sleep(0.01)
        # change_CT002_state(self.MC101_processing, "abort", False, False, reject_reason=f'recv MC102')   
        # notice 主控决定停止时会给出速度

    def reset_task(self, ):
        '''
           收到新任务之后, 执行新的任务
        '''
        self.MC101_processing = get_global('MC101')
        self.stop_flag = False
               
    def hoist_control(self, target_hoist, MC101_processing):
        '''
        控制起升, 目标位置, todo 增加停止时速度设置（让过程切换更加流畅）
        '''
        MC001 = get_global('MC001')
        y_start, z_start = MC001['data']['trolley_pos'], MC001['data']['hoist_height']
        hoist_para = PIDParameters(kp= 0.6, 
                                ki= 0.0, 
                                kd= 0.0, 
                                lower= -2.5, 
                                upper= 2.5
                                )
        hoist_controller = PIDController(hoist_para)
        t0 = time.time()
        exit_count = 0

        # control loop
        while True:
            time.sleep(0.115)
            if check_new_task(MC101_processing) or self.stop_flag:
                self.stop_flag = True
                change_CT002_state( MC101_processing, "abort", False, False, reject_reason=f'recv new task') 
                return False # 每次控制前都判断一次是否有新任务收到
            
            MC001 = get_global('MC001')
            MC114 = get_global('MC114')
            # print(MC114)
            theta = MC114['data']['spreader_target_theta']
            y, vy = MC001['data']['trolley_pos'], MC001['data']['trolley_vel']
            z, vz = MC001['data']['hoist_height'], MC001['data']['rope_vel']

            t = time.time() - t0 
            if MC001['data']["land_state"] == 1 and vz < 0.0: # 着箱之后中断
                stop()
                break      
            if MC001['data']["ctr_mod_auto"] != 1: # 非自动或主动暂停
                stop()
                MC101 = get_global('MC101')
                change_CT002_state(MC101_processing,"abort", False, False, reject_reason=f'not in auto mod')
                break
            # exit condition
            if t > 100:
                print('hoist control timeout Error.')
                change_CT002_state(MC101_processing,"abort", False, False, reject_reason=f'hoist control timeout Error.')
                stop()
                break
            
            if 0.0 <= (z-target_hoist) < 0.1:
                exit_count += 1
            else:
                exit_count = 0
            if exit_count >= 1.0:
                print('Hoist Arrives.')
                stop()
                key_logger.info('cost time: {}s'.format(time.time() - t0))
                return True # 顺利执行完
                break
            # calculate control input
            uz = hoist_controller.calculate_output(target_hoist, z)
            print(f't:{t:.2f}, y:{y:.2f}, z:{z:.2f}, theta:{theta:.4f}, u:{uz:.2f}')
            set_velocity(0.0, 1.0 * uz)  
        return True # 顺利执行完

    def fast_hosit(self, v: float, target_hoist, need_complete: bool, MC101_processing):
        '''
        以指定v移动, 到目标位置target_z, 是否需要中途停止 need_complete, MC101_processing
        '''
        # control loop
        t0 = time.time()
        exit_count = 0
        while True:
            time.sleep(0.115)
            if check_new_task(MC101_processing) or self.stop_flag: # check new task id 
                self.stop_flag = True
                change_CT002_state( MC101_processing, "abort", False, False, reject_reason=f'recv new task') 
                return # 每次控制前都判断一次是否有新任务收到
            MC001 = get_global('MC001')
            y, vy = MC001['data']['trolley_pos'], MC001['data']['trolley_vel']
            z, vz = MC001['data']['hoist_height'], MC001['data']['rope_vel']                    
            if MC001['data']["land_state"] == 1 and vz < 0.0: # 着箱之后中断
                stop()
                break      
            if MC001['data']["ctr_mod_auto"] != 1: # 非自动或主动暂停
                stop()
                MC101 = get_global('MC101')
                change_CT002_state(MC101_processing,"abort", False, False, reject_reason=f'not in auto mod')
                break
            
            # exit condition
            t = time.time() - t0 
            if t > 100:
                print('hoist control timeout Error.')
                change_CT002_state(MC101_processing,"abort", False, False, reject_reason=f'hoist control timeout Error.')
                stop()
                break
                        
            if 0.0 <= (z-target_hoist) < 0.2:
                exit_count += 1
            else:
                exit_count = 0
            
            if z > 10.0 and need_complete: # 起升到移动高度时给出任务结束
                key_logger.info('cost time: {}s'.format(time.time() - t0))
                change_CT002_state(MC101_processing, "complete", False, True) 
                need_complete = False
            if exit_count >= 1.0:
                print('Fast Hoist Arrives.')
                set_velocity(0.0, 0.0) 
                key_logger.info('cost time: {}s'.format(time.time() - t0))
                return True # 顺利执行完
            set_velocity(0.0, v)
            print(f't:{t:.2f}, y:{y:.2f}, z:{z:.2f}, vy:{vy:.2f}, vz:{vz:.2f}')

    def anti_swing_mv(self, target_y, target_z_1, target_z_2, MC101_processing):
        MC001 = get_global('MC001')
        y_start, z_start = MC001['data']['trolley_pos'], MC001['data']['hoist_height']
        hoist_para = PIDParameters(kp= 0.6, 
                                ki= 0.0, 
                                kd= 0.0, 
                                lower= -2.0, 
                                upper= 2.0
                                )
        pos_para = PIDParameters(kp= 0.21, 
                                ki= 0.0, 
                                kd= 0.5, 
                                lower= -3.8, 
                                upper= 3.8
                                )
        angle_para = PIDParameters(kp=2.0, 
                                ki=0.0, 
                                kd=8.0, 
                                lower=-3.0, 
                                upper=3.0
                                )
        trolley_controller = CraneController(3.8, 0.6, pos_para, angle_para)
        trolley_controller.set(y_start, target_y)
        hoist_controller = PIDController(hoist_para)
        t0 = time.time()
        y_list, vy_list, yd_list, uy_list = [], [], [], []
        z_list, vz_list, uz_list = [], [], []
        theta_list = []
        t_list = []
        exit_count = 0

        # main control loop
        while True:
            time.sleep(0.115)
            if check_new_task(MC101_processing) or self.stop_flag: # check new task id 
                self.stop_flag = True
                change_CT002_state( MC101_processing, "abort", False, False, reject_reason=f'recv new task') 
                return # 每次控制前都判断一次是否有新任务收到
            
            MC001 = get_global('MC001')
            if MC001['data']['ctr_mod_auto'] == 0:
                stop() # 切手动后任务失败
                change_CT002_state(MC101_processing ,"abort", False, False, reject_reason='auto change to manual') 
                break
            if judge_stop():
                change_CT002_state(MC101_processing, "abort", False, False, reject_reason='recv MC102') 
                break  

            if MC001['data']['wind'] > 10.0: # 风速大于10m时小车限速
                trolley_controller.planner.V = 0.6 * 3
                trolley_controller.angle_controller.parameters.lower = 0.6 * (-3)
                trolley_controller.angle_controller.parameters.upper = 0.6 * 3                   
                trolley_controller.pos_controller.parameters.lower = 0.6 * (-3)
                trolley_controller.pos_controller.parameters.upper = 0.6 * 3

            MC114 = get_global('MC114')
            theta = MC114['data']['spreader_target_theta']
            y, vy = MC001['data']['trolley_pos'], MC001['data']['trolley_vel']
            z, vz = MC001['data']['hoist_height'], MC001['data']['rope_vel']

            t = time.time() - t0 
            
            if abs(y - y_start) < 10:
                target_z = target_z_1
            if abs(y - target_y) < 10:
                target_z = target_z_2

            # exit condition
            print(y_start, target_y, y)

            if (y_start < target_y):
                p  = 1
            else:
                p = -1
            if (y - (y_start - p * 1)) * (y - (target_y + p * 1)) > 0:
                self.stop_flag = True
                stop()
                Ep = {
                        "exception_code": 'E103',#int,异常代码
                        "detail":f"{y_start}|{target_y}|{y}", #string,具体信息描述
                        "happen_time": int(time.time()*1000), #long, 时间戳,单位毫秒
                        "has_solved": False, #bool,是否已解决
                        "solve_time": None #long, 时间戳,单位毫秒
                    }
                CT007 = get_global('CT007')
                CT007['msg_uid'] = str(uuid.uuid1())
                CT007['timestamp'] = int(time.time()*1000)
                CT007['data'] = Ep
                set_global('CT007', CT007)
                send_msg = json.dumps(CT007, ensure_ascii=False)
                CT2MC_pub.send_msg(send_msg)
                error_logger.error(f"out of range y_start|target_y|y {y_start}|{target_y}|{y}")
                change_CT002_state( MC101_processing, "abort", False, False, reject_reason=f'out of range') 
            
            if (12.0 < y < 21.6) and ( z < 10.0):
                self.stop_flag = True
                stop()
                change_CT002_state( MC101_processing, "abort", False, False, reject_reason=f'in forbiden area - land beam') 
            
            if (46.8 < y < 55.8) and ( z < 10.0):
                self.stop_flag = True
                stop()
                change_CT002_state( MC101_processing, "abort", False, False, reject_reason=f'in forbiden area - sea beam') 
            
            if y < 5 or y > 110:
                self.stop_flag = True
                stop()
                change_CT002_state( MC101_processing, "abort", False, False, reject_reason=f'in forbiden area ') 
        
            if abs(theta) > 0.6:
                self.stop_flag = True
                stop()
                change_CT002_state( MC101_processing, "abort", False, False, reject_reason=f'in forbiden area ') 
                break

            if t > 100:
                print('Timeout Error.')
                stop()
                break

            if abs(y-target_y) <= 0.05 and abs(theta)< 0.05 and (0.0 <= (z-target_z) < 0.1) and (vy < 0.5):
                exit_count += 1
            else:
                exit_count = 0
            if exit_count >= 1.0:
                print('Trolley Arrives.')
                stop()
                key_logger.info('cost time: {}s'.format(time.time() - t0))
                break

            # calculate control input
            if abs(target_y-y) < 0.5:
                trolley_controller.angle_controller.parameters.kp = 0.1
                trolley_controller.angle_controller.parameters.ki = 0
                trolley_controller.angle_controller.parameters.kd = 0
                trolley_controller.pos_controller.parameters.kp = 0.4
                trolley_controller.pos_controller.parameters.ki = 0
                trolley_controller.pos_controller.parameters.kd = 0.2
            uy, u_pos, u_angle, yd = trolley_controller.step(t, y, theta)
            uz = hoist_controller.calculate_output(target_z, z)
            #if -0.05 < uy < 0.05:
            #    uy = 0.0
            if 0.0 <= (z-target_z) < 0.1:
                uz = 0.0
            print(f't:{t:.2f}, y:{y:.2f}, z:{z:.2f}, theta:{theta:.4f}, u:{uy:.2f}')
            set_velocity(uy, 1.0*uz)

            # store the data
            y_list.append(y)
            yd_list.append(yd)
            vy_list.append(vy)
            uy_list.append(uy)
            z_list.append(z)
            vz_list.append(vz)
            uz_list.append(uz)
            theta_list.append(theta)
            t_list.append(t)

        # plot the test result
        plt.figure(1)
        plt.subplot(221)
        plt.scatter(y_list, z_list)
        plt.title('trajectory')
        plt.subplot(222)
        plt.plot(t_list, np.array(uy_list), label='trolley reference velocity')
        plt.plot(t_list, np.array(vy_list), label='trolley actual velocity')    
        plt.legend()    
        plt.subplot(223)
        plt.plot(t_list, np.array(theta_list))
        plt.title('theta')
        plt.subplot(224)
        plt.plot(t_list, np.array(uz_list), label='hoist reference velocity')
        plt.plot(t_list, np.array(vz_list), label='hoist actual velocity')
        plt.legend()
        plt.savefig(f"./log/{MC101_processing['timestamp']}_{MC101_processing['msg_uid']}\
                    _{MC101_processing['data']['currentAction']['actionType']}.jpg")    
        plt.close('all')
   
    def land_cntr(self, target_y, target_z, MC101_processing):
        hoist_para = PIDParameters(kp=0.8, 
                                ki=0, 
                                kd=1.0, 
                                lower=-2.0, 
                                upper=2.0
                                )
        hoist_controller = PIDController(hoist_para)
        last_lock_action = 0
        error_predictor = Predictor(10)
        iou_predictor = Predictor(10)
        state = 'lowering'
        # first_enter = 
        t0 = time.time()
        t = time.time() - t0
        iou_list_1 = []
        iou_list_2 = []
        t_list = []
        error_list_1 = []
        error_list_2 = []
        actionType = self.MC101_processing["data"]["currentAction"]["actionType"] if "actionType" in self.MC101_processing["data"]["currentAction"].keys() else None
        truck_pos = MC101_processing["data"]["currentAction"]['targetPosition']['truckPos']
        if truck_pos == 'rear':
            dt = 0.49 if actionType==2 else 0.55 # rear
        elif truck_pos == 'front':
            dt = 0.54 if actionType==2 else 0.62 # front 前后车板有高低差
        else:
            dt = 0.52 if actionType==2 else 0.62 # center 前后车板有高低差

        hover_z = target_z + dt+0.1
        # main control loop
        while True:
            time.sleep(0.05) # 控制频率
            if check_new_task(MC101_processing) or self.stop_flag: # check new task id 
                self.stop_flag = True
                change_CT002_state( MC101_processing, "abort", False, False, reject_reason=f'recv new task') 
                break # 每次控制前都判断一次是否有新任务收到
            
            MC001 = get_global('MC001')
            if MC001['data']['ctr_mod_auto'] == 0:
                stop() # 切手动后任务失败
                change_CT002_state(MC101_processing , "abort", False, False, reject_reason='auto change to manual') 
                break
            if judge_stop(): # todo 增加新收到任务后重置 stop
                change_CT002_state(MC101_processing,"abort", False, False, reject_reason='recv MC102') 
                break            
            MC114 = get_global('MC114')
            TEMP = get_global('TEMP')
            spreader_bbox = TEMP['hanger_pos']['bbox']
            target_bbox = TEMP['target_pos']['bbox']
            lock_ratio_real = TEMP['lock_dis']['ratio']
            lock_ratio = lock_ratio_real
            if lock_ratio_real == None:
                lock_ratio = 1
            print(f'bbox:{spreader_bbox} and {target_bbox}')
            t = time.time() - t0
            y = MC001['data']['trolley_pos']
            z = MC001['data']['hoist_height']
            rope_length = MC001['data']['rope_pos']
            land_state = MC001['data']['land_state']

            theta = MC114['data']['spreader_target_theta']
            spreader_y = y + sin(theta) * rope_length
            error = target_y - spreader_y
            error_pred = error_predictor.predict(t, error, dt)
            try:
                iou = cal_iou(spreader_bbox, target_bbox)
            except:
                iou = 0
            iou_pred = iou_predictor.predict(t, iou, dt)
            t_list.append(t)
            error_list_1.append(error)
            error_list_2.append(error_pred)
            iou_list_1.append(iou)
            iou_list_2.append(iou_pred)
            cmd_list = []
            print(f'error:{error:.3f}, lock_ratio:{lock_ratio_real}, iou:{iou:.3f}, state:{state}, land_state:{land_state}')

            if z < 8: # 启升限速
                hoist_controller.parameters.lower = -1.0
                hoist_controller.parameters.upper = 1.0                 
            
            # exit condition
            if t > 100:
                print('Timeout Error.')
                stop()
                return 0
            if error > 1.0:
                print('erro limit')
                stop()
                return 0
            # finite state machine
            if state == 'lowering':
                if (0 < z - hover_z < 0.05):
                    state = 'hovering'
                    key_logger.info(f'lowering -> hovering')
                    continue
                uz = hoist_controller.calculate_output(hover_z, z)
                if abs(z - hover_z) < 0.05:
                    uz = 0
                cmd_list.append({"cmd": "hoist_velocity", "value": 1.0 * uz})
                set_cmd(cmd_list)
            elif state == 'hovering':
                # if abs(error_pred) < 0.02:
                actionType = self.MC101_processing["data"]["currentAction"]["actionType"] if "actionType" in self.MC101_processing["data"]["currentAction"].keys() else None
                error_pred_limit = 0.05 if actionType==2 else 0.038 # 抓放的条件阈值不同
                if (iou > 0.45 and 0.58 <= lock_ratio <= 0.65) or MC001['data']['land_state'] == 1:
                    state = 'touching'
                    key_logger.info(f'hovering -> touching')
                    if last_lock_action != 0:
                        cmd_list.append({"cmd": "spreader_mid_lock", "value": int(lock_action-1)})
                        set_cmd(cmd_list)
                    continue
                else:
                    if lock_ratio > 0.65:
                        lock_action = 21
                        last_lock_action = lock_action
                        cmd_list.append({"cmd": "spreader_mid_lock", "value": int(lock_action)})
                    elif lock_ratio < 0.58:
                        lock_action = 11
                        last_lock_action = lock_action
                        cmd_list.append({"cmd": "spreader_mid_lock", "value": int(lock_action)})                        
                    cmd_list.append({"cmd": "hoist_velocity", "value": 0.0})
                    set_cmd(cmd_list)
                    continue
            elif state == 'touching':
                if MC001['data']['land_state'] == 1:
                    print('着箱成功')
                    time.sleep(0.1)
                    stop()
                    key_logger.info('cost time: {}s'.format(time.time() - t0))
                    time.sleep(5.0)
                    break
                else:
                    uz = hoist_controller.calculate_output(target_z, z)
                    cmd_list.append({"cmd": "hoist_velocity", "value": 0.4 * uz})
                    set_cmd(cmd_list)
        np.save('./log/t.npy', np.array(t_list))
        np.save('./log/e1.npy', np.array(error_list_1))
        np.save('./log/e2.npy', np.array(error_list_2))
        np.save('./log/iou1.npy', np.array(iou_list_1))
        np.save('./log/iou2.npy', np.array(iou_list_2))

    def check_MC101(self, ):
        '''
        检查任务时间、车道与位置是否匹配
        '''
        target_json = self.MC101_processing["data"]["currentAction"]["targetPosition"]
        trolley_pos, hoist_height = target_json["trolleyPos"], target_json["hoistHeight"]
        if (trolley_pos < 5.0 or  trolley_pos > 110.0 or hoist_height < 3.8 or hoist_height > 45.0 ) \
        or ((12.0 < trolley_pos < 22.6) and ( hoist_height < 10.0)) \
        or ((46.8 < trolley_pos < 55.8) and ( hoist_height < 10.0)):      
            return False
        # todo  
        return True

    def check_pos(self, trolley_pos, hoist_height):
        
        return True


# temp
_thread_relative_pos = cal_relative_pos()
_thread_relative_pos.start()
_thread_midlock = cal_midlock()
_thread_midlock.start()

global _thread_MC101
_thread_MC101 = thread_MC101()
_thread_MC101.start()
def process_MC101(): 
        global _thread_MC101
        MC101 = get_global('MC101')
#    try:
        _thread_relative_pos.cal_target()

        run_task_id = _thread_MC101.MC101_processing["data"]["currentAction"]["task_id"] if "task_id" in _thread_MC101.MC101_processing["data"]["currentAction"].keys() else ''
        new_task_id = MC101["data"]["currentAction"]["task_id"] if "task_id" in MC101["data"]["currentAction"].keys() else ''
        if run_task_id != new_task_id \
        or _thread_MC101.MC101_processing['data']["currentAction"]['actionIndex'] != MC101['data']["currentAction"]['actionIndex']:
            _thread_MC101.stop()
            _thread_MC101.reset_task()
            if not _thread_MC101.is_alive():
                _thread_MC101 = thread_MC101()
                _thread_MC101.reset_task()
                _thread_MC101.start()
        else:
            pass
            # change_CT002_state(MC101, "abort", False, False, reject_reason=f'the same task')
        
 #   except Exception as error: # 校验错误也停止当前任务
 #       print('MC101 error', error)

def process_MC102():
    '''
        停止设备动作
    '''
    _thread_MC101.stop()
    stop()
    key_logger.info(f'recv MC102 stop')

def process_MC103():
    '''
        清空任务, 弃用, 任务管理在主控做
    ''' 
    key_logger.info(f'recv MC103')
    pass

def process_MC104():
    '''
        设置作业模式 todo 增加最后一段是否自动着箱判断
    '''
    key_logger.info(f'recv MC104') 
    pass

def process_MC105():
    '''
        请求控制模块状态, 反馈CT004
    '''
    key_logger.info(f'recv MC104') 
    pass

def process_MC106():
    '''
        贝扫任务
    '''
    pass

def process_MC107():
    '''
        发送贝扫数据
    '''
    pass

def process_MC108():
    '''
        发送陆侧集装箱/集卡位置
    '''
    pass

def process_MC110():
    '''
        发送海侧集装箱计划位置
    '''
    pass

def process_MC111():
    '''
        箱高数据
    '''
    pass

def process_MC112():
    '''
        请求任务执行状态
    '''
    pass

def process_MC113():
    '''
        设置禁行区域
    '''
    pass

def process_MC114():
    '''
        发送吊具姿态与位置 MC114
        在收到之后就做了更新
    '''
    # key_logger.info(f'CT has processed - MC114')
    pass
    

process_dict = {
    # MC -> CT
    "MC101": process_MC101,
    "MC102": process_MC102,
    "MC103": process_MC103,
    "MC104": process_MC104,
    "MC105": process_MC105,
    "MC106": process_MC106,
    "MC107": process_MC107,
    "MC108": process_MC108,
    # "MC109":MC109,
    "MC110": process_MC110,
    "MC111": process_MC111,
    "MC112": process_MC112,
    "MC113": process_MC113,
    "MC114": process_MC114,
}

class recv_MC2CT(threading.Thread):
    def __init__(self) :
        super().__init__()
        MC2CT_url = 'tcp://10.142.1.200:9001' # todo config list
        MC2CT_sub_context = zmq.Context()
        self.MC2CT_sub_socket = MC2CT_sub_context.socket(zmq.SUB)
        self.MC2CT_sub_socket.setsockopt(zmq.SUBSCRIBE, b'')
        self.MC2CT_sub_socket.connect(MC2CT_url) 
    
    def run(self, ):
        '''
        循环收取主控信息
        '''
        while True:
            MC2CT_msg = json.loads(self.MC2CT_sub_socket.recv_string()) 
            if MC2CT_msg['msg_name'] in process_dict.keys():
                set_global(MC2CT_msg['msg_name'], MC2CT_msg)
                if MC2CT_msg['msg_name'] == 'MC114':
                    main_logger.debug(f'MC to CT has procesing - {json.dumps(MC2CT_msg)}')
                else:
                    main_logger.info(f'MC to CT has procesing - {json.dumps(MC2CT_msg)}')
                p = threading.Thread(target =process_dict[MC2CT_msg['msg_name']]())
                p.start()
                # process_dict[MC2CT_msg['msg_name']]() 用函数处理会阻塞
            else:
                print('erro info \t', MC2CT_msg)
                error_logger.info(f'error msg - {json.dumps(MC2CT_msg)}')
            
