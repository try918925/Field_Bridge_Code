from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from pathlib import Path
import sys
import os

FILE = Path(__file__).resolve()
ROOT = FILE.parents[1]  # YOLOv5 root directory
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative


import numpy as np
import cv2
import yaml
import os
import sys
import json
import paddle
from algorithms.ppocr.data import create_operators, transform
from algorithms.ppocr.modeling.architectures import build_model
from algorithms.ppocr.postprocess import build_post_process
from algorithms.ppocr.utils.save_load import load_model

def load_config(file_path):
    """
    Load config from yml/yaml file.
    Args:
        file_path (str): Path of the config file to be loaded.
    Returns: global config
    """
    _, ext = os.path.splitext(file_path)
    assert ext in ['.yml', '.yaml'], "only support yaml files for now"
    config = yaml.load(open(file_path, 'rb'), Loader=yaml.Loader)
    return config

class OCR_rec:
    def __init__(self, config_path):
        # self.config, self.device, self.logger, self.vdl_writer = self.program.preprocess()
        self.config = load_config(config_path)
        self.global_config = self.config['Global']
    
    def load_checkpoint(self):
        # build post process
        self.post_process_class = build_post_process(self.config['PostProcess'],
                                                self.global_config)

        # build model
        if hasattr(self.post_process_class, 'character'):
            char_num = len(getattr(self.post_process_class, 'character'))
            if self.config["Architecture"]["algorithm"] in ["Distillation",
                                                    ]:  # distillation model
                for key in self.config["Architecture"]["Models"]:
                    if self.config["Architecture"]["Models"][key]["Head"][
                            "name"] == 'MultiHead':  # multi head
                        out_channels_list = {}
                        if self.config['PostProcess'][
                                'name'] == 'DistillationSARLabelDecode':
                            char_num = char_num - 2
                        if self.config['PostProcess'][
                                'name'] == 'DistillationNRTRLabelDecode':
                            char_num = char_num - 3
                        out_channels_list['CTCLabelDecode'] = char_num
                        out_channels_list['SARLabelDecode'] = char_num + 2
                        out_channels_list['NRTRLabelDecode'] = char_num + 3
                        self.config['Architecture']['Models'][key]['Head'][
                            'out_channels_list'] = out_channels_list
                    else:
                        self.config["Architecture"]["Models"][key]["Head"][
                            "out_channels"] = char_num
            elif self.config['Architecture']['Head'][
                    'name'] == 'MultiHead':  # multi head
                out_channels_list = {}
                char_num = len(getattr(self.post_process_class, 'character'))
                if self.config['PostProcess']['name'] == 'SARLabelDecode':
                    char_num = char_num - 2
                if self.config['PostProcess']['name'] == 'NRTRLabelDecode':
                    char_num = char_num - 3
                out_channels_list['CTCLabelDecode'] = char_num
                out_channels_list['SARLabelDecode'] = char_num + 2
                out_channels_list['NRTRLabelDecode'] = char_num + 3
                self.config['Architecture']['Head'][
                    'out_channels_list'] = out_channels_list
            else:  # base rec model
                self.config["Architecture"]["Head"]["out_channels"] = char_num
        self.model = build_model(self.config['Architecture'])

        load_model(self.config, self.model)
        # print(self.model)

        self.transforms = []
        for op in self.config['Eval']['dataset']['transforms']:
            op_name = list(op)[0]
            if 'Label' in op_name:
                continue
            elif op_name in ['RecResizeImg']:
                op[op_name]['infer_mode'] = True
            elif op_name == 'KeepKeys':
                if self.config['Architecture']['algorithm'] == "SRN":
                    op[op_name]['keep_keys'] = [
                        'image', 'encoder_word_pos', 'gsrm_word_pos',
                        'gsrm_slf_attn_bias1', 'gsrm_slf_attn_bias2'
                    ]
                elif self.config['Architecture']['algorithm'] == "SAR":
                    op[op_name]['keep_keys'] = ['image', 'valid_ratio']
                elif self.config['Architecture']['algorithm'] == "RobustScanner":
                    op[op_name][
                        'keep_keys'] = ['image', 'valid_ratio', 'word_positons']
                else:
                    op[op_name]['keep_keys'] = ['image']
            self.transforms.append(op)
        self.global_config['infer_mode'] = True
        self.ops = create_operators(self.transforms, self.global_config)
        self.model.eval()
    
    def predict(self, img_list):
        res_list = []
        for img_data in img_list:   #get_image_file_list(img_path):
            try:
                _, encoded_image = cv2.imencode(".jpg", img_data)
            except:
                # print(len(img_data))
                # print(img_data)
                continue
            img = encoded_image.tobytes() 
            data = {'image': img}
            batch = transform(data, self.ops)
            if self.config['Architecture']['algorithm'] == "SRN":
                encoder_word_pos_list = np.expand_dims(batch[1], axis=0)
                gsrm_word_pos_list = np.expand_dims(batch[2], axis=0)
                gsrm_slf_attn_bias1_list = np.expand_dims(batch[3], axis=0)
                gsrm_slf_attn_bias2_list = np.expand_dims(batch[4], axis=0)

                others = [
                    paddle.to_tensor(encoder_word_pos_list),
                    paddle.to_tensor(gsrm_word_pos_list),
                    paddle.to_tensor(gsrm_slf_attn_bias1_list),
                    paddle.to_tensor(gsrm_slf_attn_bias2_list)
                ]
            if self.config['Architecture']['algorithm'] == "SAR":
                valid_ratio = np.expand_dims(batch[-1], axis=0)
                img_metas = [paddle.to_tensor(valid_ratio)]
            if self.config['Architecture']['algorithm'] == "RobustScanner":
                valid_ratio = np.expand_dims(batch[1], axis=0)
                word_positons = np.expand_dims(batch[2], axis=0)
                img_metas = [
                    paddle.to_tensor(valid_ratio),
                    paddle.to_tensor(word_positons),
                ]
            if self.config['Architecture']['algorithm'] == "CAN":
                image_mask = paddle.ones(
                    (np.expand_dims(
                        batch[0], axis=0).shape), dtype='float32')
                label = paddle.ones((1, 36), dtype='int64')
            images = np.expand_dims(batch[0], axis=0)
            images = paddle.to_tensor(images)
            if self.config['Architecture']['algorithm'] == "SRN":
                preds = self.model(images, others)
            elif self.config['Architecture']['algorithm'] == "SAR":
                preds = self.model(images, img_metas)
            elif self.config['Architecture']['algorithm'] == "RobustScanner":
                preds = self.model(images, img_metas)
            elif self.config['Architecture']['algorithm'] == "CAN":
                preds = self.model([images, image_mask, label])
            else:
                preds = self.model(images)
            post_result = self.post_process_class(preds)
            info = None
            if isinstance(post_result, dict):
                rec_info = dict()
                for key in post_result:
                    if len(post_result[key][0]) >= 2:
                        rec_info[key] = {
                            "label": post_result[key][0][0],
                            "score": float(post_result[key][0][1]),
                        }
                info = json.dumps(rec_info, ensure_ascii=False)
            elif isinstance(post_result, list) and isinstance(post_result[0],
                                                              int):
                # for RFLearning CNT branch 
                info = str(post_result[0])
            else:
                if len(post_result[0]) >= 2:
                    info = post_result[0][0] + "\t" + str(post_result[0][1])

            # if info is not None:
            #     print(info)
            # res_list.append( )
        return info.split("\t")

def main():
    global_config = config['Global']

    # build post process
    post_process_class = build_post_process(config['PostProcess'],
                                            global_config)

    # build model
    if hasattr(post_process_class, 'character'):
        char_num = len(getattr(post_process_class, 'character'))
        if config["Architecture"]["algorithm"] in ["Distillation",
                                                   ]:  # distillation model
            for key in config["Architecture"]["Models"]:
                if config["Architecture"]["Models"][key]["Head"][
                        "name"] == 'MultiHead':  # multi head
                    out_channels_list = {}
                    if config['PostProcess'][
                            'name'] == 'DistillationSARLabelDecode':
                        char_num = char_num - 2
                    if config['PostProcess'][
                            'name'] == 'DistillationNRTRLabelDecode':
                        char_num = char_num - 3
                    out_channels_list['CTCLabelDecode'] = char_num
                    out_channels_list['SARLabelDecode'] = char_num + 2
                    out_channels_list['NRTRLabelDecode'] = char_num + 3
                    config['Architecture']['Models'][key]['Head'][
                        'out_channels_list'] = out_channels_list
                else:
                    config["Architecture"]["Models"][key]["Head"][
                        "out_channels"] = char_num
        elif config['Architecture']['Head'][
                'name'] == 'MultiHead':  # multi head
            out_channels_list = {}
            char_num = len(getattr(post_process_class, 'character'))
            if config['PostProcess']['name'] == 'SARLabelDecode':
                char_num = char_num - 2
            if config['PostProcess']['name'] == 'NRTRLabelDecode':
                char_num = char_num - 3
            out_channels_list['CTCLabelDecode'] = char_num
            out_channels_list['SARLabelDecode'] = char_num + 2
            out_channels_list['NRTRLabelDecode'] = char_num + 3
            config['Architecture']['Head'][
                'out_channels_list'] = out_channels_list
        else:  # base rec model
            config["Architecture"]["Head"]["out_channels"] = char_num
    model = build_model(config['Architecture'])

    load_model(config, model)

    # create data ops
    transforms = []
    for op in config['Eval']['dataset']['transforms']:
        op_name = list(op)[0]
        if 'Label' in op_name:
            continue
        elif op_name in ['RecResizeImg']:
            op[op_name]['infer_mode'] = True
        elif op_name == 'KeepKeys':
            if config['Architecture']['algorithm'] == "SRN":
                op[op_name]['keep_keys'] = [
                    'image', 'encoder_word_pos', 'gsrm_word_pos',
                    'gsrm_slf_attn_bias1', 'gsrm_slf_attn_bias2'
                ]
            elif config['Architecture']['algorithm'] == "SAR":
                op[op_name]['keep_keys'] = ['image', 'valid_ratio']
            elif config['Architecture']['algorithm'] == "RobustScanner":
                op[op_name][
                    'keep_keys'] = ['image', 'valid_ratio', 'word_positons']
            else:
                op[op_name]['keep_keys'] = ['image']
        transforms.append(op)
    global_config['infer_mode'] = True
    ops = create_operators(transforms, global_config)

    save_res_path = config['Global'].get('save_res_path',
                                         "./weights/car_num_rec/predicts_ppocrv4.txt")
    if not os.path.exists(os.path.dirname(save_res_path)):
        os.makedirs(os.path.dirname(save_res_path))

    model.eval()

    with open(save_res_path, "w") as fout:
        for file in img_file:
            with open(file, 'rb') as f:
                img = f.read()
                data = {'image': img}
            batch = transform(data, ops)
            if config['Architecture']['algorithm'] == "SRN":
                encoder_word_pos_list = np.expand_dims(batch[1], axis=0)
                gsrm_word_pos_list = np.expand_dims(batch[2], axis=0)
                gsrm_slf_attn_bias1_list = np.expand_dims(batch[3], axis=0)
                gsrm_slf_attn_bias2_list = np.expand_dims(batch[4], axis=0)

                others = [
                    paddle.to_tensor(encoder_word_pos_list),
                    paddle.to_tensor(gsrm_word_pos_list),
                    paddle.to_tensor(gsrm_slf_attn_bias1_list),
                    paddle.to_tensor(gsrm_slf_attn_bias2_list)
                ]
            if config['Architecture']['algorithm'] == "SAR":
                valid_ratio = np.expand_dims(batch[-1], axis=0)
                img_metas = [paddle.to_tensor(valid_ratio)]
            if config['Architecture']['algorithm'] == "RobustScanner":
                valid_ratio = np.expand_dims(batch[1], axis=0)
                word_positons = np.expand_dims(batch[2], axis=0)
                img_metas = [
                    paddle.to_tensor(valid_ratio),
                    paddle.to_tensor(word_positons),
                ]
            if config['Architecture']['algorithm'] == "CAN":
                image_mask = paddle.ones(
                    (np.expand_dims(
                        batch[0], axis=0).shape), dtype='float32')
                label = paddle.ones((1, 36), dtype='int64')
            images = np.expand_dims(batch[0], axis=0)
            images = paddle.to_tensor(images)
            if config['Architecture']['algorithm'] == "SRN":
                preds = model(images, others)
            elif config['Architecture']['algorithm'] == "SAR":
                preds = model(images, img_metas)
            elif config['Architecture']['algorithm'] == "RobustScanner":
                preds = model(images, img_metas)
            elif config['Architecture']['algorithm'] == "CAN":
                preds = model([images, image_mask, label])
            else:
                preds = model(images)
            post_result = post_process_class(preds)
            info = None
            if isinstance(post_result, dict):
                rec_info = dict()
                for key in post_result:
                    if len(post_result[key][0]) >= 2:
                        rec_info[key] = {
                            "label": post_result[key][0][0],
                            "score": float(post_result[key][0][1]),
                        }
                info = json.dumps(rec_info, ensure_ascii=False)
            elif isinstance(post_result, list) and isinstance(post_result[0],
                                                              int):
                # for RFLearning CNT branch 
                info = str(post_result[0])
            else:
                if len(post_result[0]) >= 2:
                    info = post_result[0][0] + "\t" + str(post_result[0][1])
            print(info)

if __name__ == "__main__":
    ocr_rec = OCR_rec("./config/rec/en_PP-OCRv4_rec.yml")
    config = load_config("./configs/en_PP-OCRv4_rec.yml")
    img_file = ["./test_data/car_num.jpg"]
    # main()
    ocr_rec.load_checkpoint()
    img = cv2.imread("/home/zhenjue3/sr_work/20240412-155421.jpg")
    # img = cv2.resize(img, (480, 32))
    # cv2.imwrite("./1.jpg", img)
    info_stream = ocr_rec.predict([img])
    for info in info_stream:     
        # !!! 这个要增加ocr_tool中的筛选逻辑 目前只给了简单的置信度筛选     
        ocr_str, score_str = info.split("\t") 
        print(ocr_str, score_str)