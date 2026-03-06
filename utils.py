import cv2
import numpy as np

from time import sleep, time
from settings import *
import json

class PID:
    def __init__(self, lookback = 10):
        self.memory = [0] * lookback
        self.last = 0

    def process(self, error):
        self.memory.append(error)
        self.memory.pop(0)

        speed = error * kP
        speed += sum(self.memory) / len(self.memory) * kI
        speed += (error - self.last) * kD

        self.last = error
        return int(np.clip(speed, -255, 255))

class Stats:
    def __init__(self, l1, l2):
        self.lost_balls = l1
        self.lost_robots = l2

        self.last = []
        self.was_time = time()

    def update(self):
        _time = time()
        self.last.append(_time - self.was_time)
        self.was_time = _time

        if len(self.last) >= 60:
            print('FPS -', 1 / (sum(self.last) / len(self.last) + 1e-9),
                '| Lost balls - %i/%i' % (sum(self.lost_balls), len(self.lost_balls)),
                '| Lost robots - %i/%i' % (sum(self.lost_robots), len(self.lost_robots)))
            self.lost_balls.clear()
            self.lost_robots.clear()
            self.last.clear()

class Camera:
    def __init__(self, camera_name):
        self.cam = cv2.VideoCapture(camera_name, cv2.CAP_DSHOW)
        self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, camera_size[0])
        self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_size[1])
        self.cam.set(cv2.CAP_PROP_FPS, camera_fps)
        self.cam.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))

    def __call__(self):
        img = self.cam.read()[1]
        if camera_rotation is not None:
            img = cv2.rotate(img, camera_rotation - 1)
        if camera_flip is not None:
            img = cv2.flip(img, camera_flip)

        return img

    def __del__(self):
        if not hasattr(self, 'cam'):
            return
        self.cam.release()
        cv2.destroyAllWindows()

class Line:
    def __init__(self, x1, y1, x2, y2):
        self.A, self.B = y2 - y1, x1 - x2
        magnitude = (self.A * self.A + self.B * self.B) ** 0.5
        if magnitude > 1e-8:
            self.A /= magnitude
            self.B /= magnitude
        self.C = self.A * x1 + self.B * y1
        self.A2, self.B2 = -self.B, self.A

#   sAx + sBy = C
#   lAx + lBy = F
    def intersection(s, l):
#        if s.A * l.A2 + s.B * l.B2 > 0:
#            return None

        d = s.A * l.B - s.B * l.A
        if abs(d) < 1e-3:
            return None

        x = (s.C * l.B - s.B * l.C) / d
        y = (s.A * l.C - s.C * l.A) / d
        return x, y

    def get_side(self, x, y):
        return (self.A * x + self.B * y) < self.C

utils_globals = globals()

def prepare_color(color):
    return (int(color[0]), int(color[1]), int(color[2]))

def prepare_rectangle(area):
    return (int(area[0]), int(area[1])), (int(area[2]), int(area[3]))

def encode(a):
    return (int(a)).to_bytes(1, byteorder = 'big')

def ps(l): return l.astype(np.int32)

def resize(img):
    return cv2.resize(img, (int(img.shape[1] / scale), int(img.shape[0] / scale)))
