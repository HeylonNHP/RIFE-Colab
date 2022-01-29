import os
import subprocess
import sys
import addInstalldirToPath
from addInstalldirToPath import *
from Globals.BuildConfig import BuildConfig

REQUIRED_PACKAGES = ['numpy>=1.16', 'tqdm>=4.35.0', 'opencv-python>=4.1.2', 'pyqt5', 'requests']


def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])


def download_file(url, out_file):
    import requests
    r = requests.get(url, allow_redirects=True)
    open(out_file, 'wb').write(r.content)


def extract_archive(archive_file, exclusions: list = []):
    seven_zip = "7z"
    if os.name == 'nt':
        seven_zip = r"C:\Program Files\7-Zip\7z.exe"

    # TODO: Use prependArray()
    seven_zip_exclusions = []
    for exclusion in exclusions:
        seven_zip_exclusions.append('-xr!' + exclusion)

    success = False
    while not success:
        try:
            subprocess.run([seven_zip, 'e', archive_file, '-aoa'] + seven_zip_exclusions)
            success = True
        except:
            print('Cannot execute 7-zip to extract archive. Do you have x64 7-zip installed?')
            print('If not, please do so now before hitting enter: https://www.7-zip.org/a/7z1900-x64.exe')
            input('...')


def prepend_array(arr: list, prepend_string: str):
    arr = arr.copy()
    for i in range(0, len(arr)):
        arr[i] = prepend_string + arr[i]
    return arr


def main_install():
    path_cwd = os.path.realpath(__file__)
    path_cwd = path_cwd[:path_cwd.rindex(os.path.sep)]
    path_cwd_rife_model = path_cwd + os.path.sep + 'arXiv2020RIFE' + os.path.sep + 'model' + os.path.sep
    path_cwd_rife_train_log = path_cwd + os.path.sep + 'arXiv2020RIFE' + os.path.sep + 'train_log' + os.path.sep
    print(path_cwd_rife_model)

    if not os.path.exists(path_cwd_rife_model):
        os.mkdir(path_cwd_rife_model)

    if not os.path.exists(path_cwd_rife_train_log):
        os.mkdir(path_cwd_rife_train_log)

    rife_code_files = prepend_array(os.listdir(path_cwd_rife_model), path_cwd_rife_model)
    rife_code_files += prepend_array(os.listdir(path_cwd_rife_train_log), path_cwd_rife_train_log)

    for file in rife_code_files:
        if not os.path.isfile(file):
            continue
        if '.pkl' in file:
            continue
        print(file)
        file_obj = open(file, 'r')

        file_str = file_obj.read()
        file_obj.close()
        file_str = file_str.replace('from model.', 'from arXiv2020RIFE.model.')
        file_str = file_str.replace('from train_log.', 'from arXiv2020RIFE.train_log.')

        out_file_obj = open(file, 'w')
        out_file_obj.write(file_str)
        out_file_obj.close()

    if BuildConfig().isPyInstallerBuild():
        return

    for package in REQUIRED_PACKAGES:
        install(package)

    # Get torch
    try:
        import torch

        version_string = torch.__version__
        subversions = version_string.split('.')

        if int(subversions[0]) < 1:
            # Torch less than 1.0.0
            raise Exception
        if '+cpu' in subversions[2]:
            # Torch CPU only version
            raise Exception
        print('Found torch', torch.__version__)
    except:
        # Install torch
        print("Pytorch not found, getting 1.7.1 CUDA 11")
        if os.name == 'nt':
            # On windows
            subprocess.check_call(
                [sys.executable, '-m', 'pip', 'install', 'torch===1.7.1+cu110', 'torchvision===0.8.2+cu110',
                 'torchaudio===0.7.2', '-f', 'https://download.pytorch.org/whl/torch_stable.html'])
        else:
            # On linux
            subprocess.check_call(
                [sys.executable, '-m', 'pip', 'install', 'torch==1.7.1+cu110', 'torchvision==0.8.2+cu110',
                 'torchaudio===0.7.2', '-f', 'https://download.pytorch.org/whl/torch_stable.html'])

    # Check ffmpeg
    ffmpeg_exists = False
    ffprobe_exists = False
    while not ffmpeg_exists or not ffprobe_exists:
        try:
            subprocess.run(['ffmpeg'])
            ffmpeg_exists = True
            subprocess.run(['ffprobe'])
            ffprobe_exists = True
        except:
            print("Can't find ffmpeg/ffprobe - Downloading")
            download_file(
                r'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-n5.0-latest-win64-gpl-5.0.zip',
                'ffmpeg.zip')
            extract_archive('ffmpeg.zip', ['doc'])

    print('----DEPENDENCY INSTALLATION COMPLETE----')


main_install()
