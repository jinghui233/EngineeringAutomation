import os
import gerber
import cv2
from ProcessService.RoutLineProcess.PreProcess.GerberPreProcess import GerberPreProcess

cv2.namedWindow("test", 0)
cv2.resizeWindow("test", int(1728/100*100), int(972/100*100))
cv2.moveWindow("test", 0, 0)
ratek = 100  # 放大倍率

GerberSingleFilePath = f"D:\ProjectFile\EngineeringAutomation\HoleDensity\ok\gko"
# gerberLayer = gerber.read(GerberSingleFilePath)
# gerberLayer.to_metric()
# StaticFuncs.DrawingShow(gerberLayer)

gerberFilePath = f"D:\ProjectFile\EngineeringAutomation\GongProcessing\TestDataSet\GerberFile"
groupDirs = os.listdir(gerberFilePath)
index = 0
for groupDir in groupDirs:
    orderDirs = os.listdir(f"{gerberFilePath}\{groupDir}")
    for orderDir in orderDirs:
        gerberLayer = gerber.read(f"{gerberFilePath}\{groupDir}\{orderDir}\gko")
        gerberLayer.to_metric()
        index += 1
        if index > 0 :
            lineset = GerberPreProcess(gerberLayer)
            lineset.ToGerberLayer()
            lineset.TempShow(gerberLayer)
            # if orderDir == "JP-1W2310736":
            #     cv2.waitKey(-1)
            break
