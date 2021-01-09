from googleDriveDownloader import *
import shutil
import glob
import os

RIFEPATH = 'arXiv2020RIFE'

def downloadRIFE(installPath,onWindows):
    # Run if not previously setup
    os.chdir(installPath)
    if not os.path.exists('arXiv2020RIFE'):
        os.system(r'git clone https://github.com/hzwer/arXiv2020-RIFE arXiv2020RIFE')

    # Check model files are downloaded
    modelFiles = ['contextnet.pkl','flownet.pkl','unet.pkl']
    modelFilesMissing = False
    for modelFile in modelFiles:
        if not os.path.exists(installPath + os.path.sep + RIFEPATH + os.path.sep + 'train_log' + os.path.sep + modelFile):
            modelFilesMissing = True

    # If they are missing, grab them
    if modelFilesMissing:
        download_file_from_google_drive('11l8zknO1V5hapv2-Ke4DG9mHyBomS0Fc', 'RIFE_trained_model_new.zip')
        sevenZip = "7z"
        if onWindows:
            sevenZip = r"C:\Program Files\7-Zip\7z.exe"

        os.system('"'+sevenZip+'"' + r' e RIFE_trained_model_new.zip -aoa')

        if not os.path.exists(installPath + '/arXiv2020RIFE/train_log'):
            os.mkdir(installPath + '/arXiv2020RIFE/train_log')
            for data in glob.glob("*.pkl"):
                shutil.move(data, installPath + "/arXiv2020RIFE/train_log/")
        # os.chdir(installPath + '/arXiv2020RIFE/')
        os.remove(installPath+"/RIFE_trained_model_new.zip")


