from str2bool import *
import argparse
parser = argparse.ArgumentParser(description='Interpolation for video input')
parser.add_argument('-i', dest='inputFile', type=str, default=None)
parser.add_argument('-if', dest='interpolationFactor', type=int, default=2)
parser.add_argument('-loop', dest='loopable', type=str2bool, default=False)
parser.add_argument('-mode', dest='mode', type=int, default=3)
parser.add_argument('-crf', dest='crfout', type=int, default=20)
parser.add_argument('-clearpngs', dest='clearpngs', type=str2bool, default=False)
parser.add_argument('-nonlocalpngs', dest='nonlocalpngs', type=str2bool, default=False)
parser.add_argument('-scenesens', dest='scenechangeSensitivity', type=float, default=0.2)
parser.add_argument('-mpdecimate', dest='mpdecimateSensitivity', type=str, default="64*12,64*8,0.33")
parser.add_argument('-usenvenc', dest='useNvenc', type=str2bool, default=False)
parser.add_argument('-gpuid', dest='gpuid', type=int, default=0)

parser.add_argument('-step1', dest='step1', action='store_true')
parser.set_defaults(step1=False)
parser.add_argument('-step2', dest='step2', action='store_true')
parser.set_defaults(step2=False)
parser.add_argument('-step3', dest='step3', action='store_true')
parser.set_defaults(step3=False)
args = parser.parse_args()

import os
import sys

# Why should we need to add the submodule to the path, just for the RIFE import to work
# Thanks for being consistently terrible, python
sys.path.insert(0, os.getcwd() + os.path.sep + 'arXiv2020RIFE')

from generalInterpolationProceedures import *
setupRIFE(os.getcwd(),args.gpuid)
setNvencSettings(args.gpuid,'p7')

print('Step1',args.step1,'Step2',args.step2,'Step3',args.step3)

projectFolder = args.inputFile[:args.inputFile.rindex(os.path.sep)]
if args.nonlocalpngs:
    projectFolder = installPath + os.path.sep + "tempFrames"
    if not os.path.exists(projectFolder):
        os.mkdir(projectFolder)

fpsDataFilePath = projectFolder + os.path.sep + 'fpsout.txt'

if args.step1:
    # Clear pngs if they exist
    if os.path.exists(projectFolder + '/' + 'original_frames'):
        shutil.rmtree(projectFolder + '/' + 'original_frames')

    if os.path.exists(projectFolder + '/' + 'interpolated_frames'):
        shutil.rmtree(projectFolder + '/' + 'interpolated_frames')

    extractFrames(args.inputFile, projectFolder, args.mode, args.mpdecimateSensitivity)

if args.step2:
    outParams = runInterpolator(args.inputFile, projectFolder, args.interpolationFactor, args.loopable, args.mode, args.scenechangeSensitivity)
    print('---INTERPOLATION DONE---')
    fpsFile = open(fpsDataFilePath,'w')
    fpsFile.write(str(outParams[0]))
    fpsFile.close()

if args.step3:
    fpsFile = open(fpsDataFilePath,'r')
    outputFPS = float(fpsFile.readline())
    fpsFile.close()
    outputVideoName = args.inputFile[:args.inputFile.rindex(os.path.sep) + 1]
    outputVideoName += '{:.2f}fps-{}x-mode{}-rife-output.mp4'.format(outputFPS, args.interpolationFactor, args.mode)

    createOutput(args.inputFile, projectFolder, outputVideoName, outputFPS, args.loopable, args.mode, args.crfout, args.useNvenc)

    if args.clearpngs:
        shutil.rmtree(projectFolder + '/' + 'original_frames')
        shutil.rmtree(projectFolder + '/' + 'interpolated_frames')