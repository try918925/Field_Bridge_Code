#!/bin/bash
source ~/anaconda3/bin/activate py310
CURRENT_PATH=$(readlink -f "$(dirname "$0")")
PYTHON_PATH=`which python`
PYTHON_BIN_DIR=`dirname $PYTHON_PATH`
PYTHON_HOME=`dirname $PYTHON_BIN_DIR`

export LD_LIBRARY_PATH="${CURRENT_PATH}/cam_utils/lib/deepstream-4.0:${PYTHON_HOME}/lib"
export LD_LIBRARY_PATH="${CURRENT_PATH}/cam_utils/lib/hikvision:${LD_LIBRARY_PATH}"
python cam_utils/setup.py build_ext --inplace

python ./workers/test_158.py
# python msg_manager.py