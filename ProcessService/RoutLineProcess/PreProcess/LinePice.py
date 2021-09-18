import time

from gerber.primitives import Line as Gbt_Line

import numpy as np
from ProcessService.RoutLineProcess.PreProcess.SignType import SignType


class LinePice:
    def __init__(self, gbLine: Gbt_Line):
        self.gbLine = gbLine
        self.signType = SignType.Unchange
        self.cutPoints = []
        self._lineLength = None
        self.HasCompared = False

    @property
    def start(self):
        return self.gbLine.start

    @property
    def end(self):
        return self.gbLine.end

    @property
    def bounding_box(self):
        return self.gbLine.bounding_box

    @property
    def aperture(self):
        return self.gbLine.aperture

    @property
    def LineLength(self):
        if self._lineLength == None:
            self._lineLength = np.linalg.norm(np.array([self.end[0] - self.start[0], self.end[1] - self.start[1]]))
        return self._lineLength
    @property
    def radius(self):
        return self.gbLine.aperture.radius
    def CutSelf(self):
        self.SortCutPoints()
        newlineList = []
        prePoint = self.gbLine.start
        for cutPoint in self.cutPoints:
            if np.linalg.norm(np.array([prePoint[0] - cutPoint[0], prePoint[1] - cutPoint[1]])) < self.gbLine.aperture.radius:
                continue
            newlineList.append(LinePice(Gbt_Line(prePoint, cutPoint, self.aperture)))
            prePoint = cutPoint
        newlineList.append(LinePice(Gbt_Line(prePoint, self.end, self.aperture)))
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
# cutPoint(129.61503970093406, 248.23099959999973)
# <Line (129.8156154, 248.18510179999998) to (129.66143739999998, 248.22038239999998)>
# r=0.0999998
