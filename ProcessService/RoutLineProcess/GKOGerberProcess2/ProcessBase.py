from typing import List

from gerber.cam import CamFile
from gerber.primitives import Line as Gbt_Line

from ProcessService.RoutLineProcess.GKOGerberProcess2.AnalyticGeometry import AnalyticGeometry as AGFuncs
from ProcessService.RoutLineProcess.GKOGerberProcess2.LinePiceSet import LinePice, LineSet, SignType


class ProcessBase:
    def __init__(self, gerberLayer: CamFile):
        self.gerberLayer = gerberLayer
        self.__init()

    def __init(self):
        self.sets = []
        curSet = LineSet()
        self.sets.append(curSet)
        for primitive in self.gerberLayer.primitives:
            if not isinstance(primitive, Gbt_Line):
                continue
            if curSet.tryaddLine(LinePice(primitive.start, primitive.end, primitive.aperture.radius)):
                pass
            else:
                curSet = LineSet()
                self.sets.append(curSet)
                curSet.tryaddLine(LinePice(primitive.start, primitive.end, primitive.aperture.radius))

    def CombineSets(self, sets: List[LineSet]):
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
                    d_curEnd_nxtStart = AGFuncs.P_to_P_BlockDistance(curSet.end, SameSet.start)
                    d_nxtEnd_curStart = AGFuncs.P_to_P_BlockDistance(curSet.start, SameSet.end)
                    d_curEnd_nxtEnd = AGFuncs.P_to_P_BlockDistance(curSet.end, SameSet.end)
                    d_curStart_nxtStart = AGFuncs.P_to_P_BlockDistance(curSet.start, SameSet.start)
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
                    curSet.endPoint_isolated = True  # 该set两端是孤立的

    def FindCoincide(self, lineSet1: LineSet, sets: List[LineSet]):  # 寻找bounding_box相交的项
        coincideSets = []
        for lineSet2 in sets:
            if lineSet1 != lineSet2:
                if AGFuncs.IsCoincide(lineSet1.bounding_box, lineSet2.bounding_box):
                    coincideSets.append(lineSet2)
        return coincideSets

    def OverLapping_Set(self, sets: List[LineSet]):
        for curSet in sets:
            SameSets = self.FindCoincide(curSet, sets)
            for SameSet in SameSets:
                if SameSet.HasCompared:
                    continue
                self.OverLapping_Pice(curSet, SameSet)
            curSet.HasCompared = True

    def OverLapping_Pice(self, lineSet1: LineSet, lineSet2: LineSet):
        for line1index in range(lineSet1.linesNum):
            line1 = lineSet1.GetLine(line1index)
            for line2index in range(lineSet2.linesNum):
                line2 = lineSet2.GetLine(line2index)
                if line2.HasCompared or (not AGFuncs.IsCoincide(line1.bounding_box, line2.bounding_box)):
                    continue
                isl1spinl2, l1spinl2 = AGFuncs.PointIsInLine(line2, line1.start)
                isl1epinl2, l1epinl2 = AGFuncs.PointIsInLine(line2, line1.end)
                isl2spinl1, l2spinl1 = AGFuncs.PointIsInLine(line1, line2.start)
                isl2epinl1, l2epinl1 = AGFuncs.PointIsInLine(line1, line2.end)
                # ******************处理删除************************************
                l1_pre_sign = line1.signType
                if isl1spinl2 and isl1epinl2:
                    line1.signType = SignType.Delete
                if isl2spinl1 and isl2epinl1:
                    line2.signType = SignType.Delete
                if line1.signType == SignType.Delete and line2.signType == SignType.Delete and l1_pre_sign != SignType.Delete:
                    line1.signType = SignType.Unchange
            line1.HasCompared = True

    def CutSet_Set(self, sets: List[LineSet]):
        for curSet in sets:
            SameSets = self.FindCoincide(curSet, sets)
            for SameSet in SameSets:
                if SameSet.HasCompared:
                    continue
                self.CutSet_Pice(curSet, SameSet)
            curSet.HasCompared = True

    def CutSet_Pice(self, lineSet1: LineSet, lineSet2: LineSet):
        for line1index in range(lineSet1.linesNum):
            line1 = lineSet1.GetLine(line1index)
            for line2index in range(lineSet2.linesNum):
                line2 = lineSet2.GetLine(line2index)
                if line2.HasCompared or (not AGFuncs.IsCoincide(line1.bounding_box, line2.bounding_box)):
                    continue
                isl1spinl2, l1spinl2 = AGFuncs.PointIsInLine(line2, line1.start)
                isl1epinl2, l1epinl2 = AGFuncs.PointIsInLine(line2, line1.end)
                isl2spinl1, l2spinl1 = AGFuncs.PointIsInLine(line1, line2.start)
                isl2epinl1, l2epinl1 = AGFuncs.PointIsInLine(line1, line2.end)
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

    def CutLine_Set(self, sets: List[LineSet]):
        for curSet in sets:
            SameSets = self.FindCoincide(curSet, sets)
            for SameSet in SameSets:
                if SameSet.HasCompared:
                    continue
                self.CutLine_Pice(curSet, SameSet)
            curSet.HasCompared = True

    def CutLine_Pice(self, lineSet1: LineSet, lineSet2: LineSet):
        for line1index in range(lineSet1.linesNum):
            line1 = lineSet1.GetLine(line1index)
            for line2index in range(lineSet2.linesNum):
                line2 = lineSet2.GetLine(line2index)
                if line2.HasCompared or (not AGFuncs.IsCoincide(line1.bounding_box, line2.bounding_box)):
                    continue
                isl1spinl2, l1spinl2 = AGFuncs.PointIsInLine(line2, line1.start)
                isl1epinl2, l1epinl2 = AGFuncs.PointIsInLine(line2, line1.end)
                isl2spinl1, l2spinl1 = AGFuncs.PointIsInLine(line1, line2.start)
                isl2epinl1, l2epinl1 = AGFuncs.PointIsInLine(line1, line2.end)
                crossPoint = AGFuncs.get_line_cross_point(line1, line2)
                # **********************************处理交叉************************************************
                if crossPoint != None and not (isl1spinl2 or isl1epinl2 or isl2spinl1 or isl2epinl1):
                    iscpinl1, cpinl1 = AGFuncs.PointIsInLine(line1, crossPoint)
                    iscpinl2, cpinl2 = AGFuncs.PointIsInLine(line2, crossPoint)
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

    def Regenerate(self, sets: List[LineSet]):
        newsets = []
        for set in sets:
            newsets.extend(set.Regenerate())
        return newsets
