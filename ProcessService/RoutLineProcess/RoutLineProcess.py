import os
from typing import List

import cv2
from gerber.gerber_statements import CoordStmt
from gerber.rs274x import GerberFile
from gerber.rs274x import FileSettings
# from ProcessService.RoutLineProcess.GKOGerberProcess.LineSet import LineSet
# from ProcessService.RoutLineProcess.GKOGerberProcess.PreProcess import PreProcess
# from ProcessService.RoutLineProcess.GKOGerberProcess.LastProcess import LastProcess
from ProcessService.RoutLineProcess.GKOGerberProcess2.LinePiceSet import LineSet
from ProcessService.RoutLineProcess.GKOGerberProcess2.GKOGerberProcess import GKOGerberProcess
from ProcessService.RoutLineProcess.GKOImageProcess.GKOImageProcess import GKOImageProcess
from ProcessService.SupportFuncs.ImageGenerater import ImageGenerater

class RoutLineProcess:
    def __init__(self, imageGenerater: ImageGenerater):
        self.imageGenerater = imageGenerater
        self.__init()

    def __init(self):
        # 图像处理部分
        self.gkoImgPcs = GKOImageProcess(self.imageGenerater)
        self.gkoGbrPcs = GKOGerberProcess(self.imageGenerater.gerberLayers["gko"])
        # 线层去重切割分组预处理
        self.gkoGbrPcs.PreProc()
        image = self.imageGenerater.DrawShow(self.gkoGbrPcs.sets, False, -1)
        cv2.imshow("test", image)
        kval = 13
        while kval == 13:
            kval = cv2.waitKey(-1)

        # 线线对应
        lineSets = self.getLineSets(self.gkoGbrPcs.sets, self.gkoImgPcs.line_dict.values())
        self.gkoGbrPcs.sets = lineSets
        # rout层后处理
        # self.gkoGbrPcs.LastProc()

    def getLineSets(self, lineSets: List[LineSet], pointPairs):
        newLineSets = []
        for pointPair in pointPairs:
            if len(pointPair) == 2:
                lineset = self.__findset(pointPair, lineSets)
                if lineset != None:
                    newLineSets.append(lineset)
                    lineSets.remove(lineset)
        for lineSet in lineSets:
            if lineSet.start == lineSet.end:
                newLineSets.append(lineSet)
        return newLineSets

    def ToGerberFile(self):
        settings = FileSettings()
        lineSets = self.gkoGbrPcs.sets
        primitives = []
        statements = []
        for set in lineSets:
            for pice in set.GetLineSet():
                coord = {"function": None, "x": '%f10' % pice.start[0], "y": '%f10' % pice.start[1], "i": None, "j": None, "op": "D02"}
                coordstmt = CoordStmt.from_dict(coord, settings)
                statements.append(coordstmt)
                coord = {"function": None, "x": '%f10' % pice.end[0], "y": '%f10' % pice.end[1], "i": None, "j": None, "op": "D01"}
                coordstmt = CoordStmt.from_dict(coord, settings)
                statements.append(coordstmt)
                primitives.append(pice.gbLine)
        # gerberFile = GerberFile(statements, self.gkoGbrPcs.gerberLayer.settings, primitives, None)
        writestr = "*\n%FSLAX26Y26*%\n%MOIN*%\n%ADD10C,0.007874*%\n%IPPOS*%\n%LNgko11.gbr*%\n%LPD*%\nG75*\nG54D10*\n"
        for statement in statements:
            strr = statement.to_gerber(settings) + "\n"
            writestr += strr
        return writestr

    def __findset(self, pointPair, lineSets: List[LineSet]) -> LineSet:
        ratek = self.imageGenerater.ratek
        offset = self.imageGenerater.offset
        mindistance = 10000000000
        minlineSet = None
        for lineSet in lineSets:
            d_start1 = abs(pointPair[0][0] - (lineSet.start[0] - offset[0]) * ratek) + abs(pointPair[0][1] - (lineSet.start[1] - offset[1]) * ratek)
            d_end1 = abs(pointPair[1][0] - (lineSet.end[0] - offset[0]) * ratek) + abs(pointPair[1][1] - (lineSet.end[1] - offset[1]) * ratek)
            d_start2 = abs(pointPair[0][0] - (lineSet.end[0] - offset[0]) * ratek) + abs(pointPair[0][1] - (lineSet.end[1] - offset[1]) * ratek)
            d_end2 = abs(pointPair[1][0] - (lineSet.start[0] - offset[0]) * ratek) + abs(pointPair[1][1] - (lineSet.start[1] - offset[1]) * ratek)
            curdistance = min((d_start1 + d_end1), (d_start2 + d_end2))
            if curdistance < mindistance:
                mindistance = curdistance
                minlineSet = lineSet
        return minlineSet


def dataPrepar(path):
    readlayers = ["gko", "drl", "gbs", "gbo", "gbl", "gts", "gto", "gtl"]
    layers = os.listdir(path)
    gerbers = {}
    for layer in layers:
        if not readlayers.__contains__(layer):
            continue
        with open(f"{path}\\{layer}", "rU") as fp:
            data = fp.read()
            gerbers[layer] = data
    return gerbers


if __name__ == '__main__':
    path = "D:\ProjectFile\EngineeringAutomation\GongProcessing\TestDataSet\GerberFile\ALL-1W2308512\JP-1W2310736"
    gerbers = dataPrepar(path)
    imageGenerater = ImageGenerater(gerbers)
    routlinepces = RoutLineProcess(imageGenerater)
    filestr = routlinepces.ToGerberFile()
    with open(f"{path}\\rout", 'w') as f:
        f.write(filestr)
