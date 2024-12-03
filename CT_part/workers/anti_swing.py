from global_info import *
from initializers import *
from ctrl_utils import *
import threading
import zmq
import time 
from scipy.ndimage import median_filter

class thread_anti_swing(threading.Thread):
    def __init__(self):
        super().__init__()
        self.complete_flag = False

    def run(self):
        while True:
            time.sleep(0.115)
            MC001 = get_global('MC001') 
            if MC001['data']['ctr_mod_manual'] and MC001['data']['spreader_anti_sway']: # 手动模式下触发原地防摇
                if self.complete_flag == False:# 如果防摇未完成，进行一次防摇任务
                    self.anti_swing()
            else:
                self.complete_flag = False

            if abs(MC001['data']['trolley_handle_value']) > 1e-6 or\
            abs(MC001['data']['spreader_handle_value']) > 1e-6 or\
            abs(MC001['data']['gantry_handle_value']) > 1e-6: # 手柄信号重置防摇标志位
                self.complete_flag =  False
                
    def anti_swing(self):
        MC001 = get_global('MC001')
        y_start = MC001['data']['trolley_pos']
        pos_para = PIDParameters(kp= 0.0, 
                                ki= 0.0, 
                                kd= 0.0, 
                                lower= -3.8, 
                                upper= 3.8
                                )
        angle_para = PIDParameters(kp=5.0, 
                                ki=0.0, 
                                kd=10.0, 
                                lower=-3.8, 
                                upper=3.8
                                )
        trolley_controller = CraneController(3.8, 0.6, pos_para, angle_para)
        trolley_controller.set(y_start, y_start)
        t0 = time.time()
        count = 0
        theta_list = []
        while True:
            MC001 = get_global('MC001')
            MC114 = get_global('MC114')
            t = time.time() - t0
            y, vy = MC001['data']['trolley_pos'], MC001['data']['trolley_vel']
            z = MC001['data']['hoist_height']
            theta = MC114['data']['spreader_target_theta']
            zeta = MC114['data']['spreader_target_zeta']
            theta_list.append(zeta)
            # 退出条件
            if t > 30: # 超时退出 
                print('Timeout error.')
                self.complete_flag = True
                stop()
                break

            if abs(MC001['data']['trolley_handle_value']) > 1e-6 or\
            abs(MC001['data']['spreader_handle_value']) > 1e-6 or\
            abs(MC001['data']['gantry_handle_value']) > 1e-6: # 手柄信号打断
                print('Handle Signal.')
                self.complete_flag = True
                stop()
                break
                
            if MC001['data']['ctr_mod_manual'] == 0 or\
                MC001['data']['spreader_anti_sway'] == 0: # 取消防摇退出
                print('Anti-swing stop.')
                self.complete_flag = True
                stop()
                break

            if abs(y-y_start) > 10: # 超出位置范围退出
                print('Out of range.')
                self.complete_flag = True
                stop()
                break
            
            if abs(theta) < 0.015 and abs(y - y_start) < 10: # 满足消摆条件退出
                count += 1
            else:
                count = 0
            if count > 20:
                print('Swinging eliminated.')
                self.complete_flag = True
                stop()
                break
            
            # 计算控制量
            uy, u_pos, u_angle, yd = trolley_controller.step(t, y, theta)
            print(f't:{t:.2f}, y:{y:.2f}, theta:{theta:.4f}, zeta:{zeta:.4f}, v:{vy:.2f}, u:{uy:.2f}')
            set_velocity(uy, 0.0)

            # 等待控制周期
            time.sleep(0.04)
        theta_list = np.array(theta_list)
        np.save('zeta.npy', theta_list)
        theta_list = median_filter(theta_list, 20)
        # print("zero position:", np.mean(theta_list))