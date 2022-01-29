import re
import subprocess
from Globals.GlobalValues import GlobalValues

ffmpegLocation = GlobalValues().getFFmpegPath()
ffprobeLocation = GlobalValues().getFFmpegPath(ffprobe=True)


def set_ffmpeg_location(location):
    global ffmpegLocation
    ffmpegLocation = location


def get_frame_count(input_path, mpdecimate, mpdecimate_sensitivity="64*12,64*8,0.33"):
    """
    Gets the frame count of the video
    """
    hi, lo, frac = mpdecimate_sensitivity.split(",")
    mpdecimate = "mpdecimate=hi={}:lo={}:frac={}".format(hi, lo, frac)
    if mpdecimate:
        # ffmpeg -i input.mkv -map 0:v:0 -c copy -f null -
        command_line = [ffmpegLocation, '-i', input_path, '-vf', mpdecimate, '-map', '0:v:0', '-c', 'rawvideo', '-f', 'null', '-']
    else:
        command_line = [ffmpegLocation, '-i', input_path, '-map', '0:v:0', '-c', 'rawvideo', '-f', 'null', '-']

    result = subprocess.run(command_line, stderr=subprocess.PIPE)
    lines = result.stderr.splitlines()

    decoded_lines = []
    for line in lines:
        try:
            decoded_line = line.decode('UTF-8')
        except:
            continue
        decoded_lines.append(decoded_line)

    for i in range(len(decoded_lines) - 1, 0, -1):
        decoded_line = decoded_lines[i]
        if 'frame=' in decoded_line:
            print('Fetched frame count:', decoded_line)
            x = re.search(r"frame=[ ]*([0-9]+)", decoded_line)
            frame_count = int(x.group(1))
            return frame_count


def get_fps(input_path):
    """
    Gets the FPS as a float from a given video path
    """
    result = subprocess.run([ffmpegLocation, '-i', input_path], stderr=subprocess.PIPE)
    lines = result.stderr.splitlines()

    for line in lines:
        try:
            decoded_line = line.decode('UTF-8')
        except:
            continue
        if 'Stream #0:' in decoded_line:
            x = re.search(r"([0-9]+\.*[0-9]*) fps,", decoded_line)
            try:
                video_fps = float(x.group(1))
                print('Fetched FPS:', video_fps)
                return video_fps
            except:
                continue
    return None


def get_fps_accurate(input_path):
    """
    Gets the FPS as a float from a given video path - Acquires fractional framerate for accuracy
    """

    result = subprocess.run(
        [ffprobeLocation, '-v', '0', '-of', 'csv=p=0', '-select_streams', 'v:0', '-show_entries', 'stream=r_frame_rate',
         input_path], stdout=subprocess.PIPE)
    lines = result.stdout.splitlines()

    decoded_line = lines[0].decode('UTF-8')
    num, den = decoded_line.split("/")
    print('Fetched accurate FPS:', "{}/{}".format(num,den))
    return float(num) / float(den)


def get_length(input_path):
    """
    Get the duration of a video in seconds as a float
    """
    length_seconds = 0.0
    result = subprocess.run([ffmpegLocation, '-i', input_path], stderr=subprocess.PIPE)
    lines = result.stderr.splitlines()

    for line in lines:
        try:
            decoded_line = line.decode('UTF-8')
        except:
            continue
        if 'Duration:' in decoded_line:
            x = re.search(r"Duration: ([0-9]+:[0-9]+:[0-9]+\.*[0-9]*)", decoded_line)
            time_string = x.group(1)
            time_string_list = time_string.split(':')
            length_seconds += float(time_string_list[0]) * 3600
            length_seconds += float(time_string_list[1]) * 60
            length_seconds += float(time_string_list[2])
            print('Fetched video length (secs):', length_seconds)
            return length_seconds
