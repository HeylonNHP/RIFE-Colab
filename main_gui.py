# https://raevskymichail.medium.com/python-gui-building-a-simple-application-with-pyqt-and-qt-designer-e9f8cda76246
import glob
import json
# from PyQt5 import uic
import os
import sys

# from PyQt5 import QtWidgets
from PyQt5 import QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import mainGuiUi
from Globals.MachinePowerStatesHandler import MachinePowerStatesHandler

sys.path.insert(0, os.getcwd() + os.path.sep + 'arXiv2020RIFE')
print(sys.path)

from generalInterpolationProceedures import *


def grab_latest_rife_model():
    download_rife(installPath, onWindows, force_download_models=True)


class RIFEGUIMAINWINDOW(QMainWindow, mainGuiUi.Ui_MainWindow):
    main_gui_path = os.path.realpath(__file__)
    main_gui_path = main_gui_path[:main_gui_path.rindex(os.path.sep)]
    MAIN_PRESET_FILE = main_gui_path + os.path.sep + "defaults.preset"

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

        self.mode3_extra_options_enable(False)

        self.verticalLayout_6.setAlignment(Qt.AlignTop)
        self.verticalLayout_5.setAlignment(Qt.AlignTop)
        self.verticalLayout_4.setAlignment(Qt.AlignTop)
        self.verticalLayout_3.setAlignment(Qt.AlignTop)
        self.verticalLayout_2.setAlignment(Qt.AlignTop)

        self.updateRifeModelButton.clicked.connect(grab_latest_rife_model)

        self.browseInputButton.clicked.connect(self.browse_input_file)
        self.runAllStepsButton.clicked.connect(self.run_all_steps)
        self.extractFramesButton.clicked.connect(self.run_step_1)
        self.interpolateFramesButton.clicked.connect(self.run_step_2)
        self.encodeOutputButton.clicked.connect(self.run_step_3)

        self.interpolationFactorSelect.currentTextChanged.connect(self.update_video_fps_stats)
        self.accountForDuplicateFramesCheckbox.stateChanged.connect(self.update_video_fps_stats)
        self.useAccurateFPSCheckbox.stateChanged.connect(self.update_video_fps_stats)
        self.modeSelect.currentTextChanged.connect(self.update_video_fps_stats)
        self.mode3TargetFPS.valueChanged.connect(self.update_video_fps_stats)
        self.mode3UseTargetFPS.toggled.connect(self.update_video_fps_stats)
        self.mode3UseInterpolationFactor.toggled.connect(self.update_video_fps_stats)

        self.modeSelect.currentTextChanged.connect(self.check_current_mode)

        subscribeTointerpolationProgressUpdate(self.get_progress_update)
        self.progressBarUpdateSignal.connect(self.update_ui_progress)

        self.runAllStepsButtonEnabledSignal.connect(self.update_run_all_steps_button_enabled)
        self.extractFramesButtonEnabledSignal.connect(self.update_extract_frames_button_enabled)
        self.interpolateFramesButtonEnabledSignal.connect(self.update_interpolate_frames_button_enabled)
        self.encodeOutputButtonEnabledSignal.connect(self.update_encode_output_button_enabled)

        self.tabWidget.currentChanged.connect(self.changed_tabs)

        self.nonBatchControlLabels['input'] = self.inputLabel.text()
        self.nonBatchControlLabels['runall'] = self.runAllStepsButton.text()

        self.saveGUIstateCheck.stateChanged.connect(self.on_save_gui_state_check_change)

        self.load_settings_file(self.MAIN_PRESET_FILE)

        self.preset_update_list()
        self.createNewPresetButton.clicked.connect(self.preset_create_new)
        self.saveSelectedPresetButton.clicked.connect(self.preset_save)
        self.loadSelectedPresetButton.clicked.connect(self.preset_load)
        self.deleteSelectedPresetButton.clicked.connect(self.preset_delete)

        self.inputFilePathText.textChanged.connect(self.input_box_text_changed)

        self.enableLosslessEncodingCheck.stateChanged.connect(self.lossless_mode_check_change)

    def changed_tabs(self):
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

    def lossless_mode_check_change(self):
        self.crfoutNumber.setEnabled(not self.enableLosslessEncodingCheck.isChecked())

    def mode3_extra_options_enable(self, enable: bool):
        self.mode3UseInterpolationFactor.setHidden(not enable)
        self.mode3UseTargetFPS.setHidden(not enable)
        self.mode3TargetFPS.setHidden(not enable)

    def check_current_mode(self):
        mode: int = int(self.modeSelect.currentText())
        if mode == 3:
            self.mode3_extra_options_enable(True)
        else:
            self.mode3_extra_options_enable(False)

    def input_box_text_changed(self):
        if not self.batchProcessingMode:
            self.update_video_fps_stats()

    def browse_input_file(self):
        file = None
        if not self.batchProcessingMode:
            file, _filter = QFileDialog.getOpenFileName(caption="Open video file to interpolate")
        else:
            file = str(QFileDialog.getExistingDirectory(caption="Open folder of files to interpolate"))
        print(str(file))
        self.inputFilePathText.setText(file)

        if not self.batchProcessingMode:
            self.update_video_fps_stats()

    lastMPdecimate: str = ""
    lastVideoPath: str = ""
    lastVideoFPS: float = None

    def update_video_fps_stats(self):
        file = str(self.inputFilePathText.text())
        if not os.path.exists(file):
            return
        if not os.path.isfile(file):
            return

        accurate_fps: bool = self.useAccurateFPSCheckbox.isChecked()
        account_for_duplicates_in_fps: bool = self.accountForDuplicateFramesCheckbox.isChecked()

        video_fps = None
        mode = int(str(self.modeSelect.currentText()))
        current_mpdecimate = str(self.mpdecimateText.text())
        current_video_path = str(self.inputFilePathText.text())
        if (mode == 3 or mode == 4) and account_for_duplicates_in_fps:
            if self.lastVideoFPS is not None and self.lastMPdecimate == current_mpdecimate and current_video_path == self.lastVideoPath:
                video_fps = self.lastVideoFPS

        if video_fps is None:
            video_fps = getOutputFPS(str(file), int(str(self.modeSelect.currentText())), 1,
                                     accurate_fps, account_for_duplicates_in_fps, str(self.mpdecimateText.text()))

        if (mode == 3 or mode == 4) and account_for_duplicates_in_fps:
            self.lastVideoFPS = video_fps
            self.lastMPdecimate = str(self.mpdecimateText.text())
            self.lastVideoPath = current_video_path

        print(video_fps)
        self.VideostatsInputFPStext.setText(str(video_fps))
        if mode == 3 and self.mode3UseTargetFPS.isChecked():
            self.VideostatsOutputFPStext.setText(str(self.mode3TargetFPS.value()))
        else:
            self.VideostatsOutputFPStext.setText(str(video_fps * float(self.interpolationFactorSelect.currentText())))

    def run_step_1(self):
        self.run_all_interpolation_steps(step1=True, step2=False, step3=False)

    def run_step_2(self):
        self.run_all_interpolation_steps(step1=False, step2=True, step3=False)

    def run_step_3(self):
        self.run_all_interpolation_steps(step1=False, step2=False, step3=True)

    def run_all_steps(self):
        # This function is required because python is stupid, and will set the first boolean function parameter to false
        self.run_all_interpolation_steps()

    def run_all_interpolation_steps(self, step1=True, step2=True, step3=True):
        selected_gpus = str(self.gpuidsSelect.currentText()).split(",")
        selected_gpus = [int(i) for i in selected_gpus]

        encoder_config: EncoderConfig = EncoderConfig()

        encoder_config.set_nvenc_gpu_id(selected_gpus[0])

        # setNvencSettings(selected_gpus[0], 'slow')

        setGPUinterpolationOptions(int(self.batchthreadsNumber.value()), selected_gpus)

        input_file = str(self.inputFilePathText.text())
        if os.name == 'nt':
            input_file = input_file.replace('/', '\\')

        if self.batchProcessingMode:
            if not os.path.isdir(input_file):
                QMessageBox.critical(self, "Path", "For batch processing, the input path must be a folder")
                return
        else:
            if not os.path.isfile(input_file):
                QMessageBox.critical(self, "Path", "For single video processing, the input path must be a video file")
                return

        interpolation_factor = int(self.interpolationFactorSelect.currentText())

        loopable = bool(self.loopoutputCheck.isChecked())
        loop_repetitions = bool(self.loopOutputRepeatedLoopsCheck.isChecked())
        loop_preferred_length = float(self.loopOutputPreferredLengthNumber.value())
        loop_max_length = float(self.loopOutputMaxLengthNumber.value())

        mode = int(self.modeSelect.currentText())
        crf_out = int(self.crfoutNumber.value())
        clear_pngs = bool(self.clearpngsCheck.isChecked())
        non_local_pngs = bool(self.nonlocalpngsCheck.isChecked())
        scenechange_sensitivity = float(self.scenechangeSensitivityNumber.value())
        mpdecimate_sensitivity = str(self.mpdecimateText.text())
        mpdecimate_enabled = bool(self.mpdecimateEnableCheck.isChecked())
        use_nvenc = bool(self.nvencCheck.isChecked())
        use_autoencode = bool(self.autoencodeCheck.isChecked())
        block_size = int(self.autoencodeBlocksizeNumber.value())
        limit_fps_enabled: bool = bool(self.enableLimitFPScheck.isChecked())
        limit_fps_value: float = float(self.limitFPSnumber.value())
        mode3_target_fps_enabled: bool = bool(self.mode3UseTargetFPS.isChecked())
        mode3_target_fps_value: float = float(self.mode3TargetFPS.value())
        interpolation_ai: str = str(self.InterpolationAIComboBox.currentText())
        losslessEncoding: bool = bool(self.enableLosslessEncodingCheck.isChecked())

        target_fps = float(self.targetFPSnumber.value())

        accurate_fps: bool = self.useAccurateFPSCheckbox.isChecked()
        account_for_duplicates_in_fps: bool = self.accountForDuplicateFramesCheckbox.isChecked()

        after_interpolation_action: int = self.systemPowerOptionsComboBox.currentIndex()

        use_half_precision_checked: bool = self.enableHalfPrecisionFloatsCheck.isChecked()

        output_encoder_selection: int = self.outputEncoderSelectComboBox.currentIndex()

        output_colourspace: str = self.colourspaceSelectionComboBox.currentText()

        uhd_scale_factor: float = self.UHDscaleNumber.value()

        set_use_half_precision(use_half_precision_checked)

        if use_nvenc:
            encoder_config.enable_nvenc(True)
            encoder_config.set_encoding_preset('slow')
            encoder_config.set_encoding_crf(crf_out + 10)
        else:
            encoder_config.set_encoding_preset('veryslow')
            encoder_config.set_encoding_crf(crf_out)

        if output_encoder_selection == 0:
            encoder_config.enable_h265(False)
            encoder_config.set_encoding_profile('high')
        else:
            encoder_config.enable_h265(True)
            encoder_config.set_encoding_profile('main')
        if limit_fps_enabled:
            encoder_config.set_ffmpeg_output_fps(limit_fps_enabled, limit_fps_value)

        encoder_config.set_lossless_encoding(losslessEncoding)
        encoder_config.set_pixel_format(output_colourspace)
        encoder_config.set_looping_options(loop_preferred_length, loop_max_length, loop_repetitions)

        interpolator_config = InterpolatorConfig()
        interpolator_config.setMode(mode)
        interpolator_config.setClearPngs(clear_pngs)
        interpolator_config.setLoopable(loopable)
        interpolator_config.setAccountForDuplicateFrames(account_for_duplicates_in_fps)
        interpolator_config.setInterpolationFactor(interpolation_factor)
        interpolator_config.setMpdecimateSensitivity(mpdecimate_sensitivity)
        interpolator_config.setUseAccurateFPS(accurate_fps)
        interpolator_config.setNonlocalPngs(non_local_pngs)
        interpolator_config.setScenechangeSensitivity(scenechange_sensitivity)
        interpolator_config.setUhdScale(uhd_scale_factor)
        interpolator_config.setMode3TargetFPS(mode3_target_fps_enabled, mode3_target_fps_value)
        interpolator_config.setInterpolator(interpolation_ai)
        interpolator_config.enableMpdecimate(mpdecimate_enabled)
        interpolator_config.setExitOnBackupThreadLimit(bool(self.threadRestartsMaxCheckbox.isChecked()))
        interpolator_config.setBackupThreadStartLimit(int(self.threadRestartsMaxSpinBox.value()))

        # Exceptions are hidden on the PYQt5 thread - Run interpolator on separate thread to see them
        interpolate_thread = threading.Thread(target=self.run_all_interpolation_steps_thread, args=(
            input_file, interpolator_config, use_autoencode, block_size, target_fps, step1, step2, step3,
            encoder_config,
            after_interpolation_action))

        interpolate_thread.start()

    def run_all_interpolation_steps_thread(self, input_file, interpolator_config: InterpolatorConfig, use_auto_encode,
                                           block_size, target_fps, step1,
                                           step2, step3, encoder_config: EncoderConfig,
                                           after_interpolation_is_finished_action_choice=0):

        batch_processing = self.batchProcessingMode

        self.runAllStepsButtonEnabledSignal.emit(False)
        if not batch_processing:
            self.extractFramesButtonEnabledSignal.emit(False)
            self.interpolateFramesButtonEnabledSignal.emit(False)
            self.encodeOutputButtonEnabledSignal.emit(False)

        if not batch_processing:
            performAllSteps(input_file, interpolator_config, encoder_config, use_auto_encode, block_size, step1=step1,
                            step2=step2,
                            step3=step3)
        else:
            batchInterpolateFolder(input_file, interpolator_config, target_fps, encoder_config, use_auto_encode,
                                   block_size)

        self.runAllStepsButtonEnabledSignal.emit(True)
        if not batch_processing:
            self.extractFramesButtonEnabledSignal.emit(True)
            self.interpolateFramesButtonEnabledSignal.emit(True)
            self.encodeOutputButtonEnabledSignal.emit(True)

        if step3 or (use_auto_encode and step2):
            # The user likely doesn't want the machine to shutdown/suspend before the output is processed
            mps = MachinePowerStatesHandler()
            if after_interpolation_is_finished_action_choice == 1:
                # Shutdown
                mps.shutdownComputer()
            elif after_interpolation_is_finished_action_choice == 2:
                # Suspend
                mps.suspendComputer()

    def get_progress_update(self, progress: InterpolationProgress):
        self.progressBarUpdateSignal.emit(progress)

    def update_ui_progress(self, data: InterpolationProgress):
        self.interpolationProgressBar.setMaximum(data.totalFrames)
        self.interpolationProgressBar.setValue(data.completedFrames)

    def update_run_all_steps_button_enabled(self, data: bool):
        self.runAllStepsButton.setEnabled(data)

    def update_extract_frames_button_enabled(self, data: bool):
        self.extractFramesButton.setEnabled(data)

    def update_interpolate_frames_button_enabled(self, data: bool):
        self.interpolateFramesButton.setEnabled(data)

    def update_encode_output_button_enabled(self, data: bool):
        self.encodeOutputButton.setEnabled(data)

    def get_current_ui_settings(self):
        settings_dict = {'mpdecimate': str(self.mpdecimateText.text()),
                         'nonlocalpngs': bool(self.nonlocalpngsCheck.isChecked()),
                         'clearpngs': bool(self.clearpngsCheck.isChecked()),
                         'enableMpdecimate': bool(self.mpdecimateEnableCheck.isChecked()),
                         'useaccuratefps': bool(self.useAccurateFPSCheckbox.isChecked()),
                         'accountforduplicateframes': bool(self.accountForDuplicateFramesCheckbox.isChecked()),
                         'interpolationfactor': str(self.interpolationFactorSelect.currentText()),
                         'framehandlingmode': int(self.modeSelect.currentIndex()),
                         'scenechangesensitivity': float(self.scenechangeSensitivityNumber.value()),
                         'gpuids': str(self.gpuidsSelect.currentText()),
                         'batchthreads': int(self.batchthreadsNumber.value()),
                         'useHalfPrecisionFloats': bool(self.enableHalfPrecisionFloatsCheck.isChecked()),
                         'UHDscaleFactor': float(self.UHDscaleNumber.value()),
                         'interpolationAIchoice': int(self.InterpolationAIComboBox.currentIndex()),
                         'mode3UseInterpolationFactor': bool(self.mode3UseInterpolationFactor.isChecked()),
                         'mode3UseTargetFPS': bool(self.mode3UseTargetFPS.isChecked()),
                         'mode3TargetFPS': float(self.mode3TargetFPS.value()),
                         'loopoutput': bool(self.loopoutputCheck.isChecked()),
                         'loopablePreferredLength': float(self.loopOutputPreferredLengthNumber.value()),
                         'loopableMaxLength': float(self.loopOutputMaxLengthNumber.value()),
                         'loopRepetitionsEnabled': bool(self.loopOutputRepeatedLoopsCheck.isChecked()),
                         'usenvenc': bool(self.nvencCheck.isChecked()), 'crfout': float(self.crfoutNumber.value()),
                         'useautoencoding': bool(self.autoencodeCheck.isChecked()),
                         'autoencodingblocksize': int(self.autoencodeBlocksizeNumber.value()),
                         'outputEncoderSelection': int(self.outputEncoderSelectComboBox.currentIndex()),
                         'outputPixelFormat': int(self.colourspaceSelectionComboBox.currentIndex()),
                         'limitFPSEnable': bool(self.enableLimitFPScheck.isChecked()),
                         'limitFPSValue': float(self.limitFPSnumber.value()),
                         'batchtargetfps': float(self.targetFPSnumber.value()),
                         'saveguistate': bool(self.saveGUIstateCheck.isChecked()),
                         'systemPowerOption': int(self.systemPowerOptionsComboBox.currentIndex()),
                         'limitBackupThreadRestarts': (
                             bool(self.threadRestartsMaxCheckbox.isChecked()),
                             int(self.threadRestartsMaxSpinBox.value())),
                         'losslessEncodingEnabled': bool(self.enableLosslessEncodingCheck.isChecked())}

        return settings_dict

    def set_current_ui_settings(self, settings_dict: dict):
        settings_mapping = {
            'mpdecimate': self.mpdecimateText.setText,
            'nonlocalpngs': self.nonlocalpngsCheck.setChecked,
            'clearpngs': self.clearpngsCheck.setChecked,
            'enableMpdecimate': self.mpdecimateEnableCheck.setChecked,
            'useaccuratefps': self.useAccurateFPSCheckbox.setChecked,
            'accountforduplicateframes': self.accountForDuplicateFramesCheckbox.setChecked,
            'interpolationfactor': self.interpolationFactorSelect.setCurrentText,
            'framehandlingmode': self.modeSelect.setCurrentIndex,
            'scenechangesensitivity': self.scenechangeSensitivityNumber.setValue,
            'gpuids': self.gpuidsSelect.setCurrentText,
            'batchthreads': self.batchthreadsNumber.setValue,
            'useHalfPrecisionFloats': self.enableHalfPrecisionFloatsCheck.setChecked,
            'UHDscaleFactor': self.UHDscaleNumber.setValue,
            'interpolationAIchoice': self.InterpolationAIComboBox.setCurrentIndex,
            'mode3UseInterpolationFactor': self.mode3UseInterpolationFactor.setChecked,
            'mode3UseTargetFPS': self.mode3UseTargetFPS.setChecked,
            'mode3TargetFPS': self.mode3TargetFPS.setValue,
            'loopoutput': self.loopoutputCheck.setChecked,
            'loopablePreferredLength': self.loopOutputPreferredLengthNumber.setValue,
            'loopableMaxLength': self.loopOutputMaxLengthNumber.setValue,
            'loopRepetitionsEnabled': self.loopOutputRepeatedLoopsCheck.setChecked,
            'usenvenc': self.nvencCheck.setChecked,
            'crfout': self.crfoutNumber.setValue,
            'useautoencoding': self.autoencodeCheck.setChecked,
            'autoencodingblocksize': self.autoencodeBlocksizeNumber.setValue,
            'outputEncoderSelection': self.outputEncoderSelectComboBox.setCurrentIndex,
            'outputPixelFormat': self.colourspaceSelectionComboBox.setCurrentIndex,
            'limitFPSEnable': self.enableLimitFPScheck.setChecked,
            'limitFPSValue': self.limitFPSnumber.setValue,
            'batchtargetfps': self.targetFPSnumber.setValue,
            'saveguistate': self.saveGUIstateCheck.setChecked,
            'systemPowerOption': self.systemPowerOptionsComboBox.setCurrentIndex,
            'limitBackupThreadRestarts': self._set_limit_backup_thread_restarts
        }
        for key, value in settings_dict.items():
            if key in settings_mapping:
                settings_mapping[key](value)

    def _set_limit_backup_thread_restarts(self, value):
        self.threadRestartsMaxCheckbox.setChecked(value[0])
        self.threadRestartsMaxSpinBox.setValue(value[1])

    def save_settings_file(self, filename: str):
        settings_dict = self.get_current_ui_settings()
        out_file = open(filename, 'w')
        out_file.write(json.dumps(settings_dict))
        out_file.close()

    def load_settings_file(self, filename: str):
        if not os.path.isfile(filename):
            return
        in_file = open(filename, 'r')
        settings_dict: dict = json.loads(in_file.read())
        in_file.close()
        self.set_current_ui_settings(settings_dict)

    def on_save_gui_state_check_change(self):
        # Remove preset file if user chooses not to save GUI state
        if not self.saveGUIstateCheck.isChecked():
            if os.path.isfile(self.MAIN_PRESET_FILE):
                os.remove(self.MAIN_PRESET_FILE)

    def preset_update_list(self):
        self.presetListComboBox.clear()

        for data in glob.glob(self.main_gui_path + os.path.sep + "*.preset"):
            self.presetListComboBox.addItem(data[data.rindex(os.path.sep) + 1:])

    def preset_create_new(self):
        preset_name, ok_pressed = QInputDialog.getText(self, "Enter new preset name", "Preset name:", QLineEdit.Normal,
                                                       "")
        if not ok_pressed or preset_name == "":
            return
        if preset_name[-7:] != ".preset":
            preset_name = preset_name + ".preset"

        self.save_settings_file(self.main_gui_path + os.path.sep + preset_name)
        self.preset_update_list()

    def preset_load(self):
        selected_preset = self.presetListComboBox.currentText()

        self.load_settings_file(self.main_gui_path + os.path.sep + selected_preset)

    def preset_save(self):
        selected_preset = self.presetListComboBox.currentText()

        self.save_settings_file(self.main_gui_path + os.path.sep + selected_preset)

    def preset_delete(self):
        selected_preset = self.presetListComboBox.currentIndex()
        selected_preset_text = self.presetListComboBox.currentText()
        self.presetListComboBox.removeItem(selected_preset)

        if os.path.isfile(self.main_gui_path + os.path.sep + selected_preset_text):
            print("DELETE", self.main_gui_path + os.path.sep + selected_preset_text)
            os.remove(self.main_gui_path + os.path.sep + selected_preset_text)

    def closeEvent(self, a0: QCloseEvent) -> None:
        if self.saveGUIstateCheck.isChecked():
            self.save_settings_file(self.MAIN_PRESET_FILE)


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

    base_intensity = 50

    pal = QPalette()
    pal.setColor(QPalette.Background, QColor(base_intensity, base_intensity, base_intensity))
    pal.setColor(QPalette.Window, QColor(base_intensity, base_intensity, base_intensity))
    pal.setColor(QPalette.WindowText, QColor(255 - base_intensity, 255 - base_intensity, 255 - base_intensity))
    pal.setColor(QPalette.Base, QColor(base_intensity + 10, base_intensity + 10, base_intensity + 10))
    pal.setColor(QPalette.AlternateBase, QColor(base_intensity, base_intensity, base_intensity))
    pal.setColor(QPalette.ToolTipBase, QColor(base_intensity, base_intensity, base_intensity))
    pal.setColor(QPalette.ToolTipText, QColor(255 - base_intensity, 255 - base_intensity, 255 - base_intensity))
    pal.setColor(QPalette.Text, QColor(255 - base_intensity, 255 - base_intensity, 255 - base_intensity))
    pal.setColor(QPalette.Button, QColor(base_intensity + 10, base_intensity + 10, base_intensity + 10))
    pal.setColor(QPalette.ButtonText, QColor(255 - base_intensity, 255 - base_intensity, 255 - base_intensity))
    pal.setColor(QPalette.BrightText, QColor(255, 0, 0))
    pal.setColor(QPalette.Highlight, QColor(125, 125, 200))
    pal.setColor(QPalette.HighlightedText, QColor(255 - base_intensity, 255 - base_intensity, 255 - base_intensity))
    pal.setColor(QPalette.Dark, QColor(base_intensity, base_intensity, base_intensity))
    pal.setColor(QPalette.Light, QColor(255 - base_intensity, 255 - base_intensity, 255 - base_intensity))
    app.setPalette(pal)

    sys.excepthook = excepthook
    window = RIFEGUIMAINWINDOW()
    window.show()
    ret = app.exec_()
    print("event loop exited")
    sys.exit(ret)


if __name__ == '__main__':
    main()
