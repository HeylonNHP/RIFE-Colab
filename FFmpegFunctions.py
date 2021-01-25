import re
import subprocess
from Globals.GlobalValues import GlobalValues

ffmpegLocation = GlobalValues().getFFmpegPath()
ffprobeLocation = GlobalValues().getFFmpegPath(ffprobe=True)
def setFFmpegLocation(location):
    global ffmpegLocation
    ffmpegLocation = location

def getFrameCount(inputPath,mpdecimate):
    '''
    Gets the frame count of the video
    '''
    frameCount = 0
    result = None
    if mpdecimate:
        # ffmpeg -i input.mkv -map 0:v:0 -c copy -f null -
        result = subprocess.run([ffmpegLocation, '-i',inputPath,'-vf','mpdecimate','-map','0:v:0','-c','rawvideo','-f','null','-'], stderr=subprocess.PIPE)
    else:
        result = subprocess.run([ffmpegLocation, '-i',inputPath,'-map','0:v:0','-c','rawvideo','-f','null','-'], stderr=subprocess.PIPE)
    lines = result.stderr.splitlines()

    print("------LINES------")
    decodedLines = []
    for line in lines:
        decodedLine = ""
        try:
            decodedLine = line.decode('UTF-8')
        except:
            continue
        decodedLines.append(decodedLine)

    for i in range(len(decodedLines)-1,0,-1):
        decodedLine = decodedLines[i]
        print("Decoded line:",decodedLine)
        if 'frame=' in decodedLine:
            print(decodedLine)
            x = re.search(r"frame=[ ]*([0-9]+)", decodedLine)
            frameCount = int(x.group(1))
            return frameCount

def getFPS(inputPath):
    '''
    Gets the FPS as a float from a given video path
    '''
    videoFPS = 0
    result = subprocess.run([ffmpegLocation, '-i',inputPath], stderr=subprocess.PIPE)
    lines = result.stderr.splitlines()

    print("------LINES------")
    for line in lines:
        decodedLine = ""
        try:
            decodedLine = line.decode('UTF-8')
        except:
            continue
        if 'Stream #0:0' in decodedLine:
            print(decodedLine)
            x = re.search(r"([0-9]+\.*[0-9]*) fps,", decodedLine)
            videoFPS = float(x.group(1))
            return videoFPS

def getFPSaccurate(inputPath):
    '''
    Gets the FPS as a float from a given video path - Acquires fractional framerate for accuracy
    '''
    videoFPS = 0

    result = subprocess.run([ffprobeLocation,'-v','0','-of','csv=p=0','-select_streams','v:0','-show_entries','stream=r_frame_rate',inputPath], stdout=subprocess.PIPE)
    lines = result.stdout.splitlines()

    print("------LINES------")
    for line in lines:
        decodedLine = ""
        try:
            decodedLine = line.decode('UTF-8')
        except:
            continue
        print(decodedLine)
        num,den = decodedLine.split("/")
        return float(num)/float(den)

def getLength(inputPath):
    '''
    Get the duration of a video in seconds as a float
    '''
    lengthSeconds = 0.0
    result = subprocess.run([ffmpegLocation, '-i',inputPath], stderr=subprocess.PIPE)
    lines = result.stderr.splitlines()

    print("------LINES------")
    for line in lines:
        decodedLine = ""
        try:
            decodedLine = line.decode('UTF-8')
        except:
            continue
        if 'Duration:' in decodedLine:
            print(decodedLine)
            x = re.search(r"Duration: ([0-9]+:[0-9]+:[0-9]+\.*[0-9]*)", decodedLine)
            timeString = x.group(1)
            timeStringList = timeString.split(':')
            lengthSeconds += float(timeStringList[0]) * 3600
            lengthSeconds += float(timeStringList[1]) * 60
            lengthSeconds += float(timeStringList[2])
            return lengthSeconds