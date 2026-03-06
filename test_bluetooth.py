from bluetooth import *

# addr = 'C8:C9:A3:CF:2A:56'
# addr = 'C8:C9:A3:CF:2A:56'
addr = 'F0:08:D1:C8:1E:5E'
port = 1

sock = BluetoothSocket(RFCOMM)

while 1:
    try:
        sock.connect((addr, port))
        break
    except OSError:
        pass

print('Connected!')

while 1:
    try:
        a = int(input())
        if a < 0 or a > 4:
            throw
    except:
        print('0-4 int')
        continue

    sock.send((1 << a).to_bytes(1, byteorder = 'big'))
    if a == 1 or a == 2:
        try:
            s = int(input('speed: '))
            if s < 0 or s > 255:
                throw
        except:
            print('0-255 int')
            s = 0

        sock.send(s.to_bytes(1, byteorder = 'big'))
    else:
        sock.send((0).to_bytes(1, byteorder = 'big'))

sock.close()
