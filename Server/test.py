import struct
import numpy as np
import scipy
Trolleys = [[0x94, 0xAA, 0x82, 0x12, 0xCF, 0xA4],
            [0xa4, 0x20, 0xb9, 0xab, 0x62, 0x24]]


Beacons = [[0x97, 0xf9, 0x61, 0x20, 0x41, 0x58],
           [0xc1, 0x4f, 0x79, 0x20, 0x41, 0x58],
           [0x6c, 0xfa, 0x61, 0x20, 0x41, 0x58],
           [0x99, 0xfa, 0x61, 0x20, 0x41, 0x58],
           [0xd8, 0x6b, 0x79, 0x20, 0x41, 0x58],
           [0xef, 0x6f, 0x79, 0x20, 0x41, 0x58],
           [0x58, 0x41, 0x20, 0x79, 0x6F, 0xEF]]
BeaconXs = [0.66, 8.36, 9.00, 13.13, 16.12, 17.44]
BeaconYs = [4.43, 7.49, 13.98, 6.75, 7.31, 9.71]

def macCompare(self, mac, Array):# to do...
        flag = True
        for i in range(0,len(Array)):
            flag = True
            for j in range(0,len(Array[0])):
                if Array[i][j] != mac[j]:
                    flag = False
                    break
            if flag:
                return i
        return -1

#!/usr/bin/env python2

# a simple script for one of my articles - https://cryptolok.blogspot.com/2017/08/practical-wifi-hosts-triangulation-with.html

from math import log10

def dbm2m(self, dbm):
    MHz = 2400
    dBm = 54 
    FSPL = 27.55
    # Free-Space Path Loss adapted avarage constant for home WiFI routers and following units
    m = 10 ** (( FSPL - (20 * log10(MHz)) + dBm ) / 20 )
    m = round(m,2)
    print ('DISTANCE : ',m,'m')
    return m

from scipy import optimize
import math

def locate(self, Xs, Ys, Beacons):
        x_Beacons = []
        y_Beacons = []
        for i in range(0, len(self.sensedBeacons)):
            id = self.macCompare(self.sensedBeacons[i], Beacons)
            x_Beacons.append(Xs[id])
            y_Beacons.append(Ys[id])

        def mse(pos, x_Beacons, y_Beacons, distances):
            mse = 0.0
            for x,y, distance in zip(x_Beacons, y_Beacons,distances):
                mse += (np.sqrt((pos[0]-x)**2 + (pos[1]-y)**2) - distance)**2
            return mse / len(distances)

        initial_location = (x_Beacons[0], y_Beacons[0])

        result = scipy.optimize.minimize(
        mse,                         # The error function
        initial_location,            # The initial guess
        args=(x_Beacons, y_Beacons, self.sensedDistance), # Additional parameters for mse
        method='L-BFGS-B',           # The optimisation algorithm
        options={
            'ftol':1e-5,         # Tolerance
            'maxiter': 1e+4      # Maximum iterations
        })
        (self.x, self.y) = result.x


def mse(pos, x_Beacons, y_Beacons, distances):
        mse = 0.0
        for x,y, distance in zip(x_Beacons, y_Beacons,distances):
            mse += (np.sqrt((pos[0]-x)**2 + (pos[1]-y)**2) - distance)**2
        return mse / len(distances) 

initial_location = [5, 6]
x_Beacons = [1,2,3]
y_Beacons = [1,2,3]
result = optimize.minimize(
        mse,                         # The error function
        initial_location,            # The initial guess
        args=(x_Beacons, y_Beacons, [1, 2, 3]), # Additional parameters for mse
        method='L-BFGS-B',           # The optimisation algorithm
        options={
            'ftol':1e-5,         # Tolerance
            'maxiter': 1e+4      # Maximum iterations
        })

import cv2 as cv
img = cv.imread('J:\GoogleDrive\HKUST\ISDN 3002\Map.JPG')

loc2pixel_x = img.shape[1] / 22.35
loc2pixel_y = img.shape[0] / 14.9

# for i in range(0,6):
#     img2 = cv.circle(img2,
#                  (round(trolleylist[i].x*loc2pixel_x), round(trolleylist[i].y*loc2pixel_y)),
#                  10, (0,255,0), -1)

# while True:
#     cv.imshow('4223', img)
#     cv.waitKey(1)

map = [[0] * 11] * 7
print(map)
print(map[6][10])
