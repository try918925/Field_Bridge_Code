from global_info import *
from initializers import *
from PID_ctrl import *

import uuid
import time
import json
import numpy as np
from matplotlib import pyplot as plt

def check_new_task(MC101_processing):
    MC101 = get_global('MC101')
def check_new_task(MC101_processing):
    MC101 = get_global('MC101')
    try:
        run_task_id = MC101["data"]["currentAction"]["task_id"] if "task_id" in MC101["data"]["currentAction"].keys() else ''
        new_task_id = MC101["data"]["currentAction"]["task_id"] if "task_id" in MC101["data"]["currentAction"].keys() else ''
        if run_task_id != new_task_id \
        or MC101_processing['data']["currentAction"]['actionIndex'] != MC101['data']["currentAction"]['actionIndex']:
            return True
        return False
    except Exception as error: # 校验错误也停止当前任务
        print(error)
        return True
        
   
def set_cmd(cmd_list):
    '''
        设置控制指令
    '''
    send_msg = get_global('CT001')
    send_msg["msg_uid"] = str(uuid.uuid1())
    send_msg["timestamp"] = int(time.time() * 1000)
    send_msg["data"] = cmd_list
    set_global('CT001', send_msg)
    send_msg = json.dumps(send_msg, ensure_ascii=False)
    CT2MC_pub.send_msg(send_msg)

def stop():
    '''
        急停, 速度减为0
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

def judge_stop():
    '''
        MC102消息, stopMode 判断有停止信号
        
    '''
    MC102 = get_global('MC102')
    if MC102['data']['stopMode'] is None or abs(MC102["timestamp"]-int(time.time()*1000)) > 1000:
        return False
    else:
        stop()
        MC102['data']['stopMode'] = None
        set_global('MC102', MC102)
        key_logger.info('set stop and renew MC102')
        return True

def change_CT002_state(MC101: dict, state: str, pick_complete: bool, drop_complete: bool, reject_reason= None):
    '''
        MC101: 当前执行任务
        state: string,任务状态 received running reject abort complete
        pick_complete: bool
        drop_complete: bool 
        reject_reason: 任务拒绝原因
    '''
    send_msg = get_global('CT002')
    if state == 'abort' and send_msg["data"]["task_state"] == 'complete': # 避免任务完成后
        error_logger.warning('complete task cannot set abort {}'.format(send_msg))
        return
    send_msg["timestamp"] = int(time.time()*1000)
    send_msg["msg_uid"] = str(uuid.uuid1())
    send_msg["data"]["request_mode"] = "auto"
    if "task_id" in MC101["data"]["currentAction"].keys():
        send_msg["data"]["task_id"] = MC101["data"]["currentAction"]["task_id"] 
    else:
        send_msg["data"]["task_id"] = None
    send_msg["data"]["actionIndex"] = MC101["data"]["currentAction"]["actionIndex"]
    send_msg["data"]["task_state"] = state
    send_msg["data"]["pick_complete"] = pick_complete
    send_msg["data"]["drop_complete"] = drop_complete
    send_msg["data"]["reject_reason"] = reject_reason
    set_global('CT002', send_msg)
    key_logger.info(f'MC101 {state} task: {MC101}') # 记录任务状态
    send_msg = json.dumps(send_msg, ensure_ascii=False)
    CT2MC_pub.send_msg(send_msg)

def request_manual_mode(MC101, request_reason= None):
    '''
        请求切换手动, 等待超时执行
    '''
    time_cnt = 0
    while True:
        try:
            MC001 = get_global('MC001')
            if MC001['data']['ctr_mod_auto'] == 0 \
                and  MC001['data']['ctr_mod_manual'] == 1:
                return True
            else:
                send_msg = get_global('CT003')
                send_msg["timestamp"] = int(time.time()*1000)
                send_msg["msg_uid"] = str(uuid.uuid1())   
                send_msg["data"]["task_id"] = MC101["data"]["currentAction"]["task_id"]
                send_msg["data"]["request_mode"] = "manual"
                send_msg["data"]["request_reason"] = request_reason
                
                set_global('CT003', send_msg)
                send_msg = json.dumps(send_msg, ensure_ascii=False)
                CT2MC_pub.send_msg(send_msg)
                
                print("at time {} send msg to MC:\n{}\n".format(time.asctime(time.localtime()), send_msg))
                if time_cnt > 10:
                    print('time out')
                    key_logger.warning('request manual mode time out')
                    return False
                time_cnt += 1
                time.sleep(0.3)
        except Exception as error:
            print(error)
            return False
        
def set_velocity(trolley_velocity: float, hoist_velocity: float):
    '''
        设置小车/起升速度
    '''
    send_msg = get_global('CT001')
    send_msg["msg_uid"] = str(uuid.uuid1())
    send_msg["timestamp"] = int(time.time() * 1000)
    send_msg["data"] = [
        {"cmd": "trolley_velocity", "value": trolley_velocity},
        {"cmd": "hoist_velocity", "value": hoist_velocity}
    ]
    send_msg = json.dumps(send_msg, ensure_ascii=False)
    CT2MC_pub.send_msg(send_msg)

def hoist_control(target_hoist, MC101_processing):
    y_start, z_start = MC001['data']['trolley_pos'], MC001['data']['hoist_height']
    hoist_para = PIDParameters(kp= 1.0, 
                               ki= 0.0, 
                               kd= 0.0, 
                               lower= -1.0, 
                               upper= 1.0
                            )
    hoist_controller = PIDController(hoist_para)
    t0 = time.time()
    exit_count = 0

    # main control loop
    while True:
        if check_new_task(MC101_processing):
            change_CT002_state( MC101_processing, "abort", False, False, reject_reason=f'recv new task') 
            return # 每次控制前都判断一次是否有新任务收到
        MC001 = get_global('MC001')
        MC114 = get_global('MC114')
        print(MC114)
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
            change_CT002_state(MC101,"abort", False, False)
            break

        # exit condition
        if t > 100:
            print('hoist control timeout Error.')
            stop()
            break
        
        if (z - target_hoist) < 0.1:
            exit_count += 1
        else:
            exit_count = 0
        if exit_count >= 1.0:
            print('Hoist Arrives.')
            stop()
            break
        # calculate control input
        uz = hoist_controller.calculate_output(target_hoist, z)
        print(f't:{t:.2f}, y:{y:.2f}, z:{z:.2f}, theta:{theta:.4f}, u:{uz:.2f}')
        set_velocity(0.0, 1.0 * uz)   

def trolley_control(target_y, MC101_processing):
    MC001 = get_global('MC001')
    trolley_start, trolley_start = MC001['data']['trolley_pos'], MC001['data']['hoist_height'] 
    pos_para = PIDParameters(kp= 0.2, 
                             ki= 0.0, 
                             kd= 0.5, 
                             lower= -3.0, 
                             upper= 3.0
                            )
    angle_para = PIDParameters(kp=2.5, 
                               ki=0.0, 
                               kd=10.0, 
                               lower=-3.0, 
                               upper=3.0
                            )
    trolley_controller = CraneController(3.0, 0.4, pos_para, angle_para)
    trolley_controller.set(trolley_start, target_y)
    t0 = time.time()
    y_list, theta_list, u_list, v_list = [], [], [], []
    xd_list = []
    t_list = []
    exit_count = 0
    # main control loop
    while True:
        if check_new_task(MC101_processing):
            change_CT002_state( MC101_processing, "abort", False, False, reject_reason=f'recv new task') 
            return # 每次控制前都判断一次是否有新任务收到
        MC001 = get_global('MC001')
        MC114 = get_global('MC114')
        theta = MC114['data']['spreader_target_theta']
        y, v = MC001['data']['trolley_pos'], MC001['data']['trolley_vel']
        z = MC001['data']['hoist_height']
        t = time.time() - t0 
        
        # exit condition
        if y < 5 or y > 110:
            print('Trolley out of Range.')
        if abs(theta) > 0.6:
            print('Swing out of Control.')
            stop()
            break
        if t > 100:
            print('Timeout Error.')
            stop()
            break
        if abs(y - target_y) <= 0.05 and abs(theta)< 0.05:
            exit_count += 1
        else:
            exit_count = 0
        if exit_count >= 1.0:
            print('Trolley Arrives.')
            stop()
            break

        if abs(target_y - y) < 0.5:
            trolley_controller.angle_controller.parameters.kp = 0.1
            trolley_controller.angle_controller.parameters.ki = 0
            trolley_controller.angle_controller.parameters.kd = 0
            trolley_controller.pos_controller.parameters.kp = 0.4
            trolley_controller.pos_controller.parameters.ki = 0
            trolley_controller.pos_controller.parameters.kd = 0.2

        # calculate control input for the system
        u, u_pos, u_angle, xd = trolley_controller.step(t, y, theta)
        print(f't:{t}, y:{y}, theta:{theta}, u:{u}')
        if -0.05 < u < 0.05:
            u = 0.0
        set_velocity(1.0 * u, 0.0)
        
        # store data
        y_list.append(y)
        theta_list.append(theta)
        u_list.append(u)
        v_list.append(v)
        xd_list.append(xd)
        t_list.append(t)

    # plot the test result
    plt.figure(1)
    plt.plot(t_list, np.array(y_list), label='actual position')
    plt.plot(t_list, np.array(xd_list), label = 'desired position')
    plt.legend()
    plt.figure(2)
    plt.plot(t_list, np.array(theta_list))
    plt.title('angle(rad)')
    plt.figure(3)
    plt.plot(t_list, np.array(u_list), label='reference velocity')
    plt.plot(t_list, np.array(v_list), label='actual velocity')
    plt.legend()
    plt.savefig(f"{int(time.time()*1000)}.jpg")   
    
def fast_mv(target_y, target_z, MC101_processing):
    pass

def anti_swing_mv(target_y, target_z_1, target_z_2, MC101_processing):
    MC001 = get_global('MC001')
    y_start, z_start = MC001['data']['trolley_pos'], MC001['data']['hoist_height']
    hoist_para = PIDParameters(kp= 1.0, 
                               ki= 0.0, 
                               kd= 0.0, 
                               lower= -1.0, 
                               upper= 1.0
                            )
    pos_para = PIDParameters(kp= 0.2, 
                             ki= 0.0, 
                             kd= 0.5, 
                             lower= -3.0, 
                             upper= 3.0
                            )
    angle_para = PIDParameters(kp=2.5, 
                               ki=0.0, 
                               kd=10.0, 
                               lower=-3.0, 
                               upper=3.0
                            )
    trolley_controller = CraneController(3.0, 0.4, pos_para, angle_para)
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
        if check_new_task(MC101_processing):
            change_CT002_state( MC101_processing, "abort", False, False, reject_reason=f'recv new task') 
            return # 每次控制前都判断一次是否有新任务收到
        MC001 = get_global('MC001')
        if MC001['data']['ctr_mod_auto'] == 0:
            stop() # 切手动后任务失败
            change_CT002_state(MC101,"abort", False, False, reject_reason='auto change to manual') 
            break
        if judge_stop():
            change_CT002_state(MC101,"abort", False, False, reject_reason='recv MC102') 
            break            
        MC114 = get_global('MC114')
        theta = MC114['data']['spreader_target_theta']
        y, vy = MC001['data']['trolley_pos'], MC001['data']['trolley_vel']
        z, vz = MC001['data']['hoist_height'], MC001['data']['rope_vel']
        t = time.time() - t0 
        if abs(y - y_start) < 10:
            target_z = target_z_1
        elif abs(y - target_y) < 10:
            target_z = target_z_2

        # exit condition
        if y < 5 or y > 110:
            print('Trolley out of Range.')
        if abs(theta) > 0.6:
            print('Swing out of Control.')
            stop()
            break
        if t > 100:
            print('Timeout Error.')
            stop()
            break
        if abs(y-target_y) <= 0.05 and abs(theta)< 0.05 and (0.0 < (z-target_z) < 0.1):
            exit_count += 1
        else:
            exit_count = 0
        if exit_count >= 1.0:
            print('Trolley Arrives.')
            stop()
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
        if abs(z-target_z) < 0.1:
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
    plt.scatter(y_list, z_list)
    plt.title('trajectory')
    plt.figure(2)
    plt.plot(t_list, np.array(theta_list))
    plt.title('theta')
    plt.figure(3)
    plt.plot(t_list, np.array(uy_list), label='reference velocity')
    plt.plot(t_list, np.array(vy_list), label='actual velocity')
    plt.legend()
    plt.savefig(f"./log/{int(time.time()*1000)}.jpg")    

def twist_lock(value):
    # 闭锁
    send_msg = get_global('CT001') 
    send_msg["timestamp"] = int(time.time() * 1000)
    send_msg["msg_uid"] = str(uuid.uuid1())
    send_msg["data"] = [ {"cmd": "twist_lock", "value":value}, ]
    set_global('CT001', send_msg)
    send_msg = json.dumps(send_msg, ensure_ascii=False)
    CT2MC_pub.send_msg(send_msg)
    print("at time {} send msg to MC:\n{}\n".format(time.asctime(time.localtime()), send_msg))

def set_flip(mode, down_list):
    '''
        mode: 升/放导板
        [1,2,3,4], #//需要下翻的导板 1=海左2=海右3=陆左4=陆右
    '''
    print(mode, down_list)
    if mode == 'up': # 升导板
        time_cnt = 0 
        while True: # 控制升导板 直到plc反馈执行完
            try:
                # ！！！ todo 流畅作业时
                send_msg = get_global('CT001')
                send_msg["msg_uid"] = str(uuid.uuid1())
                send_msg["timestamp"] = int(time.time() * 1000)
                send_msg["data"] = [{'cmd': 'flipper', 'value': 0}]
                set_global('CT001', send_msg)
                send_msg = json.dumps(send_msg, ensure_ascii=False)
                CT2MC_pub.send_msg(send_msg)
                
                time.sleep(0.2)
                MC001 = get_global('MC001')
                if MC001['data']['spreader_flipper_sea_side_l_status'] == 0\
                and MC001['data']['spreader_flipper_sea_side_r_status'] == 0\
                and MC001['data']['spreader_flipper_land_side_l_status'] == 0\
                and MC001['data']['spreader_flipper_land_side_r_status'] == 0:
                    return True
            except Exception as error:
                print(error)
                error_logger.error(f'set flip up: {error}')
                return False
            if time_cnt > 10:
                return False
                break
            time_cnt += 1
            
    elif mode == 'down':
        cmdlist = []
        flipper_multi = 0
        for item in down_list:
            flipper_multi += 2 ** (4-int(item))
            # cmdlist.append({'cmd': 'flipper_single', 'value': int(item)})
        cmdlist = [{'cmd': 'flipper_multi', 'value': flipper_multi}]
        print(down_list, cmdlist)
        time_cnt = 0
        while True:
            try:
                send_msg = get_global('CT001')
                send_msg["msg_uid"] = str(uuid.uuid1())
                send_msg["timestamp"] = int(time.time() * 1000)
                send_msg["data"] = cmdlist
                set_global('CT001', send_msg)
                send_msg = json.dumps(send_msg, ensure_ascii=False)
                CT2MC_pub.send_msg(send_msg)

                single_flip_list = ['spreader_flipper_sea_side_l_status', 'spreader_flipper_sea_side_r_status', \
                                    'spreader_flipper_land_side_l_status', 'spreader_flipper_land_side_r_status']
                finished = True
                MC001 = get_global('MC001')
                for item in down_list:              
                    if MC001['data'][single_flip_list[item-1]] != 1:
                        finished = False
                if finished:
                    return True
            except Exception as error:
                print(error)
                error_logger.error(f'set down {down_list}, use {cmdlist}, but {error}')
                return False
            if time_cnt > 10:
                return False
                break
            time_cnt += 1
            time.sleep(0.3)            
    return True

def plc_spreader_state():
    '''
        plc_spreader_single_state #/int,/单箱模式状态, 0-单箱模式未到位,1-单箱模式到位
        plc_spreader_double_state #int,双箱模式状态, 0-单双箱模式未到位,1-双箱模式到位
        plc_spreader_20f  #int,20尺状态, 0-20尺状态未到位,1-20尺状态到位
        plc_spreader_40f  #int,40尺状态, 0-20尺状态未到位,1-20尺状态到位
        plc_spreader_45f  #int,45尺状态, 0-20尺状态未到位,1-20尺状态到位   
    '''
    MC001 = get_global('MC001')
    plc_spreader_single_state = MC001["data"]["spreader_single_state"] #/int,/单箱模式状态, 0-单箱模式未到位,1-单箱模式到位
    plc_spreader_double_state = MC001["data"]["spreader_double_state"] #int,双箱模式状态, 0-单双箱模式未到位,1-双箱模式到位
    plc_spreader_20f = MC001["data"]["spreader_20f"] #int,20尺状态, 0-20尺状态未到位,1-20尺状态到位
    plc_spreader_40f = MC001["data"]["spreader_40f"] #int,40尺状态, 0-20尺状态未到位,1-20尺状态到位
    plc_spreader_45f = MC001["data"]["spreader_45f"] #int,45尺状态, 0-20尺状态未到位,1-20尺状态到位
    
    plc_spreader_size, plc_spreader_twin_mode= 0, 0 #未到位
    
    # 
    if plc_spreader_single_state == 1:
        plc_spreader_twin_mode = 1 
    elif plc_spreader_double_state == 1:
        plc_spreader_twin_mode = 2

    if plc_spreader_20f == 1:
        plc_spreader_size = 1 
    elif plc_spreader_40f == 1:
        plc_spreader_size = 2
    elif plc_spreader_45f == 1:
        plc_spreader_size = 3
    return plc_spreader_size, plc_spreader_twin_mode


def set_spreader(change_spreader_twin_mode, change_spreader_size):
    # {"cmd":"spreader_size", "value": 2} # 1-20尺，2-40尺，3-45尺
    # {"cmd":"spreader_twin_mode", "value": 2} 1-单箱模式，2-双箱模式
    # 单箱 -> 双箱：先设置20尺 再输入单箱
    # 双箱 -> 单箱：先设置单箱 再改20尺
    CmdSet, set_flag = [], False
    plc_spreader_size, plc_spreader_twin_mode = plc_spreader_state()
    if change_spreader_size == '20f': change_spreader_size, change_spreader_twin_mode = 1,1
    elif change_spreader_size == '40f': change_spreader_size, change_spreader_twin_mode = 2,1
    elif change_spreader_size == 'D20f': change_spreader_size, change_spreader_twin_mode = 2,2
    elif change_spreader_size == '45f': change_spreader_size, change_spreader_twin_mode = 3,1
    
    print(plc_spreader_twin_mode, change_spreader_twin_mode, plc_spreader_size, change_spreader_size)
    
    if plc_spreader_twin_mode == change_spreader_twin_mode and  plc_spreader_size == change_spreader_size:
        return True 
    elif (plc_spreader_twin_mode == change_spreader_twin_mode):
        # 双箱模式下不需要等待吊具尺寸到位
        if plc_spreader_twin_mode == 2 and change_spreader_twin_mode == 2:
            return True  
        # 单箱等待吊具尺寸到位、之后输入控制双箱状态
        reset_cnt = 0
        while True:
            time.sleep(0.1)
            plc_spreader_size, plc_spreader_twin_mode = plc_spreader_state()
            if (plc_spreader_size == change_spreader_size):
                set_cmd([{"cmd":"spreader_twin_mode", "value": change_spreader_twin_mode}])
                break
            if reset_cnt < 1000:
                set_cmd([{"cmd":"spreader_size", "value": change_spreader_size}])          
            else:
                print(f"set spreader_size: {change_spreader_size} failed")
                error_logger.error(f"set spreader_size: {change_spreader_size} failed")
                break
            reset_cnt += 1
    elif (plc_spreader_twin_mode == 1) and (change_spreader_size == 2):
        set_cmd([{"cmd":"spreader_size", "value": change_spreader_size}])
        # 等待吊具尺寸到位、之后输入控制双箱状态
        reset_cnt = 0
        while True:
            time.sleep(0.1)
            plc_spreader_size, plc_spreader_twin_mode = plc_spreader_state()
            if (plc_spreader_size == change_spreader_size):
                set_cmd([{"cmd":"spreader_twin_mode", "value": change_spreader_twin_mode}])
                break
            if reset_cnt < 1000:
                set_cmd([{"cmd":"spreader_size", "value": change_spreader_size}])          
            else:
                # log
                print(f"set spreader_size: {change_spreader_size} failed")
                break
            reset_cnt += 1

        # 等待吊具单/双箱到位
        reset_cnt = 0
        while True:
            time.sleep(0.1)
            plc_spreader_size, plc_spreader_twin_mode = plc_spreader_state()
            if (plc_spreader_twin_mode == change_spreader_twin_mode):
                set_flag = True
                break
            if reset_cnt > 1000:
                print(f"set spreader_twin_mode: {change_spreader_twin_mode} failed")
                break           
            # log
            reset_cnt += 1
    
    elif (plc_spreader_twin_mode == 2) and (change_spreader_size != 2):
        set_cmd([{"cmd": "spreader_twin_mode", "value": change_spreader_twin_mode}])
        # 等待单箱状态到位、之后控制吊具尺寸
        reset_cnt = 0
        while True:
            time.sleep(0.1)
            plc_spreader_size, plc_spreader_twin_mode = plc_spreader_state()
            if (plc_spreader_twin_mode == change_spreader_twin_mode):
                set_cmd([{"cmd":"spreader_size", "value": change_spreader_size}])
                break
            if reset_cnt < 1000:
                CmdSet.append({"cmd":"spreader_twin_mode", "value": change_spreader_twin_mode})        
            else:
                # log
                print(f"set spreader_twin_mode: {change_spreader_twin_mode} failed")
                break
            reset_cnt += 1

        # 等待控制吊具尺寸
        reset_cnt = 0
        while True:
            time.sleep(0.1)
            plc_spreader_size, plc_spreader_twin_mode = plc_spreader_state()
            if (plc_spreader_size == change_spreader_size):
                set_flag = True
                break
            if reset_cnt > 1000:
                print(f"set change_spreader_size: {change_spreader_size} failed")
                break           
            # log
            reset_cnt += 1

    return set_flag


def set_midlock(midlock_value:int):
    '''
    midlock_value: 11-中锁缩运动  10-中锁缩停止，
           21-中锁伸运动  20-中锁伸停止
    '''
    send_msg = get_global('CT001') 
    send_msg["timestamp"] = int(time.time() * 1000)
    send_msg["msg_uid"] = str(uuid.uuid1())
    send_msg["data"] = [ {"cmd": "spreader_mid_lock", "value": midlock_value}, ]
    set_global('CT001', send_msg)
    send_msg = json.dumps(send_msg, ensure_ascii=False)
    CT2MC_pub.send_msg(send_msg)
    print("at time {} send msg to MC:\n{}\n".format(time.asctime(time.localtime()), send_msg))    


if __name__ == "__main__":
    # 测试项
    hoist_control()
    trolley_control()
