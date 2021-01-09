import os
import sys

# Why should we need to add the submodule to the path, just for the RIFE import to work
# Thanks for being consistently terrible, python
sys.path.insert(0, os.getcwd() + os.path.sep + 'arXiv2020RIFE')
print(sys.path)

inputFile = r'D:\Videos\test\2020-08-10 18.38.30.mov'

from generalInterpolationProceedures import *

def test_interpolation():
    print('HELLO PYTHON?!?!?!?!?',os.getcwd())
    setupRIFE(os.getcwd(),1)
    setNvencSettings(1,'p7')
    performAllSteps(inputFile,2,False,3,20,True,True,0.2,"64*12,64*8,0.33",True)