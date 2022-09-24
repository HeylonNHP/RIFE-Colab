from googleDriveDownloader import *
import shutil
import glob
import os
from Globals.BuildConfig import BuildConfig

RIFEPATH = 'arXiv2020RIFE'


def download_rife(install_path, on_windows, force_download_models=False):
    # Run if not previously setup
    os.chdir(install_path)
    if not BuildConfig().isPyInstallerBuild():
        if not os.path.exists('arXiv2020RIFE'):
            os.system(r'git clone https://github.com/hzwer/Practical-RIFE arXiv2020RIFE')

    # Check model files are downloaded
    # model_files = ['contextnet.pkl','flownet.pkl','unet.pkl']
    model_files = ['flownet.pkl']
    model_files_missing = False
    for modelFile in model_files:
        model_path = install_path + os.path.sep + RIFEPATH + os.path.sep + 'train_log' + os.path.sep + modelFile

        if force_download_models and os.path.exists(model_path):
            os.remove(model_path)

        if not os.path.exists(model_path):
            model_files_missing = True

    # If they are missing, grab them
    if model_files_missing:
        # download_file_from_google_drive('11l8zknO1V5hapv2-Ke4DG9mHyBomS0Fc', 'RIFE_trained_model_new.zip')
        # download_file_from_google_drive('1wsQIhHZ3Eg4_AfCXItFKqqyDMB4NS0Yd', 'RIFE_trained_model_new.zip')

        # 3.8
        # download_file_from_google_drive('1O5KfS3KzZCY3imeCr2LCsntLhutKuAqj', 'RIFE_trained_model_new.zip')
        # 3.1
        # download_file_from_google_drive('1xn4R3TQyFhtMXN2pa3lRB8cd4E1zckQe', 'RIFE_trained_model_new.zip')
        # 4.5
        download_file_from_google_drive('17Bl_IhTBexogI9BV817kTjf7eTuJEDc0', 'RIFE_trained_model_new.zip')

        seven_zip = "7z"
        if on_windows:
            seven_zip = r"C:\Program Files\7-Zip\7z.exe"

        os.system('"' + seven_zip + '"' + r' e RIFE_trained_model_new.zip -aoa')

        if not os.path.exists(install_path + '/arXiv2020RIFE'):
            os.mkdir(install_path + '/arXiv2020RIFE')
        if not os.path.exists(install_path + '/arXiv2020RIFE/train_log'):
            os.mkdir(install_path + '/arXiv2020RIFE/train_log')
        for data in glob.glob("*.pkl"):
            shutil.move(data, install_path + "/arXiv2020RIFE/train_log/")
        shutil.move('IFNet_HDv3.py', install_path + '/arXiv2020RIFE/train_log/IFNet_HDv3.py')
        shutil.move('RIFE_HDv3.py', install_path + '/arXiv2020RIFE/train_log/RIFE_HDv3.py')

        os.remove(install_path + "/RIFE_trained_model_new.zip")
