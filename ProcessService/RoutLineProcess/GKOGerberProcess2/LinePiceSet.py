import math
from typing import List

import numpy as np
from gerber.primitives import Line as Gbt_Line, Circle as Gbt_Circle


class SignType():
    Unchange = 0
    Delete = 1
    Cut = 2
    CutSetStart = 3
    CutSetEnd = 4


class LineBase:
    def __init__(self, start, end, radius):
        self._start = start
        self._end = end
        self._radius = radius
        self._lineLength = None
        self._bounding_box = None

    def _changed(self):
        self._lineLength = None
        self._bounding_box = None

    @property
    def gbLine(self):
        return Gbt_Line(self.start, self.end, Gbt_Circle(None, self.radius * 2))

    @property
    def start(self):
        return self._start

    @start.setter
    def start(self, value):
        self._changed()
        self._start = value

    @property
    def end(self):
        return self._end

    @end.setter
    def end(self, value):
        self._changed()
        self._end = value

    @property
    def bounding_box(self):
        if self._bounding_box is None:
            width_2 = self._radius
            height_2 = width_2
            min_x = min(self.start[0], self.end[0]) - width_2
            max_x = max(self.start[0], self.end[0]) + width_2
            min_y = min(self.start[1], self.end[1]) - height_2
            max_y = max(self.start[1], self.end[1]) + height_2
            self._bounding_box = ((min_x, max_x), (min_y, max_y))
        return self._bounding_box

    @property
    def bounding_box_no_aperture(self):
        min_x = min(self.start[0], self.end[0])
        max_x = max(self.start[0], self.end[0])
        min_y = min(self.start[1], self.end[1])
        max_y = max(self.start[1], self.end[1])
        return ((min_x, max_x), (min_y, max_y))

    @property
    def angle(self):
        delta_x, delta_y = tuple(
            [end - start for end, start in zip(self.end, self.start)])
        angle = math.atan2(delta_y, delta_x)
        return angle

    @property
    def radius(self):
        return self._radius

    @property
    def LineLength(self):
        if self._lineLength == None:
            self._lineLength = np.linalg.norm(np.array([self.end[0] - self.start[0], self.end[1] - self.start[1]]))
        return self._lineLength


class LinePice(LineBase):
    def __init__(self, start, end, radius):
        LineBase.__init__(self, start, end, radius)
        self.signType = SignType.Unchange
        self.cutPoints = []
        self._lineLength = None
        self.HasCompared = False

    def CutSelf(self):
        self.SortCutPoints()
        newlineList = []
        prePoint = self.start
        for cutPoint in self.cutPoints:
            if np.linalg.norm(np.array([prePoint[0] - cutPoint[0], prePoint[1] - cutPoint[1]])) < self.radius:
                continue
            newlineList.append(LinePice(prePoint, cutPoint, self.radius))
            prePoint = cutPoint
        newlineList.append(LinePice(prePoint, self.end, self.radius))
        return newlineList

    def SortCutPoints(self):
        newCutPoints = []
        while len(self.cutPoints) > 0:
            minDistance = self.LineLength
            minPoint = None
            for cutPoint in self.cutPoints:
                curdistance = np.linalg.norm(np.array([cutPoint[0] - self.start[0], cutPoint[1] - self.start[1]]))
                if curdistance < minDistance:
                    minDistance = curdistance
                    minPoint = cutPoint
            if self.cutPoints.__contains__(minPoint):
                self.cutPoints.remove(minPoint)
                newCutPoints.append(minPoint)
        self.cutPoints = newCutPoints


class LineSetBase:
    def __init__(self):
        self.bounding_box = ()
        self._lines = []
        self.linesNum = 0

    @property
    def FirstLine(self) -> LinePice:
        return self._lines[0]

    @property
    def LastLine(self) -> LinePice:
        return self._lines[self.linesNum - 1]

    @property
    def start(self) -> List[float]:
        return self._lines[0].start

    @property
    def end(self) -> List[float]:
        return self._lines[self.linesNum - 1].end

    def GetLine(self, index: int) -> LinePice:
        return self._lines[index]

    def GetLineSet(self) -> []:
        return self._lines

    def bound_box(self, bounding_box1, bounding_box2):
        bdbox00 = min(bounding_box1[0][0], bounding_box2[0][0])
        bdbox01 = max(bounding_box1[0][1], bounding_box2[0][1])
        bdbox10 = min(bounding_box1[1][0], bounding_box2[1][0])
        bdbox11 = max(bounding_box1[1][1], bounding_box2[1][1])
        return (bdbox00, bdbox01), (bdbox10, bdbox11)

    def addLine(self, line: LinePice):
        self.linesNum += 1
        self._lines.append(line)
        if len(self.bounding_box) == 0:
            try:
                self.bounding_box = line.bounding_box
            except:
                pass
        else:
            self.bounding_box = self.bound_box(self.bounding_box, line.bounding_box)
        return self


class LineSet(LineSetBase):
    def __init__(self):
        LineSetBase.__init__(self)
        self.HasCompared = False
        self.endPoint_isolated = False

    def tryaddLine(self, line: LinePice) -> bool:
        if (self.linesNum == 0 or self._lines[self.linesNum - 1].end == line.start):
            self.addLine(line)
            return True
        else:
            return False

    def ReverseSortold(self):
        self._lines.reverse()
        for index in range(len(self._lines)):
            linepice = self._lines[index]
            newlinepice = LinePice(linepice.end, linepice.start, linepice.radius)
            self._lines[index] = newlinepice

    def ReverseSort(self):
        self._lines.reverse()
        for line in self._lines:
            line.start, line.end = line.end, line.start

    def Combine(self, lineSet, afterOrBefor: bool, needSort: bool):
        if needSort:
            lineSet.ReverseSort()
        if afterOrBefor:
            self._lines.extend(lineSet.GetLineSet())
        else:
            lineSet.GetLineSet().extend(self._lines)
            self._lines = lineSet.GetLineSet()
        self.linesNum = len(self._lines)
        self.bounding_box = self.bound_box(self.bounding_box, lineSet.bounding_box)

    def Regenerate(self):
        newLinesSets = []
        newLines = LineSet()
        newLinesSets.append(newLines)
        for line in self._lines:
            line.HasCompared = False
            if line.signType == SignType.Unchange:
                newLines.addLine(line)
            if line.signType == SignType.Cut:
                temp = line.CutSelf()
                for tempp in temp:
                    newLines = LineSet()
                    newLines.addLine(tempp)
                    newLinesSets.append(newLines)
            if line.signType == SignType.Delete:
                newLines = LineSet()
                newLinesSets.append(newLines)
            if line.signType == SignType.CutSetStart:
                newLines = LineSet()
                newLines.addLine(line)
                newLinesSets.append(newLines)
            if line.signType == SignType.CutSetEnd:
                newLines.addLine(line)
                newLines = LineSet()
                newLinesSets.append(newLines)

        resultSets = []
        for item in newLinesSets:
            if item.linesNum != 0:
                resultSets.append(item)
        return resultSets
