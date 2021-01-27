# https://raevskymichail.medium.com/python-gui-building-a-simple-application-with-pyqt-and-qt-designer-e9f8cda76246
import sys
#from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import mainGuiUi
import os
import threading
import addInstalldirToPath

sys.path.insert(0, os.getcwd() + os.path.sep + 'arXiv2020RIFE')
print(sys.path)
from generalInterpolationProceedures import *

class RIFEGUIMAINWINDOW(QMainWindow,mainGuiUi.Ui_MainWindow):
    def __init__(self):
        # This is needed here for variable and method access
        super().__init__()
        self.setupUi(self)  # Initialize a design

        self.verticalLayout_4.setAlignment(Qt.AlignTop)
        self.verticalLayout_3.setAlignment(Qt.AlignTop)
        self.verticalLayout_2.setAlignment(Qt.AlignTop)

        self.browseInputButton.clicked.connect(self.browseInputFile)
        self.runAllStepsButton.clicked.connect(self.runAllSteps)
        self.extractFramesButton.clicked.connect(self.runStep1)
        self.interpolateFramesButton.clicked.connect(self.runStep2)
        self.encodeOutputButton.clicked.connect(self.runStep3)

        self.interpolationFactorSelect.currentTextChanged.connect(self.updateVideoFPSstats)

        subscribeTointerpolationProgressUpdate(self.getProgressUpdate)

    def browseInputFile(self):
        file, _filter = QFileDialog.getOpenFileName(caption="Open video file to interpolate")
        print(str(file))
        self.inputFilePathText.setText(file)
        
        self.updateVideoFPSstats()

    def updateVideoFPSstats(self):
        file = str(self.inputFilePathText.text())
        if not os.path.exists(file):
            return

        videoFPS = getFPSaccurate(str(file))
        self.VideostatsInputFPStext.setText(str(videoFPS))
        videoFPS = videoFPS * float(self.interpolationFactorSelect.currentText())
        self.VideostatsOutputFPStext.setText(str(videoFPS))

    def runStep1(self):
        self.runAllInterpolationSteps(step1=True,step2=False,step3=False)

    def runStep2(self):
        self.runAllInterpolationSteps(step1=False,step2=True,step3=False)

    def runStep3(self):
        self.runAllInterpolationSteps(step1=False,step2=False,step3=True)

    def runAllSteps(self,nigger):
        # This function is required because python is stupid, and will set the first boolean function parameter to false
        self.runAllInterpolationSteps()

    def runAllInterpolationSteps(self,step1=True,step2=True,step3=True):
        selectedGPUs = str(self.gpuidsSelect.currentText()).split(",")
        selectedGPUs = [int(i) for i in selectedGPUs]
        setNvencSettings(selectedGPUs[0], 'slow')
        setGPUinterpolationOptions(int(self.batchthreadsNumber.value()), selectedGPUs)

        inputFile = str(self.inputFilePathText.text())
        if os.name == 'nt':
            inputFile = inputFile.replace('/','\\')

        interpolationFactor = int(self.interpolationFactorSelect.currentText())
        loopable = bool(self.loopoutputCheck.isChecked())
        mode = int(self.modeSelect.currentText())
        crfout = int(self.crfoutNumber.value())
        clearpngs = bool(self.clearpngsCheck.isChecked())
        nonlocalpngs = bool(self.nonlocalpngsCheck.isChecked())
        scenechangeSensitivity = float(self.scenechangeSensitivityNumber.value())
        mpdecimateSensitivity = str(self.mpdecimateText.text())
        usenvenc = bool(self.nvencCheck.isChecked())
        useAutoencode = bool(self.autoencodeCheck.isChecked())
        blocksize = int(self.autoencodeBlocksizeNumber.value())

        # Exceptions are hidden on the PYQt5 thread - Run interpolator on separate thread to see them
        interpolateThread = threading.Thread(target=self.runAllInterpolationStepsThread,args=(inputFile, interpolationFactor, loopable, mode, crfout, clearpngs, nonlocalpngs,
                        scenechangeSensitivity, mpdecimateSensitivity, usenvenc, useAutoencode, blocksize,step1,step2,step3,))

        interpolateThread.start()

    def runAllInterpolationStepsThread(self,inputFile, interpolationFactor, loopable, mode, crfout, clearpngs, nonlocalpngs,
                        scenechangeSensitivity, mpdecimateSensitivity, usenvenc, useAutoencode, blocksize,step1,step2,step3):
        self.runAllStepsButton.setEnabled(False)
        self.extractFramesButton.setEnabled(False)
        self.interpolateFramesButton.setEnabled(False)
        self.encodeOutputButton.setEnabled(False)
        performAllSteps(inputFile,interpolationFactor,loopable,mode,crfout,clearpngs,nonlocalpngs,scenechangeSensitivity,mpdecimateSensitivity,
                        usenvenc,useAutoencode,blocksize,step1=step1,step2=step2,step3=step3)
        self.runAllStepsButton.setEnabled(True)
        self.extractFramesButton.setEnabled(True)
        self.interpolateFramesButton.setEnabled(True)
        self.encodeOutputButton.setEnabled(True)

    def getProgressUpdate(self,progress:InterpolationProgress):
        self.interpolationProgressBar.setMaximum(progress.totalFrames)
        self.interpolationProgressBar.setValue(progress.completedFrames)

def main():
    app = QApplication(sys.argv)
    if 'Fusion' in QStyleFactory.keys():
        app.setStyle('Fusion')

    baseIntensity = 50

    pal = QPalette()
    pal.setColor(QPalette.Background, QColor(baseIntensity,baseIntensity,baseIntensity))
    pal.setColor(QPalette.Window, QColor(baseIntensity,baseIntensity,baseIntensity))
    pal.setColor(QPalette.WindowText, QColor(255-baseIntensity, 255-baseIntensity, 255-baseIntensity))
    pal.setColor(QPalette.Base, QColor(baseIntensity+10, baseIntensity+10, baseIntensity+10))
    pal.setColor(QPalette.AlternateBase, QColor(baseIntensity, baseIntensity, baseIntensity))
    pal.setColor(QPalette.ToolTipBase, QColor(baseIntensity, baseIntensity, baseIntensity))
    pal.setColor(QPalette.ToolTipText, QColor(255-baseIntensity, 255-baseIntensity, 255-baseIntensity))
    pal.setColor(QPalette.Text, QColor(255-baseIntensity, 255-baseIntensity, 255-baseIntensity))
    pal.setColor(QPalette.Button, QColor(baseIntensity+10, baseIntensity+10, baseIntensity+10))
    pal.setColor(QPalette.ButtonText, QColor(255-baseIntensity, 255-baseIntensity, 255-baseIntensity))
    pal.setColor(QPalette.BrightText, QColor(255, 0, 0))
    pal.setColor(QPalette.Highlight, QColor(125, 125, 200))
    pal.setColor(QPalette.HighlightedText, QColor(255-baseIntensity, 255-baseIntensity, 255-baseIntensity))
    app.setPalette(pal)

    window = RIFEGUIMAINWINDOW()
    window.show()
    app.exec_()

if __name__ == '__main__':
    main()