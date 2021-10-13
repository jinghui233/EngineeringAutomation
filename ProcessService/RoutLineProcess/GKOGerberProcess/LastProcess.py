import os
from typing import List
import cv2
from gerber.cam import CamFile
from gerber.gerber_statements import CoordStmt
from gerber.primitives import Line as Gbt_Line
from gerber.rs274x import GerberFile

from ProcessService.RoutLineProcess.GKOGerberProcess.LinePice import LinePice
from ProcessService.RoutLineProcess.GKOGerberProcess.LineSet import LineSet
from ProcessService.RoutLineProcess.GKOGerberProcess.SignType import SignType
from ProcessService.SupportFuncs.AnalyticGeometry import AnalyticGeometry as AGFuncs
from ProcessService.SupportFuncs.ImageGenerater import ImageGenerater


class LastProcess:
    def __init__(self, lineSets: List[LineSet], stats, ratek):
        self.lineSets = lineSets
        self.__applyOffset(lineSets, stats, ratek)

    def __CombineSets(self, sets):
        thresh = 0.01
        usethresh = 1
        flag = True
        while flag:
            flag = False
            for curSet in sets:
                if curSet.endPoint_isolated:
                    continue
                SameSets = self.FindCoincide(curSet, sets)
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
                    sets.remove(toEnd[0][0])
                    flag = True
                if len(toStart) == 1:
                    curSet.Combine(toStart[0][0], False, toStart[0][1])
                    if sets.__contains__(toStart[0][0]):
                        sets.remove(toStart[0][0])
                    flag = True
                if flag:
                    break
                else:
                    curSet.endPoint_isolated = True

    def FindCoincide(self, lineSet1: LineSet, sets):  # 寻找bounding_box相交的项
        coincideSets = []
        for lineSet2 in sets:
            if lineSet1 != lineSet2:
                if AGFuncs.IsCoincide(lineSet1.bounding_box, lineSet2.bounding_box):
                    coincideSets.append(lineSet2)
        return coincideSets

    def __CombinePices(self, set: LineSet):
        prePice = None
        for curPice in set.GetLineSet():
            if prePice != None:
                if abs(curPice.angle - prePice.angle) < 0.00000001:


    def line_line(self, line1: LinePice, line2: LinePice):  # 判断两条线共线

    def __applyOffset(self, lineSets, stats, ratek):
        rectslines = []
        for stat in stats:
            # 左右上下
            rectslines.append((((stat[0], stat[1]), (stat[0], stat[1] + stat[3])), ((stat[0] + stat[2], stat[1]), (stat[0] + stat[2], stat[1] + stat[3])),
                               ((stat[0], stat[1]), (stat[0] + stat[2], stat[1])), ((stat[0], stat[1] + stat[3]), (stat[0] + stat[2], stat[1] + stat[3]))))

        offset = 0.001
        for lineSet in lineSets:
            for curlinePice in lineSet.GetLineSet():
                if not ((abs(curlinePice.gbLine.angle - 0) < 0.0000001 or abs(
                        curlinePice.gbLine.angle - 1.5707963267948966) < 0.0000001) and curlinePice.LineLength > curlinePice.radius * 16):  # 该线必须横平或竖直且长度大于线宽的8倍
                    continue
                curline = ((curlinePice.start[0] * ratek, curlinePice.start[1] * ratek), (curlinePice.end[0] * ratek, curlinePice.end[1] * ratek))
                for rectlines in rectslines:
                    d_left = self.__linesDistance(curline, rectlines[0])
                    d_right = self.__linesDistance(curline, rectlines[1])
                    d_up = self.__linesDistance(curline, rectlines[2])
                    d_down = self.__linesDistance(curline, rectlines[3])
                    if d_left < 500000:
                        curlinePice.gbLine = Gbt_Line((curlinePice.start[0] + offset, curlinePice.start[1]), (curlinePice.end[0] + offset, curlinePice.end[1]),
                                                      curlinePice.aperture)
                        curlinePice._lineLength = None
                    if d_right < 500000:
                        curlinePice.gbLine = Gbt_Line((curlinePice.start[0] - offset, curlinePice.start[1]), (curlinePice.end[0] - offset, curlinePice.end[1]),
                                                      curlinePice.aperture)
                        curlinePice._lineLength = None
                    if d_up < 500000:
                        curlinePice.gbLine = Gbt_Line((curlinePice.start[0], curlinePice.start[1] + offset), (curlinePice.end[0], curlinePice.end[1] + offset),
                                                      curlinePice.aperture)
                        curlinePice._lineLength = None
                    if d_down < 500000:
                        curlinePice.gbLine = Gbt_Line((curlinePice.start[0], curlinePice.start[1] + offset), (curlinePice.end[0], curlinePice.end[1] + offset),
                                                      curlinePice.aperture)
                        curlinePice._lineLength = None

    def __linesDistance(self, line1, line2):
        d_start1 = abs(line1[0][0] - line2[0][0]) + abs(line1[0][1] - line2[0][1])
        d_end1 = abs(line1[1][0] - line2[1][0]) + abs(line1[1][1] - line2[1][1])
        d_start2 = abs(line1[0][0] - line2[1][0]) + abs(line1[0][1] - line2[1][1])
        d_end2 = abs(line1[1][0] - line2[0][0]) + abs(line1[1][1] - line2[0][1])
        return min((d_start1 + d_end1), (d_start2 + d_end2))
