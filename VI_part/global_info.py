'''
    多线程同时对以下变量做更新
    消息协议 v1.3.0

    主控广播
    广播端口: 9000
    发送方：主控
    接收方：不指定（控制、感知、引导、船扫等订阅）
'''

PlcQcStatus = {
    "spreader_up_status": 1,  # int,吊具手柄起升信号,0：无、1：有
    "spreader_down_status": 1,  # int,吊具手柄下降信号,0：无、1：有
    "no_estop_status": 1,  # int,无急停信号,1：无急停、0：有急停
    "wind": 0.0,  # float,风速,单位m/s
    "ctr_on_state": 1,  # int,控制合状态位,0-控制下状态,1-控制上状态
    "ctr_mod_auto": 0,  # int,自动控制状态标志位,0-控制下状态,1-控制上状态
    "ctr_mod_manual": 0,  # int,手动控制状态标志位,0-控制下状态,1-控制上状态
    "ctr_mod_local": 0,  # int,本地控制状态标志位,0-控制下状态,1-控制上状态
    "ctr_mod_remote": 0,  # int,远程控制状态标志位,0-控制下状态,1-控制上状态
    "trolley_pos": 20.0,  # float,小车位置,单位m
    "trolley_vel": 0.0,  # float,小车速度,单位m/s
    # "trolley_stop_pos_status": 0, #小车停车位指示状态,0-小车不再停车位,1-小车在停车位
    "hoist_height": 18.8,
    "rope_pos": 10.0,  # float,起升绳长值,单位m
    "rope_vel": 0.0,  # float起升速度,单位m/s
    "weight": 12,  # float,吊具下总重量,单位t
    "weight1": 2,  # float,吊具左上重量,单位t
    "weight2": 2,  # float,吊具左下重量,单位t
    "weight3": 2,  # float,吊具右上重量,单位t
    "weight4": 2,  # float,吊具右下重量,单位t
    "lock_state": 0,  # int,闭锁状态, 0-闭锁灯灭,1-闭锁灯亮
    "unlock_state": 0,  # int,开锁状态, 0-开锁灯灭,1-开锁灯亮
    "mid_lock_ud_state": 0,  # int,中锁上升下降状态, 0-上升状态,1-下降状态
    "mid_lock_ss_state": 0,  # 中锁伸缩状态, 0-拉伸状态,1-收缩状态
    "mid_lock_gap": 0,  # int, 中锁间距
    "land_state": 0,  # int,着箱状态, 0-着箱灯灭,1-着箱灯亮
    "spreader_single_state": 0,  # /int,/单箱模式状态, 0-单箱模式未到位,1-单箱模式到位
    "spreader_double_state": 0,  # int,双箱模式状态, 0-单双箱模式未到位,1-双箱模式到位
    "spreader_20f": 0,  # int,20尺状态, 0-20尺状态未到位,1-20尺状态到位
    "spreader_40f": 0,  # int,40尺状态, 0-40尺状态未到位,1-40尺状态到位
    "spreader_45f": 0,  # int,45尺状态, 0-45尺状态未到位,1-45尺状态到位
    "spreader_on_state": 0,  # int,吊具泵合状态位,0-吊具泵下状态,1-吊具泵上状态
    "spreader_reset_state": 0,  # int,吊具回零状态位, 0-吊具未回零,1-吊具回零（吊具姿态回零）
    "spreader_anti_sway": 0,  # int,吊具防摇状态位,0-吊具防摇下状态,1-吊具防摇上状态
    "spreader_anti_twist": 0,  # int,吊具防扭状态位,0-吊具防扭下状态,1-吊具防扭上状态
    "spreader_flipper_sea_side_l_status": 0,  # int,吊具海侧左导板状态位,0-升起状态,1-放下状态
    "spreader_flipper_sea_side_r_status": 0,  # int,吊具海侧右导板状态位,0-升起状态,1-放下状态
    "spreader_flipper_land_side_l_status": 0,  # int,吊具海侧左导板状态位,0-升起状态,1-放下状态
    "spreader_flipper_land_side_r_status": 0,  # int,吊具海侧右导板状态位,0-升起状态,1-放下状态
    "spreader_lr_tilt_dir": 0,  # int,吊具左右倾斜方向,0-无倾斜,1-吊具左倾,2-吊具右倾
    "spreader_lr_tilt_angle": 0.0,  # float,吊具左右倾斜角度
    "spreader_fb_tilt_dir": 0,  # int,吊具前后倾斜方向,0-无倾斜,1-吊具前倾,2-吊具后倾
    "spreader_fb_tilt_angle": 0.0,  # float,吊具前后倾斜角度
    "spreader_lr_rotate_dir": 0,  # int,吊具左右旋转方向,0-无旋转,1-吊具左旋,2-吊具右旋
    "spreader_lr_rotate_angle": 0.0,  # float,吊具左右旋转角度
    "gantry_clamp_status": 1,  # int,大车夹轮器状态位,0-松轨状态,1-夹轨状态
    "gantry_skid_status": 1,  # int,大车铁鞋状态位,1-释放状态,0-未释放状态
    "gantry_pos": 0.0,  # float,大车位置, 单位m
    "gantry_vel": 0.0,  # float,大车速度,单位m/s
    "gantry_move_left": 0,  # int,大车向左移动, 0-否,1-是
    "gantry_move_right": 0,  # int,大车向右移动, 0-否,1-是
    "bypass_status": 0,  # int,旁路状态,0-旁路未开状态,1-旁路开状态
    "beam_stilt_speed": 0.0,  # float,大梁俯仰速度,m/s
    "beam_stilt_angle": 0.0,  # float,大梁俯仰角度
    "beam_latch_status": 0,  # 大梁落钩状态,1-落钩、0-起钩
    "front_beam_light_status": 0,  # int,前梁灯状态, 0-关,1-开
    "gantry_light_status": 0,  # int,大车灯状态, 0-关,1-开
    "escalator_light_status": 0,  # int,扶梯灯状态, 0-关,1-开
    "trolley_light_status": 0,  # int,小车灯状态, 0-关,1-开
    "mid_back_beam_light_status": 0,  # int,中后梁灯状态, 0-关,1-开
    "footpath_light_status": 0,  # int,步道灯状态, 0-关,1-开
    "conn_beam_light_status": 0,  # int,联系梁灯状态, 0-关,1-开
    # "camera_up_status": 0, # int,手柄控制摄像头上转 0-关,1-开
    # "camera_down_status":0, # int,手柄控制摄像头下转 0-关,1-开
    # "camera_left_status":0, # int,手柄控制摄像头左转 0-关,1-开
    # "camera_right_status":0, # int,手柄控制摄像头右转 0-关,1-开
    # "camera_zoomin_status":0, # int,手柄控制摄像头放大 0-关,1-开
    # "camera_zoomout_status":0, # int,手柄控制摄像头缩小 0-关,1-开
    "dive_plat_door_status": 1,  # int, 跳水平台门状态,0-关,1-开
    "car_stoppos_status": 1,  # int, 小车在停车位 0 - 不在, 1 - 在
    "car_backpos_motion_status": 1,  # int, 小车回停车位运动中0-停止,1-正在回	"trolley_handle_value":1,#float,小车手柄速度给定值
    "spreader_handle_value": 1,  # float,起升手柄速度给定值
    "gantry_handle_value": 1,  # float,大车手柄速度给定值
    "fault_code": ["", ]  # string[],设备故障代码
}

MC001 = {
    "msg_uid": "1234567890",  # string,消息序号
    "msg_name": "MC001",  # string,消息名称
    "sender": "MC",  # string,发送方
    "timestamp": 16879546201,  # long, 时间戳,单位毫秒
    "receiver": "CT",  # string,接收方
    "craneId": "404-1",  # string, 设备号
    "data": PlcQcStatus  # PlcQcStatus
}

# 主控到感知
# 广播端口：9003
# 发送方：主控
# 接收方：感知
# MC201 请求陆侧箱信息识别结果
MC201 = {
    "msg_uid": "1234567890",  # string,消息序号
    "msg_name": "MC201",  # string,消息名称
    "sender": "MC",  # string,发送方
    "timestamp": 16879546201,  # long, 时间戳,单位毫秒
    "receiver": "VI",  # string,接收方
    "craneId": "404-1",  # string, 设备号
    "data": {
        "task_id": "1234",
        "lane_id": "1",
        "truck_id": "T008",
    }
}

# MC202 请求车道集卡识别结果
MC202 = {
    "msg_uid": "1234567890",  # string,消息序号
    "msg_name": "MC202",  # string,消息名称
    "sender": "MC",  # string,发送方
    "timestamp": 16879546201,  # long, 时间戳,单位毫秒
    "receiver": "VI",  # string,接收方
    "craneId": "404-1",  # string, 设备号
    "data": {
        "lane_id": "5",  # 若指定集卡道,返回车道上识别到的车号。否则返回所有车道识别结果
    }
}

# MC203 发送作业任务信息
MC203 = {
    "msg_uid": "1234567890",  # string,消息序号
    "msg_name": "MC203",  # string,消息名称
    "sender": "MC",  # string,发送方
    "timestamp": 16879546201,  # long, 时间戳,单位毫秒
    "receiver": "VI",  # string,接收方
    "craneId": "404-1",  # string, 设备号
    "data": {
        "task_list": []  # [,,] # Task[]
    }

}

# MC204 车道开启关闭
WorkLaneSetting = {
    "lane_id": "1",
    "activate": True
}

MC204 = {
    "msg_uid": "1234567890",  # string,消息序号
    "msg_name": "MC204",  # string,消息名称
    "sender": "MC",  # string,发送方
    "timestamp": 16879546201,  # long, 时间戳,单位毫秒
    "receiver": "VI",  # string,接收方
    "craneId": "404-1",  # string, 设备号
    "data": {
        "lane_settings": WorkLaneSetting  # [,,] #WorkLaneSetting[]
    }

}

# MC205 请求吊具姿态和位置
MC205 = {
    "msg_uid": "1234567890",  # string,消息序号
    "msg_name": "MC205",  # string,消息名称
    "sender": "MC",  # string,发送方
    "timestamp": 16879546201,  # long, 时间戳,单位毫秒
    "receiver": "VI",  # string,接收方
    "craneId": "404-1",  # string, 设备号
    "data": "null"
}
# MC206 人员安全功能触发
MC206 = {
    "msg_uid": "1234567890",  # string,消息序号
    "msg_name": "MC206",  # string,消息名称
    "sender": "MC",  # string,发送方
    "timestamp": 16879546201,  # long, 时间戳,单位毫秒
    "receiver": "VI",  # string,接收方
    "craneId": "404-1",  # string, 设备号
    "data": {
        "cam_code": "1",  # 摄像头编号
    }

}

# MC207 请求图片和视频流信息
MC207 = {
    "msg_uid": "1234567890",  # string,消息序号
    "msg_name": "MC207",  # string,消息名称
    "sender": "MC",  # string,发送方
    "timestamp": 16879546201,  # long, 时间戳,单位毫秒
    "receiver": "VI",  # string,接收方
    "craneId": "404-1",  # string, 设备号
    "data": None
}

# MC301 发送引导任务
MC301 = {
    "msg_uid": "20241201_2",  # string,消息序号
    "msg_name": "MC301",  # string,消息名称
    "sender": "MC",  # string,发送方
    "timestamp": 16879546201,  # long, 时间戳,单位毫秒
    "receiver": "VI",  # string,接收方
    "craneId": "404-1",  # string, 设备号
    "data": {
        "lane_id": "4",  #
        "guide_mission": {
            "task_id": "1",  # 任务id
            "lane_id": "4",
            "workflow": 1,  # 作业工艺0、单箱吊；1、双箱吊； int类型
            "work_type": "LOAD",  # 作业类型,LOAD-装船,DSCH-卸船
            "truck_id": "T008",
            "work_size": 20,
            "truck_pos": 2,  # 1=前,2=中,3=后,0=自动判断
        },  # GuideMission
    }
}

GuideMission = {
    "task_id": "1",  # 任务id
    "lane_id": "1",
    "workflow": 1,  # 作业工艺1、单箱吊；2、双箱吊； int类型
    "work_type": "DSCH",  # 作业类型,LOAD-装船,DSCH-卸船
    "truck_id": "Y56",
    "work_size": 20,
    "truck_pos": 2,  # 1=前,2=中,3=后,0=自动判断
}

# MC302 结束引导任务
MC302 = {
    "msg_uid": "1234567890",  # string,消息序号
    "msg_name": "MC302",  # string,消息名称
    "sender": "MC",  # string,发送方
    "timestamp": 16879546201,  # long, 时间戳,单位毫秒
    "receiver": "VI",  # string,接收方
    "craneId": "404-1",  # string, 设备号
    "data": {
        "lane_id": "3",  #
    }

}

# MC303 请求车道集卡引导状态
MC303 = {
    "msg_uid": "1234567890",  # string,消息序号
    "msg_name": "MC303",  # string,消息名称
    "sender": "MC",  # string,发送方
    "timestamp": 16879546201,  # long, 时间戳,单位毫秒
    "receiver": "VI",  # string,接收方
    "craneId": "404-1",  # string, 设备号
    "data": {
        "lane_id": "5",  #
    }

}

# MC304 请求集卡和集装箱位置
MC304 = {
    "msg_uid": "1234567890",  # string,消息序号
    "msg_name": "MC304",  # string,消息名称
    "sender": "MC",  # string,发送方
    "timestamp": 16879546201,  # long, 时间戳,单位毫秒
    "receiver": "VI",  # string,接收方
    "craneId": "404-1",  # string, 设备号
    "data": {
        "lane_id": "5",  #
    }

}

# MC305 车道开启关闭
MC305 = {
    "msg_uid": "1234567890",  # string,消息序号
    "msg_name": "MC305",  # string,消息名称
    "sender": "MC",  # string,发送方
    "timestamp": 16879546201,  # long, 时间戳,单位毫秒
    "receiver": "VI",  # string,接收方
    "craneId": "404-1",  # string, 设备号
    "data": {
        "lane_settings": WorkLaneSetting  # [,,] #WorkLaneSetting[]
    }
}

# MC306 关路安全检测设置
MC306 = {
    "msg_uid": "1234567890",  # //string，消息序号
    "msg_name": "MC306",  # //string,消息名称
    "sender": "MC",  # //string，发送方
    "timestamp": 16879546201,  # //long, 时间戳，单位毫秒
    "receiver": "VI",  # //string，接收方
    "craneId": "404-1",  # //string, 设备号
    "data": {
        "area_code": 5,  # //5=陆侧，6=海侧
        "scan_x_range": 2.5,  # //扫描范围小车方向宽度
        "scan_y_range": 15.0,  # //扫描范围大车方向宽度
        "scan_direction": 1,  # //0=全向，1=向陆侧，2=向海侧，3=仅小车下方
        "scan_x_pos_min": 1.0,  # // 最小小车方向扫描位置
        "scan_x_pos_max": 65.2,  # // 最大小车方向扫描位置
    }
}

# MC307 开启关闭大车轨道障碍检测
MC307 = {
    "msg_uid": "1234567890",  # //string，消息序号
    "msg_name": "MC307",  # //string，消息名称
    "sender": "MC",  # //string，发送方
    "timestamp": 16879546201,  # //long, 时间戳，单位毫秒
    "receiver": "VI",  # //string，接收方
    "craneId": "404-1",  # //string, 设备号
    "data": {
        "switchOn": 1,  # //1=开，2=关
        "scan_area_list": [1, 2, 3, 4]
    }
}

# MC308 查询大车轨道障碍物检测开启状态
MC308 = {
    "msg_uid": "1234567890",  # //string，消息序号
    "msg_name": "MC308",  # //string，消息名称
    "sender": "MC",  # //string，发送方
    "timestamp": 16879546201,  # //long, 时间戳，单位毫秒
    "receiver": "VI",  # //string，接收方
    "craneId": "404-1",  # //string, 设备号
    "data": None
}

# MC309 查询雾天状态
MC309 = {
    "msg_uid": "1234567890",  # //string，消息序号
    "msg_name": "MC308",  # //string，消息名称
    "sender": "MC",  # //string，发送方
    "timestamp": 16879546201,  # //long, 时间戳，单位毫秒
    "receiver": "VI",  # //string，接收方
    "craneId": "404-1",  # //string, 设备号
    "data": None
}

# 感知到主控
# 广播端口：9004
# 发送方：感知
# 接收方：主控
# VI000 心跳
# 发送频率：每200毫秒
VI000 = {
    "msg_uid": "1234567890",  # string,消息序号
    "msg_name": "VI000",  # string,消息名称
    "sender": "VI",  # string,发送方
    "timestamp": 16879546201,  # long, 时间戳,单位毫秒
    "receiver": "MC",  # string,接收方
    "craneId": "404-1",  # string, 设备号
    "data": {
        "heartbeat": 1  # int,心跳1-9999
    }
}

# VI001 反馈箱信息识别结果
# 发送频率：识别到结果或收到请求时发送

ContainerRecognizeResult = {
    "recognizeResults": [
        {
            "item": "container_code",
            "state": 1,
            "result": "",
            "images": []
        },
        {
            "item": "container_iso",
            "state": 1,
            "result": "",
            "images": []
        },
        {
            "item": "container_door_dir",
            "state": 1,
            "result": "",
            "images": []
        },
        {
            "item": "container_lock",
            "state": 1,
            "result": "",
            "images": []

        },
        {
            "item": "container_seal",
            "state": 1,
            "result": "",
            "images": []
        },
        {
            "item": "container_height",
            "state": 1,
            "result": "",
            "images": []
        },
    ]

}

ImageData = {
    "image": "/pathto/ret-1.jpg",
    "datetime": 1615427917108
}
RecognizeResult = {
    "item": "container_code",
    "state": 1,  # 0=未识别,1=已识别,2=识别异常
    "result": "",
    "images": [ImageData, ]  # ImageData[]
}
ContainerRecognizeResult = {
    "recognizeResults": [RecognizeResult, ]
}

Container_INFO = {
    "container_num_front": [],
    "thresh_front": 0.0,
    "container_num_center": [],
    "thresh_center": 0.0,
    "container_num_rear": [],
    "thresh_rear": 0.0
}

TruckHeadRecognizeResult = {
    "1": [],
    "2": [],
    "3": [],
    "4": [],
    "5": [],
    "6": [],
}


VI001 = {
    "msg_uid": "1234567890",  # string,消息序号
    "msg_name": "VI001",  # string,消息名称
    "sender": "VI",  # string,发送方
    "timestamp": 16879546201,  # long, 时间戳,单位毫秒
    "receiver": "MC",  # string,接收方
    "craneId": "404-1",  # string, 设备号
    "data": {
        "container1": {},  # ContainerRecognizeResult,
        "container2": {},  # ContainerRecognizeResult,

    }

}

# VI002 反馈车道集卡识别结果
# 发送频率：识别到结果或收到请求时发送
TruckRecognizeResult = {
    "lane_id": "2",
    "recognizeResults": [
        {
            "item": "truck_id",
            "state": 1,
            "result": "",
            "images": []
        },
        {
            "item": "truck_direction",
            "state": 1,
            "result": "",
            "images": []
        },
        {
            "item": "truck_type",
            "state": 1,
            "result": "",
            "images": []
        },
        {
            "item": "truck_height",
            "state": 1,
            "result": "",
            "images": []
        },
        {
            "item": "truck_load_state",
            "state": 1,
            "result": "",  # 000=无箱 100=前20尺 001=后20尺 010=中20尺 111=大箱 101=双箱
            "images": []
        },
        {
            "item": "container_id_front",
            "state": 1,
            "result": "",
            "images": []
        },
        {
            "item": "container_id_center",
            "state": 1,
            "result": "",
            "images": []
        },
        {
            "item": "container_id_rear",
            "state": 1,
            "result": "",
            "images": []
        },
    ]
}

VI002 = {
    "msg_uid": "1234567890",  # string,消息序号
    "msg_name": "VI002",  # string,消息名称
    "sender": "VI",  # string,发送方
    "timestamp": 16879546201,  # long, 时间戳,单位毫秒
    "receiver": "MC",  # string,接收方
    "craneId": "404-1",  # string, 设备号
    "data": {
        "truck_recognize_results": [
            {
                "lane_id": "1",
                "recognizeResults": []
            },
            {
                "lane_id": "2",
                "recognizeResults": []
            }, {
                "lane_id": "3",
                "recognizeResults": []
            }, {
                "lane_id": "4",
                "recognizeResults": []
            }, {
                "lane_id": "5",
                "recognizeResults": []
            }, {
                "lane_id": "6",
                "recognizeResults": []
            },
        ],  # TruckRecognizeResult[] 对应六个车道
    }
}

# VI003 异常上报
VI003 = {
    "msg_uid": "1234567890",  # string,消息序号
    "msg_name": "VI003",  # string,消息名称
    "sender": "VI",  # string,发送方
    "timestamp": 16879546201,  # long, 时间戳,单位毫秒
    "receiver": "MC",  # string,接收方
    "craneId": "404-1",  # string, 设备号
    "data": []  # Exception,异常信息
}

SpreaderPositionStatus = {
    "has_spreader": True,  # True-目标下有吊具,False-目标下无吊具
    "spreader_target_x": 20.5,  # float 型,目标吊具小车方向位置,单位：m
    "spreader_target_z": 1.5,  # float 型,目标吊具高度,单位：m
    "spreader_target_y": 0.3,  # float 型,目标吊具大车方向位置,单位：m
    "spreader_target_theta": 0.01,  # float 型,目标吊具摆角,单位rad
    "spreader_target_zeta": 0.01,  # float 型,目标吊具扭角,单位rad
    "spreader_cntr_num": 1,  # 吊具当前抓起的箱子,0-无箱子,1-一个箱子,2-两个箱子
    "spreader_code": 0,  # 备用
}

# VI004 吊具姿态和位置上报
VI004 = {
    "msg_uid": "1234567890",  # string,消息序号
    "msg_name": "VI004",  # string,消息名称
    "sender": "VI",  # string,发送方
    "timestamp": 16879546201,  # long, 时间戳,单位毫秒
    "receiver": "MC",  # string,接收方
    "craneId": "404-1",  # string, 设备号
    "data": None  # SpreaderPositionStatus,吊具位置状态
}

# VI005 人员检测情况上报
VI005 = {
    "msg_uid": "1234567890",  # string,消息序号
    "msg_name": "VI005",  # string,消息名称
    "sender": "VI",  # string,发送方
    "timestamp": 16879546201,  # long, 时间戳,单位毫秒
    "receiver": "MC",  # string,接收方
    "craneId": "404-1",  # string, 设备号
    "data": {
        "cam_code": "1",  # 摄像头编号
        "has_person": False,  # True-目标下有人员,False-目标下无人员
        "person_target_x": "0",  # string 型,目标场景中所有人员横向位置,用逗号隔开,单位：m
        "person_target_y": "0",  # string 型,目标场景中所有人员纵向位置,用逗号隔开,单位：m
        "person_num": 0,  # int型,当前场景中人员数量
    }
}

# VI006 发送图片和视频流信息
VI006 = {
    "msg_uid": "1234567890",  # string,消息序号
    "msg_name": "VI006",  # string,消息名称
    "sender": "VI",  # string,发送方
    "timestamp": 16879546201,  # long, 时间戳,单位毫秒
    "receiver": "MC",  # string,接收方
    "craneId": "404-1",  # string, 设备号
    "data": {
        "cam_id": "3",  # 摄像头编号
        "frame_num": 102,  # int,帧数
        "timestart": 16879546201,  # long, 开始时间戳,单位毫秒
        "timeend": 16879592394,  # long, 结束时间戳,单位毫秒
        "video_info": ""  # string,视频路径
    }
}
GuideStatus = {
    "lane_id": "1",
    "guide_state": 1,  # 0=未引导 1=引导中 2=引导到位
    "truck_distance": 52,  # 集卡距离作业位置行驶距离
    "truck_move_dir": 0,  # 0=到位,1=面海向右,2=面海向左,3=不在视野中
}
# VI007 反馈引导状态
VI007 = {
    "msg_uid": "1234567890",  # string,消息序号
    "msg_name": "VI007",  # string,消息名称
    "sender": "VI",  # string,发送方
    "timestamp": 16879546201,  # long, 时间戳,单位毫秒
    "receiver": "MC",  # string,接收方
    "craneId": "404-1",  # string, 设备号
    "data": {
        "lane_guide_status": [
            {
                "lane_id": "1",
                "guide_state": 0,  # 0=未引导 1=引导中 2=引导到位
                "truck_distance": None,  # 集卡距离作业位置行驶距离
                "truck_move_dir": None,  # 0=到位,1=面海向右,2=面海向左,3=不在视野中
                "has_truck": None
            },
            {
                "lane_id": "2",
                "guide_state": 0,  # 0=未引导 1=引导中 2=引导到位
                "truck_distance": None,  # 集卡距离作业位置行驶距离
                "truck_move_dir": None,  # 0=到位,1=面海向右,2=面海向左,3=不在视野中
                "has_truck": None

            },
            {
                "lane_id": "3",
                "guide_state": 0,  # 0=未引导 1=引导中 2=引导到位
                "truck_distance": None,  # 集卡距离作业位置行驶距离
                "truck_move_dir": None,  # 0=到位,1=面海向右,2=面海向左,3=不在视野中
                "has_truck": None
            },
            {
                "lane_id": "4",
                "guide_state": 0,  # 0=未引导 1=引导中 2=引导到位
                "truck_distance": None,  # 集卡距离作业位置行驶距离
                "truck_move_dir": None,  # 0=到位,1=面海向右,2=面海向左,3=不在视野中
                "has_truck": None
            },
            {
                "lane_id": "5",
                "guide_state": 0,  # 0=未引导 1=引导中 2=引导到位
                "truck_distance": None,  # 集卡距离作业位置行驶距离
                "truck_move_dir": None,  # 0=到位,1=面海向右,2=面海向左,3=不在视野中
                "has_truck": None
            },
            {
                "lane_id": "6",
                "guide_state": 0,  # 0=未引导 1=引导中 2=引导到位
                "truck_distance": None,  # 集卡距离作业位置行驶距离
                "truck_move_dir": None,  # 0=到位,1=面海向右,2=面海向左,3=不在视野中
                "has_truck": None
            },
        ]  # [GuideStatus,] #GuideStatus[]
    }
}

# VI008 反馈集卡和集装箱位置
VI008 = {
    "msg_uid": "1234567890",  # string,消息序号
    "msg_name": "VI008",  # string,消息名称
    "sender": "VI",  # string,发送方
    "timestamp": 16879546201,  # long, 时间戳,单位毫秒
    "receiver": "MC",  # string,接收方
    "craneId": "404-1",  # string, 设备号
    "data": {
        "lane_id": "5",  # string, 车道号
        "has_car": True,  # True-目标车道有集卡,False-目标车道无集卡
        "car_target_x": None,  # float 型,目标集卡小车方向位置,单位：m
        "car_target_y": None,  # float 型,目标集卡大车方向位置,单位：m
        "car_target_t": 0.01,  # float 型,目标集卡扭角,单位rad
        "has_cntr": True,  # True-目标车道有集装箱,False-目标车道无集装箱
        "cntr_target_x": None,  # float 型,目标集装箱小车方向位置,单位：m
        "cntr_target_y": None,  # float 型,目标集装箱大车方向位置,单位：m
        "cntr_target_t": None,  # float 型,目标集装箱扭角,单位rad}
        "cntr2_target_x": None,  # float 型,目标集装箱小车方向位置,单位：m
        "cntr2_target_y": None,  # float 型,目标集装箱大车方向位置,单位：m
        "cntr2_target_t": None,  # float 型,目标集装箱扭角,单位rad}
        "target_dis": 0.0,  # 双箱间距,单箱时返回0,单位m
        "cntr_dislocation": False,  # 双箱时是否错位 True/False
        "cntr_pos": 3,  # 1-前小箱位置, 2-后小箱位置,3-中间位置
        "vehicle_dir": None,  # 0-底端（面海向左）1-高端（面海向右）
    }
}

# VI009 障碍物检测情况上报
VI009 = {
    "msg_uid": "1234567890",  # //string，消息序号
    "msg_name": "VI009",  # //string，消息名称
    "sender": "VI",  # //string，发送方
    "timestamp": 16879546201,  # //long, 时间戳，单位毫秒
    "receiver": "MC",  # //string，接收方
    "craneId": "404-1",  # //string, 设备号
    "data": {
        "area_code": 1,  # //区域编号，1=海左大车轨道，2=海右大车轨道，3=陆左大车轨道，4=陆右大车轨道，5=海侧关路，6=陆侧关路
        "cam_code_list": [],  # //发现障碍物的摄像头编号列表
        "has_object": False,
        "object_distance": 2.3,  # //float,距离最近障碍物距离,单位米（用于大车轨道方向）
        "object_type": None,  # //障碍物类型，person，truck，qc，other
        "has_person": False,  # //True-目标下有人员，False-目标下无人员
        "person_target_x": '',  # //string 型，目标场景中所有人员横向位置，用逗号隔开，单位：m
        "person_target_y": '',  # //string 型，目标场景中所有人员纵向位置，用逗号隔开，单位：m
        "person_num": None,  # //int型，当前场景中人员数量
    }
}

# VI010 反馈障碍物检测开启状态

VI010 = {
    "msg_uid": "1234567890",  # //string，消息序号
    "msg_name": "VI010",  # //string，消息名称
    "sender": "VI",  # //string，发送方
    "timestamp": 16879546201,  # //long, 时间戳，单位毫秒
    "receiver": "MC",  # //string，接收方
    "craneId": "404-1",  # //string, 设备号
    "data": {
        "on_area_list": [1, 2, 3, 4, 5, 6],  # //开启的区域编号
        "off_area_list": [],  # //关闭的区域编号
    }
}

# VI011 反馈雾天检测结果
VI011 = {
    "msg_uid": "1234567890",  # //string，消息序号
    "msg_name": "VI011",  # //string，消息名称
    "sender": "VI",  # //string，发送方
    "timestamp": 16879546201,  # //long, 时间戳，单位毫秒
    "receiver": "MC",  # //string，接收方
    "craneId": "404-1",  # //string, 设备号
    "data": {
        "fog_level": 0  # //int, 大雾级别 0=无，1=有，99=检测失败
    }
}

Has_task = [{'lane': 1, 'has_task': False}, {'lane': 2, 'has_task': False}, {'lane': 3, 'has_task': False},
            {'lane': 4, 'has_task': False}, {'lane': 5, 'has_task': False}, {'lane': 6, 'has_task': False}]

global VI_msg_dict
VI_msg_dict = {
    "Container_INFO": Container_INFO,
    "Has_task": Has_task,
    "TruckHeadRecognizeResult": TruckHeadRecognizeResult,
    # MC PUB
    "MC001": MC001,

    # MC -> VI
    "MC201": MC201,
    "MC202": MC202,
    "MC203": MC203,
    "MC204": MC204,
    "MC205": MC205,
    "MC206": MC206,
    "MC207": MC207,

    "MC301": MC301,
    "MC302": MC302,
    "MC303": MC303,
    "MC304": MC304,
    "MC305": MC305,
    "MC306": MC306,
    "MC307": MC307,
    "MC308": MC308,
    "MC309": MC309,

    "VI000": VI000,
    "VI001": VI001,
    "VI002": VI002,
    "VI003": VI003,
    "VI004": VI004,
    "VI005": VI005,
    "VI006": VI006,
    "VI007": VI007,
    "VI008": VI008,
    "VI009": VI009,
    "VI010": VI010,
    "VI011": VI011,
}

from initializers import *


def set_global(key: str, value):
    try:
        global VI_msg_dict
        VI_msg_dict[key] = value
        return True
    except Exception as error:
        print(f"Failed set global {key} -- '{type(error).__name__}: {error}'.")
        error_logger.error(f"Failed set global {key} -- '{type(error).__name__}: {error}'.")
        return False


def get_global(key: str):
    # 获得一个全局变量，不存在则提示读取对应变量失败
    try:
        global VI_msg_dict
        return VI_msg_dict[key]
    except Exception as error:
        print(f"Failed get global {key} -- '{type(error).__name__}: {error}'")
        error_logger.error(f"Failed get global {key} -- '{type(error).__name__}: {error}'")
        return None


# !!! 目前没在set/get时加线程锁限制
import json


def save_global():
    global VI_msg_dict
    file_path = './global_info.json'
    with open(file_path, 'w') as f:
        json.dump(VI_msg_dict, f, ensure_ascii=False, indent=4)


def reload_global():
    global VI_msg_dict
    file_path = './global_info.json'
    with open(file_path, 'r') as f:
        VI_msg_dict = json.load(f)

        # reload_global() # 每次初始化的时候, 都会加载上一次保存的状态
