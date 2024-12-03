# 0705 更新内容
1. 箱号识别文本检测后处理的crop部分
2. 集卡引导功能对于不同车道的
3. 车号识别对于不同车道的
4. 模型相关:更新侧面箱定位模型


# 06-14 
#### 服务架构
1. algroithms 算法模块
   -> yolo 目标检测定位, 目前所有的用的yolov5-s, predictor
   -> ppocr 文本识别, 箱号/车号, infer_rec / infer_det_rec
2. cam_utils 相机读取模块, 目前只使用了hksdk, 
   预留了deepstream的接口, 待下一阶段实现
3. configs 配置文件 检测模型/相机-车道信息
4. debug_utils / test_data 单元测试时用例与测试数据
5. initializers 复用模块的初始化
6. workers 工作线程
7. global_info 所有消息字段的全局变量, 参考消息内容
8. msg_manager.py 
todo: 增加调试模块, 接受端口转发指令

#### 使用说明
1. 运行时bash run_vi.py
2. 日志模块 
   main 所有消息交互的日志
   key  程序内部关键结果存储
   erro 报错信息
关于日志分析: 

