import os
import shutil

from generalInterpolationProceedures import extractFrames,generateLoopContinuityFrame,createOutput
from FFmpegFunctions import *
inputFolder = r'D:\Videos\test'
inputFile = r'D:\Videos\test\2020-08-10 18.38.30.mov'

def test_extract_frames():
    mode = 3
    extractFrames(inputFile,inputFolder,mode)
    mode = 1
    extractFrames(inputFile, inputFolder, mode)

    framesFolder = inputFolder + r'\original_frames'
    generateLoopContinuityFrame(framesFolder)
    assert True

def test_createOutput():
    mode = 1
    extractFrames(inputFile,inputFolder,mode)
    shutil.move(inputFolder + os.path.sep + 'original_frames',
                inputFolder + os.path.sep + 'interpolated_frames')
    createOutput(inputFile,inputFolder,'out-unittest.mp4',getFPS(inputFile),
                 False,mode,20,True)

    shutil.rmtree(inputFolder + os.path.sep + 'interpolated_frames')
    mode = 3
    extractFrames(inputFile, inputFolder, mode)
    shutil.move(inputFolder + os.path.sep + 'original_frames',
                inputFolder + os.path.sep + 'interpolated_frames')
    createOutput(inputFile, inputFolder, 'out-unittest.mp4', getFPS(inputFile),
                 True, mode, 20, True)