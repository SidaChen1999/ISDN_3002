import sys
import socket
import selectors
import traceback

import libserver
import libtrolley
import cv2 as cv
import numpy as np

trolleylist:'list[libtrolley.Trolley]' = [] 
Beacons_TPlink = [[0x58, 0x41, 0x20, 0x61, 0xf9, 0x97], # matrix
               [0x58, 0x41, 0x20, 0x79, 0x4f, 0xc1], #sub 1 #screen 
               [0x58, 0x41, 0x20, 0x61, 0xfa, 0x6c], #sub 5 # wielding room
               [0x58, 0x41, 0x20, 0x61, 0xfa, 0x99], # sub 3 # office
               [0x58, 0x41, 0x20, 0x79, 0x6b, 0xd8], # sub 2 # storage
               [0x58, 0x41, 0x20, 0x79, 0x6f, 0xef]] #sub 4 # workshop
Beacons_ITSC = [[0x70, 0x18, 0xa7, 0x11, 0x21, 0xe0], # storage
               [0x70, 0x18, 0xa7, 0x12, 0xc0, 0xe0], # workshop
               [0xd4, 0xad, 0x71, 0x69, 0x60, 0x80], # wielding room
               [0xd4, 0xad, 0x71, 0x6b, 0x7f, 0xa0], # screen
               [0x70, 0x18, 0xa7, 0x11, 0xe9, 0x80]] # office
BeaconXs_TPlink = [4.08, 10.78, 10.78, 4.08, 18.62, 18.62]
BeaconYs_TPlink = [3.69, 11.31, 3.69, 11.31, 11.31, 3.69]
BeaconXs_ITSC = [17.68, 18.57, 9.75, 8.72, 4.61]
BeaconYs_ITSC = [9.85, 2.17, 5.00, 9.85, 5.08]
samples = 3
mode = 'MIX'
if mode == 'TPlink':
    Beacons = Beacons_TPlink
    BeaconXs = BeaconXs_TPlink
    BeaconYs = BeaconYs_TPlink
elif mode == 'ITSC':
    Beacons = Beacons_ITSC
    BeaconXs = BeaconXs_ITSC
    BeaconYs = BeaconYs_ITSC
else:
    Beacons = np.vstack((Beacons_TPlink, Beacons_ITSC))
    BeaconXs = BeaconXs_TPlink + BeaconXs_ITSC
    BeaconYs = BeaconYs_TPlink + BeaconYs_ITSC
numWifi = len(Beacons)

img = cv.imread('J:\GoogleDrive\HKUST\ISDN 3002\Floor_Plan.JPG')
scale_percent = 80 # percent of original size
width = int(img.shape[1] * scale_percent / 100)
height = int(img.shape[0] * scale_percent / 100)
dim = (width, height)
# img = cv.resize(img, dim)
loc2pixel_x = img.shape[1] / 22.35
loc2pixel_y = img.shape[0] / 14.9
for i in range(0, numWifi):
    img = cv.circle(img, (round(BeaconXs[i]*loc2pixel_x), round(BeaconYs[i]*loc2pixel_y)),
        10, (0,0,255), -1)
# for i in range(0, len(fakeTrolleysX)):
#     img = cv.circle(img, (round(fakeTrolleysX[i]*loc2pixel_x), round(fakeTrooleysY[i]*loc2pixel_y)),
#         5, (255,0,0), -1)

drawTrilateration = False

def accept_wrapper(sock):
    conn, addr = sock.accept()  # Should be ready to read
    print("accepted connection from", addr)
    conn.setblocking(False)
    message = libserver.Message(sel, conn, addr)
    sel.register(conn, selectors.EVENT_READ, data=message)


host = socket.gethostbyname(socket.gethostname())
port = 65432
sel = selectors.DefaultSelector()
# host, port = sys.argv[1], int(sys.argv[2])
lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Avoid bind() exception: OSError: [Errno 48] Address already in use
lsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
lsock.bind((host, port))
lsock.listen()
print("listening on", (host, port))
lsock.setblocking(False)
sel.register(lsock, selectors.EVENT_READ, data=None)

try:
    while True:
        events = sel.select(timeout=None)
        for key, mask in events:
            if key.data is None:
                accept_wrapper(key.fileobj)
            else:
                message = key.data
                try:
                    message.process_events(mask)
                    message.process_data(
                        trolleylist,
                        BeaconXs,
                        BeaconYs,
                        Beacons,
                        samples
                        )
                    
                except Exception as e:
                    print(
                        "main: error: exception for",
                        f"{message.addr}:\n{traceback.format_exc()}",
                    )
                    message.close()
        img2 = img.copy()
        for i in range(0,len(trolleylist)):
            if len(trolleylist[i].x) >= 3:
                if len(trolleylist) == 1:
                    for j in range(len(trolleylist[i].x)):
                        img2 = cv.circle(img2,
                            (int(round(trolleylist[i].x[j]*loc2pixel_x)), int(round(trolleylist[i].y[j]*loc2pixel_y))),
                            10, (0,255,0), -1)
                    for j in range(len(trolleylist[i].averageDistance)):
                        # if trolleylist[i].sensedDistance[j] == 0:
                        #     continue
                        if np.isnan(trolleylist[i].averageDistance[j]):
                            continue
                        img2 = cv.circle(img2,
                            (int(round(trolleylist[i].Xs[j]*loc2pixel_x)), int(round(trolleylist[i].Ys[j]*loc2pixel_y))),
                            int(round(trolleylist[i].averageDistance[j]*loc2pixel_x)), (255,255,0), 2)
                        img2 = cv.putText(img2, str(round(trolleylist[i].averageRSSI[j], 2)),
                            (int(round(trolleylist[i].Xs[j]*loc2pixel_x)-10), int(round(trolleylist[i].Ys[j]*loc2pixel_y)+5)),
                            0, 0.5, (0,0,0), 1)
                    # for j in range(len(trolleylist[i].lastRSSI)):
                    #     img2 = cv.putText(img2, str(round(trolleylist[i].lastRSSI[j], 2)),
                    #         (int(round(trolleylist[i].x_Beacons[j]*loc2pixel_x)-10), int(round(trolleylist[i].y_Beacons[j]*loc2pixel_y)+5)),
                    #         0, 0.5, (0,0,0), 1)
                img2 = cv.circle(img2,
                    (int(round(trolleylist[i].realX*loc2pixel_x)), int(round(trolleylist[i].realY*loc2pixel_y))),
                    14, (0,0,0), -1)
                img2 = cv.putText(img2, str(i),
                    (int(round(trolleylist[i].realX*loc2pixel_x)-7), int(round(trolleylist[i].realY*loc2pixel_y)+6)),
                    0, 0.7, (255,0,255), 2)
                img2 = cv.putText(img2, str(trolleylist[i].reliability),
                    (int(round(trolleylist[i].realX*loc2pixel_x)-12), int(round(trolleylist[i].realY*loc2pixel_y)-14)),
                    0, 0.5, (0,0,0), 1)

        cv.imshow('4223', img2)
        if cv.waitKey(10) == 27:
            break
except KeyboardInterrupt:
    print("caught keyboard interrupt, exiting")
finally:
    sel.close()