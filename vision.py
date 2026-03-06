import cv2
import numpy as np
from utils import Line

_fetchRobot_lost = []
_fetchRobot_last_pos = np.zeros(2)
def fetchRobot(img):
    global _fetchRobot_last_pos, _fetchRobot_lost

    img_crop = img[robot_area[1]: robot_area[3], robot_area[0]: robot_area[2]]

    blue_channel = cv2.inRange(img_crop, *blue_range)
    blue_channel = cv2.medianBlur(blue_channel, 3)

    cnts = cv2.findContours(blue_channel.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]

    _fetchRobot_lost.append(1)
    if cnts is not None:
        for c in cnts:
            perimeter = cv2.arcLength(c, True)
            if perimeter < robot_perimeter[0] or perimeter > robot_perimeter[1]:
                continue

            approx = cv2.approxPolyDP(c, 0.1 * perimeter, True) + robot_area[:2]
            if len(approx) != 4:
                continue

            pos = np.sum(approx, axis = 0)[0] / 4
            _fetchRobot_last_pos = pos

            cv2.drawContours(img, [approx], 0, (255, 255, 255), 2)
            cv2.circle(img, pos.astype(int), 2, (255, 255, 255), -1)

            _fetchRobot_lost[-1] = 0
            break
    return _fetchRobot_last_pos, blue_channel

_fetchBall_lost = []
_fetchBall_last_pos = np.array([1280, 720]) / 2
def fetchBall(img):
    global _fetchBall_last_pos, _fetchBall_lost

    img_crop = img[ball_area[1]: ball_area[3], ball_area[0]: ball_area[2]]

    red_channel = cv2.inRange(img_crop, *red_range)
    red_channel = cv2.medianBlur(red_channel, 5)

    circles = cv2.HoughCircles(red_channel, cv2.HOUGH_GRADIENT, 2, 10, param1 = 40, param2 = 15, minRadius = ball_radius[0], maxRadius = ball_radius[1])

    _fetchBall_lost.append(1)
    if circles is not None:
        for circle in np.around(circles):
            pos = circle[0] + [*ball_area[:2], 0]

            cv2.circle(img, pos[:2].astype(int), pos[2].astype(int), (255, 255, 255), 2)
            cv2.circle(img, pos[:2].astype(int), 1, (255, 255, 255), -1)

            _fetchBall_last_pos = circle[0][:2] + ball_area[:2]
            _fetchBall_lost[-1] = 0
            break
    return _fetchBall_last_pos, red_channel

def get_mean(last):
    return np.sum(last, axis = 0) / len(last)

def get_distance(a, b):
    return np.sqrt(np.sum(np.power(a - b, 2)))

class PushLine(Line):
    def __init__(self):
        super().__init__(100, 0, 100, 1)
        self.memory = []

    def set_x(self, x):
        self.update(x, 0, x, 1)

    def adjust(self, pos):
        for i in range(len(self.memory)):
            if get_distance(self.memory[i], pos) < 10:
                return
        self.memory.append(pos)
        if len(self.memory) < 10:
            return

        x = np.linalg.lstsq(np.array(self.memory), np.ones((len(self.memory), )) * 100, rcond = None)[0].T
#        a = get_mean(self.memory[:5])
#        b = get_mean(self.memory[5:])
#        if a[1] > b[1]:
#            a, b = b, a

        self.update(pos[0] + x[1], pos[1], pos[0], pos[1] + x[0])
        self.memory.clear()

    def update_gui(self):
        a = upper_line.intersection(self)
        b = bottom_line.intersection(self)
        if a is None or b is None:
            return

        push_line[0], push_line[1] = a
        push_line[2], push_line[3] = b

    def update(self, x1, y1, x2, y2):
        super().__init__(x1, y1, x2, y2)
        self.C -= push_offset
        self.update_gui()

class PredictMotion:
    def __init__(self):
        self.detect_frames = 8
        self.smooth_frames = 10
        self.pos = np.zeros(2)
        self.last = []
        self.avg = []

    def process(self, pos, posNext):
        delta = posNext - pos
        l = np.sqrt(np.sum(delta ** 2))
        if l <= 2 or l >= 200:
            return np.zeros(2)
        return delta

    def update(self, pos):
        self.last.append(pos)
        self.last = self.last[-self.detect_frames:]

        vels = []
        if len(self.last) > 1:
            for i in range(1, len(self.last)):
                vels.append(self.process(self.last[0], self.last[i]))
        else:
            vels = [np.zeros(2), np.zeros(2)]

        self.velocity = get_mean(vels)
        self.pos = pos + self.velocity * 5

        vector = Line(*pos, *self.pos)
        r = vector.intersection(_push_line)
        if r is not None:
            ln = ((push_line[2] - push_line[0]) ** 2 + (push_line[3] - push_line[1]) ** 2) ** 0.5
            t = (_push_line.A2 * (r[0] - push_line[0]) + _push_line.B2 * (r[1] - push_line[1])) % (ln * 2)
            if t > ln: t = 2 * ln - t
            self.pos = np.array([push_line[0] + _push_line.A2 * t, push_line[1] + _push_line.B2 * t])

        self.avg.append(self.pos)
        self.avg = self.avg[-self.smooth_frames:]
        sum = self.avg[0]
        sumk = 1
        for i in range(1, len(self.avg)):
            k = (1 - i / (self.smooth_frames - 1) * 0.9)
            sum += self.avg[i] * k
            sumk += k
        return sum / sumk
        return self.pos

vision_globals = globals()
# btbtbbtbtbt BABABABABABA btbtbtbt BABABABABA
