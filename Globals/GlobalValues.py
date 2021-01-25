import os
import subprocess

class GlobalValues:
    timebase = 100000

    def getFFmpegPath(self):
        path = os.path.realpath(__file__)
        path = path[:path.rindex(os.path.sep)]

        orig_path = os.getcwd()

        os.chdir(path)

        try:
            subprocess.run(['ffmpeg'])
            os.chdir(orig_path)
            return 'ffmpeg'
        except:
            print("Global ffmpeg doesn't exist")

        path = path[:path.rindex(os.path.sep)]

        path = path + os.path.sep + 'ffmpeg.exe'

        try:
            subprocess.run([path])
            os.chdir(orig_path)
            return path
        except:
            print("Can't find local ffmpeg either :(")
        os.chdir(orig_path)

