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

#sys.path.insert(0, os.getcwd() + os.path.sep + 'arXiv2020RIFE')
#print(sys.path)
from generalInterpolationProceedures import *

class RIFEGUIMAINWINDOW(QMainWindow,mainGuiUi.Ui_MainWindow):
    progressBarUpdateSignal = pyqtSignal(object)
    runAllStepsButtonEnabledSignal = pyqtSignal(bool)
    extractFramesButtonEnabledSignal = pyqtSignal(bool)
    interpolateFramesButtonEnabledSignal = pyqtSignal(bool)
    encodeOutputButtonEnabledSignal = pyqtSignal(bool)

    batchProcessingMode:bool = False
    nonBatchControlLabels:dict = {}

    def __init__(self):
        # This is needed here for variable and method access
        super().__init__()
        self.setupUi(self)  # Initialize a design

        self.verticalLayout_5.setAlignment(Qt.AlignTop)
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
        self.progressBarUpdateSignal.connect(self.updateUIprogress)

        self.runAllStepsButtonEnabledSignal.connect(self.updaterunAllStepsButtonEnabled)
        self.extractFramesButtonEnabledSignal.connect(self.updateextractFramesButtonEnabled)
        self.interpolateFramesButtonEnabledSignal.connect(self.updateinterpolateFramesButtonEnabled)
        self.encodeOutputButtonEnabledSignal.connect(self.updateencodeOutputButtonEnabled)

        self.tabWidget.currentChanged.connect(self.changedTabs)

        self.nonBatchControlLabels['input'] = self.inputLabel.text()
        self.nonBatchControlLabels['runall'] = self.runAllStepsButton.text()

    def changedTabs(self):
        if self.tabWidget.currentIndex() == 3:
            self.batchProcessingMode = True

            self.inputLabel.setText("Input folder")
            self.runAllStepsButton.setText("Run Batch")

            self.extractFramesButton.setEnabled(False)
            self.interpolateFramesButton.setEnabled(False)
            self.encodeOutputButton.setEnabled(False)
        else:
            self.batchProcessingMode = False

            self.inputLabel.setText(self.nonBatchControlLabels['input'])
            self.runAllStepsButton.setText(self.nonBatchControlLabels['runall'])

            self.extractFramesButton.setEnabled(True)
            self.interpolateFramesButton.setEnabled(True)
            self.encodeOutputButton.setEnabled(True)

    def browseInputFile(self):
        file = None
        if not self.batchProcessingMode:
            file, _filter = QFileDialog.getOpenFileName(caption="Open video file to interpolate")
        else:
            file = str(QFileDialog.getExistingDirectory(caption="Open folder of files to interpolate"))
        print(str(file))
        self.inputFilePathText.setText(file)

        if not self.batchProcessingMode:
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

    def runAllSteps(self):
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

        if self.batchProcessingMode:
            if not os.path.isdir(inputFile):
                QMessageBox.critical(self,"Path","For batch processing, the input path must be a folder")
                return
        else:
            if not os.path.isfile(inputFile):
                QMessageBox.critical(self,"Path", "For single video processing, the input path must be a video file")
                return

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

        targetFPS = float(self.targetFPSnumber.value())

        # Exceptions are hidden on the PYQt5 thread - Run interpolator on separate thread to see them
        interpolateThread = threading.Thread(target=self.runAllInterpolationStepsThread,args=(inputFile, interpolationFactor, loopable, mode, crfout, clearpngs, nonlocalpngs,
                        scenechangeSensitivity, mpdecimateSensitivity, usenvenc, useAutoencode, blocksize, targetFPS,step1,step2,step3,))

        interpolateThread.start()

    def runAllInterpolationStepsThread(self,inputFile, interpolationFactor, loopable, mode, crfout, clearpngs, nonlocalpngs,
                        scenechangeSensitivity, mpdecimateSensitivity, usenvenc, useAutoencode, blocksize, targetFPS,step1,step2,step3):

        batchProcessing = self.batchProcessingMode

        self.runAllStepsButtonEnabledSignal.emit(False)
        if not batchProcessing:
            self.extractFramesButtonEnabledSignal.emit(False)
            self.interpolateFramesButtonEnabledSignal.emit(False)
            self.encodeOutputButtonEnabledSignal.emit(False)

        if not batchProcessing:
            performAllSteps(inputFile,interpolationFactor,loopable,mode,crfout,clearpngs,nonlocalpngs,scenechangeSensitivity,mpdecimateSensitivity,
                            usenvenc,useAutoencode,blocksize,step1=step1,step2=step2,step3=step3)
        else:
            batchInterpolateFolder(inputFile,mode,crfout,targetFPS,clearpngs,nonlocalpngs,scenechangeSensitivity,mpdecimateSensitivity,
                                   usenvenc,useAutoencode,blocksize)

        self.runAllStepsButtonEnabledSignal.emit(True)
        if not batchProcessing:
            self.extractFramesButtonEnabledSignal.emit(True)
            self.interpolateFramesButtonEnabledSignal.emit(True)
            self.encodeOutputButtonEnabledSignal.emit(True)

    def getProgressUpdate(self,progress:InterpolationProgress):
        self.progressBarUpdateSignal.emit(progress)

    def updateUIprogress(self,data:InterpolationProgress):
        self.interpolationProgressBar.setMaximum(data.totalFrames)
        self.interpolationProgressBar.setValue(data.completedFrames)

    def updaterunAllStepsButtonEnabled(self,data:bool):
        self.runAllStepsButton.setEnabled(data)

    def updateextractFramesButtonEnabled(self,data:bool):
        self.extractFramesButton.setEnabled(data)

    def updateinterpolateFramesButtonEnabled(self,data:bool):
        self.interpolateFramesButton.setEnabled(data)

    def updateencodeOutputButtonEnabled(self,data:bool):
        self.encodeOutputButton.setEnabled(data)

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