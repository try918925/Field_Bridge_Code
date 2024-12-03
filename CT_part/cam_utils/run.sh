#!/bin/bash


export LD_LIBRARY_PATH="/home/root123/桌面/workspace/CT0704/cam_utils/lib/hikvision:${LD_LIBRARY_PATH}"
export LD_LIBRARY_PATH="/home/root123/桌面/workspace/CT0704/cam_utils/lib/deepstream-4.0:${LD_LIBRARY_PATH}"


python3 setup.py build_ext --inplace

#gdb python
CUDA_VISIBLE_DEVICES=0 python3 reader_test.py
