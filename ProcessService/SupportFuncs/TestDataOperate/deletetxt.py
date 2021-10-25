import os
import shutil

import cv2
from ProcessService.SupportFuncs.ImageGenerater import ImageGenerater


def removetxt(txt):
    gko = txt
    lines = gko.split("\n")
    largest = ""
    delete = False
    newLines = []
    for line in lines:
        if line[:4] == "%ADD":
            largest = f"G54D{line[4:6]}*"
        if line == largest:
            delete = True
        if delete and line[:4] == "G54D" and line != largest:
            delete = False
        if not delete:
            newLines.append(line)
    return "\n".join(newLines)


path = "D:\ProjectFile\EngineeringAutomation\TestData123"
orderDirs = os.listdir(f"{path}")
for orderDir in orderDirs:
    if not os.path.isdir(f"{path}\\{orderDir}"):
        continue
    with open(f"{path}\\{orderDir}\\ok\\gko", 'r') as f:
        data = f.read()
        data = removetxt(data)
    with open(f"{path}\\{orderDir}\\ok\\gko", 'w') as f:
        f.write(data)
    print(orderDir)
    # img_gko = imageGnrt.getlayerimg("gko")
    # cv2.imwrite(f"{distDir}\\{orderDir}.png", img_gko)
    # cv2.imshow("test", img_gko)
    # kval = 13
    # while kval == 13:
    #     kval = cv2.waitKey(-1)
