from str2bool import *
import argparse
import os
import sys
import addInstalldirToPath

# Why should we need to add the submodule to the path, just for the RIFE import to work
# Thanks for being consistently terrible, python
sys.path.insert(0, os.getcwd() + os.path.sep + 'arXiv2020RIFE')

from generalInterpolationProceedures import *

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
parser.add_argument('-gpuids', dest='gpuid', type=str, default="0")
parser.add_argument('-batch', dest='batchSize', type=int, default=1)

parser.add_argument('-step1', dest='step1', action='store_true')
parser.set_defaults(step1=False)
parser.add_argument('-step2', dest='step2', action='store_true')
parser.set_defaults(step2=False)
parser.add_argument('-step3', dest='step3', action='store_true')
parser.set_defaults(step3=False)
args = parser.parse_args()

selectedGPUs = str(args.gpuid).split(",")
selectedGPUs = [int(i) for i in selectedGPUs]

setGPUinterpolationOptions(args.batchSize, selectedGPUs)

print('Step1', args.step1, 'Step2', args.step2, 'Step3', args.step3)

projectFolder = args.inputFile[:args.inputFile.rindex(os.path.sep)]
if args.nonlocalpngs:
    projectFolder = installPath + os.path.sep + "tempFrames"
    if not os.path.exists(projectFolder):
        os.mkdir(projectFolder)

fpsDataFilePath = projectFolder + os.path.sep + 'fpsout.txt'

encoderConfig = EncoderConfig()
encoderConfig.setEncodingCRF(float(args.crfout))
if bool(args.useNvenc):
    encoderConfig.enableNvenc(True)
    encoderConfig.setEncodingPreset('slow')
encoderConfig.setNvencGPUID(selectedGPUs[0])

interpolatorConfig = InterpolatorConfig()

interpolatorConfig.setMode(args.mode)
interpolatorConfig.setClearPngs(args.clearpngs)
interpolatorConfig.setLoopable(args.loopable)

interpolatorConfig.setInterpolationFactor(args.interpolationFactor)
interpolatorConfig.setMpdecimateSensitivity(args.mpdecimateSensitivity)

interpolatorConfig.setNonlocalPngs(args.nonlocalpngs)
interpolatorConfig.setScenechangeSensitivity(args.scenechangeSensitivity)

if args.step1:
    performAllSteps(args.inputFile, interpolatorConfig, encoderConfig, step1=True, step2=False, step3=False)

if args.step2:
    performAllSteps(args.inputFile, interpolatorConfig, encoderConfig, step1=False, step2=True, step3=False)

if args.step3:
    performAllSteps(args.inputFile, interpolatorConfig, encoderConfig, step1=False, step2=False, step3=True)
