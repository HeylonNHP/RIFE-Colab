from googleDriveDownloader import *
import shutil
import glob
import os
from Globals.BuildConfig import BuildConfig

RIFEPATH = 'arXiv2020RIFE'

def downloadRIFE(installPath,onWindows, forceDownloadModels=False):
    # Run if not previously setup
    os.chdir(installPath)
    if not BuildConfig().isPyInstallerBuild():
        if not os.path.exists('arXiv2020RIFE'):
            os.system(r'git clone https://github.com/hzwer/Practical-RIFE arXiv2020RIFE')

    # Check model files are downloaded
    modelFiles = ['contextnet.pkl','flownet.pkl','unet.pkl']
    modelFilesMissing = False
    for modelFile in modelFiles:
        modelPath = installPath + os.path.sep + RIFEPATH + os.path.sep + 'train_log' + os.path.sep + modelFile

        if forceDownloadModels and os.path.exists(modelPath):
            os.remove(modelPath)

        if not os.path.exists(modelPath):
            modelFilesMissing = True

    # If they are missing, grab them
    if modelFilesMissing:
        #download_file_from_google_drive('11l8zknO1V5hapv2-Ke4DG9mHyBomS0Fc', 'RIFE_trained_model_new.zip')
        #download_file_from_google_drive('1wsQIhHZ3Eg4_AfCXItFKqqyDMB4NS0Yd', 'RIFE_trained_model_new.zip')
        download_file_from_google_drive('1xn4R3TQyFhtMXN2pa3lRB8cd4E1zckQe', 'RIFE_trained_model_new.zip')
        sevenZip = "7z"
        if onWindows:
            sevenZip = r"C:\Program Files\7-Zip\7z.exe"

        os.system('"'+sevenZip+'"' + r' e RIFE_trained_model_new.zip -aoa')

        if not os.path.exists(installPath + '/arXiv2020RIFE'):
            os.mkdir(installPath + '/arXiv2020RIFE')
        if not os.path.exists(installPath + '/arXiv2020RIFE/train_log'):
            os.mkdir(installPath + '/arXiv2020RIFE/train_log')
        for data in glob.glob("*.pkl"):
            shutil.move(data, installPath + "/arXiv2020RIFE/train_log/")
        shutil.move('IFNet_HDv3.py',installPath+'/arXiv2020RIFE/train_log/IFNet_HDv3.py')
        shutil.move('RIFE_HDv3.py',installPath+'/arXiv2020RIFE/train_log/RIFE_HDv3.py')

        os.remove(installPath+"/RIFE_trained_model_new.zip")
