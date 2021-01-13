import math
import os
import shutil
import traceback
from queue import Queue

from runAndPrintOutput import runAndPrintOutput
from FFmpegFunctions import *
from frameChooser import chooseFrames
FFMPEG4 = 'ffmpeg'
GPUID = 0
nvencPreset = 'p7'
installPath = os.getcwd()
print('INSTALL:',installPath)

# Check if running on Windows or not
onWindows = None
if os.name == 'nt':
    onWindows = True
else:
    onWindows = False

# Get and initialise RIFE
from rifeFunctions import downloadRIFE
downloadRIFE(installPath,onWindows)
os.chdir(installPath)
from rifeInterpolationFunctions import *

def setFFmpeg4Path(path):
    global FFMPEG4
    FFMPEG4 = path
    setFFmpegLocation(FFMPEG4)

def setNvencSettings(nvencGpuID,preset):
    global GPUID
    global nvencPreset
    GPUID = nvencGpuID
    nvencPreset = preset

def extractFrames(inputFile, projectFolder, mode, mpdecimateSensitivity="64*12,64*8,0.33"):
    '''
    Equivalent to DAINAPP Step 1
    '''
    os.chdir(projectFolder)
    if os.path.exists("original_frames"):
        shutil.rmtree("original_frames")
    if not os.path.exists("original_frames"):
        os.mkdir("original_frames")

    if mode == 1:
        runAndPrintOutput([FFMPEG4,'-i',inputFile,'-map_metadata','-1','-pix_fmt','rgb24','original_frames/%15d.png'])
    elif mode == 3 or mode == 4:
        hi, lo, frac = mpdecimateSensitivity.split(",")
        mpdecimate = "mpdecimate=hi={}:lo={}:frac={}".format(hi, lo, frac)
        runAndPrintOutput([FFMPEG4,'-i',inputFile,'-map_metadata','-1','-pix_fmt','rgb24','-copyts','-r','1000','-vsync','0','-frame_pts','true','-vf', mpdecimate,'-qscale:v','1','original_frames/%15d.png'])


def runInterpolator(inputFile, projectFolder, interpolationFactor, loopable, mode, scenechangeSensitivity):
    '''
    Equivalent to DAINAPP Step 2
    '''
    os.chdir(installPath + '/arXiv2020RIFE/')
    origFramesFolder = projectFolder + '/' + "original_frames"
    interpFramesFolder = projectFolder + '/' + "interpolated_frames"

    if not os.path.exists(interpFramesFolder):
        os.mkdir(interpFramesFolder)

    # Get output FPS
    outputFPS = 0
    if mode == 1 or mode == 3:
        outputFPS = getFPSaccurate(inputFile) * interpolationFactor
    elif mode == 4:
        outputFPS = (getFrameCount(inputFile, True) / getLength(inputFile)) * interpolationFactor

    # Loopable
    if loopable:
        generateLoopContinuityFrame(origFramesFolder)

    files = os.listdir(origFramesFolder)
    files.sort()

    framesQueue = Queue()

    if mode == 1:

        count = 0
        shutil.copy(origFramesFolder + '/' + files[0], interpFramesFolder + '/' + '{:015d}.png'.format(count))

        for i in range(0, len(files) - 1):
            print("Interpolating frame:", i + 1, "Of", len(files), "{:.2f}%".format(((i + 1) / len(files)) * 100))
            shutil.copy(origFramesFolder + '/' + files[i], interpFramesFolder + '/' + '{:015d}.png'.format(count))
            shutil.copy(origFramesFolder + '/' + files[i + 1],
                        interpFramesFolder + '/' + '{:015d}.png'.format(count + interpolationFactor))

            currentFactor = interpolationFactor

            while currentFactor > 1:
                period = int(interpolationFactor / currentFactor)
                for j in range(0, period):
                    offset = int(currentFactor * j)
                    beginFrame = interpFramesFolder + '/' + '{:015d}.png'.format(count + offset)
                    endFrame = interpFramesFolder + '/' + '{:015d}.png'.format(count + currentFactor + offset)
                    middleFrame = interpFramesFolder + '/' + '{:015d}.png'.format(
                        count + int(currentFactor / 2) + offset)
                    rifeInterpolate(beginFrame, endFrame, middleFrame, scenechangeSensitivity)
                currentFactor = int(currentFactor / 2)

            count += interpolationFactor

    elif mode == 3 or mode == 4:
        count = 0
        shutil.copy(origFramesFolder + '/' + files[0], interpFramesFolder + '/' + '{:015d}.png'.format(count))
        # To ensure no duplicates on the output with the new VFR to CFR algorithm, double the interpolation factor. TODO: Investigate
        modeModOutputFPS = outputFPS
        if mode == 3:
            interpolationFactor = interpolationFactor * 2
            modeModOutputFPS = modeModOutputFPS * 2
        for i in range(0, len(files) - 1):

            localInterpolationFactor = interpolationFactor
            # If mode 3, calculate interpolation factor on a per-frame basis to maintain desired FPS

            beginFrameTime = int(files[i][:-4])
            endFrameTime = int(files[i + 1][:-4])
            timeDiff = endFrameTime - beginFrameTime
            if mode == 3:
                localInterpolationFactor = 2

                while 1 / (((endFrameTime - beginFrameTime) / localInterpolationFactor) / 1000) < modeModOutputFPS:
                    localInterpolationFactor = int(localInterpolationFactor * 2)

            print("Interpolating frame:", i + 1, "Of", len(files), "{:.2f}%".format(((i + 1) / len(files)) * 100),
                  "Frame interp. factor", "{}x".format(localInterpolationFactor))

            # Get timecodes of both working frames
            currentTimecode = int(files[i][:-4])
            nextTimecode = int(files[i + 1][:-4])

            shutil.copy(origFramesFolder + '/' + files[i],
                        interpFramesFolder + '/' + '{:015d}.png'.format(currentTimecode))
            shutil.copy(origFramesFolder + '/' + files[i + 1],
                        interpFramesFolder + '/' + '{:015d}.png'.format(nextTimecode))

            currentFactor = localInterpolationFactor

            while currentFactor > 1:
                period = int(round(localInterpolationFactor / currentFactor))
                for j in range(0, period):
                    # Get offset from the first frame
                    offset = (timeDiff / period) * j
                    # print(currentTimecode,offset, "j ",j)
                    # Time difference between 'begin' and 'end' frames relative to current interpolation factor (Block size)
                    currentFactor2 = (currentFactor / localInterpolationFactor) * timeDiff
                    beginFrameTime = int(currentTimecode + offset)
                    endFrameTime = int(currentTimecode + currentFactor2 + offset)
                    middleFrameTime = int(currentTimecode + (currentFactor2 / 2) + offset)

                    beginFrame = interpFramesFolder + '/' + '{:015d}.png'.format(beginFrameTime)
                    endFrame = interpFramesFolder + '/' + '{:015d}.png'.format(endFrameTime)
                    middleFrame = interpFramesFolder + '/' + '{:015d}.png'.format(middleFrameTime)

                    # print("times",beginFrameTime,middleFrameTime,endFrameTime)
                    rifeInterpolate(beginFrame, endFrame, middleFrame, scenechangeSensitivity)
                currentFactor = int(currentFactor / 2)

            # count += interpolationFactor
    # Loopable
    if loopable:
        removeLoopContinuityFrame(interpFramesFolder)

    return [outputFPS]

def queueThreadInterpolator(framesQueue:Queue):
    pass

def createOutput(inputFile, projectFolder, outputVideo, outputFPS, loopable, mode, crfout, useNvenc):
    '''
    Equivalent to DAINAPP Step 3
    '''
    os.chdir(projectFolder)
    maxLoopLength = 15
    preferredLoopLength = 10
    inputLength = getLength(inputFile)

    inputFFmpeg = ""

    encoderPreset = ['-pix_fmt','yuv420p','-c:v','libx264','-preset','veryslow',
                     '-crf','{}'.format(crfout)]
    ffmpegSelected = FFMPEG4
    if useNvenc:
        encoderPreset = ['-pix_fmt','yuv420p','-c:v','h264_nvenc','-gpu',str(GPUID),'-preset',str(nvencPreset),'-profile','high','-rc','vbr','-b:v','0','-cq',str(crfout + 10)]
        ffmpegSelected = 'ffmpeg'

    if mode == 1:
        inputFFmpeg = ['-r',str(outputFPS),'-i','interpolated_frames/%15d.png']
    if mode == 3 or mode == 4:
        # generateTimecodesFile(projectFolder)
        chooseFrames(projectFolder + os.path.sep + "interpolated_frames", outputFPS)
        inputFFmpeg = ['-vsync','1','-r',str(outputFPS),'-f','concat','-safe','0','-i','interpolated_frames/framesCFR.txt']

    if loopable == False or (maxLoopLength / float(inputLength) < 2):
        # Don't loop, too long input
        print('Dont loop', maxLoopLength / float(inputLength))

        command = [ffmpegSelected,'-hide_banner','-stats','-loglevel','error','-y']
        command = command + inputFFmpeg
        command = command + ['-i', str(inputFile),'-map','0','-map','1:a?','-vf','pad=ceil(iw/2)*2:ceil(ih/2)*2']
        command = command + encoderPreset + [str(outputVideo)]

        runAndPrintOutput(command)
    else:
        loopCount = math.ceil(preferredLoopLength / float(inputLength)) - 1
        loopCount = str(loopCount)
        print('Loop', loopCount)

        command = [FFMPEG4,'-y','-stream_loop',str(loopCount),'-i',str(inputFile),'-vn','loop.flac']
        runAndPrintOutput(command)

        audioInput = []
        if os.path.exists('loop.flac'):
            audioInput = ['-i','loop.flac','-map','0','-map','1']
            print("Looped audio exists")

        command = [FFMPEG4, '-hide_banner', '-stats', '-loglevel', 'error', '-y', '-stream_loop', str(loopCount)]
        command = command + inputFFmpeg
        command = command + ['-pix_fmt', 'yuv420p', '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-f', 'yuv4mpegpipe', '-']
        command2 = [ffmpegSelected, '-y', '-i', '-']
        command2 = command2 + audioInput + encoderPreset + [str(outputVideo)]

        pipe1 = subprocess.Popen(command, stdout=subprocess.PIPE)
        output = subprocess.check_output(command2, stdin=pipe1.stdout)
        pipe1.wait()
        if os.path.exists('loop.flac'):
            os.remove('loop.flac')


def generateLoopContinuityFrame(framesFolder):
    files = os.listdir(framesFolder)
    files.sort()

    # Find the distance between the first two and last two frames
    # Use this distance to calculate position for the loop continuity frame
    beginFirst = int(files[0][:-4])
    endFirst = int(files[1][:-4])

    beginLast = int(files[-2][:-4])
    endLast = int(files[-1][:-4])

    averageDistance = int(((endFirst-beginFirst) + (endLast-beginLast)) / 2)

    # Create frame
    shutil.copy(framesFolder + '/' + files[0], framesFolder + '/' + '{:015d}.png'.format(endLast + averageDistance))
    print("Made loop continuity frame:",framesFolder + '/' + '{:015d}.png'.format(endLast + averageDistance))

def removeLoopContinuityFrame(framesFolder):
    files = os.listdir(framesFolder)
    files.sort()
    os.remove(framesFolder + '/' + files[-1])


def generateTimecodesFile(projectFolder):
    '''
    Scan a folder full of PNG frames and generate a timecodes file for FFmpeg
    '''
    os.chdir(projectFolder)
    files = os.listdir("interpolated_frames")
    files.sort()

    # Generate duration for last frame
    beginFirst = int(files[0][:-4])
    endFirst = int(files[1][:-4])

    beginLast = int(files[-2][:-4])
    endLast = int(files[-1][:-4])

    averageDistance = int(((endFirst - beginFirst) + (endLast - beginLast)) / 2)

    f = open("interpolated_frames/frames.txt", "w")
    for i in range(0, len(files) - 1):
        # Calculate time duration between frames
        currentFrameFile = files[i]
        nextFrameFile = files[i + 1]
        # Each file has a .png extention, use [:-4] to remove
        frameDuration = int(int(nextFrameFile[:-4]) - int(currentFrameFile[:-4]))
        # Write line
        f.write(
            "file '" + projectFolder + "/interpolated_frames/" + currentFrameFile + "'\nduration " + "{:.5f}".format(
                float(frameDuration / 1000.0)) + "\n")

    # Generate last frame
    lastFrameName = "{:015d}.png".format(endLast)
    f.write("file '" + projectFolder + "/interpolated_frames/" + lastFrameName + "'\nduration " + "{:.5f}".format(
        float(averageDistance / 1000.0)) + "\n")
    f.close()


def performAllSteps(inputFile, interpolationFactor, loopable, mode, crf, clearPNGs, nonLocalPNGs,
                    scenechangeSensitivity, mpdecimateSensitivity, useNvenc):
    projectFolder = inputFile[:inputFile.rindex(os.path.sep)]
    if nonLocalPNGs:
        projectFolder = installPath + os.path.sep + "tempFrames"
        if not os.path.exists(projectFolder):
            os.mkdir(projectFolder)

    # Clear pngs if they exist
    if os.path.exists(projectFolder + '/' + 'original_frames'):
        shutil.rmtree(projectFolder + '/' + 'original_frames')

    if os.path.exists(projectFolder + '/' + 'interpolated_frames'):
        shutil.rmtree(projectFolder + '/' + 'interpolated_frames')

    extractFrames(inputFile, projectFolder, mode, mpdecimateSensitivity)

    outParams = runInterpolator(inputFile, projectFolder, interpolationFactor, loopable, mode, scenechangeSensitivity)
    print('---INTERPOLATION DONE---')
    outputVideoName = inputFile[:inputFile.rindex(os.path.sep) + 1]
    outputVideoName += '{:.2f}fps-{}x-mode{}-rife-output.mp4'.format(outParams[0], interpolationFactor, mode)

    createOutput(inputFile, projectFolder, outputVideoName, outParams[0], loopable, mode, crf, useNvenc)

    if clearPNGs:
        shutil.rmtree(projectFolder + '/' + 'original_frames')
        shutil.rmtree(projectFolder + '/' + 'interpolated_frames')

def batchInterpolateFolder(inputDirectory,mode,crf,fpsTarget,clearpngs,nonlocalpngs,
                           scenechangeSensitivity,mpdecimateSensitivity,useNvenc):
    files = []
    # r=root, d=directories, f = files
    for r, d, f in os.walk(inputDirectory):
        for file in f:
            files.append(os.path.join(r, file))

    files.sort()

    for inputVideoFile in files:
        try:
            print(inputVideoFile)

            if mode == 1 or mode == 3:
                currentFPS = getFPSaccurate(inputVideoFile)
            elif mode == 4 or mode == 3:
                currentFPS = getFrameCount(inputVideoFile, True) / getLength(inputVideoFile)

            # Attempt to interpolate everything to above 59fps
            targetFPS = fpsTarget
            exponent = 1
            if currentFPS < targetFPS:
                while (currentFPS * (2 ** exponent)) < targetFPS:
                    exponent += 1
            else:
                continue
            # use [l] to denote whether the file is a loopable video
            print("looping?", '[l]' in inputVideoFile)
            if '[l]' in inputVideoFile:
                print("LOOP")
                performAllSteps(inputVideoFile, (2 ** exponent), True, mode, crf, clearpngs,
                                nonlocalpngs, scenechangeSensitivity, mpdecimateSensitivity,
                                useNvenc)
            else:
                print("DON'T LOOP")
                performAllSteps(inputVideoFile, (2 ** exponent), False, mode, crf, clearpngs,
                                nonlocalpngs, scenechangeSensitivity, mpdecimateSensitivity,
                                useNvenc)
        except:
            traceback.print_exc()
