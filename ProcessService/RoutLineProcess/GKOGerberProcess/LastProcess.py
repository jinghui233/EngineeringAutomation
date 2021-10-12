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
    def __reCombineSets(self):

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
