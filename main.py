
# TODO: FISH EYE FIX CALCULATE (linal)

from bluetooth import *
from utils import *
from vision import *

import os, sys

def AI_motion():
    global speed

    delta = robot - ball
    if delta[0] < 0:
        speed = 0
        return

    if ball_predict.velocity[0] * cm_koef > 2.4 and delta[0] > distance_predict:
        y = ball_predict.pos[1]
    else:
        y = ball[1]

    y = np.clip(y, robot_area[1] + robot_width, robot_area[3] - robot_width)
#    print(ball_predict.velocity[0] * cm_koef * 0.1)
    aspeed = (y - robot[1])
#    aspeed *= max(ball_predict.velocity[0] * cm_koef * 0.1, 1)
    aspeed *= max(abs(delta[1]) * cm_koef * 0.1, 1)
#    print(max(abs(delta[1]) * cm_koef * 0.1, 1), delta[1] * cm_koef)
    speed = aspeed * 0.5 + 0.5 * speed

AI_push_push_start = -1
AI_push_last_d = False
def AI_push():
    global AI_push_last_d, AI_push_push_start

    pos = ball
    pos += ball_predict.velocity * 0.15
    cv2.circle(img, ps(pos), 5, (255, 0, 150), -1)

    d = _push_line.get_side(*pos)
    if d == False and robot[0] > ball[0]:
        if AI_push_last_d != d:
            AI_push_push_start = time()

        dt = time() - AI_push_push_start
        if dt < 0.3: send_action(PUSH)
        elif dt < 1.5: send_action(UNPUSH)
        else: d = True
    else:
        send_action(UNPUSH)

    AI_push_last_d = d

stats = Stats(vision_globals['_fetchBall_lost'], vision_globals['_fetchRobot_lost'])
camera = Camera(camera_name)
ball_predict = PredictMotion()
_push_line = PushLine()
pid = PID()

upper_line = Line(robot_area[2], robot_area[1], robot_area[0], robot_area[1])
bottom_line = Line(robot_area[2], robot_area[3], robot_area[0], robot_area[3])

robot_perimeter = [int(i / cm_koef) for i in robot_perimeter]
ball_radius = [int(i / cm_koef) for i in ball_radius]
robot_width /= cm_koef
distance_predict /= cm_koef
push_offset /= cm_koef

red_range = np.array(red_range)
blue_range = np.array(blue_range)
center = np.array([robot_area[0] + abs(robot_area[0] - robot_area[2]) / 2,
    robot_area[1] + abs(robot_area[1] - robot_area[3]) / 2])

if camera_flip is not None and camera_flip != -1:
    DRIVE_LEFT, DRIVE_RIGHT = DRIVE_RIGHT, DRIVE_LEFT

cmd = 0
speed = 0

vision_globals.update(globals())
utils_globals.update(globals())

if use_socket:
    sock = BluetoothSocket(RFCOMM)
    sock.connect((addr, port))

send_all_last_speed = speed
send_all_last_cmd = cmd
def send_all():
    global send_all_last_speed, send_all_last_cmd, sock, cmd
    if not use_socket:
#        print('Speed:', speed)
        return

    _speed = pid.process(speed)
    if abs(_speed) < 20:
        _speed = 0
    if abs(_speed) > 160:
        _speed = int(255 * np.sign(speed))

    if _speed == 0: send_action(STOP)
    elif _speed > 0: send_action(DRIVE_LEFT)
    else: send_action(DRIVE_RIGHT)

#    _speed = int(np.clip(_speed // 0.8, -255, 255))

    if cmd != 0 and (cmd != send_all_last_cmd or abs(_speed - send_all_last_speed) > 0):
        try:
#            print(_speed)
            sock.send(encode(cmd) + encode(abs(round(_speed) // 1.0)))
        except:
            sock.close()
            os.startfile(sys.argv[0])
            sys.exit()

        send_all_last_cmd = cmd
        send_all_last_speed = _speed
        cmd = 0

def send_action(a):
    global cmd
    cmd |= (1 << a)

from random import randint

fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter('record%d.avi' % (randint(0, 1000000000)), fourcc, camera_fps, camera_size[::-1])

initialize = True
while True:
    img = camera()

    robot, blue_channel = fetchRobot(img)
    ball, red_channel = fetchBall(img)
    ball_predict.update(ball)

    robot[1] -= (robot[1] - center[1]) * fix_pos
    if initialize and not stats.lost_robots[-1]:
        initialize = False
        _push_line.set_x(robot[0])
    _push_line.adjust(robot)

    AI_motion()
    AI_push()
    send_all()

    crop = img[ball_area[1]: ball_area[3], ball_area[0]: ball_area[2], 2]
    crop += np.minimum(255 - crop, red_channel * 100)
    crop = img[robot_area[1]: robot_area[3], robot_area[0]: robot_area[2], 0]
    crop += np.minimum(255 - crop, blue_channel * 100)

    cv2.arrowedLine(img, ps(ball), ps(ball + ball_predict.velocity), (255, 255, 0), 2)
    cv2.circle(img, ps(ball_predict.pos), 4, (0, 0, 255), -1)
    cv2.circle(img, ps(robot), 4, (0, 0, 255), -1)
    cv2.circle(img, ps(center), 4, (200, 200, 255), -1)

    cv2.line(img, robot_area[:2], (robot_area[2], robot_area[1]), (200, 50, 50), 2)
    cv2.line(img, robot_area[2:], (robot_area[0], robot_area[3]), (200, 50, 50), 2)
    cv2.rectangle(img, ball_area[:2], ball_area[2:], (50, 50, 200), 2)
    cv2.line(img, *prepare_rectangle(push_line), (255, 255, 0), 2)

    cv2.imshow('Camera', resize(img))
    out.write(img)
    stats.update()

    if cv2.waitKey(1) == 27:
        break

if use_socket:
    sock.send(encode(1) + encode(0))
    sock.close()
out.release()
