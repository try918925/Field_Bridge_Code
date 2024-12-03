from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np

import os
import sys
import json

__dir__ = os.path.dirname(os.path.abspath(__file__))
sys.path.append(__dir__)
sys.path.insert(0, os.path.abspath(os.path.join(__dir__, '..')))

os.environ["FLAGS_allocator_strategy"] = 'auto_growth'

import paddle
import subprocess
import tracemalloc
from ppocr.data import create_operators, transform
from ppocr.modeling.architectures import build_model
from ppocr.postprocess import build_post_process
from ppocr.utils.save_load import load_model
from ppocr.utils.utility import get_image_file_list

import cv2
import yaml
import ocr_tool as ocr_check
from collections import Counter
from itertools import zip_longest


def draw_det_res(dt_boxes, img, img_name, save_path):
    src_im = img
    for box in dt_boxes:
        box = np.array(box).astype(np.int32).reshape((-1, 1, 2))
        cv2.polylines(src_im, [box], True, color=(255, 255, 0), thickness=2)
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    save_path = os.path.join(save_path, os.path.basename(img_name))
    cv2.imwrite(save_path, src_im)


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


def merge_config(config, opts):
    """
    Merge config into global config.
    Args:
        config (dict): Config to be merged.
    Returns: global config
    """
    for key, value in opts.items():
        if "." not in key:
            if isinstance(value, dict) and key in config:
                config[key].update(value)
            else:
                config[key] = value
        else:
            sub_keys = key.split('.')
            assert (
                    sub_keys[0] in config
            ), "the sub_keys can only be one of global_config: {}, but get: " \
               "{}, please check your running command".format(
                config.keys(), sub_keys[0])
            cur = config[sub_keys[0]]
            for idx, sub_key in enumerate(sub_keys[1:]):
                if idx == len(sub_keys) - 2:
                    cur[sub_key] = value
                else:
                    cur = cur[sub_key]
    return config


class Detection:
    def __init__(self, config_path):
        # self.config, self.device, self.logger, self.vdl_writer = self.program.preprocess()
        self.config = load_config(config_path)
        self.global_config = self.config['Global']

    def load_checkpoint(self):
        self.model = build_model(self.config['Architecture'])

        load_model(self.config, self.model)
        # build post process
        self.post_process_class = build_post_process(self.config['PostProcess'])
        self.transforms = []
        for op in self.config['Eval']['dataset']['transforms']:
            op_name = list(op)[0]
            if 'Label' in op_name:
                continue
            elif op_name == 'KeepKeys':
                op[op_name]['keep_keys'] = ['image', 'shape']
            self.transforms.append(op)
        self.ops = create_operators(self.transforms, self.global_config)
        self.model.eval()

    def _predict2box(self, img):
        data = {'image': img}
        batch = transform(data, self.ops)

        images = np.expand_dims(batch[0], axis=0)
        shape_list = np.expand_dims(batch[1], axis=0)
        images = paddle.to_tensor(images)

        preds = self.model(images)
        post_result, score = self.post_process_class(preds, shape_list)
        boxes = post_result[0]['points']
        return boxes, score

    def predict(self, img_list):
        img_box = []
        box_scores = []
        for img_data in img_list:
            _, encoded_image = cv2.imencode(".jpg", img_data)
            img = encoded_image.tobytes()
            box, score = self._predict2box(img)
            box_scores.append(score)
            img_box.append(box)

        return img_box, box_scores


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
        for img_data in img_list:  # get_image_file_list(img_path):
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
            yield info


class OCR_process(object):
    def __init__(self, config_dict):
        # 文本检测
        self.ocr_det = Detection(config_dict["ocr_det_config"])
        self.ocr_det.load_checkpoint()

        self.ocr_rec = OCR_rec(config_dict["ocr_rec_config"])
        self.ocr_rec.load_checkpoint()

        self.debug_show = False

    def test_per_img(self, img):
        flag, crop_img_list, result_list = False, [], []
        # result_list [[container_id_1, iso_num_1], [, ]] 
        boxes = self.ocr_det.predict([img])
        if len(boxes) > 0:
            flag = True
            for box in boxes[0]:
                x1 = box[0][0]
                y1 = box[0][1]
                x2 = box[2][0]
                y2 = box[2][1]
                crop_img = img[y1: y2, x1: x2]
                if (y2 - y1) > (x2 - x1):
                    crop_img = cv2.rotate(crop_img, cv2.ROTATE_90_COUNTERCLOCKWISE)
                crop_img_list.append(crop_img)

            info_stream = self.ocr_rec.predict(crop_img_list)

            for info in info_stream:
                ocr_str, score_str = info.split("\t")
                result_list.append([ocr_str, score_str])

            if self.debug_show:
                import uuid
                import copy
                img_debug = copy.deepcopy(img)
                if len(result_list) > 0:
                    for i, result in enumerate(result_list):
                        x1, y1 = boxes[0][i][0][0], boxes[0][i][0][1]
                        x2, y2 = boxes[0][i][2][0], boxes[0][i][2][1]
                        ocr_str = result[0]
                        score_str = result[1]
                        img_debug = cv2.rectangle(img_debug, (x1, y1), (x2, y2), (128, 128, 0), 2)
                        img_debug = cv2.putText(img_debug, ocr_str + " : " + score_str[:4], (x2, y2),
                                                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (128, 128, 0), 2)

                    cv2.imwrite(f"{uuid.uuid1()}.jpg", img_debug)

        return flag, result_list

    def sort_boxes(self, boxes):
        # 定义排序规则的函数
        def box_sort_key(box):
            return (box[0][1], box[0][0])  # 先按照y，再按照x

        sorted_boxes = sorted(boxes, key=box_sort_key)
        return sorted_boxes

    def clearbox(self, boxes):
        newbox = []
        for box in boxes:
            if len(box) == 0:
                continue
            for i in box:
                newbox.append(i.tolist())
        return newbox

    def process_imgs(self, img_list):
        # 待补充逻辑：一组图片输入时取最终结果
        result_list = []
        result_item = ["", ""]  # 箱号，iso号
        score_item = [0, 0]
        boxes, scores = self.ocr_det.predict(img_list)
        # print(torch.cuda.memory_summary(device=None, abbreviated=False))
        # result = subprocess.run(['nvidia-smi'], stdout=subprocess.PIPE)
        # print(result.stdout.decode('utf-8'))        
        import time
        data1 = []
        data2 = []
        # newboxes = self.clearbox(boxes)
        # print(newboxes)
        # sortboxes = self.sort_boxes(newboxes) 
        # print(sortboxes)

        for i, i_boxes in enumerate(boxes):
            crop_img_list = []
            score_det = scores[i]
            sortboxes = self.sort_boxes(i_boxes)
            for j in range(len(sortboxes)):
                bbox_info = get_bbox_info(sortboxes[j])
                crop_img = rectify_crop(img_list[i], bbox_info)
                # cv2.imwrite(f'/home/zhenjue3/xcy_temp_work/gxg/door_cemian_ocr/gxg_ocr/test/{time.time()}_{save_name}', crop_img)
                crop_img_list.append(crop_img)

            # 👇👇👇👇👇👇👇👇👇👇👇👇👇👇👇👇👇👇👇👇👇👇👇👇👇 #
            # 原来的bbox crop

            # for i, i_boxes in enumerate(boxes):

            #     # 单张图片里的文本检测bboxes
            #     crop_img_list = []
            #     result_item = ["", ""] # 箱号，iso号
            #     score_item = [0, 0]
            #     img = img_list[i]

            #     score_det = scores[i]
            #     sortboxes = self.sort_boxes(i_boxes)
            #     for box in sortboxes:
            #         x_coords = [point[0] for point in box]
            #         y_coords = [point[1] for point in box]

            #         # 计算x和y的最小值和最大值
            #         min_x = min(x_coords)
            #         max_x = max(x_coords)
            #         min_y = min(y_coords)
            #         max_y = max(y_coords)

            #         crop_img = img[max(min_y - 15, 0):min(max_y + 15, img.shape[0]), max(min_x - 15, 0):min(max_x + 15, img.shape[1])]

            #         if (max_y - min_y) > (max_x - min_x):
            #             crop_img = cv2.rotate(crop_img, cv2.ROTATE_90_COUNTERCLOCKWISE)
            #         crop_img_list.append(crop_img)

            # 原来的bbox crop
            # 👆👆👆👆👆👆👆👆👆👆👆👆👆👆👆👆👆👆👆👆👆👆👆👆👆 #

            info_stream = self.ocr_rec.predict(crop_img_list)
            # current, peak = tracemalloc.get_traced_memory()
            # print(f"Current memory usage: {current / 10**6} MB")
            # print(f"Peak memory usage: {peak / 10**6} MB")
            # result = subprocess.run(['nvidia-smi'], stdout=subprocess.PIPE)
            # print(result.stdout.decode('utf-8'))   

            fflag = False
            fglag = False
            for info in info_stream:
                # !!! 这个要增加ocr_tool中的筛选逻辑 目前只给了简单的置信度筛选     
                ocr_str, score_str = info.split("\t")
                score = float(score_str)

                # print(ocr_str, score_str)

                #######################################################
                if len(ocr_str) == 4 and 'U' in ocr_str and not fglag:
                    contain_alpht = ocr_str
                    fflag = True
                    continue
                if fflag:
                    fflag = False
                    # if ocr_str.isdigit():
                    ocr_str = contain_alpht + ocr_str

                if (len(ocr_str) == 6 or len(ocr_str) == 7) and ocr_str.isdigit():
                    fglag = True
                    digit_ocr = ocr_str
                    continue
                if fglag:
                    fglag = False
                    if (len(ocr_str) == 4 and 'U' in ocr_str):
                        ocr_str = ocr_str + digit_ocr

                #########################################################
                if not ocr_check.isPartOfContainerCode(ocr_str) and not ocr_check.check_95code(ocr_str):
                    continue
                # print(info.split("\t") , result_item, score_item)

                # # 该过程判断三段式箱号 即 4+7这种结构
                # if len(ocr_str) == 4 and 'U' in ocr_str:
                #     contain_alpht = ocr_str
                #     fflag = True
                #     continue
                # if fflag:
                #     fflag =False

                #     ocr_str = contain_alpht + ocr_str

                # 判断箱号以及格式
                if len(ocr_str) > 5 and score > (score_item[0] - 0.1):
                    check_flag = ocr_check.check_Container_code(ocr_str)
                    if check_flag:
                        result_item[0] = ocr_str
                        score_item[0] = score
                        data1.append(ocr_str)
                # 判断iso
                if len(ocr_str) <= 4 and score > (score_item[1] - 0.1) and ocr_check.check_95code(ocr_str):
                    result_item[1] = ocr_str
                    score_item[1] = score
                    data2.append(ocr_str)

        final_result1 = getstr(data1)
        ocr_flag = ocr_check.check_Container_code(final_result1)

        if (ocr_flag == "0"):
            check_4_flag = True
            if len(final_result1) == 10:
                top_4 = final_result1[0:4]

                for alp in top_4:
                    if alp.isalpha() is False:
                        check_4_flag = False

                if check_4_flag:
                    new_check = ocr_check.check_code_count(final_result1)
                    final_result1 = final_result1 + new_check
            new_check = ocr_check.check_code_count(final_result1[:-1])
            # print("right check mode:", new_check)
            final_result1 = final_result1[:-1] + new_check
        final_result2 = getstr(data2)

        draw = True

        if len(final_result1) != 11:
            final_result1 = ''
            draw = False
        if len(final_result2) != 4:
            draw = False
            final_result2 = ''
        # del img_list
        # del boxes
        # del info_stream

        # draw_det_res(i_boxes, img_list[i], f'{final_result1}-{final_result2}_{save_name}', '/home/zhenjue3/xcy_temp_work/gxg/door_cemian_ocr/gxg_ocr/test/test_result')

        return final_result1, final_result2, score_item


def getstr(strlist):
    transposed_data = list(zip_longest(*strlist, fillvalue=''))
    # print(transposed_data)
    result = [Counter(column).most_common(1)[0][0] for column in transposed_data]
    final_result1 = ''.join(result)
    return final_result1


def distance(point1, point2):
    point1 = np.array(point1)
    point2 = np.array(point2)
    return np.linalg.norm(point2 - point1)


def dis_axis(pt1, pt2, axis):
    if axis == 'x':
        return abs(pt2[0] - pt1[0])
    elif axis == 'y':
        return abs(pt2[1] - pt1[1])


def get_bbox_info(box):
    info_dict = {}
    if len(box) > 3:
        distances = [distance(box[i], box[(i + 1) % 4]) for i in range(4)]
        short_side = int(min(distances))
        long_side = int(max(distances))

        dis_x = [dis_axis(box[i], box[(i + 1) % 4], 'x') for i in range(4)]
        dis_y = [dis_axis(box[i], box[(i + 1) % 4], 'y') for i in range(4)]

        img_horizontal = abs(max(dis_x) - min(dis_x)) > abs(max(dis_y) - min(dis_y))

        if not img_horizontal:
            sorted_by_y = sorted(box, key=lambda x: x[1], reverse=True)
            sorted_lst_down = sorted(sorted_by_y[:2], key=lambda m: m[0])
            sorted_lst_top = sorted(sorted_by_y[2:], key=lambda m: m[0])

            left_down = sorted_lst_down[0]
            right_down = sorted_lst_down[1]
            left_top = sorted_lst_top[0]
            right_top = sorted_lst_top[1]

        else:
            sorted_by_x = sorted(box, key=lambda x: x[0])
            sorted_lst_left = sorted(sorted_by_x[:2], key=lambda m: m[1])
            sorted_lst_right = sorted(sorted_by_x[2:], key=lambda m: m[1])

            left_down = sorted_lst_left[1]
            right_down = sorted_lst_right[1]
            left_top = sorted_lst_left[0]
            right_top = sorted_lst_right[0]

        info_dict = {
            'bbox_long': long_side,
            'bbox_short': short_side,
            'ori_pt': [left_top, right_top, right_down, left_down],
            'is_vertical': not img_horizontal
        }
    return info_dict


def rectify_crop(img, info):
    h, w = img.shape[:2]
    left_top, right_top, right_down, left_down = info['ori_pt']
    if info['is_vertical']:
        crop_h = info['bbox_long']
        crop_w = info['bbox_short']
    else:
        crop_h = info['bbox_short']
        crop_w = info['bbox_long']

    new_ld = left_down
    new_lt = [new_ld[0], new_ld[1] - crop_h]
    new_rt = [new_ld[0] + crop_w, new_ld[1] - crop_h]
    new_rd = [new_ld[0] + crop_w, new_ld[1]]

    pts1 = np.array([left_top, right_top, right_down, left_down], dtype=np.float32)
    pts2 = np.array([new_lt, new_rt, new_rd, new_ld], dtype=np.float32)

    M = cv2.getPerspectiveTransform(pts1, pts2)

    dst = cv2.warpPerspective(img, M, (w, h))

    new_crop = dst[max(new_lt[1] - 8, 0):min(new_ld[1] + 8, h), max(new_lt[0] - 8, 0):min(new_rt[0] + 8, w)]

    if info['is_vertical']:
        new_crop = cv2.rotate(new_crop, cv2.ROTATE_90_COUNTERCLOCKWISE)
    # import time
    # cv2.imwrite(f'/home/zhenjue3/xcy_temp_work/gxg/door_cemian_ocr/gxg_ocr/test/test_result/{time.time()}.jpg', new_crop)
    return new_crop


# from pympler import asizeof
if __name__ == "__main__":
    # 参数文件传入

    # tracemalloc.start()

    config_dict = {
        "ocr_det_config": "/home/zhenjue4/xcy_work/guangxigang/gxg_ocr/configs/door_container_num_det_r50_db++_td_tr.yml",
        "ocr_rec_config": "/home/zhenjue4/xcy_work/guangxigang/gxg_ocr/configs/door_container_num_rec_en_PP-OCRv3.yml"
        # "ocr_h_rec_config": "./config/rec/my_en_PP-OCRv3_rec.yml",
        # "ocr_v_rec_config": "./config/rec/my_en_PP-OCRv3_rec.yml"
    }
    my_ocr_process = OCR_process(config_dict)

    img = cv2.imread("/home/zhenjue4/xcy_work/guangxigang/OCR/1/BD_1713579019.1728804_0.jpg")
    # img_list.append(img)
    # flag, result = my_ocr_process.process_imgs([img])
    # if flag:
    print(my_ocr_process.process_imgs([img]))

    # img = cv2.imread("/home/hj1/sr/OCR/test/ID_left1.jpg") 
    # img_list.append(img)
    # flag, result = my_ocr_process.test_per_img(img)
    # if flag:
    #     print(result)

    # img = cv2.imread("/home/hj1/sr/OCR/test/rear.jpg") 
    # img_list.append(img)
    # flag, result = my_ocr_process.test_per_img(img)
    # if flag:
    #     print(result)

    # process = psutil.Process()
    # imgtest = cv2.imread("/home/hj1/sr/OCR/what/frame_20231206163336597947.jpg")
    # my_ocr_process.test_per_img(imgtest)

    # for i in range(4):
    #     # memory_usage = asizeof.asizeof(my_ocr_process)/10**6
    #     # print(memory_usage)
    #     strlist = ['what', 'xz','new','test']
    #     img_list = []
    #     imgfile_path = "/home/zhenjue3/sr_work/ocr_data_extern/" + strlist[i] + "/"
    #     filelist = os.listdir(imgfile_path)

    #     for file in filelist:
    #         img_path = imgfile_path + file
    #         img = cv2.imread(img_path)
    #         # img = cv2.rotate(img,cv2.ROTATE_90_COUNTERCLOCKWISE)
    #         img_list.append(img)

    #     results = my_ocr_process.process_imgs(img_list)
    #     print(results)

    # del img_list
    # memory_usage = asizeof.asizeof(my_ocr_process)/10**6
    # print("aaa", memory_usage)
    # paddle.device.cuda.empty_cache()
    # current, peak = tracemalloc.get_traced_memory()
    # print(f"out of Current memory usage: {current / 10**6} MB")
    # print(f"out of Peak memory usage: {peak / 10**6} MB")
    # print(results)
    # traceback_output = tracemalloc.get_object_traceback(my_ocr_process.process_imgs)

    # memory_info = process.memory_info()
    # print(memory_info)
    # tracemalloc.stop()
