import os
import shutil

import cv2
from ProcessService.SupportFuncs.ImageGenerater import ImageGenerater

path = "D:\ProjectFile\EngineeringAutomation\TestData\GerberFile"
distDir = "D:\ProjectFile\EngineeringAutomation\TestData\ImageFile"

orderDirs = os.listdir(f"{path}")
count = orderDirs.__len__()
index = 0
for orderDir in orderDirs:
    index += 1
    print(f"{count}-{index}-{orderDir}")
    # if index < 31:
    #     continue
    imageGnrt = ImageGenerater.fromDir(f"{path}\\{orderDir}")
    img_gko = imageGnrt.getlayerimg("gko")
    cv2.imwrite(f"{distDir}\\{orderDir}.png", img_gko)
