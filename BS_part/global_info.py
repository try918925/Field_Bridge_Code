
# 数据定义：
PlcQcStatus = {
    "spreader_up_status":1, #int,吊具手柄起升信号,0：无、1：有
    "spreader_down_status":1, #int,吊具手柄下降信号,0：无、1：有
    "no_estop_status":1, #int,无急停信号,1：无急停、0：有急停
    "wind":0.0, #float,风速,单位m/s
    "ctr_on_state":1, #int,控制合状态位,0-控制下状态,1-控制上状态
    "ctr_mod_auto": 0, #int,自动控制状态标志位,0-控制下状态,1-控制上状态
    "ctr_mod_manual": 0, #int,手动控制状态标志位,0-控制下状态,1-控制上状态
    "ctr_mod_local": 0, #int,本地控制状态标志位,0-控制下状态,1-控制上状态
    "ctr_mod_remote": 0, #int,远程控制状态标志位,0-控制下状态,1-控制上状态
    "trolley_pos": 20.0, #float,小车位置,单位m
    "trolley_vel": 0.0, #float,小车速度,单位m/s
    # "trolley_stop_pos_status": 0, #小车停车位指示状态,0-小车不再停车位,1-小车在停车位
    "hoist_height":18.8,
    "rope_pos": 10.0, # float,起升绳长值,单位m
    "rope_vel": 0.0, #float起升速度,单位m/s
    "weight":12, #float,吊具下总重量,单位t
    "weight1":2, #float,吊具左上重量,单位t
    "weight2":2, #float,吊具左下重量,单位t
    "weight3":2, #float,吊具右上重量,单位t
    "weight4":2, #float,吊具右下重量,单位t
    "lock_state":0,#int,闭锁状态, 0-闭锁灯灭,1-闭锁灯亮
    "unlock_state":0,#int,开锁状态, 0-开锁灯灭,1-开锁灯亮
    "mid_lock_ud_state":0,#int,中锁上升下降状态, 0-上升状态,1-下降状态 
    "mid_lock_ss_state":0,#中锁伸缩状态, 0-拉伸状态,1-收缩状态
    "mid_lock_gap":0,#int, 中锁间距
    "land_state":0,#int,着箱状态, 0-着箱灯灭,1-着箱灯亮
    "spreader_single_state":0, #/int,/单箱模式状态, 0-单箱模式未到位,1-单箱模式到位
    "spreader_double_state":0, #int,双箱模式状态, 0-单双箱模式未到位,1-双箱模式到位
    "spreader_20f":0,#int,20尺状态, 0-20尺状态未到位,1-20尺状态到位
    "spreader_40f":0,#int,40尺状态, 0-40尺状态未到位,1-40尺状态到位
    "spreader_45f":0,#int,45尺状态, 0-45尺状态未到位,1-45尺状态到位
    "spreader_on_state":0,#int,吊具泵合状态位,0-吊具泵下状态,1-吊具泵上状态
    "spreader_reset_state":0,#int,吊具回零状态位, 0-吊具未回零,1-吊具回零（吊具姿态回零）
    "spreader_anti_sway":0,#int,吊具防摇状态位,0-吊具防摇下状态,1-吊具防摇上状态
    "spreader_anti_twist":0,#int,吊具防扭状态位,0-吊具防扭下状态,1-吊具防扭上状态
    "spreader_flipper_sea_side_l_status":0,#int,吊具海侧左导板状态位,0-升起状态,1-放下状态
    "spreader_flipper_sea_side_r_status":0,#int,吊具海侧右导板状态位,0-升起状态,1-放下状态
    "spreader_flipper_land_side_l_status":0,#int,吊具海侧左导板状态位,0-升起状态,1-放下状态
    "spreader_flipper_land_side_r_status":0,#int,吊具海侧右导板状态位,0-升起状态,1-放下状态
    "spreader_lr_tilt_dir":0,#int,吊具左右倾斜方向,0-无倾斜,1-吊具左倾,2-吊具右倾
    "spreader_lr_tilt_angle":0.0,#float,吊具左右倾斜角度
    "spreader_fb_tilt_dir":0,#int,吊具前后倾斜方向,0-无倾斜,1-吊具前倾,2-吊具后倾
    "spreader_fb_tilt_angle":0.0,#float,吊具前后倾斜角度
    "spreader_lr_rotate_dir":0,#int,吊具左右旋转方向,0-无旋转,1-吊具左旋,2-吊具右旋
    "spreader_lr_rotate_angle":0.0,#float,吊具左右旋转角度
    "gantry_clamp_status":1, #int,大车夹轮器状态位,0-松轨状态,1-夹轨状态
    "gantry_skid_status":1, #int,大车铁鞋状态位,1-释放状态,0-未释放状态
    "gantry_pos": 0.0, #float,大车位置, 单位m
    "gantry_vel": 0.0, #float,大车速度,单位m/s
    "gantry_move_left": 0, #int,大车向左移动, 0-否,1-是
    "gantry_move_right": 0, #int,大车向右移动, 0-否,1-是
    "bypass_status": 0, #int,旁路状态,0-旁路未开状态,1-旁路开状态
    "beam_stilt_speed": 0.0, #float,大梁俯仰速度,m/s
    "beam_stilt_angle": 0.0, #float,大梁俯仰角度
    "beam_latch_status": 0, #大梁落钩状态,1-落钩、0-起钩
    "front_beam_light_status": 0, #int,前梁灯状态, 0-关,1-开
    "gantry_light_status": 0, #int,大车灯状态, 0-关,1-开
    "escalator_light_status": 0, #int,扶梯灯状态, 0-关,1-开
    "trolley_light_status": 0, #int,小车灯状态, 0-关,1-开
    "mid_back_beam_light_status": 0, #int,中后梁灯状态, 0-关,1-开
    "footpath_light_status": 0, #int,步道灯状态, 0-关,1-开
    "conn_beam_light_status": 0, #int,联系梁灯状态, 0-关,1-开
    # "camera_up_status": 0, # int,手柄控制摄像头上转 0-关,1-开
    # "camera_down_status":0, # int,手柄控制摄像头下转 0-关,1-开
    # "camera_left_status":0, # int,手柄控制摄像头左转 0-关,1-开
    # "camera_right_status":0, # int,手柄控制摄像头右转 0-关,1-开
    # "camera_zoomin_status":0, # int,手柄控制摄像头放大 0-关,1-开
    # "camera_zoomout_status":0, # int,手柄控制摄像头缩小 0-关,1-开
    "dive_plat_door_status": 1, # int, 跳水平台门状态,0-关,1-开
    "car_stoppos_status": 1, # int, 小车在停车位 0 - 不在, 1 - 在
    "car_backpos_motion_status": 1, #int, 小车回停车位运动中0-停止,1-正在回	"trolley_handle_value":1,#float,小车手柄速度给定值
    "spreader_handle_value":1,#float,起升手柄速度给定值
    "gantry_handle_value":1,#float,大车手柄速度给定值
    "fault_code": ["",] #string[],设备故障代码
}

MC001 = {
    "msg_uid": "1234567890",  # string,消息序号
    "msg_name": "MC001", # string,消息名称
    "sender":"MC", #string,发送方
    "timestamp":16879546201, #long, 时间戳,单位毫秒
    "receiver":"CT", #string,接收方
    "craneId":"404-1", #string, 设备号
    "data": PlcQcStatus #PlcQcStatus
}

# 主控到船扫
# 广播端口：9007
# 发送方：主控
# 接收方：船扫
# MC401 启动贝扫
MC401 = {
    "msg_uid":"1234567890",#string,消息序号
    "msg_name":"MC401",#string,消息名称
    "sender":"MC",#string,发送方
    "timestamp":16879546201,#long, 时间戳,单位毫秒
    "receiver":"BS", #string,接收方
    "craneId":"404-1", #string, 设备号
    "data": {
        "bay_id": "03", # //string,贝位号
        "bay_type" : 0, # //int,0=小贝 1=大贝
        "ship_direction": 1, #int,船头方向,1代表面海向左,2代表面海向右
        "ship_place":0, #int, 船位置,0代表船是里档,1代表船是外档
        "ship_start_pos": 45, #float,船在小车方向上的起始位置,单位m
        "ship_stop_pos":85 #float,船在小车方向上的结束位置,单位m
    }
}

# MC402 停止贝扫
MC402 = {
    "msg_uid":"1234567890",#string,消息序号
    "msg_name":"MC402",#string,消息名称
    "sender":"MC",#string,发送方
    "timestamp":16879546201,#long, 时间戳,单位毫秒
    "receiver":"BS", #string,接收方
    "craneId":"404-1", #string, 设备号
    "data": "null"
}


# MC403 贝扫轨迹移动完成
MC403 = {
    "msg_uid":"1234567890",#string,消息序号
    "msg_name":"MC403",#string,消息名称
    "sender":"MC",#string,发送方
    "timestamp":16879546201,#long, 时间戳,单位毫秒
    "receiver":"BS", #string,接收方
    "craneId":"404-1", #string, 设备号
    "data": {
        "result":1#1=成功 0=失败
    }
}


# MC404 开启贝扫
MC404 = {
    "msg_uid":"1234567890",#string,消息序号
    "msg_name":"MC404",#string,消息名称
    "sender":"MC",#string,发送方
    "timestamp":16879546201,#long, 时间戳,单位毫秒
    "receiver":"BS", #string,接收方
    "craneId":"404-1", #string, 设备号
    "data": "null"
}

# MC405 关闭贝扫
MC405 = {
    "msg_uid":"1234567890",#string,消息序号
    "msg_name":"MC405",#string,消息名称
    "sender":"MC",#string,发送方
    "timestamp":16879546201,#long, 时间戳,单位毫秒
    "receiver":"BS", #string,接收方
    "craneId":"404-1", #string, 设备号
    "data": "null"
}

# MC406 请求贝扫数据
MC406 = {
    "msg_uid":"1234567890",#string,消息序号
    "msg_name":"MC406",#string,消息名称
    "sender":"MC",#string,发送方
    "timestamp":16879546201,#long, 时间戳,单位毫秒
    "receiver":"BS", #string,接收方
    "craneId":"404-1", #string, 设备号
    "data": 
    {
        "ship_code":"",
        "ship_place":0,
        "bay_id":"8",
    }
}

# MC407 请求船舶数据
MC407 = {
    "msg_uid":"1234567890",#string,消息序号
    "msg_name":"MC407",#string,消息名称
    "sender":"MC",#string,发送方
    "timestamp":16879546201,#long, 时间戳,单位毫秒
    "receiver":"BS", #string,接收方
    "craneId":"404-1", #string, 设备号
    "data": 
    {
        "ship_place":0,
        "ship_code":"",
    }
}

# # MC408 整船作业完毕,删除贝扫数据
# MC408 = {
#     "msg_uid":"1234567890",#string,消息序号
#     "msg_name":"MC408",#string,消息名称
#     "sender":"MC",#string,发送方
#     "timestamp":16879546201,#long, 时间戳,单位毫秒
#     "receiver":"BS", #string,接收方
#     "craneId":"404-1", #string, 设备号
#     "data": 
#     {
#         "ship_place":0,
#         "ship_code":"",
#     }
# }

# MC409 设置当前贝位
MC409 = {
    "msg_uid":"1234567890",#string,消息序号
    "msg_name":"MC409",#string,消息名称
    "sender":"MC",#string,发送方
    "timestamp":16879546201,#long, 时间戳,单位毫秒
    "receiver":"BS", #string,接收方
    "craneId":"404-1", #string, 设备号
    "data": 
    {
        "ship_place":0,
        "ship_code":"",
        "bay_id":"011",
    }
}

# MC410 请求海侧计划箱位置
MC410 = {
    "msg_uid":"1234567890",#string,消息序号
    "msg_name":"MC410",#string,消息名称
    "sender":"MC",#string,发送方
    "timestamp":16879546201,#long, 时间戳,单位毫秒
    "receiver":"BS", #string,接收方
    "craneId":"404-1", #string, 设备号
    "data": 
    {
        "ship_place":0,
        "ship_code":"",
        "bay_id":"03",
        "row_index":2,
    }
}

# MC411 请求海侧实际抓放箱位置
MC411 = {
    "msg_uid":"1234567890",#string,消息序号
    "msg_name":"MC411",#string,消息名称
    "sender":"MC",#string,发送方
    "timestamp":16879546201,#long, 时间戳,单位毫秒
    "receiver":"BS", #string,接收方
    "craneId":"404-1", #string, 设备号
    "data": 
    {
        "ship_place":0,
        "ship_code":"",
        "bay_id":"03",
        "row_id":"02",
        "tier": 3
    }
}

# 船扫到主控
# 广播端口：9008
# 发送方：船扫
# 接收方：主控
# BS000 心跳
# 发送频率：每200毫秒
BS000 = {
    "msg_uid":"1234567890",#string,消息序号
    "msg_name":"BS000",#string,消息名称
    "sender":"BS",#string,发送方
    "timestamp":16879546201,#long, 时间戳,单位毫秒
    "receiver":"MC", #string,接收方
    "craneId":"404-1", #string, 设备号
    "data": {
        "heartbeat":1 #int,心跳1-9999
    }
}

# BS001 反馈贝扫状态
BS001 = {
    "msg_uid":"1234567890",#string,消息序号
    "msg_name":"BS001",#string,消息名称
    "sender":"BS",#string,发送方
    "timestamp":16879546201,#long, 时间戳,单位毫秒
    "receiver":"MC", #string,接收方
    "craneId":"404-1", #string, 设备号
    "data": {
        "state":1, #int,0=未扫描,1=扫描中,2=完成扫描,3=扫描异常
        "bay_id":"8",
        "ship_code":"",
    }
}

import random
# BS002 反馈船舶数据
BS002 = {
    "msg_uid":"1234567890",#string,消息序号
    "msg_name":"BS002",#string,消息名称
    "sender":"BS",#string,发送方
    "timestamp":16879546201,#long, 时间戳,单位毫秒
    "receiver":"MC", #string,接收方
    "craneId":"404-1", #string, 设备号
    "data": {
        "ship_code":"",
        "ship_start_pos": 53+random.uniform(-1, 2), #float,船在小车方向上的起始位置,单位m
        "ship_stop_pos": 53+random.uniform(-1, 2)+7*2.5 #float,船在小车方向上的结束位置,单位m
    }
}

# MC107 发送贝扫数据
SlotScanResult = {
    "row_index":1,
    "container_id":"",
    "container_pos" : [ 53.040710296630863, 0, -45.081278228759764 ],#集装箱坐标,x,y,z
    "size" : "40f", #集装箱尺寸,"20f"-20尺集装箱,"40f"-40尺集装箱,"D20f"-双20,"cabin_20f",-空舱位,"cabin_D20f"-空舱位双箱位置,"45f",-45尺集装箱,"other"-其他
    "tier" : "-1"#层号 
}

# BS003 反馈贝扫数据
BS003 = {
    "msg_uid":"1234567890",#string,消息序号
    "msg_name":"BS003",#string,消息名称
    "sender":"BS",#string,发送方
    "timestamp":16879546201,#long, 时间戳,单位毫秒
    "receiver":"MC", #string,接收方
    "craneId":"404-1", #string, 设备号
    "data": {
        "bay_id":"10",
        "safety_height":20.1,#安全高度
        "bay_profile":[SlotScanResult,] #[,,] #SlotScanResult[]
    }
}


# BS004 反馈海侧计划箱位置
BS004 = {
    "msg_uid":"1234567890",#string,消息序号
    "msg_name":"BS004",#string,消息名称
    "sender":"BS",#string,发送方
    "timestamp":16879546201,#long, 时间戳,单位毫秒
    "receiver":"MC", #string,接收方
    "craneId":"404-1", #string, 设备号
    "data": {
        "bay_id": "10",
        "row_index": 2,
        "isValid": False, #bool 目标位置信息是否可用,即是否可着（抓或放）箱。
        "x":0.1, #float 小车方向坐标
        "z":0.2, #float z轴坐标
        "safeHeight":0.0, #float 安全高度
        "isLastOne": False, #bool,是否为最后一个
    }
}

# BS005 反馈海侧实际抓放箱位置
BS005 = {
    "msg_uid":"1234567890",#string,消息序号
    "msg_name":"BS005",#string,消息名称
    "sender":"BS",#string,发送方
    "timestamp":16879546201,#long, 时间戳,单位毫秒
    "receiver":"MC", #string,接收方
    "craneId":"404-1", #string, 设备号
    "data": {
        "bay_id": "10",
        "row_index": 2,
        "x":0.1, #float 小车方向坐标
        "z":0.1, #float z轴坐标
        "safeHeight":0.0, #float 安全高度
        "isLastOne": False, #bool,是否为最后一,（新增：对于）
        "size":"40f"  #箱尺寸: "20f"-20尺集装箱,"40f"-40尺集装箱,"D20f"-双20,"45f"-45尺集装箱,"cabin_20f",-空舱位,"cabin_D20f"-空舱位双箱位置,"45f",-45尺集装箱
    }
}

# BS006 异常上报
BS006 = {
    "msg_uid":"1234567890",#string,消息序号
    "msg_name":"BS006",#string,消息名称
    "sender":"BS",#string,发送方
    "timestamp":16879546201,#long, 时间戳,单位毫秒
    "receiver":"MC", #string,接收方
    "craneId":"404-1", #string, 设备号
    "data": [] #Exception,异常信息
}

# BS007 请求控制开始小车移动
BS007 = {
    "msg_uid": "1234567890", # //string，消息序号
    "msg_name": "BS007", # //string，消息名称
    "sender": "BS", # //string，发送方
    "timestamp": 16879546201, # //long, 时间戳，单位毫秒
    "receiver": "MC", # //string，接收方
    "craneId": "404-1", # //string, 设备号
    "data": {
        "trolley_start_pos": 50.1, # //float,船近陆侧小车位置
        "trolley_end_pos": 80.2, # //float,船近海侧小车位置
    } 
}

BS_msg_dict = {
    # MC PUB
    "MC001":MC001,

    # MC -> BS
    "MC401":MC401,
    "MC402":MC402,
    "MC403":MC403,
    "MC404":MC404,
    "MC405":MC405,
    "MC406":MC406,
    "MC407":MC407,
    # "MC408":MC408,
    "MC409":MC409,
    "MC410":MC410,
    "MC411":MC411,

    "BS000":BS000,
    "BS001":BS001,
    "BS002":BS002,
    "BS003":BS003,
    "BS004":BS004,
    "BS005":BS005,
    "BS006":BS006,
    "BS007":BS007,
}

from initializers import * 
def set_global(key:str, value):
    try:
        BS_msg_dict[key] = value
        return True
    except Exception as error:
        print(f"Failed set global {key} -- '{type(error).__name__}: {error}'.")
        error_logger.error(f"Failed set global {key} -- '{type(error).__name__}: {error}'.")
        return False    

def get_global(key:str):
    #获得一个全局变量，不存在则提示读取对应变量失败
    try:
        return  BS_msg_dict[key]
    except Exception as error:
        print(f"Failed get global {key} -- '{type(error).__name__}: {error}'")
        error_logger.error(f"Failed get global {key} -- '{type(error).__name__}: {error}'")
        return  None

# !!! 目前没在set/get时加线程锁限制
import json
def save_global():
    global BS_msg_dict
    file_path = './global_info.json'
    with open(file_path, 'w') as f:
        json.dump(BS_msg_dict, f, ensure_ascii= False, indent=4)

def reload_global():
    global BS_msg_dict
    file_path = './global_info.json'
    with open(file_path, 'w') as f:
        BS_msg_dict = json.load(f)

# reload_global() # 每次初始化的时候, 都会加载上一次保存的状态
