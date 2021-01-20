import math
import os
import shutil
import traceback
from queue import Queue
import threading
from QueuedFrames.queuedFrameList import *
from QueuedFrames.queuedFrame import *
from QueuedFrames.FrameFile import *

from runAndPrintOutput import runAndPrintOutput
from FFmpegFunctions import *
from frameChooser import chooseFrames

import warnings
warnings.filterwarnings("ignore")

FFMPEG4 = 'ffmpeg'
GPUID = 0
nvencPreset = 'p7'
installPath = os.getcwd()
print('INSTALL:', installPath)

# Check if running on Windows or not
onWindows = None
if os.name == 'nt':
    onWindows = True
else:
    onWindows = False

# Get and initialise RIFE
from rifeFunctions import downloadRIFE

downloadRIFE(installPath, onWindows)
os.chdir(installPath)
from rifeInterpolationFunctions import *

gpuBatchSize = 2
gpuIDsList = [0]


def setFFmpeg4Path(path):
    global FFMPEG4
    FFMPEG4 = path
    setFFmpegLocation(FFMPEG4)


def setNvencSettings(nvencGpuID, preset):
    global GPUID
    global nvencPreset
    GPUID = nvencGpuID
    nvencPreset = preset


def setGPUinterpolationOptions(batchSize: int, _gpuIDsList: list):
    global gpuIDsList
    global gpuBatchSize
    gpuIDsList = _gpuIDsList
    gpuBatchSize = batchSize


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
        runAndPrintOutput(
            [FFMPEG4, '-i', inputFile, '-map_metadata', '-1', '-pix_fmt', 'rgb24', 'original_frames/%15d.png'])
    elif mode == 3 or mode == 4:
        hi, lo, frac = mpdecimateSensitivity.split(",")
        mpdecimate = "mpdecimate=hi={}:lo={}:frac={}".format(hi, lo, frac)
        runAndPrintOutput(
            [FFMPEG4, '-i', inputFile, '-map_metadata', '-1', '-pix_fmt', 'rgb24', '-copyts', '-r', '1000', '-vsync',
             '0', '-frame_pts', 'true', '-vf', mpdecimate, '-qscale:v', '1', 'original_frames/%15d.png'])


def runInterpolator(inputFile, projectFolder, interpolationFactor, loopable, mode, scenechangeSensitivity):
    '''
    Equivalent to DAINAPP Step 2
    '''
    global gpuIDsList
    global gpuBatchSize
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
            framesList: list = []

            progressMessage = "Interpolating frame: {} Of {} {:.2f}%".format(i + 1, len(files),
                                                                             ((i + 1) / len(files)) * 100)

            queuedFrameList: QueuedFrameList = QueuedFrameList(framesList,
                                                               origFramesFolder + '/' + files[i],
                                                               interpFramesFolder + '/' + '{:015d}.png'.format(count),
                                                               origFramesFolder + '/' + files[i + 1],
                                                               interpFramesFolder + '/' + '{:015d}.png'.format(
                                                                   count + interpolationFactor))
            queuedFrameList.progressMessage = progressMessage
            currentFactor = interpolationFactor

            while currentFactor > 1:
                period = int(interpolationFactor / currentFactor)
                for j in range(0, period):
                    offset = int(currentFactor * j)
                    beginFrame = interpFramesFolder + '/' + '{:015d}.png'.format(count + offset)
                    endFrame = interpFramesFolder + '/' + '{:015d}.png'.format(count + currentFactor + offset)
                    middleFrame = interpFramesFolder + '/' + '{:015d}.png'.format(
                        count + int(currentFactor / 2) + offset)

                    framesList.append(QueuedFrame(beginFrame, endFrame, middleFrame, scenechangeSensitivity))
                currentFactor = int(currentFactor / 2)

            count += interpolationFactor
            framesQueue.put(queuedFrameList)

    elif mode == 3 or mode == 4:
        count = 0
        shutil.copy(origFramesFolder + '/' + files[0], interpFramesFolder + '/' + '{:015d}.png'.format(count))
        # To ensure no duplicates on the output with the new VFR to CFR algorithm, double the interpolation factor. TODO: Investigate
        modeModOutputFPS = outputFPS
        if mode == 3:
            interpolationFactor = interpolationFactor * 2
            modeModOutputFPS = modeModOutputFPS * 2

        for i in range(0, len(files) - 1):
            framesList: list = []

            localInterpolationFactor = interpolationFactor
            # If mode 3, calculate interpolation factor on a per-frame basis to maintain desired FPS

            beginFrameTime = int(files[i][:-4])
            endFrameTime = int(files[i + 1][:-4])
            timeDiff = endFrameTime - beginFrameTime
            if mode == 3:
                localInterpolationFactor = 2

                while 1 / (((endFrameTime - beginFrameTime) / localInterpolationFactor) / 1000) < modeModOutputFPS:
                    localInterpolationFactor = int(localInterpolationFactor * 2)

            progressMessage = "Interpolating frame: {} Of {} {:.2f}% Frame interp. factor {}x".format(i + 1, len(files),
                                                                                                      ((i + 1) / len(
                                                                                                          files)) * 100,
                                                                                                      localInterpolationFactor)
            # Get timecodes of both working frames
            currentTimecode = int(files[i][:-4])
            nextTimecode = int(files[i + 1][:-4])

            queuedFrameList: QueuedFrameList = QueuedFrameList(framesList,
                                                               origFramesFolder + '/' + files[i],
                                                               interpFramesFolder + '/' + '{:015d}.png'.format(
                                                                   currentTimecode),
                                                               origFramesFolder + '/' + files[i + 1],
                                                               interpFramesFolder + '/' + '{:015d}.png'.format(
                                                                   nextTimecode))
            queuedFrameList.progressMessage = progressMessage
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

                    framesList.append(QueuedFrame(beginFrame, endFrame, middleFrame, scenechangeSensitivity))
                currentFactor = int(currentFactor / 2)

            # count += interpolationFactor
            framesQueue.put(queuedFrameList)

    inFramesList: list = []
    loadPNGThread = threading.Thread(target=queueThreadLoadFrame,args=(origFramesFolder,inFramesList,))
    loadPNGThread.start()

    outFramesQueue: Queue = Queue(maxsize=128)
    gpuList: list = gpuIDsList
    batchSize: int = gpuBatchSize
    threads: list = []
    for i in range(0, batchSize):
        for gpuID in gpuList:
            rifeThread = threading.Thread(target=queueThreadInterpolator, args=(framesQueue, outFramesQueue, inFramesList, gpuID,))
            threads.append(rifeThread)
            rifeThread.start()
        time.sleep(5)

    saveThreads = []
    for i in range(0, batchSize):
        saveThread = threading.Thread(target=queueThreadSaveFrame, args=(outFramesQueue,))
        saveThreads.append(saveThread)
        saveThread.start()

    loadPNGThread.join()

    for rifeThread in threads:
        rifeThread.join()

    print("Put none")
    outFramesQueue.put(None)

    for saveThread in saveThreads:
        saveThread.join()

    # Loopable
    if loopable:
        removeLoopContinuityFrame(interpFramesFolder)

    return [outputFPS]

inFrameGetLock = threading.Lock()

def queueThreadInterpolator(framesQueue: Queue, outFramesQueue: Queue, inFramesList:list, gpuid):
    device, model = setupRIFE(installPath, gpuid)
    while True:
        listOfCompletedFrames = []
        if framesQueue.empty():
            break
        currentQueuedFrameList: QueuedFrameList = framesQueue.get()
        print(currentQueuedFrameList.progressMessage)
        listOfAllFramesInterpolate: list = currentQueuedFrameList.frameList

        # Copy start and end files
        if not os.path.exists(currentQueuedFrameList.startFrameDest):
            shutil.copy(currentQueuedFrameList.startFrame, currentQueuedFrameList.startFrameDest)
        if not os.path.exists(currentQueuedFrameList.endFrameDest):
            shutil.copy(currentQueuedFrameList.endFrame, currentQueuedFrameList.endFrameDest)

        for frame in listOfAllFramesInterpolate:
            queuedFrame: QueuedFrame = frame
            success = False

            # Load begin frame from HDD or RAM
            beginFrame = None
            # If the current frame pair uses an original_frame - Then grab it from RAM
            if queuedFrame.beginFrame == currentQueuedFrameList.startFrameDest:
                with inFrameGetLock:
                    for i in range(0,len(inFramesList)):
                        if currentQueuedFrameList.startFrame == str(inFramesList[i]):
                            beginFrame = inFramesList[i]
                            break

            if beginFrame is None:
                for i in range(0, len(listOfCompletedFrames)):
                    if str(listOfCompletedFrames[i]) == queuedFrame.beginFrame:
                        beginFrame = listOfCompletedFrames[i]
                        break
            if beginFrame is None:
                beginFrame = FrameFile(queuedFrame.beginFrame)
                beginFrame.loadImageData()

            # Load end frame from HDD or RAM
            endFrame = None
            # If the current frame pair uses an original_frame - Then grab it from RAM
            if queuedFrame.endFrame == currentQueuedFrameList.endFrameDest:
                with inFrameGetLock:
                    for i in range(0,len(inFramesList)):
                        if currentQueuedFrameList.endFrame == str(inFramesList[i]):
                            endFrame = inFramesList[i]
                            break


            if endFrame is None:
                for i in range(0, len(listOfCompletedFrames)):
                    if str(listOfCompletedFrames[i]) == queuedFrame.endFrame:
                        endFrame = listOfCompletedFrames[i]
                        break
            if endFrame is None:
                endFrame = FrameFile(queuedFrame.endFrame)
                endFrame.loadImageData()

            # Initialise the mid frame with the output path
            midFrame = FrameFile(queuedFrame.middleFrame)

            midFrame = rifeInterpolate(device, model, beginFrame, endFrame, midFrame,
                                       queuedFrame.scenechangeSensitivity)
            listOfCompletedFrames.append(midFrame)
            outFramesQueue.put(midFrame)

        # Start frame is no-longer needed, remove from RAM
        with inFrameGetLock:
            for i in range(0,len(inFramesList)):
                if str(inFramesList[i]) == currentQueuedFrameList.startFrame:
                    inFramesList.pop(i)
                    break


def queueThreadSaveFrame(outFramesQueue: Queue):
    while True:
        item: FrameFile = outFramesQueue.get()
        if item is None:
            print("Got none")
            outFramesQueue.put(None)
            break

        item.saveImageData()

def queueThreadLoadFrame(origFramesFolder:str,inFramesList:list):
    maxListLength = 128
    frameFilesList = os.listdir(origFramesFolder)
    frameFilesList.sort()
    for i in range(0,len(frameFilesList)):
        while len(inFramesList) > maxListLength:
            time.sleep(0.01)
        frameFile = FrameFile(origFramesFolder + '/' + frameFilesList[i])
        frameFile.loadImageData()
        inFramesList.append(frameFile)
    print("LOADED ALL FRAMES - DONE")


def createOutput(inputFile, projectFolder, outputVideo, outputFPS, loopable, mode, crfout, useNvenc):
    '''
    Equivalent to DAINAPP Step 3
    '''
    os.chdir(projectFolder)
    maxLoopLength = 15
    preferredLoopLength = 10
    inputLength = getLength(inputFile)

    inputFFmpeg = ""

    encoderPreset = ['-pix_fmt', 'yuv420p', '-c:v', 'libx264', '-preset', 'veryslow',
                     '-crf', '{}'.format(crfout)]
    ffmpegSelected = FFMPEG4
    if useNvenc:
        encoderPreset = ['-pix_fmt', 'yuv420p', '-c:v', 'h264_nvenc', '-gpu', str(GPUID), '-preset', str(nvencPreset),
                         '-profile', 'high', '-rc', 'vbr', '-b:v', '0', '-cq', str(crfout + 10)]
        ffmpegSelected = 'ffmpeg'

    if mode == 1:
        inputFFmpeg = ['-r', str(outputFPS), '-i', 'interpolated_frames/%15d.png']
    if mode == 3 or mode == 4:
        # generateTimecodesFile(projectFolder)
        chooseFrames(projectFolder + os.path.sep + "interpolated_frames", outputFPS)
        inputFFmpeg = ['-vsync', '1', '-r', str(outputFPS), '-f', 'concat', '-safe', '0', '-i',
                       'interpolated_frames/framesCFR.txt']

    if loopable == False or (maxLoopLength / float(inputLength) < 2):
        # Don't loop, too long input
        print('Dont loop', maxLoopLength / float(inputLength))

        command = [ffmpegSelected, '-hide_banner', '-stats', '-loglevel', 'error', '-y']
        command = command + inputFFmpeg
        command = command + ['-i', str(inputFile), '-map', '0', '-map', '1:a?', '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2']
        command = command + encoderPreset + [str(outputVideo)]

        runAndPrintOutput(command)
    else:
        loopCount = math.ceil(preferredLoopLength / float(inputLength)) - 1
        loopCount = str(loopCount)
        print('Loop', loopCount)

        command = [FFMPEG4, '-y', '-stream_loop', str(loopCount), '-i', str(inputFile), '-vn', 'loop.flac']
        runAndPrintOutput(command)

        audioInput = []
        if os.path.exists('loop.flac'):
            audioInput = ['-i', 'loop.flac', '-map', '0', '-map', '1']
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

    averageDistance = int(((endFirst - beginFirst) + (endLast - beginLast)) / 2)

    # Create frame
    shutil.copy(framesFolder + '/' + files[0], framesFolder + '/' + '{:015d}.png'.format(endLast + averageDistance))
    print("Made loop continuity frame:", framesFolder + '/' + '{:015d}.png'.format(endLast + averageDistance))


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
                    scenechangeSensitivity, mpdecimateSensitivity, useNvenc, useAutoEncode=True):
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

    # Get outputFPS
    outputFPS = None
    if mode == 1 or mode == 3:
        outputFPS = getFPSaccurate(inputFile) * interpolationFactor
    elif mode == 4:
        outputFPS = (getFrameCount(inputFile, True) / getLength(inputFile)) * interpolationFactor

    # Generate output name
    outputVideoNameSegments = ['{:.2f}'.format(outputFPS),'fps-',str(interpolationFactor),'x-mode',str(mode),'-rife-output.mp4']
    outputVideoName = inputFile[:inputFile.rindex(os.path.sep) + 1] + ''.join(outputVideoNameSegments)

    #Auto encoding
    interpolationDone = [False]
    import autoEncoding
    if mode == 1 and useAutoEncode:
        autoEncodeThread = threading.Thread(target=autoEncoding.mode1AutoEncoding_Thread,args=(projectFolder,inputFile,outputVideoName,interpolationDone,outputFPS,crf,useNvenc,))
        autoEncodeThread.start()
        time.sleep(5)


    outParams = runInterpolator(inputFile, projectFolder, interpolationFactor, loopable, mode, scenechangeSensitivity)
    print('---INTERPOLATION DONE---')
    interpolationDone[0] = True

    #Auto encoding
    if not useAutoEncode:
        createOutput(inputFile, projectFolder, outputVideoName, outputFPS, loopable, mode, crf, useNvenc)

    if clearPNGs:
        shutil.rmtree(projectFolder + '/' + 'original_frames')
        shutil.rmtree(projectFolder + '/' + 'interpolated_frames')


def batchInterpolateFolder(inputDirectory, mode, crf, fpsTarget, clearpngs, nonlocalpngs,
                           scenechangeSensitivity, mpdecimateSensitivity, useNvenc):
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
