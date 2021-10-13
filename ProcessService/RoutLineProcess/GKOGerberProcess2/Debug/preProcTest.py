import os

import cv2
from ProcessService.SupportFuncs.ImageGenerater import ImageGenerater
from ProcessService.RoutLineProcess.GKOGerberProcess2.GKOGerberProcess import GKOGerberProcess



def dataPrepar(path):
    layers = os.listdir(path)
    gerbers = {}
    for layer in layers:
        with open(f"{path}\\{layer}", "rU") as fp:
            data = fp.read()
            gerbers[layer] = data
    return gerbers


# if __name__ == '__main__':
#     gerbers = dataPrepar(r"D:\ProjectFile\PCBFinalInspection\Work\PCBGerberFile\JP-2W2114150\JP-2W2113820")
#     imageGenerater = ImageGenerater(gerbers)
#     lineset = GKOGerberProcess(imageGenerater.gerberLayers["gko"])
#     image = imageGenerater.DrawShow(lineset.sets, False, -1)
#     cv2.imshow("test", image)
#     kval = 13
#     while kval == 13:
#         kval = cv2.waitKey(-1)

indexset = [12, 13, 14, 15, 17, 18, 19, 20, 21, 22, 23, 24, 25, 28, 30, 31, 32, 36, 39]
if __name__ == '__main__':
    gerberFilePath = f"D:\ProjectFile\PCBFinalInspection\Work\PCBGerberFile"
    groupDirs = os.listdir(gerberFilePath)
    index = 0
    for groupDir in groupDirs:
        orderDirs = os.listdir(f"{gerberFilePath}\{groupDir}")
        for orderDir in orderDirs:
            index += 1
            print(f"{index}\\{groupDir}\\{orderDir}")
            # if index == 5:
            #     continue
            if not indexset.__contains__(index) and index < 39:
                continue
            # if index<19:
            #     continue
            gerbers = dataPrepar(f"{gerberFilePath}\{groupDir}\{orderDir}")
            imageGenerater = ImageGenerater(gerbers)
            lineset = GKOGerberProcess(imageGenerater.gerberLayers["gko"])
            lineset.PreProc()
            image = imageGenerater.DrawShow(lineset.sets, False, -1)
            cv2.imshow("test", image)
            kval = 13
            while kval == 13:
                kval = cv2.waitKey(-1)
# 206\JP-1W1748339\JP-1W1748167
# 132\ALL-2W2185504\JP-2W2181861
# 166\JP-1S2170851\JP-1S2170851
# 212\JP-1W1791540\JP-1W1789950
# 213\JP-1W1791540\JP-1W1789951
# 217\JP-1W1791540\JP-1W1789984
# 307\JP-1W2191561\ALL-1W2191205命令很多处理很慢
# 321\JP-1W2192625\JP-1W2192901
