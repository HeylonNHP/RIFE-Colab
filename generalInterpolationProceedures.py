import math
import os
import shutil
from runAndPrintOutput import runAndPrintOutput
from FFmpegFunctions import *
from frameChooser import chooseFrames
FFMPEG4 = 'ffmpeg'
GPUID = 0
nvencPreset = 'p7'


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

        audioInput = ""
        if os.path.exists('loop.flac'):
            audioInput = ['-i','loop.flac','-map','0','-map','1']
            print("Looped audio exists")

        command = [FFMPEG4,'-hide_banner','-stats','-loglevel','error','-y','-stream_loop',str(loopCount)]
        command = command + inputFFmpeg
        command = command + ['-pix_fmt','yuv420p','-vf','pad=ceil(iw/2)*2:ceil(ih/2)*2','-f','yuv4mpegpipe','-',
                             '|',ffmpegSelected,'-i','-']
        command = command + audioInput + encoderPreset + [str(outputVideo)]
        runAndPrintOutput(command)
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