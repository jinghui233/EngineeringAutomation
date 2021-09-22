import types
from typing import List
import os
from ProcessService.SupportFuncs.ImageGenerater import ImageGenerater
from ProcessService.RoutLineProcess.GKOLength2 import GKOLength
from ProcessService.RoutLineProcess.PreProcess.GerberPreProcess import GerberPreProcess
from ProcessService.RoutLineProcess.PreProcess.LineSet import LineSet
from gerber.gerber_statements import CoordStmt
from gerber.rs274x import GerberFile


class RoutLineProcess:
    def __init__(self, imageGenerater: ImageGenerater):
        self.imageGenerater = imageGenerater
        self.__init()

    def __init(self):
        self.gkoLength = GKOLength(self.imageGenerater)
        self.gbpprss = GerberPreProcess(self.imageGenerater.gerberLayers["gko"])

    def ToGerberFile(self):
        pointPairList = self.gkoLength.line_dict
        lineSets = self.gbpprss.sets
        newLineSets = []
        for pointPair in pointPairList.values():
            if len(pointPair) == 2:
                newLineSets.append(self.__findset(pointPair, lineSets))
        # def __init__(self, statements, settings, primitives, apertures, filename=None):
        #     super(GerberFile, self).__init__(statements, settings, primitives, filename)
        primitives = []
        statements = []
        statements.extend(self.gbpprss.gerberLayer.statements[0:8])
        for set in newLineSets:
            for pice in set.GetLineSet():
                coord = {"function": None, "x": str(pice.start[0]), "y": str(pice.start[1]), "i": None, "j": None, "op": "D02"}
                coordstmt = CoordStmt.from_dict(coord, self.gbpprss.gerberLayer.settings)
                statements.append(coordstmt)
                coord = {"function": None, "x": str(pice.end[0]), "y": str(pice.end[1]), "i": None, "j": None, "op": "D01"}
                coordstmt = CoordStmt.from_dict(coord, self.gbpprss.gerberLayer.settings)
                statements.append(coordstmt)
                primitives.append(pice.gbLine)
        gerberFile = GerberFile(statements, self.gbpprss.gerberLayer.settings, primitives, None)
        writestr = ""
        for statement in gerberFile.statements:
            strr = statement.to_gerber(gerberFile.settings) + "\n"
            if "".__contains__("G75*"):
                writestr += "G54D10*"
            writestr += strr
        return writestr

    def ToGerberFile2(self):
        contours = self.gkoLength.contours
        primitives = []
        statements = []
        statements.extend(self.gbpprss.gerberLayer.statements[0:8])
        for contour in contours:
            prePoint = contour[0][0]
            for curIndex in range(1, len(contour)):
                curPoint = contour[curIndex][0]
                coord = {"function": None, "x": str(prePoint[0]/self.imageGenerater.ratek), "y": str(prePoint[1]/self.imageGenerater.ratek), "i": None, "j": None, "op": "D02"}
                coordstmt = CoordStmt.from_dict(coord, self.gbpprss.gerberLayer.settings)
                statements.append(coordstmt)
                coord = {"function": None, "x": str(curPoint[0]/self.imageGenerater.ratek), "y": str(curPoint[1]/self.imageGenerater.ratek), "i": None, "j": None, "op": "D01"}
                coordstmt = CoordStmt.from_dict(coord, self.gbpprss.gerberLayer.settings)
                statements.append(coordstmt)
                prePoint = curPoint
        gerberFile = GerberFile(statements, self.gbpprss.gerberLayer.settings, primitives, None)
        writestr = ""
        for statement in statements:
            strr = statement.to_gerber(self.gbpprss.gerberLayer.settings) + "\n"
            if "".__contains__("G75*"):
                writestr += "G54D10*"
            writestr += strr
        return writestr

    def __findset(self, pointPair, lineSets: List[LineSet]) -> LineSet:
        ratek = self.imageGenerater.ratek
        mindistance = 10000000000
        minlineSet = None
        for lineSet in lineSets:
            d_start1 = abs(pointPair[0][0] - lineSet.FirstPoint[0] * ratek) + abs(pointPair[0][1] - lineSet.FirstPoint[1] * ratek)
            d_end1 = abs(pointPair[1][0] - lineSet.LastPoint[0] * ratek) + abs(pointPair[1][1] - lineSet.LastPoint[1] * ratek)
            d_start2 = abs(pointPair[0][0] - lineSet.LastPoint[0] * ratek) + abs(pointPair[0][1] - lineSet.LastPoint[1] * ratek)
            d_end2 = abs(pointPair[1][0] - lineSet.FirstPoint[0] * ratek) + abs(pointPair[1][1] - lineSet.FirstPoint[1] * ratek)
            curdistance = min((d_start1 + d_end1), (d_start2 + d_end2))
            if curdistance < mindistance:
                mindistance = curdistance
                minlineSet = lineSet
        return minlineSet


def dataPrepar(path):
    layers = os.listdir(path)
    gerbers = {}
    for layer in layers:
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
