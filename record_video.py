from utils import *

camera = Camera(camera_name)
camera_rotation = camera_flip = None
utils_globals.update(globals())

fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter('record.avi', fourcc, camera_fps, camera_size)

while True:
    img = camera()
    out.write(img)

    cv2.imshow('Camera', resize(img))
    if cv2.waitKey(1) == 27:
        break

out.release()
