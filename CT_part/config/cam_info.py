'''
所有相机信息列表, 以及是否使用本地视频替代输入
'''
VEDIO_CAM = False
if VEDIO_CAM:
    CAMERA_DICT = {
        "cam_132":{
            "ip":"./test_data/149.mp4",
            "comment": "左联系梁车道2识别",
            "resolution": (3840, 2160),  # 相机分辨率
        },
    }
else:
    CAMERA_DICT = {
        # 车道1不作业
        "cam_132": {
                "ip": "10.141.1.132", 
                "comment": "左联系梁车道2识别箱门",
                "username": "admin", 
                "password": "Dnt@QC2023",
                "resolution": (3840, 2160),  # 相机分辨率
                "gpu_id": 0,
                "allow_disconnected": False,
            },
        "cam_133": {
                "ip": "10.141.1.133", 
                "comment": "左联系梁车道3识别箱门",
                "username": "admin", 
                "password": "Dnt@QC2023",
                "resolution": (3840, 2160),  # 相机分辨率
                "gpu_id": 0,
                "allow_disconnected": False,
            },
        "cam_134": {
                "ip": "10.141.1.134", 
                "comment": "左联系梁车道4识别箱门",
                "username": "admin", 
                "password": "Dnt@QC2023",
                "resolution": (3840, 2160),  # 相机分辨率
                "gpu_id": 0,
                "allow_disconnected": False,
            },
        "cam_135": {
                "ip": "10.141.1.135", 
                "comment": "左联系梁车道5识别箱门",
                "username": "admin", 
                "password": "Dnt@QC2023",
                "resolution": (3840, 2160),  # 相机分辨率
                "gpu_id": 0,
                "allow_disconnected": False,
            },
        "cam_136": {
                "ip": "10.141.1.136", 
                "comment": "左联系梁车道6识别箱门",
                "username": "admin", 
                "password": "Dnt@QC2023",
                "resolution": (3840, 2160),  # 相机分辨率
                "gpu_id": 0,
                "allow_disconnected": False,
            },
        "cam_142": {
                "ip": "10.141.1.142", 
                "comment": "右联系梁车道2识别箱门",
                "username": "admin", 
                "password": "Dnt@QC2023",
                "resolution": (3840, 2160),  # 相机分辨率
                "gpu_id": 0,
                "allow_disconnected": False,
            },
        "cam_143": {
                "ip": "10.141.1.143", 
                "comment": "右联系梁车道3识别箱门",
                "username": "admin", 
                "password": "Dnt@QC2023",
                "resolution": (3840, 2160),  # 相机分辨率
                "gpu_id": 0,
                "allow_disconnected": False,
            },
        "cam_144": {
                "ip": "10.141.1.144", 
                "comment": "右联系梁车道4识别箱门",
                "username": "admin", 
                "password": "Dnt@QC2023",
                "resolution": (3840, 2160),  # 相机分辨率
                "gpu_id": 0,
                "allow_disconnected": False,
            },
        "cam_145": {
                "ip": "10.141.1.145", 
                "comment": "右联系梁车道5识别箱门",
                "username": "admin", 
                "password": "Dnt@QC2023",
                "resolution": (3840, 2160),  # 相机分辨率
                "gpu_id": 0,
                "allow_disconnected": False,
            },
        "cam_146": {
                "ip": "10.141.1.146", 
                "comment": "右联系梁车道6识别箱门",
                "username": "admin", 
                "password": "Dnt@QC2023",
                "resolution": (3840, 2160),  # 相机分辨率
                "gpu_id": 0,
                "allow_disconnected": False,
            },
        "cam_138": {
            "ip": "10.141.1.138",
            "comment": "左联系梁12车道间识别车号",
            "username": "admin",
            "password": "Dnt@QC2023",
            "resolution": (3840, 2160),  # 相机分辨率
            "gpu_id": 0,
            "allow_disconnected": False,
        },
        "cam_139": {
            "ip": "10.141.1.139",
            "comment": "左联系梁56车道间识别车号",
            "username": "admin",
            "password": "Dnt@QC2023",
            "resolution": (3840, 2160),  # 相机分辨率
            "gpu_id": 0,
            "allow_disconnected": False,
        },
        "cam_148": {
            "ip": "10.141.1.148",
            "comment": "右联系梁12车道间识别车号",
            "username": "admin",
            "password": "Dnt@QC2023",
            "resolution": (3840, 2160),  # 相机分辨率
            "gpu_id": 0,
            "allow_disconnected": False,
        },
        "cam_149": {
            "ip": "10.141.1.149",
            "comment": "右联系梁56车道间识别车号",
            "username": "admin",
            "password": "Dnt@QC2023",
            "resolution": (3840, 2160),  # 相机分辨率
            "gpu_id": 0,
            "allow_disconnected": False,
        },
        "cam_119": {
            "ip": "10.141.1.119",
            "comment": "陆侧集卡引导",
            "username": "admin",
            "password": "Dnt@QC2023",
            "resolution": (3840, 2160),  # 相机分辨率
            "gpu_id": 0,
            "allow_disconnected": False,
        },
        "cam_165": {
            "ip": "10.141.1.165",
            "comment": "陆侧5车道侧面箱号识别",
            "username": "admin",
            "password": "Dnt@QC2023",
            "resolution": (3840, 2160),  # 相机分辨率
            "gpu_id": 0,
            "allow_disconnected": False,
        },
        "cam_155": {
            "ip": "10.141.1.155",
            "comment": "海侧4车道侧面箱号识别",
            "username": "admin",
            "password": "Dnt@QC2023",
            "resolution": (3840, 2160),  # 相机分辨率
            "gpu_id": 0,
            "allow_disconnected": False,
        },
        "cam_153": {
            "ip": "10.141.1.153",
            "comment": "海侧3车道侧面箱号识别",
            "username": "admin",
            "password": "Dnt@QC2023",
            "resolution": (3840, 2160),  # 相机分辨率
            "gpu_id": 0,
            "allow_disconnected": False,
        },
        "cam_151": {
            "ip": "10.141.1.151",
            "comment": "海侧2车道侧面箱号识别",
            "username": "admin",
            "password": "Dnt@QC2023",
            "resolution": (3840, 2160),  # 相机分辨率
            "gpu_id": 0,
            "allow_disconnected": False,
        },
        "cam_163": {
            "ip": "10.141.1.163",
            "comment": "陆侧4车道侧面箱号识别",
            "username": "admin",
            "password": "Dnt@QC2023",
            "resolution": (3840, 2160),  # 相机分辨率
            "gpu_id": 0,
            "allow_disconnected": False,
        },
        "cam_161": {
            "ip": "10.141.1.161",
            "comment": "陆侧6车道侧面箱号识别",
            "username": "admin",
            "password": "Dnt@QC2023",
            "resolution": (3840, 2160),  # 相机分辨率
            "gpu_id": 0,
            "allow_disconnected": False,
        },
        "cam_115": {
            "ip": "10.141.1.115",
            "comment": "海侧集卡引导",
            "username": "admin",
            "password": "Dnt@QC2023",
            "resolution": (3840, 2160),  # 相机分辨率
            "gpu_id": 0,
            "allow_disconnected": False,
        },
        "cam_158": {
            "ip": "10.141.1.158",
            "comment": "海侧轨道左立柱",
            "username": "admin",
            "password": "Dnt@QC2023",
            "resolution": (2560, 1440),  # 相机分辨率
            "gpu_id": 0,
            "allow_disconnected": False,
        },
        "cam_159": {
            "ip": "10.141.1.159",
            "comment": "海侧轨道右立柱",
            "username": "admin",
            "password": "Dnt@QC2023",
            "resolution": (2560, 1440),  # 相机分辨率
            "gpu_id": 0,
            "allow_disconnected": False,
        },
        "cam_168": {
            "ip": "10.141.1.168",
            "comment": "陆侧轨道左立柱",
            "username": "admin",
            "password": "Dnt@QC2023",
            "resolution": (2560, 1440),  # 相机分辨率
            "gpu_id": 0,
            "allow_disconnected": False,
        },
        "cam_169": {
            "ip": "10.141.1.169",
            "comment": "陆侧轨道右立柱",
            "username": "admin",
            "password": "Dnt@QC2023",
            "resolution": (2560, 1440),  # 相机分辨率
            "gpu_id": 0,
            "allow_disconnected": False,
        },
        "cam_104": {
            "ip": "10.141.1.104",
            "comment": "陆侧轨道右立柱",
            "username": "admin",
            "password": "Dnt@QC2023",
            "resolution": (3840, 2160),  # 相机分辨率
            "gpu_id": 0,
            "allow_disconnected": False,
        },
        "cam_100": {
            "ip": "10.141.1.100",
            "comment": "陆侧轨道右立柱",
            "username": "admin",
            "password": "Dnt@QC2023",
            "resolution": (3840, 2160),  # 相机分辨率
            "gpu_id": 0,
            "allow_disconnected": False,
        },
        "cam_107": {
            "ip": "10.141.1.107",
            "comment": "小车60筒机",
            "username": "admin",
            "password": "Dnt@QC2023",
            "resolution": (1092, 1080),  # 相机分辨率
            "gpu_id": 0,
            "allow_disconnected": False,
        }
}
