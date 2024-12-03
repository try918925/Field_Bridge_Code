#!/bin/bash
source ~/anaconda3/bin/activate py310

export LD_LIBRARY_PATH="/home/hnks/hjk_work/rtsp_reader/lib/hikvision:${LD_LIBRARY_PATH}"
export LD_LIBRARY_PATH="/home/hnks/hjk_work/rtsp_reader/lib/deepstream-4.0:${LD_LIBRARY_PATH}"


python3 setup.py build_ext --inplace

#gdb python
CUDA_VISIBLE_DEVICES=0 python3 reader_test.py
