# https://raevskymichail.medium.com/python-gui-building-a-simple-application-with-pyqt-and-qt-designer-e9f8cda76246
import sys
# from PyQt5 import QtWidgets
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import mainGuiUi
# from PyQt5 import uic
import os
import json
import glob
import threading
import addInstalldirToPath
from Globals.MachinePowerStatesHandler import MachinePowerStatesHandler
from Globals.EncoderConfig import EncoderConfig

sys.path.insert(0, os.getcwd() + os.path.sep + 'arXiv2020RIFE')
print(sys.path)
#sys.path.insert(0, os.getcwd() + os.path.sep + 'FLAVR')
#sys.path.append(os.getcwd() + os.path.sep + 'FLAVR')
#print(sys.path)
from generalInterpolationProceedures import *


class RIFEGUIMAINWINDOW(QMainWindow, mainGuiUi.Ui_MainWindow):
    MainGUIpath = os.path.realpath(__file__)
    MainGUIpath = MainGUIpath[:MainGUIpath.rindex(os.path.sep)]
    MAIN_PRESET_FILE = MainGUIpath + os.path.sep + "defaults.preset"

    progressBarUpdateSignal = pyqtSignal(object)
    runAllStepsButtonEnabledSignal = pyqtSignal(bool)
    extractFramesButtonEnabledSignal = pyqtSignal(bool)
    interpolateFramesButtonEnabledSignal = pyqtSignal(bool)
    encodeOutputButtonEnabledSignal = pyqtSignal(bool)

    batchProcessingMode: bool = False
    nonBatchControlLabels: dict = {}

    def __init__(self):
        # This is needed here for variable and method access
        super().__init__()
        self.setupUi(self)  # Initialize a design
        # uic.loadUi("main_gui.ui", self)

        self.mode3ExtraOptionsEnable(False)

        self.verticalLayout_6.setAlignment(Qt.AlignTop)
        self.verticalLayout_5.setAlignment(Qt.AlignTop)
        self.verticalLayout_4.setAlignment(Qt.AlignTop)
        self.verticalLayout_3.setAlignment(Qt.AlignTop)
        self.verticalLayout_2.setAlignment(Qt.AlignTop)

        self.updateRifeModelButton.clicked.connect(self.grabLatestRifeModel)

        self.browseInputButton.clicked.connect(self.browseInputFile)
        self.runAllStepsButton.clicked.connect(self.runAllSteps)
        self.extractFramesButton.clicked.connect(self.runStep1)
        self.interpolateFramesButton.clicked.connect(self.runStep2)
        self.encodeOutputButton.clicked.connect(self.runStep3)

        self.interpolationFactorSelect.currentTextChanged.connect(self.updateVideoFPSstats)
        self.accountForDuplicateFramesCheckbox.stateChanged.connect(self.updateVideoFPSstats)
        self.useAccurateFPSCheckbox.stateChanged.connect(self.updateVideoFPSstats)
        self.modeSelect.currentTextChanged.connect(self.updateVideoFPSstats)
        self.mode3TargetFPS.valueChanged.connect(self.updateVideoFPSstats)
        self.mode3UseTargetFPS.toggled.connect(self.updateVideoFPSstats)
        self.mode3UseInterpolationFactor.toggled.connect(self.updateVideoFPSstats)

        self.modeSelect.currentTextChanged.connect(self.checkCurrentMode)

        subscribeTointerpolationProgressUpdate(self.getProgressUpdate)
        self.progressBarUpdateSignal.connect(self.updateUIprogress)

        self.runAllStepsButtonEnabledSignal.connect(self.updaterunAllStepsButtonEnabled)
        self.extractFramesButtonEnabledSignal.connect(self.updateextractFramesButtonEnabled)
        self.interpolateFramesButtonEnabledSignal.connect(self.updateinterpolateFramesButtonEnabled)
        self.encodeOutputButtonEnabledSignal.connect(self.updateencodeOutputButtonEnabled)

        self.tabWidget.currentChanged.connect(self.changedTabs)

        self.nonBatchControlLabels['input'] = self.inputLabel.text()
        self.nonBatchControlLabels['runall'] = self.runAllStepsButton.text()

        self.saveGUIstateCheck.stateChanged.connect(self.onSaveGUIstateCheckChange)

        self.loadSettingsFile(self.MAIN_PRESET_FILE)

        self.preset_updateList()
        self.createNewPresetButton.clicked.connect(self.preset_createNew)
        self.saveSelectedPresetButton.clicked.connect(self.preset_save)
        self.loadSelectedPresetButton.clicked.connect(self.preset_load)
        self.deleteSelectedPresetButton.clicked.connect(self.preset_delete)

        self.inputFilePathText.textChanged.connect(self.inputBoxTextChanged)

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

    def mode3ExtraOptionsEnable(self,enable:bool):
        self.mode3UseInterpolationFactor.setHidden(not enable)
        self.mode3UseTargetFPS.setHidden(not enable)
        self.mode3TargetFPS.setHidden(not enable)
    def checkCurrentMode(self):
        mode: int = int(self.modeSelect.currentText())
        if mode == 3:
            self.mode3ExtraOptionsEnable(True)
        else:
            self.mode3ExtraOptionsEnable(False)


    def inputBoxTextChanged(self):
        if not self.batchProcessingMode:
            self.updateVideoFPSstats()

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

    lastMPdecimate: str = ""
    lastVideoPath:str = ""
    lastVideoFPS: float = None

    def updateVideoFPSstats(self):
        file = str(self.inputFilePathText.text())
        if not os.path.exists(file):
            return
        if not os.path.isfile(file):
            return

        accurateFPS: bool = self.useAccurateFPSCheckbox.isChecked()
        accountForDuplicatesInFPS: bool = self.accountForDuplicateFramesCheckbox.isChecked()

        videoFPS = None
        mode = int(str(self.modeSelect.currentText()))
        currentMPdecimate = str(self.mpdecimateText.text())
        currentVideoPath = str(self.inputFilePathText.text())
        if (mode == 3 or mode == 4) and accountForDuplicatesInFPS:
            if self.lastVideoFPS is not None and self.lastMPdecimate == currentMPdecimate and currentVideoPath == self.lastVideoPath:
                videoFPS = self.lastVideoFPS

        if videoFPS is None:
            videoFPS = getOutputFPS(str(file), int(str(self.modeSelect.currentText())), 1,
                                    accurateFPS, accountForDuplicatesInFPS, str(self.mpdecimateText.text()))

        if (mode == 3 or mode == 4) and accountForDuplicatesInFPS:
            self.lastVideoFPS = videoFPS
            self.lastMPdecimate = str(self.mpdecimateText.text())
            self.lastVideoPath = currentVideoPath

        print(videoFPS)
        self.VideostatsInputFPStext.setText(str(videoFPS))
        if mode == 3 and self.mode3UseTargetFPS.isChecked():
            self.VideostatsOutputFPStext.setText(str(self.mode3TargetFPS.value()))
        else:
            self.VideostatsOutputFPStext.setText(str(videoFPS * float(self.interpolationFactorSelect.currentText())))

    def runStep1(self):
        self.runAllInterpolationSteps(step1=True, step2=False, step3=False)

    def runStep2(self):
        self.runAllInterpolationSteps(step1=False, step2=True, step3=False)

    def runStep3(self):
        self.runAllInterpolationSteps(step1=False, step2=False, step3=True)

    def runAllSteps(self):
        # This function is required because python is stupid, and will set the first boolean function parameter to false
        self.runAllInterpolationSteps()

    def runAllInterpolationSteps(self, step1=True, step2=True, step3=True):
        selectedGPUs = str(self.gpuidsSelect.currentText()).split(",")
        selectedGPUs = [int(i) for i in selectedGPUs]

        encoderConfig:EncoderConfig = EncoderConfig()

        encoderConfig.setNvencGPUID(selectedGPUs[0])

        #setNvencSettings(selectedGPUs[0], 'slow')

        setGPUinterpolationOptions(int(self.batchthreadsNumber.value()), selectedGPUs)

        inputFile = str(self.inputFilePathText.text())
        if os.name == 'nt':
            inputFile = inputFile.replace('/', '\\')

        if self.batchProcessingMode:
            if not os.path.isdir(inputFile):
                QMessageBox.critical(self, "Path", "For batch processing, the input path must be a folder")
                return
        else:
            if not os.path.isfile(inputFile):
                QMessageBox.critical(self, "Path", "For single video processing, the input path must be a video file")
                return

        interpolationFactor = int(self.interpolationFactorSelect.currentText())

        loopable = bool(self.loopoutputCheck.isChecked())
        loopRepetitions = bool(self.loopOutputRepeatedLoopsCheck.isChecked())
        loopPreferredLength = float(self.loopOutputPreferredLengthNumber.value())
        loopMaxLength = float(self.loopOutputMaxLengthNumber.value())

        mode = int(self.modeSelect.currentText())
        crfout = int(self.crfoutNumber.value())
        clearpngs = bool(self.clearpngsCheck.isChecked())
        nonlocalpngs = bool(self.nonlocalpngsCheck.isChecked())
        scenechangeSensitivity = float(self.scenechangeSensitivityNumber.value())
        mpdecimateSensitivity = str(self.mpdecimateText.text())
        mpdecimateEnabled = bool(self.mpdecimateEnableCheck.isChecked())
        usenvenc = bool(self.nvencCheck.isChecked())
        useAutoencode = bool(self.autoencodeCheck.isChecked())
        blocksize = int(self.autoencodeBlocksizeNumber.value())
        limitFPSenabled:bool = bool(self.enableLimitFPScheck.isChecked())
        limitFPSvalue:float = float(self.limitFPSnumber.value())
        mode3TargetFPSEnabled: bool = bool(self.mode3UseTargetFPS.isChecked())
        mode3TargetFPSValue: float = float(self.mode3TargetFPS.value())
        interpolationAI: str = str(self.InterpolationAIComboBox.currentText())

        targetFPS = float(self.targetFPSnumber.value())

        accurateFPS: bool = self.useAccurateFPSCheckbox.isChecked()
        accountForDuplicatesInFPS: bool = self.accountForDuplicateFramesCheckbox.isChecked()

        afterInterpolationAction: int = self.systemPowerOptionsComboBox.currentIndex()

        useHalfPrecisionChecked: bool = self.enableHalfPrecisionFloatsCheck.isChecked()

        outputEncoderSelection: int = self.outputEncoderSelectComboBox.currentIndex()

        outputColourspace: str = self.colourspaceSelectionComboBox.currentText()

        UhdScaleFactor: float = self.UHDscaleNumber.value()

        setUseHalfPrecision(useHalfPrecisionChecked)

        if usenvenc:
            encoderConfig.enableNvenc(True)
            encoderConfig.setEncodingPreset('slow')
            encoderConfig.setEncodingCRF(crfout+10)
        else:
            encoderConfig.setEncodingPreset('veryslow')
            encoderConfig.setEncodingCRF(crfout)

        if outputEncoderSelection == 0:
            encoderConfig.enableH265(False)
            encoderConfig.setEncodingProfile('high')
        else:
            encoderConfig.enableH265(True)
            encoderConfig.setEncodingProfile('main')
        if limitFPSenabled:
            encoderConfig.setFFmpegOutputFPS(limitFPSenabled,limitFPSvalue)

        encoderConfig.setPixelFormat(outputColourspace)
        encoderConfig.setLoopingOptions(loopPreferredLength,loopMaxLength,loopRepetitions)

        interpolatorConfig = InterpolatorConfig()
        interpolatorConfig.setMode(mode)
        interpolatorConfig.setClearPngs(clearpngs)
        interpolatorConfig.setLoopable(loopable)
        interpolatorConfig.setAccountForDuplicateFrames(accountForDuplicatesInFPS)
        interpolatorConfig.setInterpolationFactor(interpolationFactor)
        interpolatorConfig.setMpdecimateSensitivity(mpdecimateSensitivity)
        interpolatorConfig.setUseAccurateFPS(accurateFPS)
        interpolatorConfig.setNonlocalPngs(nonlocalpngs)
        interpolatorConfig.setScenechangeSensitivity(scenechangeSensitivity)
        interpolatorConfig.setUhdScale(UhdScaleFactor)
        interpolatorConfig.setMode3TargetFPS(mode3TargetFPSEnabled,mode3TargetFPSValue)
        interpolatorConfig.setInterpolator(interpolationAI)
        interpolatorConfig.enableMpdecimate(mpdecimateEnabled)

        # Exceptions are hidden on the PYQt5 thread - Run interpolator on separate thread to see them
        interpolateThread = threading.Thread(target=self.runAllInterpolationStepsThread, args=(
        inputFile, interpolatorConfig, useAutoencode, blocksize, targetFPS, step1, step2, step3,encoderConfig ,afterInterpolationAction))

        interpolateThread.start()

    def runAllInterpolationStepsThread(self, inputFile, interpolatorConfig: InterpolatorConfig, useAutoencode, blocksize, targetFPS, step1,
                                       step2, step3, encoderConfig: EncoderConfig,
                                       afterInterpolationIsFinishedActionChoice=0):

        batchProcessing = self.batchProcessingMode

        self.runAllStepsButtonEnabledSignal.emit(False)
        if not batchProcessing:
            self.extractFramesButtonEnabledSignal.emit(False)
            self.interpolateFramesButtonEnabledSignal.emit(False)
            self.encodeOutputButtonEnabledSignal.emit(False)

        if not batchProcessing:
            performAllSteps(inputFile, interpolatorConfig, encoderConfig, useAutoencode, blocksize, step1=step1, step2=step2,
                            step3=step3)
        else:
            batchInterpolateFolder(inputFile, interpolatorConfig, targetFPS, encoderConfig, useAutoencode, blocksize)

        self.runAllStepsButtonEnabledSignal.emit(True)
        if not batchProcessing:
            self.extractFramesButtonEnabledSignal.emit(True)
            self.interpolateFramesButtonEnabledSignal.emit(True)
            self.encodeOutputButtonEnabledSignal.emit(True)

        if step3 or (useAutoencode and step2):
            # The user likely doesn't want the machine to shutdown/suspend before the output is processed
            mps = MachinePowerStatesHandler()
            if afterInterpolationIsFinishedActionChoice == 1:
                # Shutdown
                mps.shutdownComputer()
            elif afterInterpolationIsFinishedActionChoice == 2:
                # Suspend
                mps.suspendComputer()


    def getProgressUpdate(self, progress: InterpolationProgress):
        self.progressBarUpdateSignal.emit(progress)

    def updateUIprogress(self, data: InterpolationProgress):
        self.interpolationProgressBar.setMaximum(data.totalFrames)
        self.interpolationProgressBar.setValue(data.completedFrames)

    def updaterunAllStepsButtonEnabled(self, data: bool):
        self.runAllStepsButton.setEnabled(data)

    def updateextractFramesButtonEnabled(self, data: bool):
        self.extractFramesButton.setEnabled(data)

    def updateinterpolateFramesButtonEnabled(self, data: bool):
        self.interpolateFramesButton.setEnabled(data)

    def updateencodeOutputButtonEnabled(self, data: bool):
        self.encodeOutputButton.setEnabled(data)

    def grabLatestRifeModel(self):
        downloadRIFE(installPath, onWindows,forceDownloadModels=True)

    def getCurrentUIsettings(self):
        settingsDict = {}

        settingsDict['mpdecimate'] = str(self.mpdecimateText.text())
        settingsDict['nonlocalpngs'] = bool(self.nonlocalpngsCheck.isChecked())
        settingsDict['clearpngs'] = bool(self.clearpngsCheck.isChecked())
        settingsDict['enableMpdecimate'] = bool(self.mpdecimateEnableCheck.isChecked())

        settingsDict['useaccuratefps'] = bool(self.useAccurateFPSCheckbox.isChecked())
        settingsDict['accountforduplicateframes'] = bool(self.accountForDuplicateFramesCheckbox.isChecked())
        settingsDict['interpolationfactor'] = str(self.interpolationFactorSelect.currentText())
        settingsDict['framehandlingmode'] = int(self.modeSelect.currentIndex())
        settingsDict['scenechangesensitivity'] = float(self.scenechangeSensitivityNumber.value())
        settingsDict['gpuids'] = str(self.gpuidsSelect.currentText())
        settingsDict['batchthreads'] = int(self.batchthreadsNumber.value())
        settingsDict['useHalfPrecisionFloats'] = bool(self.enableHalfPrecisionFloatsCheck.isChecked())
        settingsDict['UHDscaleFactor'] = float(self.UHDscaleNumber.value())
        settingsDict['interpolationAIchoice'] = int(self.InterpolationAIComboBox.currentIndex())

        settingsDict['mode3UseInterpolationFactor'] = bool(self.mode3UseInterpolationFactor.isChecked())
        settingsDict['mode3UseTargetFPS'] = bool(self.mode3UseTargetFPS.isChecked())
        settingsDict['mode3TargetFPS'] = float(self.mode3TargetFPS.value())

        settingsDict['loopoutput'] = bool(self.loopoutputCheck.isChecked())
        settingsDict['loopablePreferredLength'] = float(self.loopOutputPreferredLengthNumber.value())
        settingsDict['loopableMaxLength'] = float(self.loopOutputMaxLengthNumber.value())
        settingsDict['loopRepetitionsEnabled'] = bool(self.loopOutputRepeatedLoopsCheck.isChecked())
        settingsDict['usenvenc'] = bool(self.nvencCheck.isChecked())
        settingsDict['crfout'] = float(self.crfoutNumber.value())
        settingsDict['useautoencoding'] = bool(self.autoencodeCheck.isChecked())
        settingsDict['autoencodingblocksize'] = int(self.autoencodeBlocksizeNumber.value())
        settingsDict['outputEncoderSelection'] = int(self.outputEncoderSelectComboBox.currentIndex())
        settingsDict['outputPixelFormat'] = int(self.colourspaceSelectionComboBox.currentIndex())
        settingsDict['limitFPSEnable'] = bool(self.enableLimitFPScheck.isChecked())
        settingsDict['limitFPSValue'] = float(self.limitFPSnumber.value())

        settingsDict['batchtargetfps'] = float(self.targetFPSnumber.value())

        settingsDict['saveguistate'] = bool(self.saveGUIstateCheck.isChecked())

        settingsDict['systemPowerOption'] = int(self.systemPowerOptionsComboBox.currentIndex())

        return settingsDict

    def setCurrentUIsettings(self,settingsDict:dict):
        if 'mpdecimate' in settingsDict:
            self.mpdecimateText.setText(settingsDict['mpdecimate'])
        if 'nonlocalpngs' in settingsDict:
            self.nonlocalpngsCheck.setChecked(settingsDict['nonlocalpngs'])
        if 'clearpngs' in settingsDict:
            self.clearpngsCheck.setChecked(settingsDict['clearpngs'])
        if 'enableMpdecimate' in settingsDict:
            self.mpdecimateEnableCheck.setChecked(settingsDict['enableMpdecimate'])

        if 'useaccuratefps' in settingsDict:
            self.useAccurateFPSCheckbox.setChecked(settingsDict['useaccuratefps'])
        if 'accountforduplicateframes' in settingsDict:
            self.accountForDuplicateFramesCheckbox.setChecked(settingsDict['accountforduplicateframes'])
        if 'interpolationfactor' in settingsDict:
            self.interpolationFactorSelect.setCurrentText(settingsDict['interpolationfactor'])
        if 'framehandlingmode' in settingsDict:
            self.modeSelect.setCurrentIndex(settingsDict['framehandlingmode'])
        if 'scenechangesensitivity' in settingsDict:
            self.scenechangeSensitivityNumber.setValue(settingsDict['scenechangesensitivity'])
        if 'gpuids' in settingsDict:
            self.gpuidsSelect.setCurrentText(settingsDict['gpuids'])
        if 'batchthreads' in settingsDict:
            self.batchthreadsNumber.setValue(settingsDict['batchthreads'])
        if 'useHalfPrecisionFloats' in settingsDict:
            self.enableHalfPrecisionFloatsCheck.setChecked(settingsDict['useHalfPrecisionFloats'])
        if 'UHDscaleFactor' in settingsDict:
            self.UHDscaleNumber.setValue(settingsDict['UHDscaleFactor'])
        if 'interpolationAIchoice' in settingsDict:
            self.InterpolationAIComboBox.setCurrentIndex(settingsDict['interpolationAIchoice'])

        if 'mode3UseInterpolationFactor' in settingsDict:
            self.mode3UseInterpolationFactor.setChecked(settingsDict['mode3UseInterpolationFactor'])
        if 'mode3UseTargetFPS' in settingsDict:
            self.mode3UseTargetFPS.setChecked(settingsDict['mode3UseTargetFPS'])
        if 'mode3TargetFPS' in settingsDict:
            self.mode3TargetFPS.setValue(settingsDict['mode3TargetFPS'])

        if 'loopoutput' in settingsDict:
            self.loopoutputCheck.setChecked(settingsDict['loopoutput'])
        if 'loopablePreferredLength' in settingsDict:
            self.loopOutputPreferredLengthNumber.setValue(settingsDict['loopablePreferredLength'])
        if 'loopableMaxLength' in settingsDict:
            self.loopOutputMaxLengthNumber.setValue(settingsDict['loopableMaxLength'])
        if 'loopRepetitionsEnabled' in settingsDict:
            self.loopOutputRepeatedLoopsCheck.setChecked(settingsDict['loopRepetitionsEnabled'])
        if 'usenvenc' in settingsDict:
            self.nvencCheck.setChecked(settingsDict['usenvenc'])
        if 'crfout' in settingsDict:
            self.crfoutNumber.setValue(settingsDict['crfout'])
        if 'useautoencoding' in settingsDict:
            self.autoencodeCheck.setChecked(settingsDict['useautoencoding'])
        if 'autoencodingblocksize' in settingsDict:
            self.autoencodeBlocksizeNumber.setValue(settingsDict['autoencodingblocksize'])
        if 'outputEncoderSelection' in settingsDict:
            self.outputEncoderSelectComboBox.setCurrentIndex(settingsDict['outputEncoderSelection'])
        if 'outputPixelFormat' in settingsDict:
            self.colourspaceSelectionComboBox.setCurrentIndex(settingsDict['outputPixelFormat'])
        if 'limitFPSEnable' in settingsDict:
            self.enableLimitFPScheck.setChecked(settingsDict['limitFPSEnable'])
        if 'limitFPSValue' in settingsDict:
            self.limitFPSnumber.setValue(settingsDict['limitFPSValue'])

        if 'batchtargetfps' in settingsDict:
            self.targetFPSnumber.setValue(settingsDict['batchtargetfps'])

        if 'saveguistate' in settingsDict:
            self.saveGUIstateCheck.setChecked(settingsDict['saveguistate'])

        if 'systemPowerOption' in settingsDict:
            self.systemPowerOptionsComboBox.setCurrentIndex(settingsDict['systemPowerOption'])

    def saveSettingsFile(self,filename:str):
        settingsDict = self.getCurrentUIsettings()
        outFile = open(filename,'w')
        outFile.write(json.dumps(settingsDict))
        outFile.close()

    def loadSettingsFile(self,filename:str):
        if not os.path.isfile(filename):
            return
        inFile = open(filename,'r')
        settingsDict:dict = json.loads(inFile.read())
        inFile.close()
        self.setCurrentUIsettings(settingsDict)

    def onSaveGUIstateCheckChange(self):
        # Remove preset file if user chooses not to save GUI state
        if not self.saveGUIstateCheck.isChecked():
            if os.path.isfile(self.MAIN_PRESET_FILE):
                os.remove(self.MAIN_PRESET_FILE)

    def preset_updateList(self):
        self.presetListComboBox.clear()

        for data in glob.glob(self.MainGUIpath + os.path.sep +"*.preset"):
            self.presetListComboBox.addItem(data[data.rindex(os.path.sep)+1:])

    def preset_createNew(self):
        presetName,okPressed = QInputDialog.getText(self,"Enter new preset name","Preset name:",QLineEdit.Normal, "")
        if not okPressed or presetName == "":
            return
        if presetName[-7:] != ".preset":
            presetName = presetName + ".preset"

        self.saveSettingsFile(self.MainGUIpath + os.path.sep + presetName)
        self.preset_updateList()

    def preset_load(self):
        selectedPreset = self.presetListComboBox.currentText()

        self.loadSettingsFile(self.MainGUIpath + os.path.sep + selectedPreset)

    def preset_save(self):
        selectedPreset = self.presetListComboBox.currentText()

        self.saveSettingsFile(self.MainGUIpath + os.path.sep + selectedPreset)

    def preset_delete(self):
        selectedPreset = self.presetListComboBox.currentIndex()
        selectedPresetText = self.presetListComboBox.currentText()
        self.presetListComboBox.removeItem(selectedPreset)

        if os.path.isfile(self.MainGUIpath + os.path.sep + selectedPresetText):
            print("DELETE",self.MainGUIpath + os.path.sep + selectedPresetText)
            os.remove(self.MainGUIpath + os.path.sep + selectedPresetText)

    def closeEvent(self, a0: QCloseEvent) -> None:
        if self.saveGUIstateCheck.isChecked():
            self.saveSettingsFile(self.MAIN_PRESET_FILE)

def excepthook(exc_type, exc_value, exc_tb):
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print("error catched!:")
    print("error message:\n", tb)
    QtWidgets.QApplication.quit()
    # or QtWidgets.QApplication.exit(0)


def main():
    app = QApplication(sys.argv)
    if 'Fusion' in QStyleFactory.keys():
        app.setStyle('Fusion')

    baseIntensity = 50

    pal = QPalette()
    pal.setColor(QPalette.Background, QColor(baseIntensity, baseIntensity, baseIntensity))
    pal.setColor(QPalette.Window, QColor(baseIntensity, baseIntensity, baseIntensity))
    pal.setColor(QPalette.WindowText, QColor(255 - baseIntensity, 255 - baseIntensity, 255 - baseIntensity))
    pal.setColor(QPalette.Base, QColor(baseIntensity + 10, baseIntensity + 10, baseIntensity + 10))
    pal.setColor(QPalette.AlternateBase, QColor(baseIntensity, baseIntensity, baseIntensity))
    pal.setColor(QPalette.ToolTipBase, QColor(baseIntensity, baseIntensity, baseIntensity))
    pal.setColor(QPalette.ToolTipText, QColor(255 - baseIntensity, 255 - baseIntensity, 255 - baseIntensity))
    pal.setColor(QPalette.Text, QColor(255 - baseIntensity, 255 - baseIntensity, 255 - baseIntensity))
    pal.setColor(QPalette.Button, QColor(baseIntensity + 10, baseIntensity + 10, baseIntensity + 10))
    pal.setColor(QPalette.ButtonText, QColor(255 - baseIntensity, 255 - baseIntensity, 255 - baseIntensity))
    pal.setColor(QPalette.BrightText, QColor(255, 0, 0))
    pal.setColor(QPalette.Highlight, QColor(125, 125, 200))
    pal.setColor(QPalette.HighlightedText, QColor(255 - baseIntensity, 255 - baseIntensity, 255 - baseIntensity))
    pal.setColor(QPalette.Dark, QColor(baseIntensity, baseIntensity, baseIntensity))
    pal.setColor(QPalette.Light, QColor(255-baseIntensity, 255-baseIntensity, 255-baseIntensity))
    app.setPalette(pal)

    sys.excepthook = excepthook
    window = RIFEGUIMAINWINDOW()
    window.show()
    ret = app.exec_()
    print("event loop exited")
    sys.exit(ret)


if __name__ == '__main__':
    main()
