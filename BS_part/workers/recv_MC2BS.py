
from global_info import *
from initializers import *
import threading
import zmq
import time 
import uuid

def process_MC401():
    MC401 = get_global('MC401')

    BS001 = get_global('BS001')
    BS002 = get_global('BS002')
    BS003 = get_global('BS003')
    BS004 = get_global('BS004')
    BS005 = get_global('BS005')

    # 更新 BS001 BS003 BS005 bay_id
    BS001['data']['bay_id'] = MC409['data']['bay_id']
    BS003['data']['bay_id'] = MC409['data']['bay_id']
    BS004['data']['bay_id'] = MC409['data']['bay_id']
    BS005['data']['bay_id'] = MC409['data']['bay_id']

    BS001["msg_uid"] = str(uuid.uuid1())
    BS001["timestamp"] = int(time.time() * 1000)
    set_global('BS001', BS001)
    BS002["msg_uid"] = str(uuid.uuid1())
    BS002["timestamp"] = int(time.time() * 1000)
    set_global('BS002', BS002)
    BS003["msg_uid"] = str(uuid.uuid1())
    BS003["timestamp"] = int(time.time() * 1000)
    set_global('BS003', BS003)
    BS004["msg_uid"] = str(uuid.uuid1())
    BS004["timestamp"] = int(time.time() * 1000)
    set_global('BS004', BS004)
    BS005["msg_uid"] = str(uuid.uuid1())
    BS005["timestamp"] = int(time.time() * 1000)
    set_global('BS005', BS005)

    try:
        # 启动贝扫
        # 反馈贝扫执行状态进行中
        BS001 = get_global('BS001')
        BS001["msg_uid"] = str(uuid.uuid1())
        BS001["timestamp"] = int(time.time() * 1000)
        BS001['data']['state'] = 1 #int, 0=未扫描，1=扫描中，2=完成扫描，3=扫描异常
        set_global('BS001', BS001)        
        BS2MC_pub.send_msg(json.dumps(BS001))

        # 请求动小车
        BS007 = get_global('BS007')
        BS007["msg_uid"] = str(uuid.uuid1())
        BS007["timestamp"] = int(time.time() * 1000)  
        BS007['data']['trolley_start_pos'] = MC401['data']['ship_start_pos'] - 5.0
        BS007['data']['trolley_end_pos'] = MC401['data']['ship_stop_pos'] + 5.0
        set_global('BS007', BS007)        
        BS2MC_pub.send_msg(json.dumps(BS007))
        
        # todo 在指定位置等待后采集数据，更新船舶数据\贝扫数据\计划放箱位置
        import random
        # time.sleep(random.randrange(3.2, 60))
        time.sleep(5)
        BS002 = get_global('BS002')
        BS002["msg_uid"] = str(uuid.uuid1())
        BS002["timestamp"] = int(time.time() * 1000) 
        BS002['data']['ship_start_pos'] = 58.1 + 0.01*random.randrange(20, 50)
        BS002['data']['ship_stop_pos'] = MC401['data']['ship_stop_pos'] # + 0.1*random.randrange(-20, 20)
        set_global('BS002', BS002)  

        BS003 = get_global('BS003')
        BS003["msg_uid"] = str(uuid.uuid1())
        BS003["timestamp"] = int(time.time() * 1000) 
        BS003["data"]['bay_id'] = MC401["data"]['bay_id']
        BS003["data"]['safety_height'] = 20.0 
        BS003["data"]['top_object_height'] = 15.9  + 0.1*random.uniform(-20, 20)
        # BS003["data"]['bay_profile'] = [
        #     {
        #         "row_index":1,
        #         "container_id": None,
        #         "container_pos" : [BS002['data']['ship_start_pos'] + 0.01*random.randrange(10, 20), \
        #                             0.01*random.randrange(-20, 20), \
        #                             6.0465 + 0.02*random.randrange(-20, 20)],#集装箱坐标,x,y,z
        #         "size" : "D20f", #集装箱尺寸,"20f"-20尺集装箱,"40f"-40尺集装箱,"D20f"-双20,"cabin_20f",-空舱位,"cabin_D20f"-空舱位双箱位置,"45f",-45尺集装箱,"other"-其他
        #         "tier" : "0", #层号
        #         "target_object_height":6.0465 + 0.01*random.randrange(-20, 20),
        #         "adjacent_object_height":6.0465
        #     },
        #     {
        #         "row_index":2,
        #         "container_id": None,
        #         "container_pos" : [BS002['data']['ship_start_pos'] + 2.44 + 0.01*random.randrange(10, 40), \
        #                             0.01*random.randrange(-20, 20), \
        #                             6.0465+ 0.02*random.randrange(-20, 0)],#集装箱坐标,x,y,z
        #         "size" : "D20f", #集装箱尺寸,"20f"-20尺集装箱,"40f"-40尺集装箱,"D20f"-双20,"cabin_20f",-空舱位,"cabin_D20f"-空舱位双箱位置,"45f",-45尺集装箱,"other"-其他
        #         "tier" : "4", #层号
        #         "target_object_height":6.0465 + 0.02*random.randrange(-20, 0),
        #         "adjacent_object_height":6.0465
        #     },
        #     {
        #         "row_index":3,
        #         "container_id": None,
        #         "container_pos" : [BS002['data']['ship_start_pos'] + 4.8 + 0.1*random.uniform(-1, 1), \
        #                             0.01*random.randrange(-20, 20), \
        #                             6.0465+ 0.02*random.randrange(-20, 0)],#集装箱坐标,x,y,z
        #         "size" : "D20f", #集装箱尺寸,"20f"-20尺集装箱,"40f"-40尺集装箱,"D20f"-双20,"cabin_20f",-空舱位,"cabin_D20f"-空舱位双箱位置,"45f",-45尺集装箱,"other"-其他
        #         "tier" : "4", #层号
        #         "target_object_height":6.0465+ 0.01*random.randrange(-20, 0),
        #         "adjacent_object_height":6.0465
        #     },
        #     {
        #         "row_index":4,
        #         "container_id": None,
        #         "container_pos" : [BS002['data']['ship_start_pos'] + 7.2 + 0.1*random.uniform(-1, 1), \
        #                             0.01*random.randrange(-50, 50), \
        #                             6.0465+ 0.02*random.randrange(-20, 0)],#集装箱坐标,x,y,z
        #         "size" : "D20f", #集装箱尺寸,"20f"-20尺集装箱,"40f"-40尺集装箱,"D20f"-双20,"cabin_20f",-空舱位,"cabin_D20f"-空舱位双箱位置,"45f",-45尺集装箱,"other"-其他
        #         "tier" : "5", #层号
        #         "target_object_height":6.0465+ 0.01*random.randrange(-20, 0),
        #         "adjacent_object_height":6.0465
        #     },
        #     {
        #         "row_index":5,
        #         "container_id": None,
        #         "container_pos" : [BS002['data']['ship_start_pos'] + 9.72 - 0.1*random.uniform(-1, 1), \
        #                             0.01*random.randrange(-50, 50), \
        #                             6.0465+ 0.02*random.randrange(-20, 0)],#集装箱坐标,x,y,z
        #         "size" : "D20f", #集装箱尺寸,"20f"-20尺集装箱,"40f"-40尺集装箱,"D20f"-双20,"cabin_20f",-空舱位,"cabin_D20f"-空舱位双箱位置,"45f",-45尺集装箱,"other"-其他
        #         "tier" : "5", #层号
        #         "target_object_height":6.0465 + 0.01*random.randrange(-20, 0),
        #         "adjacent_object_height":6.0465
        #     },
        #     {
        #         "row_index":6,
        #         "container_id": None,
        #         "container_pos" : [BS002['data']['ship_start_pos'] + 12.0 - 0.01*random.randrange(1, 10), \
        #                             0.01*random.randrange(-50, 50), \
        #                             6.0465+ 0.01*random.randrange(-20, 0)],#集装箱坐标,x,y,z
        #         "size" : "D20f", #集装箱尺寸,"20f"-20尺集装箱,"40f"-40尺集装箱,"D20f"-双20,"cabin_20f",-空舱位,"cabin_D20f"-空舱位双箱位置,"45f",-45尺集装箱,"other"-其他
        #         "tier" : "5", #层号
        #         "target_object_height":6.0465+ 0.01*random.randrange(-20, 0),
        #         "adjacent_object_height":6.0465
        #     },
        #     {
        #         "row_index":7,
        #         "container_id": None,
        #         "container_pos" : [BS002['data']['ship_start_pos'] + 14.4 - 0.01*random.randrange(1, 10), \
        #                             0.01*random.randrange(-50, 50), \
        #                             6.0465+ 0.01*random.randrange(-20, 0)],#集装箱坐标,x,y,z
        #         "size" : "D20f", #集装箱尺寸,"20f"-20尺集装箱,"40f"-40尺集装箱,"D20f"-双20,"cabin_20f",-空舱位,"cabin_D20f"-空舱位双箱位置,"45f",-45尺集装箱,"other"-其他
        #         "tier" : "5", #层号
        #         "target_object_height":6.0465+ 0.01*random.randrange(-20, 0),
        #         "adjacent_object_height":6.0465
        #     },
        #
        # ]

        # BS003["data"]['bay_profile'] = [
        #     {
        #         "row_index":1,
        #         "container_id": None,
        #         "container_pos" : [BS002['data']['ship_start_pos'] +3.4 + 0.01*random.randrange(10, 20), \
        #                             0.01*random.randrange(-20, 20), \
        #                             6.4065 + 0.02*random.randrange(-20, 20)],#集装箱坐标,x,y,z
        #         "size" : "20f", #集装箱尺寸,"20f"-20尺集装箱,"40f"-40尺集装箱,"D20f"-双20,"cabin_20f",-空舱位,"cabin_D20f"-空舱位双箱位置,"45f",-45尺集装箱,"other"-其他
        #         "tier" : "0", #层号
        #         "target_object_height":6.4065 + 0.01*random.randrange(-20, 20),
        #         "adjacent_object_height":6.4065
        #     },
        #     {
        #         "row_index":2,
        #         "container_id": None,
        #         "container_pos" : [BS002['data']['ship_start_pos']+3.4 + 2.44 + 0.01*random.randrange(10, 40), \
        #                             0.01*random.randrange(-20, 20), \
        #                             6.0112+ 0.02*random.randrange(-20, 0)],#集装箱坐标,x,y,z
        #         "size" : "20f", #集装箱尺寸,"20f"-20尺集装箱,"40f"-40尺集装箱,"D20f"-双20,"cabin_20f",-空舱位,"cabin_D20f"-空舱位双箱位置,"45f",-45尺集装箱,"other"-其他
        #         "tier" : "4", #层号
        #         "target_object_height":6.0112 + 0.02*random.randrange(-20, 0),
        #         "adjacent_object_height":6.4065
        #     },
        #     {
        #         "row_index":3,
        #         "container_id": None,
        #         "container_pos" : [BS002['data']['ship_start_pos']+3.4 + 4.8 + 0.1*random.uniform(-1, 1), \
        #                             0.01*random.randrange(-20, 20), \
        #                             6.0112+ 0.02*random.randrange(-20, 0)],#集装箱坐标,x,y,z
        #         "size" : "20f", #集装箱尺寸,"20f"-20尺集装箱,"40f"-40尺集装箱,"D20f"-双20,"cabin_20f",-空舱位,"cabin_D20f"-空舱位双箱位置,"45f",-45尺集装箱,"other"-其他
        #         "tier" : "4", #层号
        #         "target_object_height":6.0112+ 0.01*random.randrange(-20, 0),
        #         "adjacent_object_height":6.4065
        #     },
        #     {
        #         "row_index":4,
        #         "container_id": None,
        #         "container_pos" : [BS002['data']['ship_start_pos'] +3.4+ 7.2 + 0.1*random.uniform(-1, 1), \
        #                             0.01*random.randrange(-50, 50), \
        #                             6.4065+ 0.02*random.randrange(-20, 0)],#集装箱坐标,x,y,z
        #         "size" : "20f", #集装箱尺寸,"20f"-20尺集装箱,"40f"-40尺集装箱,"D20f"-双20,"cabin_20f",-空舱位,"cabin_D20f"-空舱位双箱位置,"45f",-45尺集装箱,"other"-其他
        #         "tier" : "5", #层号
        #         "target_object_height":6.4065+ 0.01*random.randrange(-20, 0),
        #         "adjacent_object_height":6.4065
        #     },
        #
        # ]
        # BS003["data"]['bay_profile'] = [
        #     {
        #         "row_index":1,
        #         "container_id": None,
        #         "container_pos" : [BS002['data']['ship_start_pos'] + 0.01*random.randrange(10, 20), \
        #                             0.01*random.randrange(-20, 20), \
        #                             26.6265-2.8+ 0.02*random.randrange(-20, 20)],#集装箱坐标,x,y,z
        #         "size" : "D20f", #集装箱尺寸,"20f"-20尺集装箱,"40f"-40尺集装箱,"D20f"-双20,"cabin_20f",-空舱位,"cabin_D20f"-空舱位双箱位置,"45f",-45尺集装箱,"other"-其他
        #         "tier" : "4", #层号
        #         "target_object_height": 26.6265-2.8+ 0.01*random.randrange(-20, 20),
        #         "adjacent_object_height": 26.6265
        #     },
        #     {
        #         "row_index":2,
        #         "container_id": None,
        #         "container_pos" : [BS002['data']['ship_start_pos'] + 2.44 + 0.01*random.randrange(10, 40), \
        #                             0.01*random.randrange(-20, 20), \
        #                             26.6265+ 0.02*random.randrange(-20, 20)],#集装箱坐标,x,y,z
        #         "size" : "D20f", #集装箱尺寸,"20f"-20尺集装箱,"40f"-40尺集装箱,"D20f"-双20,"cabin_20f",-空舱位,"cabin_D20f"-空舱位双箱位置,"45f",-45尺集装箱,"other"-其他
        #         "tier" : "4", #层号
        #         "target_object_height": 26.6265+ 0.02*random.randrange(-20, 0),
        #         "adjacent_object_height": 26.6265
        #     },
        #     {
        #         "row_index":3,
        #         "container_id": None,
        #         "container_pos" : [BS002['data']['ship_start_pos'] + 4.8 + 0.1*random.uniform(-1, 1), \
        #                             0.01*random.randrange(-20, 20), \
        #                             26.6265+ 0.02*random.randrange(-20, 0)],#集装箱坐标,x,y,z
        #         "size" : "D20f", #集装箱尺寸,"20f"-20尺集装箱,"40f"-40尺集装箱,"D20f"-双20,"cabin_20f",-空舱位,"cabin_D20f"-空舱位双箱位置,"45f",-45尺集装箱,"other"-其他
        #         "tier" : "4", #层号
        #         "target_object_height": 26.6265+ 0.01*random.randrange(-20, 0),
        #         "adjacent_object_height": 26.6265
        #     },
        #     {
        #         "row_index":4,
        #         "container_id": None,
        #         "container_pos" : [BS002['data']['ship_start_pos'] + 7.2 + 0.1*random.uniform(-1, 1), \
        #                             0.01*random.randrange(-50, 50), \
        #                             26.6265+ 0.02*random.randrange(-20, 0)],#集装箱坐标,x,y,z
        #         "size" : "D20f", #集装箱尺寸,"20f"-20尺集装箱,"40f"-40尺集装箱,"D20f"-双20,"cabin_20f",-空舱位,"cabin_D20f"-空舱位双箱位置,"45f",-45尺集装箱,"other"-其他
        #         "tier" : "5", #层号
        #         "target_object_height": 26.6265+ 0.01*random.randrange(-20, 0),
        #         "adjacent_object_height": 26.6265
        #     },
        #     {
        #         "row_index":5,
        #         "container_id": None,
        #         "container_pos" : [BS002['data']['ship_start_pos'] + 9.72 - 0.1*random.uniform(-1, 1), \
        #                             0.01*random.randrange(-50, 50), \
        #                             26.6265+ 0.02*random.randrange(-20, 0)],#集装箱坐标,x,y,z
        #         "size" : "D20f", #集装箱尺寸,"20f"-20尺集装箱,"40f"-40尺集装箱,"D20f"-双20,"cabin_20f",-空舱位,"cabin_D20f"-空舱位双箱位置,"45f",-45尺集装箱,"other"-其他
        #         "tier" : "5", #层号
        #         "target_object_height": 26.6265+ 0.01*random.randrange(-20, 0),
        #         "adjacent_object_height": 26.6265
        #     },
        #     {
        #         "row_index":6,
        #         "container_id": None,
        #         "container_pos" : [BS002['data']['ship_start_pos'] + 12.0 - 0.01*random.randrange(1, 10), \
        #                             0.01*random.randrange(-50, 50), \
        #                             26.6265+ 0.01*random.randrange(-20, 0)],#集装箱坐标,x,y,z
        #         "size" : "D20f", #集装箱尺寸,"20f"-20尺集装箱,"40f"-40尺集装箱,"D20f"-双20,"cabin_20f",-空舱位,"cabin_D20f"-空舱位双箱位置,"45f",-45尺集装箱,"other"-其他
        #         "tier" : "5", #层号
        #         "target_object_height": 26.6265+ 0.01*random.randrange(-20, 0),
        #         "adjacent_object_height": 26.6265
        #     },
        #     {
        #         "row_index":7,
        #         "container_id": None,
        #         "container_pos" : [BS002['data']['ship_start_pos'] + 14.4 - 0.01*random.randrange(1, 10), \
        #                             0.01*random.randrange(-50, 50), \
        #                             26.6265+ 0.01*random.randrange(-20, 0)],#集装箱坐标,x,y,z
        #         "size" : "D20f", #集装箱尺寸,"20f"-20尺集装箱,"40f"-40尺集装箱,"D20f"-双20,"cabin_20f",-空舱位,"cabin_D20f"-空舱位双箱位置,"45f",-45尺集装箱,"other"-其他
        #         "tier" : "5", #层号
        #         "target_object_height": 26.6265+ 0.01*random.randrange(-20, 0),
        #         "adjacent_object_height": 26.6265
        #     },
        #     {
        #         "row_index":8,
        #         "container_id": None,
        #         "container_pos" : [BS002['data']['ship_start_pos'] + 16.8+0.01*random.randrange(1, 10), \
        #                             0.01*random.randrange(-50, 50), \
        #                             26.6265+ 0.01*random.randrange(-20, 0)],#集装箱坐标,x,y,z
        #         "size" : "D20f", #集装箱尺寸,"20f"-20尺集装箱,"40f"-40尺集装箱,"D20f"-双20,"cabin_20f",-空舱位,"cabin_D20f"-空舱位双箱位置,"45f",-45尺集装箱,"other"-其他
        #         "tier" : "5", #层号
        #         "target_object_height": 26.6265+ 0.01*random.randrange(-20, 0),
        #         "adjacent_object_height": 26.6265
        #     },
        #     {
        #         "row_index":9,
        #         "container_id": None,
        #         "container_pos" : [BS002['data']['ship_start_pos'] + 19.2 + 0.01*random.randrange(-10, 10), \
        #                             0.01*random.randrange(-50, 50), \
        #                             26.6265+ 0.01*random.randrange(-20, 0)],#集装箱坐标,x,y,z
        #         "size" : "D20f", #集装箱尺寸,"20f"-20尺集装箱,"40f"-40尺集装箱,"D20f"-双20,"cabin_20f",-空舱位,"cabin_D20f"-空舱位双箱位置,"45f",-45尺集装箱,"other"-其他
        #         "tier" : "5", #层号
        #         "target_object_height": 26.6265+ 0.01*random.randrange(-20, 0),
        #         "adjacent_object_height": 26.6265
        #     },
        #     {
        #         "row_index": 10,
        #         "container_id": None,
        #         "container_pos": [BS002['data']['ship_start_pos'] + 21.6 + 0.01 * random.randrange(-10, 10), \
        #                           0.01 * random.randrange(-50, 50), \
        #                           26.6265+ 0.01 * random.randrange(-20, 0)],  # 集装箱坐标,x,y,z
        #         "size": "D20f",
        #         # 集装箱尺寸,"20f"-20尺集装箱,"40f"-40尺集装箱,"D20f"-双20,"cabin_20f",-空舱位,"cabin_D20f"-空舱位双箱位置,"45f",-45尺集装箱,"other"-其他
        #         "tier": "5",  # 层号
        #         "target_object_height": 26.6265+ 0.01 * random.randrange(-20, 0),
        #         "adjacent_object_height": 26.6265
        #     },
        #     {
        #         "row_index": 11,
        #         "container_id": None,
        #         "container_pos": [BS002['data']['ship_start_pos'] +24.0 + 0.01 * random.randrange(-10, 10), \
        #                           0.01 * random.randrange(-50, 50), \
        #                           26.6265  + 0.01 * random.randrange(-20, 0)],  # 集装箱坐标,x,y,z
        #         "size": "D20f",
        #         # 集装箱尺寸,"20f"-20尺集装箱,"40f"-40尺集装箱,"D20f"-双20,"cabin_20f",-空舱位,"cabin_D20f"-空舱位双箱位置,"45f",-45尺集装箱,"other"-其他
        #         "tier": "5",  # 层号
        #         "target_object_height":  26.6265+ 0.01 * random.randrange(-20, 0),
        #         "adjacent_object_height": 26.6265
        #     },
        #     {
        #         "row_index": 12,
        #         "container_id": None,
        #         "container_pos": [BS002['data']['ship_start_pos'] + 26.4 + 0.01 * random.randrange(-10, 10), \
        #                           0.01 * random.randrange(-50, 50), \
        #                           26.6265  + 0.01 * random.randrange(-20, 0)],  # 集装箱坐标,x,y,z
        #         "size": "D20f",
        #         # 集装箱尺寸,"20f"-20尺集装箱,"40f"-40尺集装箱,"D20f"-双20,"cabin_20f",-空舱位,"cabin_D20f"-空舱位双箱位置,"45f",-45尺集装箱,"other"-其他
        #         "tier": "5",  # 层号
        #         "target_object_height": 26.6265  + 0.01 * random.randrange(-20, 0),
        #         "adjacent_object_height": 26.6265
        #     },
        #     {
        #         "row_index": 13,
        #         "container_id": None,
        #         "container_pos": [BS002['data']['ship_start_pos'] + 28.8 + 0.01 * random.randrange(-10, 10), \
        #                           0.01 * random.randrange(-50, 50), \
        #                           26.6265-2.6+ 0.01 * random.randrange(-20, 0)],  # 集装箱坐标,x,y,z
        #         "size": "D20f",
        #         # 集装箱尺寸,"20f"-20尺集装箱,"40f"-40尺集装箱,"D20f"-双20,"cabin_20f",-空舱位,"cabin_D20f"-空舱位双箱位置,"45f",-45尺集装箱,"other"-其他
        #         "tier": "4",  # 层号
        #         "target_object_height": 26.6265-2.6+ 0.01 * random.randrange(-20, 0),
        #         "adjacent_object_height": 26.6265
        #     },
        # ]
        BS003["data"]['bay_profile'] = [
            {
                "row_index":1,
                "container_id": None,
                "container_pos" : [BS002['data']['ship_start_pos'] + 0.01*random.randrange(10, 20), \
                                    0.01*random.randrange(-20, 20), \
                                    28.8265-2.6+ 0.02*random.randrange(-20, 20)],#集装箱坐标,x,y,z
                "size" : "D20f", #集装箱尺寸,"20f"-20尺集装箱,"40f"-40尺集装箱,"D20f"-双20,"cabin_20f",-空舱位,"cabin_D20f"-空舱位双箱位置,"45f",-45尺集装箱,"other"-其他
                "tier" : "4", #层号
                "target_object_height": 28.8265-2.6+ 0.01*random.randrange(-20, 20),
                "adjacent_object_height": 28.8265
            },
            {
                "row_index":2,
                "container_id": None,
                "container_pos" : [BS002['data']['ship_start_pos'] + 2.44 + 0.01*random.randrange(10, 40), \
                                    0.01*random.randrange(-20, 20), \
                                    28.8265+ 0.02*random.randrange(-20, 20)],#集装箱坐标,x,y,z
                "size" : "D20f", #集装箱尺寸,"20f"-20尺集装箱,"40f"-40尺集装箱,"D20f"-双20,"cabin_20f",-空舱位,"cabin_D20f"-空舱位双箱位置,"45f",-45尺集装箱,"other"-其他
                "tier" : "4", #层号
                "target_object_height": 28.8265+ 0.02*random.randrange(-20, 0),
                "adjacent_object_height": 28.8265
            },
            {
                "row_index":3,
                "container_id": None,
                "container_pos" : [BS002['data']['ship_start_pos'] + 4.8 + 0.1*random.uniform(-1, 1), \
                                    0.01*random.randrange(-20, 20), \
                                    28.8265+ 0.02*random.randrange(-20, 0)],#集装箱坐标,x,y,z
                "size" : "D20f", #集装箱尺寸,"20f"-20尺集装箱,"40f"-40尺集装箱,"D20f"-双20,"cabin_20f",-空舱位,"cabin_D20f"-空舱位双箱位置,"45f",-45尺集装箱,"other"-其他
                "tier" : "4", #层号
                "target_object_height": 28.8265+ 0.01*random.randrange(-20, 0),
                "adjacent_object_height": 28.8265
            },
            {
                "row_index":4,
                "container_id": None,
                "container_pos" : [BS002['data']['ship_start_pos'] + 7.2 + 0.1*random.uniform(-1, 1), \
                                    0.01*random.randrange(-50, 50), \
                                    28.8265+ 0.02*random.randrange(-20, 0)],#集装箱坐标,x,y,z
                "size" : "D20f", #集装箱尺寸,"20f"-20尺集装箱,"40f"-40尺集装箱,"D20f"-双20,"cabin_20f",-空舱位,"cabin_D20f"-空舱位双箱位置,"45f",-45尺集装箱,"other"-其他
                "tier" : "5", #层号
                "target_object_height": 28.8265+ 0.01*random.randrange(-20, 0),
                "adjacent_object_height": 28.8265
            },
            {
                "row_index":5,
                "container_id": None,
                "container_pos" : [BS002['data']['ship_start_pos'] + 9.72 - 0.1*random.uniform(-1, 1), \
                                    0.01*random.randrange(-50, 50), \
                                    28.8265+ 0.02*random.randrange(-20, 0)],#集装箱坐标,x,y,z
                "size" : "D20f", #集装箱尺寸,"20f"-20尺集装箱,"40f"-40尺集装箱,"D20f"-双20,"cabin_20f",-空舱位,"cabin_D20f"-空舱位双箱位置,"45f",-45尺集装箱,"other"-其他
                "tier" : "5", #层号
                "target_object_height": 28.8265+ 0.01*random.randrange(-20, 0),
                "adjacent_object_height": 28.8265
            },
            {
                "row_index":6,
                "container_id": None,
                "container_pos" : [BS002['data']['ship_start_pos'] + 12.0 - 0.01*random.randrange(1, 10), \
                                    0.01*random.randrange(-50, 50), \
                                    28.8265+ 0.01*random.randrange(-20, 0)],#集装箱坐标,x,y,z
                "size" : "D20f", #集装箱尺寸,"20f"-20尺集装箱,"40f"-40尺集装箱,"D20f"-双20,"cabin_20f",-空舱位,"cabin_D20f"-空舱位双箱位置,"45f",-45尺集装箱,"other"-其他
                "tier" : "5", #层号
                "target_object_height": 28.8265+ 0.01*random.randrange(-20, 0),
                "adjacent_object_height": 28.8265
            },
            {
                "row_index":7,
                "container_id": None,
                "container_pos" : [BS002['data']['ship_start_pos'] + 14.4 - 0.01*random.randrange(1, 10), \
                                    0.01*random.randrange(-50, 50), \
                                    28.8265+ 0.01*random.randrange(-20, 0)],#集装箱坐标,x,y,z
                "size" : "D20f", #集装箱尺寸,"20f"-20尺集装箱,"40f"-40尺集装箱,"D20f"-双20,"cabin_20f",-空舱位,"cabin_D20f"-空舱位双箱位置,"45f",-45尺集装箱,"other"-其他
                "tier" : "5", #层号
                "target_object_height": 28.8265+ 0.01*random.randrange(-20, 0),
                "adjacent_object_height": 28.8265
            },
            {
                "row_index":8,
                "container_id": None,
                "container_pos" : [BS002['data']['ship_start_pos'] + 16.8+0.01*random.randrange(1, 10), \
                                    0.01*random.randrange(-50, 50), \
                                    28.8265+ 0.01*random.randrange(-20, 0)],#集装箱坐标,x,y,z
                "size" : "D20f", #集装箱尺寸,"20f"-20尺集装箱,"40f"-40尺集装箱,"D20f"-双20,"cabin_20f",-空舱位,"cabin_D20f"-空舱位双箱位置,"45f",-45尺集装箱,"other"-其他
                "tier" : "5", #层号
                "target_object_height": 28.8265+ 0.01*random.randrange(-20, 0),
                "adjacent_object_height": 28.8265
            },
            {
                "row_index":9,
                "container_id": None,
                "container_pos" : [BS002['data']['ship_start_pos'] + 19.2 + 0.01*random.randrange(-10, 10), \
                                    0.01*random.randrange(-50, 50), \
                                    28.8265+ 0.01*random.randrange(-20, 0)],#集装箱坐标,x,y,z
                "size" : "D20f", #集装箱尺寸,"20f"-20尺集装箱,"40f"-40尺集装箱,"D20f"-双20,"cabin_20f",-空舱位,"cabin_D20f"-空舱位双箱位置,"45f",-45尺集装箱,"other"-其他
                "tier" : "5", #层号
                "target_object_height": 28.8265+ 0.01*random.randrange(-20, 0),
                "adjacent_object_height": 28.8265
            },
            {
                "row_index": 10,
                "container_id": None,
                "container_pos": [BS002['data']['ship_start_pos'] + 21.6 + 0.01 * random.randrange(-10, 10), \
                                  0.01 * random.randrange(-50, 50), \
                                  28.8265+ 0.01 * random.randrange(-20, 0)],  # 集装箱坐标,x,y,z
                "size": "D20f",
                # 集装箱尺寸,"20f"-20尺集装箱,"40f"-40尺集装箱,"D20f"-双20,"cabin_20f",-空舱位,"cabin_D20f"-空舱位双箱位置,"45f",-45尺集装箱,"other"-其他
                "tier": "5",  # 层号
                "target_object_height": 28.8265+ 0.01 * random.randrange(-20, 0),
                "adjacent_object_height": 28.8265
            },
            {
                "row_index": 11,
                "container_id": None,
                "container_pos": [BS002['data']['ship_start_pos'] +24.0 + 0.01 * random.randrange(-10, 10), \
                                  0.01 * random.randrange(-50, 50), \
                                  28.8265  + 0.01 * random.randrange(-20, 0)],  # 集装箱坐标,x,y,z
                "size": "D20f",
                # 集装箱尺寸,"20f"-20尺集装箱,"40f"-40尺集装箱,"D20f"-双20,"cabin_20f",-空舱位,"cabin_D20f"-空舱位双箱位置,"45f",-45尺集装箱,"other"-其他
                "tier": "5",  # 层号
                "target_object_height":  28.8265+ 0.01 * random.randrange(-20, 0),
                "adjacent_object_height": 28.8265
            },
            {
                "row_index": 12,
                "container_id": None,
                "container_pos": [BS002['data']['ship_start_pos'] + 26.4 + 0.01 * random.randrange(-10, 10), \
                                  0.01 * random.randrange(-50, 50), \
                                  28.8265  + 0.01 * random.randrange(-20, 0)],  # 集装箱坐标,x,y,z
                "size": "D20f",
                # 集装箱尺寸,"20f"-20尺集装箱,"40f"-40尺集装箱,"D20f"-双20,"cabin_20f",-空舱位,"cabin_D20f"-空舱位双箱位置,"45f",-45尺集装箱,"other"-其他
                "tier": "5",  # 层号
                "target_object_height": 28.8265  + 0.01 * random.randrange(-20, 0),
                "adjacent_object_height": 28.8265
            },
            {
                "row_index": 13,
                "container_id": None,
                "container_pos": [BS002['data']['ship_start_pos'] + 28.8 + 0.01 * random.randrange(-10, 10), \
                                  0.01 * random.randrange(-50, 50), \
                                  28.8265-2.6+ 0.01 * random.randrange(-20, 0)],  # 集装箱坐标,x,y,z
                "size": "D20f",
                # 集装箱尺寸,"20f"-20尺集装箱,"40f"-40尺集装箱,"D20f"-双20,"cabin_20f",-空舱位,"cabin_D20f"-空舱位双箱位置,"45f",-45尺集装箱,"other"-其他
                "tier": "4",  # 层号
                "target_object_height": 28.8265-2.6+ 0.01 * random.randrange(-20, 0),
                "adjacent_object_height": 28.8265
            },
        ]

        set_global('BS003', BS003)
        # 反馈贝扫状态已完成、船舶数据、贝扫数据、计划放箱位置、

        try:
            BS004 = get_global('BS004')
            BS004["msg_uid"] = str(uuid.uuid1())
            BS004["timestamp"] = int(time.time() * 1000)
            BS004['data']['row_index'] = random.randrange(3, 6, 1)
            BS004['data']['x'] = BS003["data"]['bay_profile'][BS004['data']['row_index']-1]["container_pos"][0]
            BS004['data']['z'] = BS003["data"]['bay_profile'][BS004['data']['row_index']-1]["container_pos"][2]
            BS004['data']['safeHeight'] = BS003["data"]['bay_profile'][BS004['data']['row_index']-1]['adjacent_object_height']
            set_global('BS004', BS004)
        except Exception as error:
            error_logger.error(error)


    except Exception as error:
        print(f"Failed process {MC401} -- '{type(error).__name__}: {error}'")
        error_logger.error(f"Failed process {MC401} -- '{type(error).__name__}: {error}'")
        return  None


def process_MC402():
    MC401 = get_global('MC402')
    try:
        # 停止被扫
        # ！！！ todo 线程阻塞
        # 结果传出船舶数据\贝扫数据\计划放箱位置
        BS002 = get_global('BS002')
        BS2MC_pub.send_msg(json.dumps(BS002))
        BS003 = get_global('BS003')
        BS2MC_pub.send_msg(json.dumps(BS003))
        BS004 = get_global('BS004')
        BS2MC_pub.send_msg(json.dumps(BS004))

        BS001 = get_global('BS001')
        BS001["msg_uid"] = str(uuid.uuid1())
        BS001["timestamp"] = int(time.time() * 1000)
        BS001['data']['state'] = 2  # int, 0=未扫描，1=扫描中，2=完成扫描，3=扫描异常
        set_global('BS001', BS001)
        BS2MC_pub.send_msg(json.dumps(BS001))

    except Exception as error:
        print(f"Failed process {MC402} -- '{type(error).__name__}: {error}'")
        error_logger.error(f"Failed process {MC402} -- '{type(error).__name__}: {error}'")

def process_MC403():
    '''
        贝扫轨迹完成
    '''
    MC403 = get_global('MC403')
    BS001 = get_global('BS001')
    BS001["msg_uid"] = str(uuid.uuid1())
    BS001["timestamp"] = int(time.time() * 1000)
    BS001['data']['state'] = 2  # int, 0=未扫描，1=扫描中，2=完成扫描，3=扫描异常
    set_global('BS001', BS001)
    BS2MC_pub.send_msg(json.dumps(BS001))
    time.sleep(5)
    try:
        # 停止被扫
        # ！！！ todo 线程阻塞
        # 结果传出船舶数据\贝扫数据\计划放箱位置
        BS002 = get_global('BS002')
        BS2MC_pub.send_msg(json.dumps(BS002))
        BS003 = get_global('BS003')
        BS2MC_pub.send_msg(json.dumps(BS003))
        BS004 = get_global('BS004')
        BS2MC_pub.send_msg(json.dumps(BS004))

    except Exception as error:
        print(f"Failed process {MC403} -- '{type(error).__name__}: {error}'")
        error_logger.error(f"Failed process {MC403} -- '{type(error).__name__}: {error}'")

def process_MC406():
    # 请求贝扫数据
    MC406 = get_global('MC406')
    # !! todo 后续还需扫全船时 需要做筛选
    BS003 = get_global('BS003')
    BS2MC_pub.send_msg(json.dumps(BS003))


def process_MC407():
    # 请求船舶数据
    MC407 = get_global('MC407')
    BS002 = get_global('BS002')
    BS2MC_pub.send_msg(json.dumps(BS002))


def process_MC409():
    '''
    设置当前贝位 ship_place ship_code bay_id

    '''
    MC409 = get_global('MC409')
    try:
        BS001 = get_global('BS001')
        BS002 = get_global('BS002')
        BS003 = get_global('BS003')
        BS004 = get_global('BS004')
        BS005 = get_global('BS005')

        # 更新 BS001 BS002  BS004  ship_code
        BS001['data']['ship_code'] = MC409['data']['ship_code']
        BS002['data']['ship_code'] = MC409['data']['ship_code']

        # 更新 BS001 BS003 BS005 bay_id
        BS001['data']['bay_id'] = MC409['data']['bay_id']
        BS003['data']['bay_id'] = MC409['data']['bay_id']
        BS004['data']['bay_id'] = MC409['data']['bay_id']
        BS005['data']['bay_id'] = MC409['data']['bay_id']

        BS001["msg_uid"] = str(uuid.uuid1())
        BS001["timestamp"] = int(time.time() * 1000)
        set_global('BS001', BS001)
        BS002["msg_uid"] = str(uuid.uuid1())
        BS002["timestamp"] = int(time.time() * 1000)
        set_global('BS002', BS002)
        BS003["msg_uid"] = str(uuid.uuid1())
        BS003["timestamp"] = int(time.time() * 1000)
        set_global('BS003', BS003)
        BS004["msg_uid"] = str(uuid.uuid1())
        BS004["timestamp"] = int(time.time() * 1000)
        set_global('BS004', BS004)
        BS005["msg_uid"] = str(uuid.uuid1())
        BS005["timestamp"] = int(time.time() * 1000)
        set_global('BS005', BS005)

    except Exception as error:
        print(f"Failed process {MC409} -- '{type(error).__name__}: {error}'")
        error_logger.error(f"Failed process {MC409} -- '{type(error).__name__}: {error}'")
        return  None

def process_MC410():
    # 请求海侧计划箱位置请求贝扫数据
    MC410 = get_global('MC410')
    BS004 = get_global('BS004')
    BS2MC_pub.send_msg(json.dumps(BS004))

process_dict = {
    # MC -> BS
    "MC401": process_MC401,
    "MC402": process_MC402,
    "MC403": process_MC403,
    # "MC404": MC404,
    # "MC405": MC405,
    "MC406": process_MC406,
    "MC407": process_MC407,
    # # "MC408":MC408,
    "MC409": process_MC409,
    "MC410": process_MC410,
    # "MC411": MC411,
}

class recv_MC2BS(threading.Thread):
    def __init__(self) :
        super().__init__()
        MC2BS_url = 'tcp://10.142.1.200:9007' # todo config list
        MC2BS_sub_context = zmq.Context()
        self.MC2BS_sub_socket = MC2BS_sub_context.socket(zmq.SUB)
        self.MC2BS_sub_socket.setsockopt(zmq.SUBSCRIBE, b'')
        self.MC2BS_sub_socket.connect(MC2BS_url)
        print("==0===")

    def run(self, ):
        '''
        循环收取主控信息
        '''
        while True:
            print("==1===")
            MC2BS_msg = json.loads(self.MC2BS_sub_socket.recv_string())
            print("===2==")
            if MC2BS_msg['msg_name'] in process_dict.keys():
                print("===3==")
                set_global(MC2BS_msg['msg_name'], MC2BS_msg)
                # 处理对应任务
                # process_dict[MC2BS_msg['msg_name']]()
                try:
                    print("===4==")
                    process_dict[MC2BS_msg['msg_name']]()
                    print("==5===")
                    # p = threading.Thread(target = process_dict[MC2BS_msg['msg_name']]())
                    # p.start()
                except Exception as error:
                    print("=====")
                    print(f"Failed process {MC2BS_msg['msg_name']} -- '{type(error).__name__}: {error}'")
                    error_logger.error(f"Failed process {MC2BS_msg['msg_name']} -- '{type(error).__name__}: {error}'")

                key_logger.info(f'BS has processed - {json.dumps(MC2BS_msg)}')
            else:
                print('erro info \t', MC2BS_msg)
