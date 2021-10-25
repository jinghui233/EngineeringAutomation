import os
import shutil

import cv2
from ProcessService.SupportFuncs.ImageGenerater import ImageGenerater

path = "D:\ProjectFile\EngineeringAutomation\GongProcessing\TestDataSet\GerberFile"
distDir = "D:\\ProjectFile\\EngineeringAutomation\\TestData\\temp\\gerber"

cv2.namedWindow("test", 0)
cv2.resizeWindow("test", int(1728 / 100 * 100), int(972 / 100 * 100))
cv2.moveWindow("test", 0, 0)
groupDirs = os.listdir(path)
for groupDir in groupDirs:
    orderDirs = os.listdir(f"{path}\\{groupDir}")
    for orderDir in orderDirs:
        gerberfilePath = f"{path}\\{groupDir}\\{orderDir}"
        imageGnrt = ImageGenerater.fromDir(gerberfilePath)
        img_gko = imageGnrt.getlayerimg("gko")
        cv2.imshow("test", img_gko)
        kval = 1
        while kval == 1:
            kval = cv2.waitKey(-1)
            if kval == 13:
                shutil.copytree(gerberfilePath, f"{distDir}\\{orderDir}")

