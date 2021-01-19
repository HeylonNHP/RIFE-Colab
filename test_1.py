import os
import sys
from QueuedFrames import *
sys.path.insert(0, os.getcwd() + os.path.sep + 'arXiv2020RIFE')
from rifeInterpolationFunctions import *

# Why should we need to add the submodule to the path, just for the RIFE import to work
# Thanks for being consistently terrible, python
sys.path.insert(0, os.getcwd() + os.path.sep + 'arXiv2020RIFE')
print(sys.path)

inputFile = r'D:\Videos\test\2020-08-10 18.38.30.mov'

from generalInterpolationProceedures import *
'''
def test_interpolation():
    print('HELLO PYTHON?!?!?!?!?',os.getcwd())
    setupRIFE(os.getcwd(),1)
    setNvencSettings(1,'p7')
    performAllSteps(inputFile,2,False,3,20,True,True,0.2,"64*12,64*8,0.33",True)
'''
def test_hbd():
    ff = FrameFile(r'C:\Users\Heylon\Desktop\hbdTest\1_f32.png')
    ff.loadImageData()
    ff.filePath = r'C:\Users\Heylon\Desktop\hbdTest\out.png'
    ff.saveImageData()

    ff1 = FrameFile(r'C:\Users\Heylon\Desktop\hbdTest\1_f32.png')
    ff3 = FrameFile(r'C:\Users\Heylon\Desktop\hbdTest\3_f32.png')

    ff2 = FrameFile(r'C:\Users\Heylon\Desktop\hbdTest\2_f32.png')

    ff1.loadImageData()
    ff3.loadImageData()

    device,model = setupRIFE(os.getcwd(),0)
    ff2 = rifeInterpolate(device, model, ff1, ff3, ff2)
    ff2.saveImageData()


