import math
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

    def MovePoints(self, sets: List[LineSet]):
        for curSet in sets:
            SameSets = self.FindCoincide(curSet, sets)
            toEnd = []
            toStart = []
            for SameSet in SameSets:
                d_curEnd_nxtStart = AGFuncs.P_to_P_Distance(curSet.end, SameSet.start)
                d_nxtEnd_curStart = AGFuncs.P_to_P_Distance(curSet.start, SameSet.end)
                d_curEnd_nxtEnd = AGFuncs.P_to_P_Distance(curSet.end, SameSet.end)
                d_curStart_nxtStart = AGFuncs.P_to_P_Distance(curSet.start, SameSet.start)

                is_curEnd_nxtStart = d_curEnd_nxtStart < curSet.LastLine.radius + SameSet.FirstLine.radius + (curSet.LastLine.radius + SameSet.FirstLine.radius) / 2
                is_nxtEnd_curStart = d_nxtEnd_curStart < curSet.FirstLine.radius + SameSet.LastLine.radius + (curSet.FirstLine.radius + SameSet.LastLine.radius) / 2
                is_curEnd_nxtEnd = d_curEnd_nxtEnd < curSet.LastLine.radius + SameSet.LastLine.radius + (curSet.LastLine.radius + SameSet.LastLine.radius) / 2
                is_curStart_nxtStart = d_curStart_nxtStart < curSet.FirstLine.radius + SameSet.FirstLine.radius + (curSet.FirstLine.radius + SameSet.FirstLine.radius) / 2

                if is_curEnd_nxtStart and not is_nxtEnd_curStart and not is_curEnd_nxtEnd and not is_curStart_nxtStart:  # 当前end —>下一个start
                    toEnd.append((SameSet, False))
                if is_nxtEnd_curStart and not is_curEnd_nxtStart and not is_curEnd_nxtEnd and not is_curStart_nxtStart:  # 下一个end —>当前start
                    toStart.append((SameSet, False))
                if is_curEnd_nxtEnd and not is_curEnd_nxtStart and not is_nxtEnd_curStart and not is_curStart_nxtStart:  # 当前end —>下一个end
                    toEnd.append((SameSet, True))
                if is_curStart_nxtStart and not is_curEnd_nxtStart and not is_nxtEnd_curStart and not is_curEnd_nxtEnd:  # 当前start —>下一个start
                    toStart.append((SameSet, True))
            if len(toEnd) > 0:
                newpoint = curSet.end
                for toend in toEnd:
                    if toend[1]:  # 当前end —>下一个end
                        newpoint = AGFuncs.P_to_P_Center(newpoint, toend[0].end)
                    else:  # 当前end —>下一个start
                        newpoint = AGFuncs.P_to_P_Center(newpoint, toend[0].start)
                curSet.LastLine.end = newpoint
                for toend in toEnd:
                    if toend[1]:  # 当前end —>下一个end
                        toend[0].LastLine.end = newpoint
                    else:  # 当前end —>下一个start
                        toend[0].FirstLine.start = newpoint

            if len(toStart) > 0:
                newpoint = curSet.start
                for tostart in toStart:
                    if tostart[1]:  # 当前start —>下一个start
                        newpoint = AGFuncs.P_to_P_Center(newpoint, tostart[0].start)
                    else:  # 下一个end —>当前start
                        newpoint = AGFuncs.P_to_P_Center(newpoint, tostart[0].end)
                curSet.FirstLine.start = newpoint
                for tostart in toStart:
                    if tostart[1]:  # 当前start —>下一个start
                        tostart[0].FirstLine.start = newpoint
                    else:  # 下一个end —>当前start
                        tostart[0].LastLine.end = newpoint

    def IsSameLine(self, point1, point2, pointa, pointb):
        d1 = abs(point1[0] - pointa[0]) + abs(point1[1] - pointa[1])
        d2 = abs(point2[0] - pointb[0]) + abs(point2[1] - pointb[1])

        d3 = abs(point1[0] - pointb[0]) + abs(point1[1] - pointb[1])
        d4 = abs(point2[0] - pointa[0]) + abs(point2[1] - pointa[1])
        d = min((d1 + d2), (d3 + d4))
        return d < 0.001

    def CombineSets(self, sets: List[LineSet], k):
        # point1 = ((-0.195, 10.6024), (-0.1964, 10.5963))
        # point2 = ((12.68571, 6.44511), (5.362897, 6.447673))
        # point3 = ((12.68571, 6.44511), (12.180511, 6.44511))
        flag = True
        while flag:
            flag = False
            for curSet in sets:
                if curSet.endPoint_isolated or curSet.IsClose():
                    continue
                SameSets = self.FindCoincide(curSet, sets)
                toEnd = []
                toStart = []
                # if self.IsSameLine(curSet.start, curSet.end, point1[0], point1[1]):
                #     print(f"{curSet.start}-{curSet.end}")
                #     aaaa = 0
                for SameSet in SameSets:
                    if SameSet.IsClose():
                        continue
                    d_curEnd_nxtStart = AGFuncs.P_to_P_Distance(curSet.end, SameSet.start)
                    d_nxtEnd_curStart = AGFuncs.P_to_P_Distance(curSet.start, SameSet.end)
                    d_curEnd_nxtEnd = AGFuncs.P_to_P_Distance(curSet.end, SameSet.end)
                    d_curStart_nxtStart = AGFuncs.P_to_P_Distance(curSet.start, SameSet.start)
                    d1_is_min = d_curEnd_nxtStart <= d_nxtEnd_curStart and d_curEnd_nxtStart <= d_curEnd_nxtEnd and d_curEnd_nxtStart <= d_curStart_nxtStart
                    d2_is_min = d_nxtEnd_curStart <= d_curEnd_nxtStart and d_nxtEnd_curStart <= d_curEnd_nxtEnd and d_nxtEnd_curStart <= d_curStart_nxtStart
                    d3_is_min = d_curEnd_nxtEnd <= d_curEnd_nxtStart and d_curEnd_nxtEnd <= d_nxtEnd_curStart and d_curEnd_nxtEnd <= d_curStart_nxtStart
                    d4_is_min = d_curStart_nxtStart <= d_curEnd_nxtStart and d_curStart_nxtStart <= d_nxtEnd_curStart and d_curStart_nxtStart <= d_curEnd_nxtEnd
                    if d_curEnd_nxtStart < (curSet.LastLine.radius + SameSet.FirstLine.radius) * k and (
                            d1_is_min or curSet.linesNum > 1 or curSet.Length > curSet.FirstLine.radius * 2):
                        toEnd.append([SameSet, False, d_curEnd_nxtStart])
                    if d_nxtEnd_curStart < (curSet.FirstLine.radius + SameSet.LastLine.radius) * k and (
                            d2_is_min or curSet.linesNum > 1 or curSet.Length > curSet.FirstLine.radius * 2):
                        toStart.append([SameSet, False, d_nxtEnd_curStart])
                    if d_curEnd_nxtEnd < (curSet.LastLine.radius + SameSet.LastLine.radius) * k and (
                            d3_is_min or curSet.linesNum > 1 or curSet.Length > curSet.FirstLine.radius * 2):
                        toEnd.append([SameSet, True, d_curEnd_nxtEnd])
                    if d_curStart_nxtStart < (curSet.FirstLine.radius + SameSet.FirstLine.radius) * k and (
                            d4_is_min or curSet.linesNum > 1 or curSet.Length > curSet.FirstLine.radius * 2):
                        toStart.append([SameSet, True, d_curStart_nxtStart])

                    # if d_curEnd_nxtStart < (curSet.LastLine.radius + SameSet.FirstLine.radius) * k:
                    #     toEnd.append((SameSet, False, d_curEnd_nxtStart))
                    # if d_nxtEnd_curStart < (curSet.FirstLine.radius + SameSet.LastLine.radius) * k:
                    #     toStart.append((SameSet, False, d_nxtEnd_curStart))
                    # if d_curEnd_nxtEnd < (curSet.LastLine.radius + SameSet.LastLine.radius) * k:
                    #     toEnd.append((SameSet, True, d_curEnd_nxtEnd))
                    # if d_curStart_nxtStart < (curSet.FirstLine.radius + SameSet.FirstLine.radius) * k:
                    #     toStart.append((SameSet, True, d_curStart_nxtStart))
                if curSet.Length <= curSet.FirstLine.radius * 2:
                    toEnd = self.ProcessCombine(toEnd)
                    toStart = self.ProcessCombine(toStart)
                if len(toEnd) == 1:
                    # if self.IsSameLine(toEnd[0][0].start, toEnd[0][0].end, point1[0], point1[1]):
                    #     print(f"{toEnd[0][0].start}-{toEnd[0][0].end}")
                    #     aaaa = 0
                    curSet.Combine(toEnd[0][0], True, toEnd[0][1])
                    sets.remove(toEnd[0][0])
                    flag = True
                if len(toStart) == 1:
                    # if self.IsSameLine(toStart[0][0].start, toStart[0][0].end, point1[0], point1[1]):
                    #     print(f"{toStart[0][0].start}-{toStart[0][0].end}")
                    #     aaaa = 0
                    curSet.Combine(toStart[0][0], False, toStart[0][1])
                    if sets.__contains__(toStart[0][0]):
                        sets.remove(toStart[0][0])
                    flag = True
                if flag:
                    break
                else:
                    curSet.endPoint_isolated = True  # 该set两端是孤立的

    def ProcessCombine(self, toNext):
        # if len(toNext) == 2:
        #     if AGFuncs.Line_Line_isConnected(toNext[0][0], toNext[1][0]):
        #         if toNext[0][2] > toNext[1][2]:
        #             toNext.remove(toNext[0])
        #         elif toNext[0][2] < toNext[1][2]:
        #             toNext.remove(toNext[1])
        remove = []
        for i in range(len(toNext)):
            for j in range(len(toNext)):
                if toNext[i] != toNext[j]:
                    if AGFuncs.Line_Line_isConnected(toNext[i][0], toNext[j][0]):
                        if toNext[i][2] > toNext[j][2]:
                            remove.append(i)
                        elif toNext[i][2] < toNext[j][2]:
                            remove.append(j)
        new = []
        for i in range(len(toNext)):
            if not remove.__contains__(i):
                new.append(toNext[i])
        return new

    def ProcessCombine2(self, toNext):
        if len(toNext) < 2:
            return toNext
        sets = []
        sets.append(toNext[-1])  # 将最后一个元素添到list中
        toNext = toNext[0:-1]  # 删除最后一个元素
        flage = True
        while flage:
            flage = False
            for tonext in toNext:
                rest = AGFuncs.Line_Line_isConnected2(sets[0][0].start, sets[-1][0].end, tonext[0].start, tonext[0].end)
                if rest == 1:
                    temp = sets
                    sets.clear()
                    tonext[0].ReverseSort()
                    if tonext[1]:
                        tonext[1] = False
                    sets.append(tonext)
                    sets.extend(temp)
                    flage = True
                if rest == 2:
                    tonext[0].ReverseSort()
                    if tonext[1]:
                        tonext[1] = False
                    sets.append(tonext)
                    flage = True
                if rest == 3:
                    temp = sets
                    sets.clear()
                    sets.append(tonext)
                    sets.extend(temp)
                    flage = True
                if rest == 4:
                    sets.append(tonext)
                    flage = True
                if flage:
                    toNext.remove(tonext)
        if len(toNext) > 0:
            return []
        if sets[0][2] > sets[-1][2]:
            return [sets[-1]]
        if sets[0][2] < sets[-1][2]:
            return [sets[0]]
        return []

    def FindCoincide(self, lineSet1: LineSet, sets: List[LineSet], padding=0.0):  # 寻找bounding_box相交的项
        coincideSets = []
        for lineSet2 in sets:
            if lineSet1 != lineSet2:
                if padding != 0:
                    bbox1 = (
                        (lineSet1.bounding_box[0][0] - padding, lineSet1.bounding_box[0][1] + padding),
                        (lineSet1.bounding_box[1][0] - padding, lineSet1.bounding_box[1][1] + padding))
                    bbox2 = (
                        (lineSet2.bounding_box[0][0] - padding, lineSet2.bounding_box[0][1] + padding),
                        (lineSet2.bounding_box[1][0] - padding, lineSet2.bounding_box[1][1] + padding))
                    if AGFuncs.IsCoincide(bbox1, bbox2):
                        coincideSets.append(lineSet2)
                else:
                    if AGFuncs.IsCoincide(lineSet1.bounding_box, lineSet2.bounding_box):
                        coincideSets.append(lineSet2)
        return coincideSets

    def OverLapping_Set(self, sets: List[LineSet], use_r2: int):
        for curSet in sets:
            SameSets = self.FindCoincide(curSet, sets)
            for SameSet in SameSets:
                if SameSet.HasCompared:
                    continue
                self.OverLapping_Pice(curSet, SameSet, use_r2)
            curSet.HasCompared = True

    def OverLapping_Pice(self, lineSet1: LineSet, lineSet2: LineSet, use_r2: int):
        point1 = ((15.3149, 1.9572), (15.3149, 2.1577))
        for line1index in range(lineSet1.linesNum):
            line1 = lineSet1.GetLine(line1index)
            for line2index in range(lineSet2.linesNum):
                line2 = lineSet2.GetLine(line2index)
                # if self.IsSameLine(line1.start, line1.end, point1[0], point1[1]):
                #     print(f"{line1.start}-{line1.end}")
                #     aaaa = 0
                # if self.IsSameLine(line2.start, line2.end, point1[0], point1[1]):
                #     print(f"{line2.start}-{line2.end}")
                #     aaaa = 0
                if line2.HasCompared or (not AGFuncs.IsCoincide(line1.bounding_box, line2.bounding_box)):
                    continue
                if use_r2 == 0 and line1.LineLength > line1.radius * 4 and line2.LineLength > line2.radius * 4:
                    use_r2 = 1
                if use_r2 == 0 and line1.LineLength > line1.radius * 2 and line2.LineLength > line2.radius * 2 and line1.LineLength < line1.radius * 4 and line2.LineLength < line2.radius * 4 and abs(
                        line1.angle - line2.angle) < 0.06981317007977318:
                    use_r2 = 1
                if line1.LineLength < line1.radius and line2.LineLength < line2.radius:
                    use_r2 = -0.2
                isl1spinl2, l1spinl2 = AGFuncs.PointIsInLine(line2, line1.start, line1.radius * use_r2)
                isl1epinl2, l1epinl2 = AGFuncs.PointIsInLine(line2, line1.end, line1.radius * use_r2)
                isl2spinl1, l2spinl1 = AGFuncs.PointIsInLine(line1, line2.start, line2.radius * use_r2)
                isl2epinl1, l2epinl1 = AGFuncs.PointIsInLine(line1, line2.end, line2.radius * use_r2)
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
        # if lineSet1.linesNum == 2:
        #     a1 = AGFuncs.P_to_P_BlockDistance(lineSet1.GetLine(0).start, (0.19685, 2.99885))
        #     a2 = AGFuncs.P_to_P_BlockDistance(lineSet1.GetLine(0).end, (2.03485, 2.99885))
        #     a3 = AGFuncs.P_to_P_BlockDistance(lineSet1.GetLine(1).start, (2.03485, 2.99885))
        #     a4 = AGFuncs.P_to_P_BlockDistance(lineSet1.GetLine(1).end, (2.03485, 5.80085))
        #     if math.fabs(a1) + math.fabs(a2) + math.fabs(a3) + math.fabs(a4) < 0.0001:
        #         aas = 0
        for line1index in range(lineSet1.linesNum):
            line1 = lineSet1.GetLine(line1index)
            for line2index in range(lineSet2.linesNum):
                line2 = lineSet2.GetLine(line2index)
                if line2.HasCompared or (not AGFuncs.IsCoincide(line1.bounding_box, line2.bounding_box)):
                    continue
                isl1spinl2, l1spinl2 = AGFuncs.PointIsInLine(line2, line1.start, line1.radius)
                isl1epinl2, l1epinl2 = AGFuncs.PointIsInLine(line2, line1.end, line1.radius)
                isl2spinl1, l2spinl1 = AGFuncs.PointIsInLine(line1, line2.start, line2.radius)
                isl2epinl1, l2epinl1 = AGFuncs.PointIsInLine(line1, line2.end, line2.radius)
                # **************************处理集合分割**************************
                if isl1spinl2 or isl1epinl2:
                    if l1spinl2 == line2.start or l1epinl2 == line2.start:
                        line2.signType = line1.signType | SignType.CutSetStart
                    if l1spinl2 == line2.end or l1epinl2 == line2.end:
                        line2.signType = line1.signType | SignType.CutSetEnd
                if isl2spinl1 or isl2epinl1:
                    if l2spinl1 == line1.start or l2epinl1 == line1.start:
                        line1.signType = line1.signType | SignType.CutSetStart
                    if l2spinl1 == line1.end or l2epinl1 == line1.end:
                        line1.signType = line1.signType | SignType.CutSetEnd
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
                # if AGFuncs.Line_Line_isConnected(line1, line2):
                #     continue
                isl1spinl2, l1spinl2 = AGFuncs.PointIsInLine(line2, line1.start, line1.radius)
                isl1epinl2, l1epinl2 = AGFuncs.PointIsInLine(line2, line1.end, line1.radius)
                isl2spinl1, l2spinl1 = AGFuncs.PointIsInLine(line1, line2.start, line2.radius)
                isl2epinl1, l2epinl1 = AGFuncs.PointIsInLine(line1, line2.end, line2.radius)
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
                    # line1.start = l1spinl2
                    if not (l1spinl2 == line2.start or l1spinl2 == line2.end):
                        line2.signType = SignType.Cut
                        line2.cutPoints.append(l1spinl2)
                        # line1.start = l1spinl2
                if isl1epinl2:
                    # line1.end = l1epinl2
                    if not (l1epinl2 == line2.start or l1epinl2 == line2.end):
                        line2.signType = SignType.Cut
                        line2.cutPoints.append(l1epinl2)
                        # line1.end = l1epinl2
                if isl2spinl1:
                    # line2.start = l2spinl1
                    if not (l2spinl1 == line1.start or l2spinl1 == line1.end):
                        line1.signType = SignType.Cut
                        line1.cutPoints.append(l2spinl1)
                        # line2.start = l2spinl1
                if isl2epinl1:
                    # line2.end = l2epinl1
                    if not (l2epinl1 == line1.start or l2epinl1 == line1.end):
                        line1.signType = SignType.Cut
                        line1.cutPoints.append(l2epinl1)
                        # line2.end = l2epinl1
            line1.HasCompared = True

    def Regenerate(self, sets: List[LineSet]):
        newsets = []
        for set in sets:
            newsets.extend(set.Regenerate())
        return newsets
