import json

######     BLUETOOTH     ######
use_socket = True

addr = 'F0:08:D1:C8:1E:5E'
# addr = '70:B8:F6:5D:84:DE'
port = 1

######       PID         ######
PIDvalue = 1.0
kP = PIDvalue * 2.0
kI = 4e-3
kD = PIDvalue * 8.0

######        AI         ######
# push_offset = 23.75 # X, from center to push, in cm
push_offset = 17 # X, from center to push, in cm
distance_predict = 20 # WHEN TO PREDICT, in cm
distance_threshold_y = 4 # FIX WIGGLE, pixels

######      CAMERA       ######
camera_name = 2
camera_rotation = None # 0: 90° | 1: 180° | 2: 270° | None: 0°
camera_flip = None # 0: Vertical | 1: Horizontal | -1: Both | None: Nothing

camera_fps = 60
camera_size = [1280, 720]
# https://stackoverflow.com/questions/19448078/python-opencv-access-webcam-maximum-resolution

scale = 1.5
fix_pos = 25 / 300 # fish eye fix

######     CONTROLS      ######
STOP = 0
DRIVE_LEFT = 1
DRIVE_RIGHT = 2
PUSH = 3
UNPUSH = 4

######      ROBOT        ######
robot_perimeter = [20, 30]
robot_perimeter_pixels = [30, 1000]
ball_radius = [1, 3]

robot_perimeter_real = 24
robot_width = 10

######  DEFAULT CALIBRATION  ######
cm_koef = 0.5
push_line = [10, 0, 10, 100]

red_range = [(0, 0, 123), (255, 80, 255)]
blue_range = [(129, 0, 0), (255, 110, 255)]

ball_area = [0, 0, 1e4, 1e4]
robot_area = [0, 0, 1e4, 1e4]

def load_settings():
    with open('settings.json', 'r') as file:
        settings = json.load(file)
    globals().update(settings)

def save_settings(d):
    try:
        with open('settings.json', 'r') as file:
            settings = json.load(file)
        settings.update(d)
        d = settings
    except:
        pass

    with open('settings.json', 'w') as file:
        json.dump(d, file)

try: load_settings()
except Exception as e: print('WARNING: Settings are not loaded!\n', e)
