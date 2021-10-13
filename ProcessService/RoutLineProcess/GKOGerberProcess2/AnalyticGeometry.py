from typing import List

import numpy as np
import math
from ProcessService.RoutLineProcess.GKOGerberProcess2.LinePiceSet import LineBase

class AnalyticGeometry:

    @staticmethod
    def Calc_k_d(sx, sy, ex, ey):
        k = (ey - sy) / (ex - sx)
        d = sy - k * sx
        return k, d

    @staticmethod
    def P_to_P_BlockDistance(point1: List[float], point2: List[float]) -> float:
        return math.fabs(point1[0] - point2[0]) + math.fabs(point1[1] - point2[1])

    @staticmethod
    def PointIsInLine(line: LineBase, point: tuple):
        if np.linalg.norm(np.array([line.end[0] - point[0], line.end[1] - point[1]])) < line.radius:
            return True, line.end
        if np.linalg.norm(np.array([line.start[0] - point[0], line.start[1] - point[1]])) < line.radius:
            return True, line.start
        # 点到线距离  交点坐标   起点到交点的距离    线长度
        distance, crossPoint, crossDistance, lineLength = AnalyticGeometry.PointToLine(line, point)
        if crossDistance > 0 and crossDistance < lineLength and distance < line.radius:
            return True, crossPoint
        return False, None

    @staticmethod
    def PointToLine(line: LineBase, point: tuple):  # 点到线的距离，交点坐标，起点到交点的距离，线长度 参考https://blog.csdn.net/tracing/article/details/46563383
        a = np.array([point[0] - line.start[0], point[1] - line.start[1]])
        b = np.array([line.end[0] - line.start[0], line.end[1] - line.start[1]])
        bLength = np.linalg.norm(b)  # 线长度
        cnorm = a.dot(b) / bLength  # 交点坐标到线起点距离，+为正向-为反向
        c = (b / bLength) * cnorm
        pc = (line.start[0] + c[0], line.start[1] + c[1])  # 垂线交点坐标
        return np.linalg.norm(a - c), pc, cnorm, bLength

    @staticmethod
    def calc_abc_from_line_2d(x0, y0, x1, y1):
        a = y0 - y1
        b = x1 - x0
        c = x0 * y1 - x1 * y0
        return a, b, c

    @staticmethod
    def get_line_cross_point(line1: LineBase, line2: LineBase):
        # x1y1x2y2
        a0, b0, c0 = AnalyticGeometry.calc_abc_from_line_2d(line1.start[0], line1.start[1], line1.end[0], line1.end[1])
        a1, b1, c1 = AnalyticGeometry.calc_abc_from_line_2d(line2.start[0], line2.start[1], line2.end[0], line2.end[1])
        D = a0 * b1 - a1 * b0
        if D == 0:
            return None
        x = (b0 * c1 - b1 * c0) / D
        y = (a1 * c0 - a0 * c1) / D
        inline1 = x >= line1.bounding_box[0][0] and x <= line1.bounding_box[0][1] and y >= line1.bounding_box[1][0] and y <= line1.bounding_box[1][1]
        inline2 = x >= line2.bounding_box[0][0] and x <= line2.bounding_box[0][1] and y >= line2.bounding_box[1][0] and y <= line2.bounding_box[1][1]
        if inline1 and inline2:
            return x, y
        return None

    @staticmethod
    def IsCoincide(bounding_box1: tuple, bounding_box2: tuple):  # 判断两矩形相交
        minx1 = bounding_box1[0][0]
        maxx1 = bounding_box1[0][1]
        miny1 = bounding_box1[1][0]
        maxy1 = bounding_box1[1][1]

        minx2 = bounding_box2[0][0]
        maxx2 = bounding_box2[0][1]
        miny2 = bounding_box2[1][0]
        maxy2 = bounding_box2[1][1]

        minx = max(minx1, minx2)
        miny = max(miny1, miny2)
        maxx = min(maxx1, maxx2)
        maxy = min(maxy1, maxy2)

        return (minx < maxx) and (miny < maxy)


class AnalyticLine:
    def __init__(self, line: LineBase):
        self.line = line
        self.k = 0
        self.d = 0
        self.sx = line.start[0]
        self.sy = line.start[1]
        self.ex = line.end[0]
        self.ey = line.end[1]
        self.thickness = line.radius
