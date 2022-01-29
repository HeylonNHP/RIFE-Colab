import os
from Globals.GlobalValues import GlobalValues


def choose_frames(frames_folder, desired_fps):
    frame_files = os.listdir(frames_folder)
    frame_files.sort()
    last_file = int(frame_files[-1][:-4])
    desired_frame_spacing = (1 / desired_fps) * GlobalValues.timebase
    timecodes_file_string = ""
    current_time = desired_frame_spacing
    count = 1
    current_list_index = 0
    while (current_time - desired_frame_spacing) <= last_file:
        current_frame = int(frame_files[current_list_index][:-4])

        while not (
                current_frame >= round(current_time - desired_frame_spacing)):  # and current_frame <= round(current_time)):
            if not current_list_index >= len(frame_files) - 1:
                current_list_index += 1
            else:
                break

            current_frame = int(frame_files[current_list_index][:-4])

        # Build timecodes file
        frame_file = frames_folder + os.path.sep + frame_files[current_list_index]
        timecodes_file_string += ("file '" + frame_file + "'\n")

        count += 1
        current_time = ((1 / desired_fps) * count) * GlobalValues.timebase
    print(timecodes_file_string)
    out_file = open(frames_folder + os.path.sep + 'framesCFR.txt', 'w')
    out_file.write(timecodes_file_string)
    out_file.close()


def choose_frames_list(frame_files, desired_fps, start_time=0, start_count=0):
    chosen_frame_list: list = []

    # frameFiles = os.listdir(framesFolder)
    frame_files.sort()

    last_file_number = int(frame_files[-1][:-4])
    desired_frame_spacing = (1 / desired_fps) * GlobalValues.timebase

    current_time = desired_frame_spacing
    count = 1
    if not start_time == 0:
        current_time = start_time
    if not start_count == 0:
        count = start_count

    current_list_index = 0

    # For when the first frame doesn't start from 0ms
    # Advance current time to the first frame's timecode
    while current_time < int(frame_files[0][:-4]):
        count += 1
        current_time = ((1 / desired_fps) * count) * GlobalValues.timebase

    while (current_time - desired_frame_spacing) <= last_file_number:
        current_frame = int(frame_files[current_list_index][:-4])
        while current_frame < round(current_time - desired_frame_spacing):
            if current_list_index < len(frame_files) - 1:
                current_list_index += 1
            else:
                break
            current_frame = int(frame_files[current_list_index][:-4])
        frame_file = frame_files[current_list_index]
        chosen_frame_list.append(frame_file)

        count += 1
        current_time = ((1 / desired_fps) * count) * GlobalValues.timebase

    return chosen_frame_list, (int(frame_files[-1][:-4]) - int(frame_files[0][:-4])), current_time, count
