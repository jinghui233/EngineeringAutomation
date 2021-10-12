from typing import List

from ProcessService.RoutLineProcess.GKOGerberProcess.LinePice import LinePice
from ProcessService.RoutLineProcess.GKOGerberProcess.SignType import SignType
from gerber.primitives import Line as Gbt_Line


class LineSet:
    def __init__(self):
        self.bounding_box = ()
        self.__lines = []
        self.linesNum = 0
        self.HasCompared = False
        self.boundingBox_isolated = False
        self.endPoint_isolated = False
        self.cross_isolated = False

    @property
    def FirstLine(self) -> LinePice:
        return self.__lines[0]

    @property
    def LastLine(self) -> LinePice:
        return self.__lines[self.linesNum - 1]

    @property
    def FirstPoint(self) -> List[float]:
        return self.__lines[0].start

    @property
    def LastPoint(self) -> List[float]:
        return self.__lines[self.linesNum - 1].end

    def GetLine(self, index: int) -> LinePice:
        return self.__lines[index]

    def GetLineSet(self) -> []:
        return self.__lines

    def addLine(self, line: LinePice):
        if (self.linesNum == 0 or self.__lines[self.linesNum - 1].end == line.start):
            self.__addLine(line)
            return True
        else:
            return False

    def __addLine(self, line: LinePice):
        self.linesNum += 1
        self.__lines.append(line)
        if len(self.bounding_box) == 0:
            try:
                self.bounding_box = line.gbLine.bounding_box
            except:
                pass
        else:
            self.bounding_box = self.bound_box(self.bounding_box, line.bounding_box)
        return self

    def ReverseSort(self):
        self.__lines.reverse()
        for index in range(len(self.__lines)):
            linepice = self.__lines[index]
            newlinepice = LinePice(Gbt_Line(linepice.end, linepice.start, linepice.aperture))
            self.__lines[index] = newlinepice

    def Combine(self, lineSet, afterOrBefor: bool, needSort: bool):
        if needSort:
            lineSet.ReverseSort()
        if afterOrBefor:
            self.__lines.extend(lineSet.GetLineSet())
        else:
            lineSet.GetLineSet().extend(self.__lines)
            self.__lines = lineSet.GetLineSet()
        self.linesNum = len(self.__lines)
        self.bounding_box = self.bound_box(self.bounding_box, lineSet.bounding_box)

    def bound_box(self, bounding_box1, bounding_box2):
        bdbox00 = min(bounding_box1[0][0], bounding_box2[0][0])
        bdbox01 = max(bounding_box1[0][1], bounding_box2[0][1])
        bdbox10 = min(bounding_box1[1][0], bounding_box2[1][0])
        bdbox11 = max(bounding_box1[1][1], bounding_box2[1][1])
        return (bdbox00, bdbox01), (bdbox10, bdbox11)

    def Regenerate(self):
        newLinesSets = []
        newLines = LineSet()
        newLinesSets.append(newLines)
        for line in self.__lines:
            line.HasCompared = False
            if line.signType == SignType.Unchange:
                newLines.__addLine(line)
            if line.signType == SignType.Cut:
                temp = line.CutSelf()
                for tempp in temp:
                    newLines = LineSet()
                    newLines.__addLine(tempp)
                    newLinesSets.append(newLines)
            if line.signType == SignType.Delete:
                newLines = LineSet()
                newLinesSets.append(newLines)
            if line.signType == SignType.CutSetStart:
                newLines = LineSet()
                newLines.__addLine(line)
                newLinesSets.append(newLines)
            if line.signType == SignType.CutSetEnd:
                newLines.__addLine(line)
                newLines = LineSet()
                newLinesSets.append(newLines)

        resultSets = []
        for item in newLinesSets:
            if item.linesNum != 0:
                resultSets.append(item)
        return resultSets
