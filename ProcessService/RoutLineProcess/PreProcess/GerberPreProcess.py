import time
import math
import cv2
import os
import numpy as np
import gerber
from gerber.gerber_statements import CoordStmt
from gerber.primitives import Line as Gbt_Line
from gerber.rs274x import GerberFile
from gerber.cam import CamFile
from ProcessService.SupportFuncs.AnalyticGeometry import AnalyticGeometry as AGFuncs
from ProcessService.RoutLineProcess.PreProcess.LinePice import LinePice
from ProcessService.RoutLineProcess.PreProcess.LineSet import LineSet
from ProcessService.RoutLineProcess.PreProcess.SignType import SignType
from ProcessService.SupportFuncs.ImageGenerater import ImageGenerater


class GerberPreProcess:
    def __init__(self, gerberLayer: CamFile):
        self.gerberLayer = gerberLayer
        self.__init()
        self.CutAndCombine()

    def __init(self):
        sampleLine = Gbt_Line((1, 1), (1, 1), 0)
        self.sets = []
        curSet = LineSet()
        self.sets.append(curSet)
        for primitive in self.gerberLayer.primitives:
            if type(primitive) != type(sampleLine):
                continue
            if curSet.addLine(LinePice(primitive)):
                pass
            else:
                curSet = LineSet()
                self.sets.append(curSet)
                curSet.addLine(LinePice(primitive))

    def CutAndCombine(self):
        # self.__CombineSets()
        self.__OverLapping_Set()
        self.__Regenerate()
        self.__CutSet_Set()
        self.__Regenerate()
        self.__CutLine_Set()
        self.__Regenerate()
        self.__CutSet_Set()
        self.__Regenerate()
        self.__CombineSets()
        pass

    def ToGerberLayer(self):
        # def __init__(self, statements, settings, primitives, apertures, filename=None):
        #     super(GerberFile, self).__init__(statements, settings, primitives, filename)
        primitives = []
        statements = []
        statements.extend(self.gerberLayer.statements[0:8])
        for set in self.sets:
            for pice in set.GetLineSet():
                coord = {"function": None, "x": str(pice.start[0]), "y": str(pice.start[1]), "i": None, "j": None, "op": "D02"}
                coordstmt = CoordStmt.from_dict(coord, self.gerberLayer.settings)
                statements.append(coordstmt)
                coord = {"function": None, "x": str(pice.end[0]), "y": str(pice.end[1]), "i": None, "j": None, "op": "D01"}
                coordstmt = CoordStmt.from_dict(coord, self.gerberLayer.settings)
                statements.append(coordstmt)
                primitives.append(pice.gbLine)
        gerberFile = GerberFile(statements, self.gerberLayer.settings, primitives, None)
        gerberFile.write("test.gko")

    def __CombineSets(self):
        thresh = 0.01 * 0
        usethresh = 1 + 1
        flag = True
        while flag:
            flag = False
            for curSet in self.sets:
                if curSet.endPoint_isolated:
                    continue
                SameSets = self.FindCoincide(curSet)
                toEnd = []
                toStart = []
                for SameSet in SameSets:
                    d_curEnd_nxtStart = AGFuncs.P_to_P_BlockDistance(curSet.LastPoint, SameSet.FirstPoint)
                    d_nxtEnd_curStart = AGFuncs.P_to_P_BlockDistance(curSet.FirstPoint, SameSet.LastPoint)
                    d_curEnd_nxtEnd = AGFuncs.P_to_P_BlockDistance(curSet.LastPoint, SameSet.LastPoint)
                    d_curStart_nxtStart = AGFuncs.P_to_P_BlockDistance(curSet.FirstPoint, SameSet.FirstPoint)
                    if d_curEnd_nxtStart < (curSet.LastLine.radius + SameSet.FirstLine.radius) * (usethresh - 1) + thresh * usethresh:
                        toEnd.append((SameSet, False))
                    if d_nxtEnd_curStart < (curSet.FirstLine.radius + SameSet.LastLine.radius) * (usethresh - 1) + thresh * usethresh:
                        toStart.append((SameSet, False))
                    if d_curEnd_nxtEnd < (curSet.LastLine.radius + SameSet.LastLine.radius) * (usethresh - 1) + thresh * usethresh:
                        toEnd.append((SameSet, True))
                    if d_curStart_nxtStart < (curSet.FirstLine.radius + SameSet.FirstLine.radius) * (usethresh - 1) + thresh * usethresh:
                        toStart.append((SameSet, True))
                if len(toEnd) == 1:
                    curSet.Combine(toEnd[0][0], True, toEnd[0][1])
                    self.sets.remove(toEnd[0][0])
                    flag = True
                if len(toStart) == 1:
                    curSet.Combine(toStart[0][0], False, toStart[0][1])
                    if self.sets.__contains__(toStart[0][0]):
                        self.sets.remove(toStart[0][0])
                    flag = True
                if flag:
                    break
                else:
                    curSet.endPoint_isolated = True

    def FindCoincide(self, lineSet1: LineSet):  # 寻找bounding_box相交的项
        coincideSets = []
        for lineSet2 in self.sets:
            if lineSet1 != lineSet2:
                if AGFuncs.IsCoincide(lineSet1.bounding_box, lineSet2.bounding_box):
                    coincideSets.append(lineSet2)
        return coincideSets

    def __OverLapping_Set(self):
        for curSet in self.sets:
            SameSets = self.FindCoincide(curSet)
            for SameSet in SameSets:
                if SameSet.HasCompared:
                    continue
                self.__OverLapping_Pice(curSet, SameSet)
            curSet.HasCompared = True

    def __OverLapping_Pice(self, lineSet1: LineSet, lineSet2: LineSet):
        for line1index in range(lineSet1.linesNum):
            line1 = lineSet1.GetLine(line1index)
            for line2index in range(lineSet2.linesNum):
                line2 = lineSet2.GetLine(line2index)
                if line2.HasCompared or (not AGFuncs.IsCoincide(line1.bounding_box, line2.bounding_box)):
                    continue
                isl1spinl2, l1spinl2 = AGFuncs.PointIsInLine(line2.gbLine, line1.start)
                isl1epinl2, l1epinl2 = AGFuncs.PointIsInLine(line2.gbLine, line1.end)
                isl2spinl1, l2spinl1 = AGFuncs.PointIsInLine(line1.gbLine, line2.start)
                isl2epinl1, l2epinl1 = AGFuncs.PointIsInLine(line1.gbLine, line2.end)
                # ******************处理删除************************************
                l1_pre_sign = line1.signType
                if isl1spinl2 and isl1epinl2:
                    line1.signType = SignType.Delete
                if isl2spinl1 and isl2epinl1:
                    line2.signType = SignType.Delete
                if line1.signType == SignType.Delete and line2.signType == SignType.Delete and l1_pre_sign != SignType.Delete:
                    line1.signType = SignType.Unchange
            line1.HasCompared = True

    def __CutSet_Set(self):
        for curSet in self.sets:
            SameSets = self.FindCoincide(curSet)
            for SameSet in SameSets:
                if SameSet.HasCompared:
                    continue
                self.__CutSet_Pice(curSet, SameSet)
            curSet.HasCompared = True

    def __CutSet_Pice(self, lineSet1: LineSet, lineSet2: LineSet):
        for line1index in range(lineSet1.linesNum):
            line1 = lineSet1.GetLine(line1index)
            for line2index in range(lineSet2.linesNum):
                line2 = lineSet2.GetLine(line2index)
                if line2.HasCompared or (not AGFuncs.IsCoincide(line1.bounding_box, line2.bounding_box)):
                    continue
                isl1spinl2, l1spinl2 = AGFuncs.PointIsInLine(line2.gbLine, line1.start)
                isl1epinl2, l1epinl2 = AGFuncs.PointIsInLine(line2.gbLine, line1.end)
                isl2spinl1, l2spinl1 = AGFuncs.PointIsInLine(line1.gbLine, line2.start)
                isl2epinl1, l2epinl1 = AGFuncs.PointIsInLine(line1.gbLine, line2.end)
                # **************************处理集合分割**************************
                if isl1spinl2 or isl1epinl2:
                    if l1spinl2 == line2.start or l1epinl2 == line2.start:
                        line2.signType = SignType.CutSetStart
                    if l1spinl2 == line2.end or l1epinl2 == line2.end:
                        line2.signType = SignType.CutSetEnd
                if isl2spinl1 or isl2epinl1:
                    if l2spinl1 == line1.start or l2epinl1 == line1.start:
                        line1.signType = SignType.CutSetStart
                    if l2spinl1 == line1.end or l2epinl1 == line1.end:
                        line1.signType = SignType.CutSetEnd
            line1.HasCompared = True

    def __CutLine_Set(self):
        for curSet in self.sets:
            SameSets = self.FindCoincide(curSet)
            for SameSet in SameSets:
                if SameSet.HasCompared:
                    continue
                self.__CutLine_Pice(curSet, SameSet)
            curSet.HasCompared = True

    def __CutLine_Pice(self, lineSet1: LineSet, lineSet2: LineSet):
        for line1index in range(lineSet1.linesNum):
            line1 = lineSet1.GetLine(line1index)
            for line2index in range(lineSet2.linesNum):
                line2 = lineSet2.GetLine(line2index)
                if line2.HasCompared or (not AGFuncs.IsCoincide(line1.bounding_box, line2.bounding_box)):
                    continue
                isl1spinl2, l1spinl2 = AGFuncs.PointIsInLine(line2.gbLine, line1.start)
                isl1epinl2, l1epinl2 = AGFuncs.PointIsInLine(line2.gbLine, line1.end)
                isl2spinl1, l2spinl1 = AGFuncs.PointIsInLine(line1.gbLine, line2.start)
                isl2epinl1, l2epinl1 = AGFuncs.PointIsInLine(line1.gbLine, line2.end)
                crossPoint = AGFuncs.get_line_cross_point(line1.gbLine, line2.gbLine)
                # **********************************处理交叉************************************************
                if crossPoint != None and not (isl1spinl2 or isl1epinl2 or isl2spinl1 or isl2epinl1):
                    iscpinl1, cpinl1 = AGFuncs.PointIsInLine(line1.gbLine, crossPoint)
                    iscpinl2, cpinl2 = AGFuncs.PointIsInLine(line2.gbLine, crossPoint)
                    if iscpinl1:
                        if not (cpinl1 == line1.start or cpinl1 == line1.end):
                            line1.signType = SignType.Cut
                            line1.cutPoints.append(crossPoint)
                    if iscpinl2:
                        if not (cpinl2 == line2.start or cpinl2 == line2.end):
                            line2.signType = SignType.Cut
                            line2.cutPoints.append(crossPoint)
                # ***********************************处理相交***********************************************
                if isl1spinl2:
                    if not (l1spinl2 == line2.start or l1spinl2 == line2.end):
                        line2.signType = SignType.Cut
                        line2.cutPoints.append(l1spinl2)
                if isl1epinl2:
                    if not (l1epinl2 == line2.start or l1epinl2 == line2.end):
                        line2.signType = SignType.Cut
                        line2.cutPoints.append(l1epinl2)
                if isl2spinl1:
                    if not (l2spinl1 == line1.start or l2spinl1 == line1.end):
                        line1.signType = SignType.Cut
                        line1.cutPoints.append(l2spinl1)
                if isl2epinl1:
                    if not (l2epinl1 == line1.start or l2epinl1 == line1.end):
                        line1.signType = SignType.Cut
                        line1.cutPoints.append(l2epinl1)
            line1.HasCompared = True

    def __Regenerate(self):
        newsets = []
        for set in self.sets:
            newsets.extend(set.Regenerate())
        self.sets = newsets


def dataPrepar(path):
    layers = os.listdir(path)
    gerbers = {}
    for layer in layers:
        with open(f"{path}\\{layer}", "rU") as fp:
            data = fp.read()
            gerbers[layer] = data
    return gerbers


# if __name__ == '__main__':
#     gerbers = dataPrepar(r"C:\Users\96941\Desktop\新建文件夹")
#     imageGenerater = ImageGenerater(gerbers)
#     lineset = GerberPreProcess(imageGenerater.gerberLayers["gko"])
#     image = imageGenerater.DrawShow(lineset.sets, True, -1)
#     cv2.imshow("test", image)
#     kval = 13
#     while kval == 13:
#         kval = cv2.waitKey(-1)
#
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
            if index < 45:
                continue
            gerbers = dataPrepar(f"{gerberFilePath}\{groupDir}\{orderDir}")
            imageGenerater = ImageGenerater(gerbers)
            lineset = GerberPreProcess(imageGenerater.gerberLayers["gko"])
            image = imageGenerater.DrawShow(lineset.sets, False, -1)
            cv2.imshow("test", image)
            kval = 13
            while kval == 13:
                kval = cv2.waitKey(-1)
#206\JP-1W1748339\JP-1W1748167测试