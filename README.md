# RIFE-Colab + GUI
RIFE interpolation script for Google Colab, and GUI for local execution under Windows and Linux.
[**RIFE Git repo**](https://github.com/hzwer/arXiv2020-RIFE)

[**Open in Google Colab**](https://colab.research.google.com/github/HeylonNHP/RIFE-Colab/blob/main/RIFE_Colab.ipynb)

## Features
* Flexible input options, using FFmpeg for decoding
* Output using x264, or NVENC for fast encoding performance
* Multiple GPU processing support (SLI not required, different GPU combinations can be used)
* Different frame handling modes - including duplicate frame removal with maintenance of output FPS
* The ability to create a loop friendly output for GIFs and looping videos
* No limit on maximum interpolation factor
* Scene-change detection
* Batch video processing

## Installation for local use
### Inital steps:
1. Ensure 7-zip is accessible from the system path (Linux/Windows) or installed in C:\Program Files\7-Zip
2. Git is installed and accessible from the system path
3. Python 3.8 is installed and accessible from the system path (**Tick Add Python 3.8 to PATH during install**)

### Installation
From within the terminal (Linux) or git bash (Windows):
1. `git clone --branch main --recurse-submodules https://github.com/HeylonNHP/RIFE-Colab.git RIFEcolab`
2. `cd RIFEcolab`
3. `python install_dependencies.py`
4. `pip install spyder` (**Linux only**)
5. `python main_gui.py`

Alternatively Windows users may visit the releases page to download a packaged and compiled version of the GUI.