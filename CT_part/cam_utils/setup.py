import sys
import os
# ----------------------------------------
from setuptools import setup, Extension
# --------------------------------------------------


PYTHON_HOME = os.path.abspath(os.path.dirname(os.path.dirname(sys.executable)))
BASE_SOURCE_DIR = os.path.abspath(os.path.dirname(__file__))


exts_hkws = Extension(
    name='cam_utils.camsdk.hksdk.HKSDK',
    language='c++',
    extra_compile_args=[
        '-std=c++11',
        '-pthread'
    ],
    include_dirs=[
        os.path.join(BASE_SOURCE_DIR, 'include'),
        # os.path.join(PYTHON_HOME, 'include/python3.6m'),
        os.path.join(PYTHON_HOME, 'include')
    ],
    libraries=[
        'hcnetsdk', 'PlayCtrl',
    ],
    library_dirs=[
        # BASE_SOURCE_DIR,
        os.path.join(PYTHON_HOME, 'lib'),
        os.path.join(BASE_SOURCE_DIR, 'lib/hikvision'),
    ],
    sources=[
        'cam_utils/camsdk/hksdk/HKSDK.cpp'
    ]
)

setup(
    name='py310',
    ext_modules=[
        exts_hkws,
    ]
)
