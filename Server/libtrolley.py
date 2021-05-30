import numpy as np
import math
from scipy import optimize
from itertools import combinations 


class Trolley:
    def __init__(self, mac, id, Xs, Ys, Beacons):
        self.MAC = mac
        self.ID = id
        self.x = []
        self.y = []
        self.z = 1
        self.sensedBeacons = [] #a list of beacons' MAC, in the same order of self.sensedRSSIs
        self.sensedRSSIs = [] # a list of signal strengths, in the same order of self.sensedBeacons
        self.sensedDistance = [] # in the same order as x_Beacons and y_Beacons # order
        self.x_Beacons = []     # order
        self.y_Beacons = []     # order
        self.initialGuess = None
        self.RSSIs = [] # a list of signal strengths, it is 2D
        self.lastRSSI = []  # order
        self.loopCount = 0
        self.averageRSSI = [] # in the same order of beacons
        self.averageDistance = [0] * len(Beacons) # in the same order of averageRSSI
        self.Xs = Xs
        self.Ys = Ys
        self.Beacons = Beacons
        self.mode = None
        if len(Beacons) == 5:
            self.mode = 'ITSC'
        elif len(Beacons) == 6:
            self.mode = 'TPlink'
        elif len(Beacons) == 11:
            self.mode = 'Mix'
        self.realX = -1
        self.realY = -1
        self.reliability = 0
        
    def update(self, list, wifis, Xs, Ys, Beacons, samples):
        sensed = 0
        self.sensedBeacons[:] = []
        self.sensedRSSIs = []
        new = [0] * len(Beacons)
        if self.loopCount == 0:
            self.RSSIs = new.copy()
        else:
            self.RSSIs = np.vstack((self.RSSIs, new))
        for i in range(0, int(wifis)):
            tempMac = list[0:6]
            if not self.macCompare2(tempMac, [0x0, 0x0, 0x0, 0x0, 0x0, 0x0]):
                self.sensedBeacons.append(list[:6])
                list = list[6:]
                sensed += 1
            else:
                break
        list = list[6 * (wifis - sensed):]
        self.sensedRSSIs = list[:sensed]
        list = list[sensed:]

        self.sensedDistance[:] = []
        # for i in range(0,len(self.sensedRSSIs)):
        #     self.sensedDistance.append(self.dbm2m(self.sensedRSSIs[i]))
        # tempDistance = self.sensedDistance.copy()
        self.x_Beacons[:] = []
        self.y_Beacons[:] = []
        self.sensedDistance[:] = []
        self.lastRSSI[:] = []
        for i in range(0, len(self.sensedBeacons)):
            id = self.macCompare(self.sensedBeacons[i], Beacons)
            if id == -1:
                continue
            if self.loopCount == 0:
                self.RSSIs[id] = self.sensedRSSIs[i]
            else:
                self.RSSIs[len(self.RSSIs)-1][id] = self.sensedRSSIs[i]
            self.x_Beacons.append(Xs[id])
            self.y_Beacons.append(Ys[id])
            # self.sensedDistance.append(tempDistance[i])
            self.lastRSSI.append(self.sensedRSSIs[i])

        self.loopCount += 1
        if self.loopCount >= samples:
            data = np.array(self.RSSIs[self.loopCount-samples: self.loopCount])
            data = data.astype(float)
            for i in range(len(data)):
                for j in range(len(data[0])):
                    data[i][j] = self.dbm2Mw(data[i][j])
            data[data == 0] = np.nan

            self.averageRSSI = np.nanmean(data, axis=0) # ...
            for i in range(len(self.averageRSSI)):
                self.averageRSSI[i] = self.mw2Dbm(self.averageRSSI[i])
            for i in range(len(self.averageRSSI)):
                if self.mode != 'Mix':
                    self.averageDistance[i] = self.dbm2m(self.averageRSSI[i], self.mode)
                elif self.mode == 'Mix':
                    if i < 6:
                        self.averageDistance[i] = self.dbm2m(self.averageRSSI[i], 'TPlink')
                    else:
                        self.averageDistance[i] = self.dbm2m(self.averageRSSI[i], 'ITSC')
        else:
            self.averageRSSI = new
        
        return

    def printInfo(self, samples):
        print("my ID is: ", self.ID)
        print("my MAC is: ", end = ' ')
        self.printMAC(self.MAC)
        # print("\nSensed beacons: ")
        # for i in range(0, len(self.sensedBeacons)):
        #     self.printMAC(self.sensedBeacons[i])
        # print("Sensed RSSIs: \t", end = ' ')
        # for i in range(0, len(self.sensedRSSIs)):
        #     print(self.sensedRSSIs[i], end = ' ')
        # print("\nRSSIs: ")
        # print(self.RSSIs, end = ' ')
        # print('\nNum. samples: ', len(self.RSSIs), end = ' ')
        print('\nAverage RSSI: ', self.averageRSSI, end = ' ')
        print('\nAverage Distance: ', self.averageDistance, end = ' ')
        # print("\nSensed distance: ", end = ' ')
        # for i in range(0, len(self.sensedDistance)):
        #     print(self.sensedDistance[i], end = ' ')
        # print("\nLast RSSI: ", end = ' ')
        # for i in range(len(self.lastRSSI)):
        #     print(self.lastRSSI[i], end = ' ')
        if self.loopCount >= samples:
            print('\nLast ', samples, ' samples: \n', self.RSSIs[self.loopCount-samples: self.loopCount], end = ' ')
        # print("\nLocation: ", end = ' ')
        # print("\tx: ", self.x, "\ty: ", self.y)
        print("\nNum of Location: ", len(self.x), end = ' ')
        print("\nReal Location: ", (self.realX, self.realY))

    def dbm2m(self, dBm, mode):
        A = -28
        n = 2.5 
        z = 3.4 - self.z
        # self.ID = 1
        if mode == 'ITSC':
            if self.ID == 0: # open case
                A = -35
                n = 2.5
            else: # with case
                A = -32 
                n = 3 
            z = 3.1 - self.z
        elif mode == 'TPlink':
            if self.ID == 0: # open case
                A = -26
                n = 2.5
            else: # with case
                A = -24.5 
                n = 3 
            z = 3.4 - self.z
        MHz = 2417 
        FSPL = 27.55
        # Free-Space Path Loss adapted avarage constant for home WiFI routers and following units
        m = 10 ** ((A + dBm) / (10 * n))
        # m = 10 ** (( FSPL - (20 * math.log10(MHz)) + dBm ) / 20 )
        # print('m^2: ', m ** 2)
        # print('z^2: ', self.z ** 2)
        if m < z:
            m = 0
        else:
            m = math.sqrt(m ** 2 - z ** 2)
        m = round(m,2)
        return m
    
    def macCompare(self, mac, Array):
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
    
    def macCompare2(self, mac1, mac2):
        flag = True
        for i in range(0,6):
            if mac1[i] != mac2[i]:
                flag = False
                break
        return flag
    
    def locate(self):
        def mse(pos, x_Beacons, y_Beacons, distances):
            mse = 0.0
            for x,y, distance in zip(x_Beacons, y_Beacons, distances):
                mse += (np.sqrt((pos[0]-x)**2 + (pos[1]-y)**2) - distance)**2
            return mse / len(distances)
        
        self.x = []
        self.y = []
        map = np.array([[0] * 11] * 7)
        comb = combinations(range(len(self.averageDistance)), 3)
        for i in list(comb):
            xBeacon = []
            yBeacon = []
            dist = []

            # rand = random.sample(range(len(self.averageDistance)), 3)
            xBeacon = [self.Xs[j] for j in i]
            yBeacon = [self.Ys[j] for j in i]
            dist = [self.averageDistance[j] for j in i]
            if np.isnan(dist).any():
                continue

            # if self.initialGuess == None:
                # self.initialGuess = (self.x_Beacons[np.argmin(self.lastRSSI)],
                #                 self.y_Beacons[np.argmin(self.lastRSSI)])
            # else:
            #     self.initialGuess = (self.x, self.y)
            self.initialGuess = (xBeacon[np.argmin(dist)], yBeacon[np.argmin(dist)])

            result = optimize.minimize(
            mse,                         # The error function
            self.initialGuess,            # The initial guess
            args=(xBeacon, yBeacon, dist), # Additional parameters for mse
            method='L-BFGS-B',           # The optimisation algorithm
            options={
                'ftol':1e-5,         # Tolerance
                'maxiter': 1e+8      # Maximum iterations
            })
            (x, y) = result.x
            if x < 0:
                x = 0
                continue
            elif x > 22.0:
                x = 22.35
                continue
            if y < 0:
                y = 0
                continue
            elif y > 14.0:
                y = 14.9
                continue
            
            map[int(y // 2)][int(x // 2)] += 1
            self.x.append(x)
            self.y.append(y)
        
        print(map)
        max = np.max(map)
        maxNum = np.count_nonzero(map == max)
        print('Num: ', maxNum, '\tMax: ', max)

        # map[map < np.max(map) / 2] = 0
        # coordinates = np.nonzero(map)
        # [x_coor, y_coor] = coordinates
        # x_coor = x_coor * 2 + 1
        # y_coor = y_coor * 2 + 1
        # [self.realY, self.realX] = [np.mean(x_coor), np.mean(y_coor)]
        if maxNum == 1:
            coordinate = np.nonzero(map == max)
            self.realY = coordinate[0][0] * 2 + 1
            self.realX = coordinate[1][0] * 2 + 1
        elif maxNum > 1 and maxNum <=4:
            coordinates = np.nonzero(map == max)
            [x_coor, y_coor] = coordinates
            x_coor = x_coor * 2 + 1
            y_coor = y_coor * 2 + 1
            [self.realY, self.realX] = [np.mean(x_coor), np.mean(y_coor)]
        self.reliability = round(max/50, 2) * 100
        if self.reliability > 99:
            self.reliability = 99
        self.reliability = int(self.reliability)
        return
            
    def only1(self, mac):
        print('Distance measuring: ', end ='')
        temp = self.macCompare(mac, self.sensedBeacons)
        if temp == -1:
            print("out of range")
        else:
            print(self.sensedRSSIs[temp], 'dBm')
        print()

    def dbm2Mw(self, dbm):
        if dbm == 0:
            return 0
        mW = dbm/10
        mW = pow(10.0, mW)
        return mW

    def mw2Dbm(self, mW):
        if mW == 0:
            return 0
        dbm = 10 * math.log10(mW)
        return dbm

    def printMAC(self, MAC):
        for j in range(0,6):
            print(hex(MAC[j]), end = ' ')

             