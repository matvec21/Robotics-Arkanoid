import numpy as np
import time, cv2, os

from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk

from bluetooth import *
from utils import *

def save_vars(*vars):
    vars = dict(zip(vars, [globals()[i] for i in vars]))
    save_settings(vars)

def update_utils():
    utils_globals.update(globals())

scale = 2.5
def process_image(img):
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (int(img.shape[1] / scale), int(img.shape[0] / scale)))
    return ImageTk.PhotoImage(Image.fromarray(img))

def process_imageColor(img, range1, range2):
    img = cv2.inRange(img, range1, range2)
    img = cv2.medianBlur(img, 3)
    return img

def loop():
    global cm_koef, height

    img = camera()
    tab = tabs.index(tabs.select())
    height = img.shape[0]

    perimeter = None
    if tab == 3:
        img_crop = img[robot_area[1]: robot_area[3], robot_area[0]: robot_area[2]]

        blue_channel = cv2.inRange(img_crop, prepare_color(blue_range[0]), prepare_color(blue_range[1]))
        blue_channel = cv2.medianBlur(blue_channel, 3)

        cnts = cv2.findContours(blue_channel.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]

        if cnts is not None:
            for c in cnts:
                perimeter = cv2.arcLength(c, True)
                if perimeter < robot_perimeter_pixels[0] or perimeter > robot_perimeter_pixels[1]:
                    perimeter = None
                    continue

                approx = cv2.approxPolyDP(c, 0.1 * perimeter, True) + robot_area[:2]
                if len(approx) != 4:
                    perimeter = None
                    continue

                pos = np.sum(approx, axis = 0)[0] / 4
                cv2.drawContours(img, [approx], 0, (255, 255, 255), 2)
                cv2.circle(img, pos.astype(int), 2, (255, 255, 255), -1)
                break

    if tab == 1:
        img = process_imageColor(img, (fscale_b.get(), fscale_g.get(), fscale_r.get()), (tscale_b.get(), tscale_g.get(), tscale_r.get()))

    elif tab == 2:
        if ball_area[3] < 5e3:
            cv2.rectangle(img, *prepare_rectangle(ball_area), (0, 0, 255), 3)
        if robot_area[3] < 5e3:
            cv2.rectangle(img, *prepare_rectangle(robot_area), (255, 0, 0), 3)

    elif tab == 3 and perimeter is not None:
        k = robot_perimeter_real / perimeter
        cm_koef = round((cm_koef + k) / 2, 3)
        cm_label.configure(text = str(cm_koef))

    img = process_image(img)
    img_label.configure(image = img)
    img_label.image = img

    win.after(10, loop)

camera = Camera(camera_name)

win = Tk()
win.geometry('800x800')
win.title('БЫСТРЕЕ ОПОПОПОП')

tabs = ttk.Notebook(win)
tabs.pack()

camera_tab = ttk.Frame(tabs)
color_tab = ttk.Frame(tabs)
area_tab = ttk.Frame(tabs)
cm_tab = ttk.Frame(tabs)

tabs.add(camera_tab, text = 'Camera')
tabs.add(color_tab, text = 'Colors')
tabs.add(area_tab, text = 'Areas')
tabs.add(cm_tab, text = 'CM')

img = camera()
camera.rotation = camera_rotation
camera.flip = camera_flip
img = process_image(img)

img_label = Label(win, image = img)
img_label.image = img
img_label.pack()

#################   CAMERA
def flip(r):
    global camera_flip
    camera_flip = r
    update_utils()

def rotate(r):
    global camera_rotation
    camera_rotation = r
    update_utils()

Label(camera_tab, text = 'Rotation:').pack()

rotate_frame = Frame(camera_tab)
Button(rotate_frame, text = '0', width = 10, command = lambda: rotate(None)).pack(side = LEFT, ipady = 15)
Button(rotate_frame, text = '90', width = 10, command = lambda: rotate(1)).pack(side = LEFT, ipady = 15)
Button(rotate_frame, text = '180', width = 10, command = lambda: rotate(2)).pack(side = LEFT, ipady = 15)
Button(rotate_frame, text = '270', width = 10, command = lambda: rotate(3)).pack(side = LEFT, ipady = 15)
rotate_frame.pack()

Label(camera_tab, text = 'Flip:').pack()

flip_frame = Frame(camera_tab)
Button(flip_frame, text = 'None', width = 10, command = lambda: flip(None)).pack(side = LEFT, ipady = 15)
Button(flip_frame, text = 'Horizontal', width = 10, command = lambda: flip(1)).pack(side = LEFT, ipady = 15)
Button(flip_frame, text = 'Vertical', width = 10, command = lambda: flip(0)).pack(side = LEFT, ipady = 15)
Button(flip_frame, text = 'Both', width = 10, command = lambda: flip(-1)).pack(side = LEFT, ipady = 15)
flip_frame.pack()

Label(camera_tab).pack()
Button(camera_tab, text = 'Save', command =
    lambda: save_vars('camera_rotation', 'camera_flip')).pack()
#################   CAMERA

#################   COLOR
def load_color():
    fscale_b.set(current_color[0][0])
    fscale_g.set(current_color[0][1])
    fscale_r.set(current_color[0][2])
    tscale_b.set(current_color[1][0])
    tscale_g.set(current_color[1][1])
    tscale_r.set(current_color[1][2])

def save_color():
    change_color(current_color)
    save_vars('red_range', 'blue_range')

def change_color(l):
    global current_color

    try:
        current_color[0] = (int(fscale_b.get()), int(fscale_g.get()), int(fscale_r.get()))
        current_color[1] = (int(tscale_b.get()), int(tscale_g.get()), int(tscale_r.get()))
    except: pass

    current_color = l
    load_color()

color_frame = Frame(color_tab)
Button(color_frame, text = 'Ball', width = 10, command = lambda: change_color(red_range)).pack(side = LEFT, ipady = 15)
Button(color_frame, text = 'Robot', width = 10, command = lambda: change_color(blue_range)).pack(side = LEFT, ipady = 15)
color_frame.pack()

fscale_r = DoubleVar()
fscale_g = DoubleVar()
fscale_b = DoubleVar()

Label(color_tab, text = 'From (RGB):').pack()

Scale(color_tab, variable = fscale_r, to = 255, orient = HORIZONTAL, length = 1200, fg = 'red').pack()
Scale(color_tab, variable = fscale_g, to = 255, orient = HORIZONTAL, length = 1200, fg = 'lime').pack()
Scale(color_tab, variable = fscale_b, to = 255, orient = HORIZONTAL, length = 1200, fg = 'blue').pack()

tscale_r = DoubleVar()
tscale_g = DoubleVar()
tscale_b = DoubleVar()

Label(color_tab, text = 'To (RGB):').pack()

Scale(color_tab, variable = tscale_r, to = 255, orient = HORIZONTAL, length = 1200, fg = 'red').pack()
Scale(color_tab, variable = tscale_g, to = 255, orient = HORIZONTAL, length = 1200, fg = 'lime').pack()
Scale(color_tab, variable = tscale_b, to = 255, orient = HORIZONTAL, length = 1200, fg = 'blue').pack()

Button(color_tab, text = 'Save', command = save_color).pack()
change_color(red_range)
#################   COLOR

#################   AREA
def change_area(l):
    global current_area
    current_area = l

active = (0, 1)
def area_press(e, area):
    global active
    active = closest_corner(e, area)

    if active is None:
        active = (2, 3)
        area[0] = area[2] = int(e.x * scale)
        area[1] = area[3] = int(e.y * scale)
    else:
        area[active[0]] = int(e.x * scale)
        area[active[1]] = int(e.y * scale)

def area_release(e, area):
    area[active[0]] = int(e.x * scale)
    area[active[1]] = int(e.y * scale)
    area_fix()

def area_motion(e, area):
    area[active[0]] = int(e.x * scale)
    area[active[1]] = int(e.y * scale)

def distance(a, b):
    return np.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)

def closest_corner(e, area):
    for i in range(0, 4, 2):
        for k in range(1, 4, 2):
            if distance((e.x * scale, e.y * scale), (area[i], area[k])) < 15:
                return (i, k)
    return None

last_cursor = ''
def change_cursor(name):
    global last_cursor
    if last_cursor != name:
        img_label.configure(cursor = name)
        last_cursor = name

def area_cursor(e):
    if closest_corner(e, robot_area) is not None \
        or closest_corner(e, ball_area) is not None:
        change_cursor('fleur')
    else:
        change_cursor('arrow')

def area_prepare(l):
    return [min(l[0], l[2]), min(l[1], l[3]),
            max(l[0], l[2]), max(l[1], l[3])]

def area_fix():
    global ball_area, robot_area
    ball_area = area_prepare(ball_area)
    robot_area = area_prepare(robot_area)

def area_save():
    area_fix()
    save_vars('ball_area', 'robot_area')

Label(area_tab).pack()
Button(area_tab, text = 'Save', command = area_save).pack()
change_area(ball_area)

img_label.bind('<Button-1>', lambda e: area_press(e, ball_area))
img_label.bind('<ButtonRelease-1>', lambda e: area_release(e, ball_area))
img_label.bind('<B1-Motion>', lambda e: area_motion(e, ball_area))

img_label.bind('<Button-3>', lambda e: area_press(e, robot_area))
img_label.bind('<ButtonRelease-3>', lambda e: area_release(e, robot_area))
img_label.bind('<B3-Motion>', lambda e: area_motion(e, robot_area))

img_label.bind('<Motion>', lambda e: area_cursor(e))
#################   AREA

#################   CM
Label(cm_tab).pack()
cm_label = Label(cm_tab, text = 'Ищу...')
cm_label.pack()

Button(cm_tab, text = 'Save', command = lambda: save_vars('cm_koef')).pack()
#################   CM

win.after(1, loop)
win.mainloop()
