import os
import subprocess

class GlobalValues:
    timebase = 100000

    def getFFmpegPath(self,ffprobe=False):
        executableName = 'ffmpeg'
        if ffprobe:
            executableName = 'ffprobe'

        path = os.path.realpath(__file__)
        path = path[:path.rindex(os.path.sep)]

        orig_path = os.getcwd()

        try:
            os.chdir(path)
        except:
            '''This will break when this code is packaged by pyInstaller'''
            pass

        try:
            subprocess.run([executableName],stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            os.chdir(orig_path)
            return executableName
        except:
            print("Global ffmpeg doesn't exist")

        path = path[:path.rindex(os.path.sep)]

        path = path + os.path.sep + executableName + '.exe'

        try:
            subprocess.run([path],stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            os.chdir(orig_path)
            return path
        except:
            print("Can't find local ffmpeg either :(")
        os.chdir(orig_path)

