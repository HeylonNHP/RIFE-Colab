# @title Step 2 - Run to setup RIFE (Mandatory)
from googleDriveDownloader import *
import shutil
import glob
import os

def downloadRIFE(installPath,onWindows):
    # Run if not previously setup
    os.chdir(installPath)
    os.system(r'git clone https://github.com/hzwer/arXiv2020-RIFE')
    download_file_from_google_drive('11l8zknO1V5hapv2-Ke4DG9mHyBomS0Fc', 'RIFE_trained_model_new.zip')
    sevenZip = "7z"
    if onWindows:
        sevenZip = r"C:\Program Files\7-Zip\7z.exe"

    os.system(sevenZip + r' e RIFE_trained_model_new.zip -aoa')

    if not os.path.exists(installPath + '/arXiv2020-RIFE/train_log'):
        os.mkdir(installPath + '/arXiv2020-RIFE/train_log')
    for data in glob.glob("*.pkl"):
        shutil.move(data, installPath + "/arXiv2020-RIFE/train_log/")
    os.chdir(installPath + '/arXiv2020-RIFE/')
    shutil.rmtree(installPath+"/RIFE_trained_model_new.zip")


