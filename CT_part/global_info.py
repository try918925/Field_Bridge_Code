
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

# 主控到控制
# 广播端口：9001
# 发送方：主控
# 接收方：控制
# MC101 发送任务


# 其中Task

ContainerInfo = {
    "cntr_no": "HIVO502611478", #箱号
    "cntr_iso": "45G1", #箱型箱高
    "cntr_size":20, #尺寸
    "full_empty":"full", #空重
    "damage":"", #残损
    "danger_code":"", #危险等级
    "unno":"" , #unno
    "cntr_height": 2900, #箱高
    "cntr_weight": 50.1, #箱标重
    "cntr_measure_weight": 52.3, #箱实重
}

Position = {
    "gantryPos": 100.1, #大车位置，float，单位米
    "trolleyPos": 55.2, # //小车位置
    "hoistHeight": 8.2,  # 起升高度
    "targetPositionType" : 1, #//作业位置类型，1=船 2=水平运输设备 3=地面 4=岸桥停车位
    "shipRowIndex": 2, #船上排位序号，从岸边向海方向，从1开始
    "bay_id": "09", # //贝号
    "bay_type" : 0, #// int, 0=小贝 1=大贝
    "truckLaneId": "3" #// 车道号
}

QcAction = {
    "task_id":"",
    "actionIndex": 0, #动作指令序号，每个task或无任务时重新从1递增。当task_id或actionIndex变化时，即认为新指令或指令更新
    "actionType":1, #//动作类型，1=停车2=抓箱 3=放箱
    "actionObject": 1, #作业对象，0=空 1=集装箱 2=舱盖板 3=其他
    "targetPosition":Position,
    "actionMode": "auto", # //自动化模式，auto=全自动 semiAuto=半自动 manual=手动
    "spreaderSize": "D20f", #// "20f"-20尺集装箱,"40f"-40尺集装箱,"D20f"-双20,"45f"-45尺集装箱,”other”
    "objectHeight" : 2.5, #//箱高或其他作业对象高度
    "flipperDownList": [1,2,3,4], #//需要下翻的导板，1=海左2=海右3=陆左4=陆右
    "dropPositionHeight" : 1.5, #//放箱位置高度，车板高度
    "seaSideSafeHeight": 20.0, #//海侧安全高度
    "landSideSafeHeight": 9.0, #//陆侧安全高度
    "workflow": 1, # //作业工艺1、单箱吊；2、双箱吊；3、双吊具，int类型
	"work_type": "LOAD", # //作业类型,LOAD-装船，DSCH-卸船
	"work_lane": "", # //作业车道
    "cntr_position": 3, #//箱位置，1左小箱,2 右小箱 3 大箱或双箱（左右以面朝海侧为基准）
    "vehicle_type": "AIV", #//车辆类型，ITK内集卡，OTK外集卡，AIV无人集卡
    "container": ContainerInfo, 
    "container2": ContainerInfo, # //双箱第二箱信息
    "soa_boat_type":0, #//int类型，船类型，0：驳船、1：大船
}

Ep = {
    "exception_code":1000,#int,异常代码
    "detail":"xxxx", #string,具体信息描述
    "happen_time":16879546201,#long, 时间戳,单位毫秒
    "has_solved":False, #bool,是否已解决
    "solve_time":0#long, 时间戳,单位毫秒
}

MC101 = {
    "msg_uid":"1234567890",#string,消息序号
    "msg_name":"MC101",#string,消息名称
    "sender":"MC",#string,发送方
    "timestamp":16879546201, #long, 时间戳,单位毫秒
    "receiver":"CT", #string,接收方
    "craneId":"404-1", #string, 设备号
    "data": {
        "currentAction":QcAction, #Task, 当前任务
        # "nextTask": Task #Task, 排队待执行任务
    }
}
# MC102 停止设备作业

MC102 = {
    "msg_uid":"1234567890",#string,消息序号
    "msg_name":"MC102",#string,消息名称
    "sender":"MC",#string,发送方
    "timestamp":16879546201,#long, 时间戳,单位毫秒
    "receiver":"CT", #string,接收方
    "craneId":"404-1", #string, 设备号
    "data": {
        "stopMode": None # //停止模式，1=急停 2=缓停
    }
}

# MC103 清空任务
MC103 = {
    "msg_uid":"1234567890",#string,消息序号
    "msg_name":"MC103",#string,消息名称
    "sender":"MC",#string,发送方
    "timestamp":16879546201,#long, 时间戳,单位毫秒
    "receiver":"CT", #string,接收方
    "craneId":"404-1", #string, 设备号
    "data": "null"
}

# MC104 设置作业模式

MC104 = {
    "msg_uid":"1234567890",#string,消息序号
    "msg_name":"MC104",#string,消息名称
    "sender":"MC",#string,发送方
    "timestamp":16879546201,#long, 时间戳,单位毫秒
    "receiver":"CT", #string,接收方
    "craneId":"404-1", #string, 设备号
    "data": {
        "auto_mode": "auto", # "auto",-自动模式设置,"assist",-司机辅助模式设置
        "auto_drop": 1, #1-开启自动着箱,0-关闭自动着箱
    }
}

# MC105 请求控制模块状态
MC105 = {
    "msg_uid":"1234567890",#string,消息序号
    "msg_name":"MC105",#string,消息名称
    "sender":"MC",#string,发送方
    "timestamp":16879546201,#long, 时间戳,单位毫秒
    "receiver":"CT", #string,接收方
    "craneId":"404-1", #string, 设备号
    "data": "null"
}

# MC106 贝扫任务
MC106 = {
    "msg_uid":"1234567890",#string,消息序号
    "msg_name":"MC106",#string,消息名称
    "sender":"MC",#string,发送方
    "timestamp":16879546201,#long, 时间戳,单位毫秒
    "receiver":"CT", #string,接收方
    "craneId":"404-1", #string, 设备号
    "data": {
        "scan_cmd_index":1,#int,贝扫指令序号
        "trolley_start_pos":45.0, #float 消息类型,小车运动起始位置
        "trolley_target_pos":89.0, #float 消息类型,小车运动目标位置
    }
}

# MC107 发送贝扫数据
SlotScanResult = {
    "row_index":1,
    "container_id":"ABCD1234567",
    "container_pos" : [ 53.040710296630863, 0, -45.081278228759764 ],#集装箱坐标,x,y,z
    "size" : "40f", #集装箱尺寸,"20f"-20尺集装箱,"40f"-40尺集装箱,"D20f"-双20,"cabin_20f",-空舱位,"cabin_D20f"-空舱位双箱位置,"45f",-45尺集装箱,"other"-其他
    "tier" : "-1"#层号 
}

MC107 = {
    "msg_uid":"1234567890",#string,消息序号
    "msg_name":"MC107",#string,消息名称
    "sender":"MC",#string,发送方
    "timestamp":16879546201,#long, 时间戳,单位毫秒
    "receiver":"CT", #string,接收方
    "craneId":"404-1", #string, 设备号
    "data": {
        "bay_id":"10",
        "safety_height":20.1,#安全高度
        "bay_profile":[SlotScanResult,] # [,,] #SlotScanResult[]
    }

}



# MC108 发送陆侧集装箱和集卡位置
MC108 = {
    "msg_uid":"1234567890",#string,消息序号
    "msg_name":"MC108",#string,消息名称
    "sender":"MC",#string,发送方
    "timestamp":16879546201,#long, 时间戳,单位毫秒
    "receiver":"CT", #string,接收方
    "craneId":"404-1", #string, 设备号
    "data": {
        "lane_id": "5", #string, 车道号
        "has_car": True,#True-目标车道有集卡,False-目标车道无集卡
        "car_target_x": 25.25, #float 型,目标集卡小车方向位置,单位：m
        "car_target_z": 1.5, #float 型,目标集卡高度,单位：m
        "car_target_y": 0.3, #float 型,目标集卡大车方向位置,单位：m
        "car_target_t": 0.01, #float 型,目标集卡扭角,单位rad
        "has_cntr": True,#True-目标车道有集装箱,False-目标车道无集装箱
        "cntr_target_x": 20.5, #float 型,目标集装箱小车方向位置,单位：m
        "cntr_target_z": 4.3, #float 型,目标集装箱高度,单位：m
        "cntr_target_y": 0.3, #float 型,目标集装箱大车方向位置,单位：m
        "cntr_target_t": 0.01, #float 型,目标集装箱扭角,单位rad
        "target_dis": 0.4, #双箱间距,单箱时返回0,单位m
        "cntr_dislocation":False,#双箱时是否错位 True/False
        "cntr_pos": 1, #1-前小箱位置, 2-后小箱位置,3-中间位置
        "vehicle_dir": 0,  # 0-底端（面海向左）1-高端（面海向右）
    }

}

# MC109 小车回停车位
# MC109 = {
#     "msg_uid":"1234567890",#string,消息序号
#     "msg_name":"MC109",#string,消息名称
#     "sender":"MC",#string,发送方
#     "timestamp":16879546201,#long, 时间戳,单位毫秒
#     "receiver":"CT", #string,接收方
#     "craneId":"404-1", #string, 设备号
#     "data": "null"
# }

# MC110 发送海侧集装箱计划位置
MC110 = {
    "msg_uid":"1234567890",#string,消息序号
    "msg_name":"MC110",#string,消息名称
    "sender":"MC",#string,发送方
    "timestamp":16879546201,#long, 时间戳,单位毫秒
    "receiver":"CT", #string,接收方
    "craneId":"404-1", #string, 设备号
    "data": {
        "bay_id": "10",
        "row_id": "03",
        "tier": 1,
        "isValid": False, #bool 目标位置信息是否可用,即是否可着（抓或放）箱。
        "x":0, #float 小车方向坐标
        "z":0, #float z轴坐标
        "safeHeight":0.0, #float 安全高度
        "isLastOne": False, #bool,是否为最后一个
    }

}

# MC111 感知箱高结果推送
MC111 = {
    "msg_uid":"1234567890",#string,消息序号
    "msg_name":"MC111",#string,消息名称
    "sender":"MC",#string,发送方
    "timestamp":16879546201,#long, 时间戳,单位毫秒
    "receiver":"CT", #string,接收方
    "craneId":"404-1", #string, 设备号
    "data": {
        "container_height":2.6
    }

}

# MC112 请求任务执行状态
MC112 = {
    "msg_uid":"1234567890",#string,消息序号
    "msg_name":"MC112",#string,消息名称
    "sender":"MC",#string,发送方
    "timestamp":16879546201,#long, 时间戳,单位毫秒
    "receiver":"CT", #string,接收方
    "craneId":"404-1", #string, 设备号
    "data": {
        "task_id":"1111",
    }

}

# MC113 设置禁行区域
MC113 = {
    "msg_uid":"1234567890",#string,消息序号
    "msg_name":"MC113",#string,消息名称
    "sender":"MC",#string,发送方
    "timestamp":16879546201,#long, 时间戳,单位毫秒
    "receiver":"CT", #string,接收方
    "craneId":"404-1", #string, 设备号
    "data": {
        "待定"
    }
}

# MC114 发送吊具姿态和位置
# 转发从感知收到的数据
SpreaderPositionStatus = { 
    "has_spreader": True,#True-目标下有吊具,False-目标下无吊具
    "spreader_target_x": 20.5, #float 型,目标吊具小车方向位置,单位：m
    "spreader_target_z": 1.5, #float 型,目标吊具高度,单位：m
    "spreader_target_y": 0.3, #float 型,目标吊具大车方向位置,单位：m
    "spreader_target_theta": 0.01, #float 型,目标吊具摆角,单位rad
    "spreader_target_zeta": 0.01, #float 型,目标吊具扭角,单位rad
    "spreader_cntr_num": 1,#吊具当前抓起的箱子,0-无箱子,1-一个箱子,2-两个箱子
    "spreader_code":0,#备用
}


MC114 = {
    "msg_uid":"1234567890",#string,消息序号
    "msg_name":"MC114",#string,消息名称
    "sender":"MC",#string,发送方
    "timestamp":16879546201,#long, 时间戳,单位毫秒
    "receiver":"CT", #string,接收方
    "craneId":"404-1", #string, 设备号
    "data":SpreaderPositionStatus #SpreaderPositionStatus,吊具位置状态
}


# 控制到主控
# 广播端口：9002
# 发送方：控制
# 接收方：主控
# CT000 心跳
# 发送频率：每200毫秒

CT000 = {
    "msg_uid":"1234567890",#string,消息序号
    "msg_name":"CT000",#string,消息名称
    "sender":"CT",#string,发送方
    "timestamp":16879546201,#long, 时间戳,单位毫秒
    "receiver":"MC", #string,接收方
    "craneId":"404-1", #string, 设备号
    "data": {
        "heartbeat":1 #int,心跳1-9999
    }

}

# CT001 单机控制命令
CmdSet = {
    "cmd":"单机控制命令",#string【见附录一】
    "value":"",#object
    }

CT001 = {
    "msg_uid":"1234567890",#string,消息序号
    "msg_name":"CT001",#string,消息名称
    "sender":"CT",#string,发送方
    "timestamp":16879546201,#long, 时间戳,单位毫秒
    "receiver":"MC", #string,接收方
    "craneId":"404-1", #string, 设备号
    "data": [CmdSet]# [,] #CmdSet[]
}



# CT002  反馈任务执行状态
CT002 = {
    "msg_uid":"1234567890",#string,消息序号
    "msg_name":"CT002",#string,消息名称
    "sender":"CT",#string,发送方
    "timestamp":16879546201,#long, 时间戳,单位毫秒
    "receiver":"MC", #string,接收方
    "craneId":"404-1", #string, 设备号
    "data": {
        "task_id":"1234",
        "actionIndex": 2,
        "task_state":"complete",#string,任务状态：received,running,reject,abort,complete
        "pick_complete":True,
        "drop_complete":True,
        "reject_reason":"",#string,任务拒绝原因
    }
}

# CT003 请求手动自动切换
CT003 = {
    "msg_uid":"1234567890",#string,消息序号
    "msg_name":"CT003",#string,消息名称
    "sender":"CT",#string,发送方
    "timestamp":16879546201,#long, 时间戳,单位毫秒
    "receiver":"MC", #string,接收方
    "craneId":"404-1", #string, 设备号
    "data": {
        "task_id":"1234",
        "request_mode":"auto",#string,请求切换模式：auto,manual
        "request_reason":"",#string,请求原因
    }
}

# CT004 反馈控制模块状态
CT004 = {
    "msg_uid":"1234567890",#string,消息序号
    "msg_name":"CT004",#string,消息名称
    "sender":"CT",#string,发送方
    "timestamp":16879546201,#long, 时间戳,单位毫秒
    "receiver":"MC", #string,接收方
    "craneId":"404-1", #string, 设备号
    "data": { 
        "auto_mode": "auto", #"auto" - 作业模式, "assist" -辅助模式, "ready"-待机（此时不接受任务）
        "auto_drop": 1, #1-开启自动着箱,0-关闭自动着箱
        "running_task_type": "DSCH", # 正在执行任务类型,"BayChange"-换贝交互任务, 	"BayScan"-贝扫任务,"DSCH"-卸船任务, "LOAD"-装船任务, "NONE",-暂无任务
        "running _task_id":"123456",#正在执行的任务id
        "waiting_task_id":"null", #待执行任务 
        "can_receive_task": 1, #1-可以接受任务信息, 0-不可以接受任务信息
    }

}

# CT005 贝扫执行状态反馈
CT005 = {
    "msg_uid":"1234567890",#string,消息序号
    "msg_name":"CT005",#string,消息名称
    "sender":"CT",#string,发送方
    "timestamp":16879546201,#long, 时间戳,单位毫秒
    "receiver":"MC", #string,接收方
    "craneId":"404-1", #string, 设备号
    "data": {
        "scan_cmd_index":1,#int,贝扫指令序号
        "scan_state":"running",#string,任务状态：received,running,reject,abort,complete
    }
}

# CT006 请求贝扫数据
CT006 = {
    "msg_uid":"1234567890",#string,消息序号
    "msg_name":"CT006",#string,消息名称
    "sender":"CT",#string,发送方
    "timestamp":16879546201,#long, 时间戳,单位毫秒
    "receiver":"MC", #string,接收方
    "craneId":"404-1", #string, 设备号
    "data": {
    "bay_id":"10",#string,贝扫指令序号,默认请求当前贝
}

}
# CT007 异常上报
CT007 = {
    "msg_uid":"1234567890",#string,消息序号
    "msg_name":"CT007",#string,消息名称
    "sender":"CT",#string,发送方
    "timestamp":16879546201,#long, 时间戳,单位毫秒
    "receiver":"MC", #string,接收方
    "craneId":"404-1", #string, 设备号
    "data": [Ep,] #Exception,异常信息
}

# CT008 请求吊具姿态和位置
CT008 = {
    "msg_uid":"1234567890",#string,消息序号
    "msg_name":"CT008",#string,消息名称
    "sender":"CT",#string,发送方
    "timestamp":16879546201,#long, 时间戳,单位毫秒
    "receiver":"MC", #string,接收方
    "craneId":"404-1", #string, 设备号
    "data": "null"
}

TEMP = {
    "lock_dis":{ # 中锁间距比值
        "timestamp":16879546201,#long, 时间戳,单位毫秒
        "ratio":None, # float 锁孔间距/中锁距离
        "latch_dis": None # 锁孔间距
    },
    "target_pos":{ # 抓放目标位置
        "timestamp":16879546201,#long, 时间戳,单位毫秒
        "bbox":None, # oxywh
    },
    "hanger_pos":{ # 吊具
        "timestamp":16879546201,#long, 时间戳,单位毫秒
        "bbox":None, # oxywh
    }
}

global CT_msg_dict
CT_msg_dict = {
    # MC PUB
    # MC PUB
    "MC001":MC001, 
    # MC -> CT
    "MC101":MC101,  # !!! todo 任务队列
    "MC102":MC102,
    "MC103":MC103,
    "MC104":MC104,
    "MC105":MC105,
    "MC106":MC106,
    "MC107":MC107,
    "MC108":MC108,
    # "MC109":MC109,
    "MC110":MC110,
    "MC111":MC111,
    "MC112":MC112,
    "MC113":MC113,
    "MC114":MC114,

    "CT000":CT000,
    "CT001":CT001,
    "CT002":CT002,
    "CT003":CT003,
    "CT004":CT004,
    "CT005":CT005,
    "CT006":CT006,
    "CT007":CT007,
    "CT008":CT008,

    "TEMP":TEMP,
}

from initializers import * 
# !!! 目前没在set/get时加线程锁限制
def set_global(key:str, value):
    try:
        global CT_msg_dict
        CT_msg_dict[key] = value
        return True
    except Exception as error:
        print(f"Failed set global {key} -- '{type(error).__name__}: {error}'.")
        error_logger.error(f"Failed set global {key} -- '{type(error).__name__}: {error}'.")
        return False    

def get_global(key:str):
    #获得一个全局变量，不存在则提示读取对应变量失败
    try:
        global CT_msg_dict
        return  CT_msg_dict[key]
    except Exception as error:
        print(f"Failed get global {key} -- '{type(error).__name__}: {error}'")
        error_logger.error(f"Failed get global {key} -- '{type(error).__name__}: {error}'")
        return  None

import json
def save_global():
    global CT_msg_dict
    file_path = './global_info.json'
    with open(file_path, 'w') as f:
        json.dump(CT_msg_dict, f, ensure_ascii= False, indent=4)
# save_global()

def reload_global():
    global BS_msg_dict
    file_path = './global_info.json'
    with open(file_path, 'r') as f:
        BS_msg_dict = json.load(f)    

# reload_global() # 每次初始化的时候, 都会加载上一次保存的状态
