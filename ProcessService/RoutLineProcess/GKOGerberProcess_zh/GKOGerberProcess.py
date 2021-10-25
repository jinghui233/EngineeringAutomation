import sys
import random
import math
import numpy as np
import gerber
from ProcessService.RoutLineProcess.GKOGerberProcess2.LinePiceSet import LinePice as LinePice_sd, LineSet as LineSet_sd


class GKOGerberProcess:
    def __init__(self, gerberLayer):
        self.gerberLayer = gerberLayer
        self.Lines = []
        self.Nodes = []
        self.Points = []
        self.NewLineList = []
        self.LineList = []
        self.LineSet = []
        self.Points_set=[]

    # [[[[0.15748, 0.5315, 1], [1.65354, 0.5315, 0]], [[1.65354, 0.5315, 0], [1.65354, 0.15748, 1]]],
    #  [[0.15748, 0.5315, 1], [1.65354, 0.15748, 1]]]
    def dataTrans(self):
        sets = []
        i=0
        for lineSet in self.LineSet:
            lines = []
            for line in lineSet:
                # print(line[0][0])
                lines.append(LinePice_sd((line[0][0], line[0][1]), (line[1][0], line[1][1]), 1))
            set = LineSet_sd()
            # print(self.Points_set)
            set.start1=[self.Points_set[i][0][0],self.Points_set[i][0][1]]
            set.end1=[self.Points_set[i][1][0],self.Points_set[i][1][1]]
            set.setLines(lines)
            sets.append(set)
            i+=1
        self.sets = sets

    def PreProc(self):
        self.Lineset()
        self.LineInit(self.Lines)
        self.Nodedetermine()
        self.LineCut()
        self.Lineclassify()
        self.dataTrans()

    # 求两点距离
    def distance(self, x1, y1, x2, y2):
        return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

    def Lineset(self):
        k = len(self.gerberLayer.primitives)
        for i in range(k):
            if type(self.gerberLayer.primitives[i]) == gerber.primitives.Line:
                x_1 = self.gerberLayer.primitives[i].start[0]
                y_1 = self.gerberLayer.primitives[i].start[1]
                x_2 = self.gerberLayer.primitives[i].end[0]
                y_2 = self.gerberLayer.primitives[i].end[1]
                b_x = self.gerberLayer.primitives[i].bounding_box[0]
                b_y = self.gerberLayer.primitives[i].bounding_box[1]
                self.Lines.append([[x_1, y_1], [x_2, y_2], [b_x[0], b_x[1]], [b_y[0], b_y[1]], i])

    # 线段去重
    def LineInit(self, Line):
        n = len(Line)
        i = 0
        while i < n:
            j = 0
            while j < n:
                if i != j:
                    p1_x = Line[i][0][0]
                    p1_y = Line[i][0][1]
                    p2_x = Line[i][1][0]
                    p2_y = Line[i][1][1]
                    q1_x = Line[j][0][0]
                    q1_y = Line[j][0][1]
                    q2_x = Line[j][1][0]
                    q2_y = Line[j][1][1]
                    A1 = p2_y - p1_y
                    B1 = p1_x - p2_x
                    C1 = p1_y * (p2_x - p1_x) - p1_x * (p2_y - p1_y)
                    A2 = q2_y - q1_y
                    B2 = q1_x - q2_x
                    C2 = q1_y * (q2_x - q1_x) - q1_x * (q2_y - q1_y)
                    D = abs(A1 * q1_x + B1 * q1_y + C1) / math.sqrt(A1 ** 2 + B1 ** 2) + abs(
                        A1 * q2_x + B1 * q2_y + C1) / math.sqrt(A1 ** 2 + B1 ** 2)
                    if D > 0.01:
                        j += 1
                        continue
                    data_p1 = (q1_x - p1_x) * (q1_y - q2_y) - (q1_y - p1_y) * (q1_x - q2_x)
                    data_p2 = (q1_x - p2_x) * (q1_y - q2_y) - (q1_y - p2_y) * (q1_x - q2_x)
                    data_q1 = (p1_x - q1_x) * (p1_y - p2_y) - (p1_y - q1_y) * (p1_x - p2_x)
                    data_q2 = (p1_x - q2_x) * (p1_y - p2_y) - (p1_y - q2_y) * (p1_x - p2_x)
                    linewidth1 = min(p1_x, p2_x) - Line[i][2][0]
                    linewidth2 = min(q1_x, q2_x) - Line[j][2][0]
                    linelength1 = self.distance(p1_x, p1_y, p2_x, p2_y)
                    linelength2 = self.distance(q1_x, q1_y, q2_x, q2_y)

                    K = 3 * linelength1 * linelength1 * linelength2
                    if linelength1 > 10 * linelength2:
                        K = 0.0005
                    if abs(A1 * B2 - B1 * A2) <= K and D <= linewidth1 * 2:

                        # if D < linewidth*3 :
                        if q1_x > Line[i][2][0] and q1_x < Line[i][2][1] and q1_y > Line[i][3][0] and q1_y < Line[i][3][
                            1]:
                            if q2_x > Line[i][2][0] and q2_x < Line[i][2][1] and q2_y > Line[i][3][0] and q2_y < \
                                    Line[i][3][1]:
                                # print(j,n,Line[j][4])
                                Line.pop(j)
                                n = len(Line)
                                if i == n: break
                                if j == n: break
                                if i > j: i = i - 1
                                continue
                            elif q2_x < Line[i][2][0] or q2_x > Line[i][2][1] or q2_y < Line[i][3][0] or q2_y > \
                                    Line[i][3][1]:
                                # print(Line[i], Line[j])
                                Line[j][0] = [q2_x, q2_y]
                                if self.distance(p1_x, p1_y, q2_x, q2_y) < self.distance(p2_x, p2_y, q2_x, q2_y):
                                    Line[j][1] = [p1_x, p1_y]
                                else:
                                    Line[j][1] = [p2_x, p2_y]
                                Line[j][2][0] = min(Line[j][0][0], Line[j][1][0]) - linewidth1
                                Line[j][2][1] = max(Line[j][0][0], Line[j][1][0]) + linewidth1
                                Line[j][3][0] = min(Line[j][0][1], Line[j][1][1]) - linewidth1
                                Line[j][3][1] = max(Line[j][0][1], Line[j][1][1]) + linewidth1

                        elif Line[i][2][0] <= q2_x <= Line[i][2][1] and Line[i][3][0] <= q2_y <= Line[i][3][1] and (
                                q1_x < Line[i][2][0] or q1_x > Line[i][2][1] or q1_y < Line[i][3][0] or q1_y >
                                Line[i][3][1]):
                            Line[j][0] = [q1_x, q1_y]
                            if self.distance(p1_x, p1_y, q1_x, q1_y) < self.distance(p2_x, p2_y, q1_x, q1_y):
                                Line[j][1] = [p1_x, p1_y]
                            else:
                                Line[j][1] = [p2_x, p2_y]

                            Line[j][2][0] = min(Line[j][0][0], Line[j][1][0]) - linewidth1
                            Line[j][2][1] = max(Line[j][0][0], Line[j][1][0]) + linewidth1
                            Line[j][3][0] = min(Line[j][0][1], Line[j][1][1]) - linewidth1
                            Line[j][3][1] = max(Line[j][0][1], Line[j][1][1]) + linewidth1
                n = len(Line)
                if i == n: break
                if j == n: break

                j += 1
            i += 1
        i = 0
        #
        i = 0
        while i < n:
            j = 0
            while j < n:
                if i != j:
                    p1_x = Line[i][0][0]
                    p1_y = Line[i][0][1]
                    p2_x = Line[i][1][0]
                    p2_y = Line[i][1][1]
                    q1_x = Line[j][0][0]
                    q1_y = Line[j][0][1]
                    q2_x = Line[j][1][0]
                    q2_y = Line[j][1][1]
                    A1 = p2_y - p1_y
                    B1 = p1_x - p2_x
                    C1 = p1_y * (p2_x - p1_x) - p1_x * (p2_y - p1_y)
                    A2 = q2_y - q1_y
                    B2 = q1_x - q2_x
                    C2 = q1_y * (q2_x - q1_x) - q1_x * (q2_y - q1_y)
                    D1 = abs(A1 * q1_x + B1 * q1_y + C1) / math.sqrt(A1 ** 2 + B1 ** 2)
                    D2 = abs(A1 * q2_x + B1 * q2_y + C1) / math.sqrt(A1 ** 2 + B1 ** 2)
                    data_p1 = (q1_x - p1_x) * (q1_y - q2_y) - (q1_y - p1_y) * (q1_x - q2_x)
                    data_p2 = (q1_x - p2_x) * (q1_y - q2_y) - (q1_y - p2_y) * (q1_x - q2_x)
                    data_q1 = (p1_x - q1_x) * (p1_y - p2_y) - (p1_y - q1_y) * (p1_x - p2_x)
                    data_q2 = (p1_x - q2_x) * (p1_y - p2_y) - (p1_y - q2_y) * (p1_x - p2_x)
                    linewidth1 = min(p1_x, p2_x) - Line[i][2][0]
                    linewidth2 = min(q1_x, q2_x) - Line[j][2][0]
                    linelength1 = self.distance(p1_x, p1_y, p2_x, p2_y)
                    linelength2 = self.distance(q1_x, q1_y, q2_x, q2_y)
                    K = 3 * linelength1 * linelength1 * linelength2
                    if linelength1 > 10 * linelength2:
                        K = 0.1
                    if abs(A1 * B2 - B1 * A2) <= K and D <= linewidth1 * 4:

                        # if D < linewidth*3 :
                        if q1_x > Line[i][2][0] and q1_x < Line[i][2][1] and q1_y > Line[i][3][0] and q1_y < Line[i][3][
                            1]:
                            if q2_x > Line[i][2][0] and q2_x < Line[i][2][1] and q2_y > Line[i][3][0] and q2_y < \
                                    Line[i][3][1]:
                                # print(j,n,Line[j][4])
                                Line.pop(j)
                                n = len(Line)
                                if i == n: break
                                if j == n: break
                                if i > j: i = i - 1
                                continue
                n = len(Line)
                if i == n - 1: break
                if j == n - 1: break

                j += 1
            i += 1

    def Pointsselect(self):
        Points = []
        Nodes = []
        k = len(self.Lines)
        # k=100
        for i in range(k):
            p1_x = self.Lines[i][0][0]
            p1_y = self.Lines[i][0][1]
            p2_x = self.Lines[i][1][0]
            p2_y = self.Lines[i][1][1]
            linewidth1 = min(p1_x, p2_x) - self.Lines[i][2][0]
            d = self.distance(p1_x, p1_y, p2_x, p2_y)
            Points.append([i, p1_x, p1_y, 0, 1])
            Points.append([i, p2_x, p2_y, d, 1])

        Points = np.mat(Points)
        Points1 = Points[:, 1:3].tolist()
        Points = Points.tolist()
        # print(Points[0])
        for i in range(len(Points)):
            n = 1
            for j in range(len(Points)):
                # print(np.array(Points1)[i][1])
                if i != j and \
                        self.distance(np.array(Points1[i][0]), np.array(Points1[i][1]), np.array(Points1[j][0]),
                                      np.array(Points1[j][1])) <= linewidth1 / 1.4 \
                        and i // 2 != j // 2:
                    # print(Points)
                    Points[i][4] += 1
        for i in range(len(Points)):
            if Points[i][4] > 2:
                Nodes.append([int(Points[i][0]), Points[i][1], Points[i][2], Points[i][3]])
        return Nodes

    def Nodedetermine(self):
        j = 0
        k = len(self.Lines)
        Line = self.Lines
        for i in range(k):

            for j in range(k):
                p1_x = Line[i][0][0]
                p1_y = Line[i][0][1]
                p2_x = Line[i][1][0]
                p2_y = Line[i][1][1]
                q1_x = Line[j][0][0]
                q1_y = Line[j][0][1]
                q2_x = Line[j][1][0]
                q2_y = Line[j][1][1]
                A1 = p2_y - p1_y
                B1 = p1_x - p2_x
                A2 = q2_y - q1_y
                B2 = q1_x - q2_x
                C1 = p1_y * (p2_x - p1_x) - p1_x * (p2_y - p1_y)
                Dq1 = abs(A1 * q1_x + B1 * q1_y + C1) / math.sqrt(A1 ** 2 + B1 ** 2)
                Dq2 = abs(A1 * q2_x + B1 * q2_y + C1) / math.sqrt(A1 ** 2 + B1 ** 2)
                linewidth = min(q1_x, q2_x) - Line[j][2][0]
                linelength1 = self.distance(p1_x, p1_y, p2_x, p2_y)
                linelength2 = self.distance(q1_x, q1_y, q2_x, q2_y)
                # if (p2_x,p2_y)==(q1_x,q1_y) or ((p1_x,p1_y)==(q2_x,q2_y)):N+=1
                # [[1.874094, 0.739961], [1.84811, 0.744094], [1.8441729999999998, 1.878031], [0.7360239999999999, 0.7480310000000001], 19]
                # [[2.124527, 0.746968], [1.821381, 0.746575], [1.8174439999999998, 2.128464], [0.742638, 0.7509049999999999], 125]
                if i == j: continue  # 排除同一条线
                # print(Line[i][2][0],)
                # 判断是否满足快速排斥实验
                if (Line[i][2][0] <= Line[j][2][1]) and (Line[j][2][0] <= Line[i][2][1]) and (
                        Line[i][3][0] <= Line[j][3][1]) and (Line[j][3][0] <= Line[i][3][1]):
                    data_p1 = (q1_x - p1_x) * (q1_y - q2_y) - (q1_y - p1_y) * (q1_x - q2_x)
                    data_p2 = (q1_x - p2_x) * (q1_y - q2_y) - (q1_y - p2_y) * (q1_x - q2_x)
                    data_q1 = (p1_x - q1_x) * (p1_y - p2_y) - (p1_y - q1_y) * (p1_x - p2_x)
                    data_q2 = (p1_x - q2_x) * (p1_y - p2_y) - (p1_y - q2_y) * (p1_x - p2_x)
                    K = -0.0000000009
                    if max(linelength1, linelength2) < 0.02 or (linelength2 > 0.02 and abs(
                            A1 / (B1 + 0.0000000000000001) - A2 / (
                                    B2 + 0.0000000000000001)) > 1000): K = -0.001  # linelength2 > 0.01
                    # print(data_p1, data_p2)
                    # print(data_p1 * data_p2, Dq1,Dq2,linewidth*5,q2_x,Line[i][2][0])
                    # print(data_p1 * data_p2 < -0.00001,Dq2 <= linewidth*5,q2_x > Line[i][2][0] , q2_x < Line[i][2][1] , q2_y > Line[i][3][0] , q2_y <Line[i][3][1])
                    if data_p1 * data_p2 < -0.0003 and (data_q1 * data_q2 < -0.0003):
                        tmpLeft = (q2_x - q1_x) * (p1_y - p2_y) - (p2_x - p1_x) * (q1_y - q2_y)
                        tmpRight = (p1_y - q1_y) * (p2_x - p1_x) * (q2_x - q1_x) + q1_x * (q2_y - q1_y) * (
                                p2_x - p1_x) - p1_x * (p2_y - p1_y) * (q2_x - q1_x)
                        x = tmpRight / tmpLeft
                        tmpLeft = (p1_x - p2_x) * (q2_y - q1_y) - (p2_y - p1_y) * (q1_x - q2_x)
                        tmpRight = p2_y * (p1_x - p2_x) * (q2_y - q1_y) + (q2_x - p2_x) * (q2_y - q1_y) * (
                                p1_y - p2_y) - q2_y * (q1_x - q2_x) * (p2_y - p1_y)
                        y = tmpRight / tmpLeft
                        d = self.distance(x, y, p1_x, p1_y)
                        self.Nodes.append([i, x, y, d, j])

                    elif data_p1 * data_p2 < K and (Dq1 <= linewidth * 3.9) and (
                            q1_x > Line[i][2][0] and q1_x < Line[i][2][1] and q1_y > Line[i][3][0] and q1_y <
                            Line[i][3][1]):
                        # print(i,p1_x, p1_y)
                        self.Nodes.append([i, q1_x, q1_y, self.distance(p1_x, p1_y, q1_x, q1_y)])
                        self.Nodes.append([j, q1_x, q1_y, self.distance(q1_x, q1_y, q1_x, q1_y)])
                        # print(self.Nodes)
                    elif data_p1 * data_p2 < K and (Dq2 <= linewidth * 3.9) \
                            and q2_x > Line[i][2][0] and q2_x < Line[i][2][1] and q2_y > Line[i][3][0] and q2_y < \
                            Line[i][3][1]:
                        # print(0000)
                        self.Nodes.append([i, q2_x, q2_y, self.distance(p1_x, p1_y, q2_x, q2_y)])
                        self.Nodes.append([j, q2_x, q2_y, self.distance(q1_x, q1_y, q2_x, q2_y)])
                    # print(i,j,Line[i],Line[j])

        Node1 = self.Pointsselect()

        for i in range(len(Node1)):
            self.Nodes.append(Node1[i])
        # print(Node1)
        self.Nodes.sort(key=lambda x: (-x[0], -x[3]), reverse=True)
        # print(self.Nodes)
        return self.Nodes

    def LineCut(self):
        k = len(self.Lines)
        Line = self.Lines
        # print(Line)
        NewList = []
        NewLineList = []
        for i in range(k):
            NewList.append([Line[i][0][0], Line[i][0][1], 0])
            for n in self.Nodes:
                X = n[0]
                if int(X) == i:
                    NewList.append([n[1], n[2], 1])
                    NewList.append([n[1], n[2], 1])
            NewList.append([Line[i][1][0], Line[i][1][1], 0])
        i = 0
        while i < len(NewList):
            NewLineList.append([NewList[i], NewList[i + 1]])
            i += 2
        i = 0
        while i < (len(NewLineList)):
            # if NewLineList[i][0]=NewLineList[i][1]
            if [NewLineList[i][0][0], NewLineList[i][0][1]] == [NewLineList[i][1][0], NewLineList[i][1][1]]:
                # if NewLineList[i][0][2] == 0:
                NewLineList.pop(i)
                continue
                # print(000)
            i += 1
        i = j = 0
        while i < len(NewLineList):
            while j < (len(NewLineList) - 1):
                if i != j and [NewLineList[i][0], NewLineList[i][1]] == [NewLineList[j][0], NewLineList[j][1]]:
                    NewLineList.pop(j)
                else:
                    j += 1
            i += 1
        self.NewLineList = NewLineList

        # print(len(NewList))

    def Lineclassify(self):
        i = 0
        j = 1
        ii = 0
        # NewLineList = [0]
        self.LineList = self.NewLineList
        NewLineList = self.LineList
        k = len(NewLineList)
        LineSet = self.LineSet
        while NewLineList != []:
            # for i in range(k):
            set = []
            PointsList = []
            PointsList.append(NewLineList[0][0])
            PointsList.append(NewLineList[0][1])
            set.append(NewLineList[0])
            # print(PointsList)
            num = NewLineList[0][0][2] + NewLineList[0][1][2]
            # print(NewLineList)
            linewidth = min(self.Lines[0][0][0], self.Lines[0][1][0]) - self.Lines[0][2][0]
            a = linewidth
            # pp=0
            while j < len(NewLineList):
                # print(i,j)
                if (abs(NewLineList[j][0][0] - PointsList[0][0]) <= a and abs(
                        NewLineList[j][0][1] - PointsList[0][1]) <= a) and NewLineList[j][0][2] == 0:
                    set.append([NewLineList[j][1], PointsList[0]])
                    set.append(NewLineList[j])
                    # print(0)
                    num = num + NewLineList[j][0][2] + NewLineList[j][1][2]
                    # if num > 1: break
                    PointsList[0] = NewLineList[j][1]
                    NewLineList.pop(j)
                    j = 1
                elif (abs(NewLineList[j][1][0] - PointsList[0][0]) <= a and abs(
                        NewLineList[j][1][1] - PointsList[0][1]) <= a) and NewLineList[j][1][2] == 0:
                    set.append(NewLineList[j])
                    # print([NewLineList[j][0],PointsList[0]])
                    num = num + NewLineList[j][0][2] + NewLineList[j][1][2]
                    # if num > 1: break
                    PointsList[0] = NewLineList[j][0]
                    NewLineList.pop(j)
                    j = 1
                # print(0)
                elif (abs(NewLineList[j][0][0] - PointsList[1][0]) <= a and abs(
                        NewLineList[j][0][1] - PointsList[1][1]) <= a) and NewLineList[j][0][2] == 0:
                    set.append(NewLineList[j])
                    # pp+=1
                    # print(pp)
                    num = num + NewLineList[j][0][2] + NewLineList[j][1][2]
                    # if num > 1: break
                    PointsList[1] = NewLineList[j][1]
                    NewLineList.pop(j)
                    j = 1
                elif (abs(NewLineList[j][1][0] - PointsList[1][0]) <= a and abs(
                        NewLineList[j][1][1] - PointsList[1][1]) <= a) and NewLineList[j][1][2] == 0:
                    set.append(NewLineList[j])
                    # print(0)
                    num = num + NewLineList[j][0][2] + NewLineList[j][1][2]
                    # if num > 1: break
                    PointsList[1] = NewLineList[j][0]
                    NewLineList.pop(j)
                    j = 1
                else:
                    j += 1
            j = 1
            # print(LineSet)
            LineSet.append(set)
            self.Points_set.append(PointsList)
            # print(PointsList)
            if NewLineList != []: NewLineList.pop(0)
            # i+=1

        self.LineSet = LineSet
        print(self.Points_set[9])
        print(LineSet[9])
        # print(self.LineSet[90])
#
# def drawFunc():
#     Line=LinesP.Lines
#     k = len(Line)
#     # print((Line[61][1][0], Line[60][1][1]))
#     # k=164
#     # print(Node)
#     glClearColor(0.0, 0.0, 0.0, 0.0)
#     glClear(GL_COLOR_BUFFER_BIT)
#     glColor3f(1.0, 0.0, 0.0)
#     # 设置线宽
#     glLineWidth(1)
#     ii = 0
#     Node = LinesP.Nodes
#     # for x in Node:
#     #     if x[0]==114:print(x)
#     #
#     for i in range(len(LinesP.LineSet)):#len(LinesP.LineSet)
#         glColor3f(0.2 + random.randint(0, 1), 0.1 + random.randint(0, 1), 0.1 + random.randint(0, 1))
#         k=len(LinesP.LineSet[i])
#         for j in range(k):
#             glBegin(GL_LINE_STRIP)
#             glVertex2f(LinesP.LineSet[i][j][0][0], LinesP.LineSet[i][j][0][1])
#             glVertex2f(LinesP.LineSet[i][j][1][0], LinesP.LineSet[i][j][1][1])
#             glEnd()
#
#     # Line = LinesP.Lines
#     # k = len(Line)
#     # for i in range(k):
#     #         glColor3f(0.2 + random.randint(0, 1), 0.1 + random.randint(0, 1), 0.1 + random.randint(0, 1))
#     #         glBegin(GL_LINE_STRIP)
#     #         glVertex2f(Line[i][0][0], Line[i][0][1])
#     #         glVertex2f(Line[i][1][0], Line[i][1][1])
#     #         glEnd()
#     # print(Line[18])#[[6.559286, 0.83118], [6.629921, 0.826772], [6.5553490000000005, 6.633858], [0.822835, 0.835117], 18]
#     # print(Line[116])
#
#
#
#     for i in range(len(Node)):
#         glPointSize(4)
#         glColor3f(0.0, 1.0, 0.0)
#         glBegin(GL_POINTS)
#         glVertex2f(Node[i][1], Node[i][2])
#         glEnd()
#     glFlush()
# # with open(f"C:\\Users\\zhang\\Desktop\\Zou\\916\\Pcbdatas\\PCBGerberFile\\ALL-2W2097821\ALL-2W2097821\\gko", "r") as fp:
#
#
# # with open(f"C:\\Users\\zhang\\Desktop\\Zou\\Textfle\\gbr.set\\jp-2w2446577\\gko", "r") as fp:#jp-2w2448598#jp-2w2448185#jp-2w2447243#jp-2w2446577#jp-2w2445881#jp-2w2445100#jp-1w2446179
# # with open(f"C:\\Users\\zhang\\Desktop\\Zou\\First\\GerberFile\\JP-1S2317689\\JP-1S2317689\\gko", "r") as fp:
# # with open(f"C:\\Users\\zhang\\Desktop\\Zou\\916\\无料号\\JP-2W2284145_2021081820345874756848\\gko", "r") as fp:
# # with open(f"C:\\Users\\zhang\\Desktop\\Zou\\916\\Pcbdatas\\PCBGerberFile\\ALL-2W2185504\ALL-2W2183708\\gko", "r") as fp:
# # with open(f"C:\\Users\\zhang\\Desktop\\Zou\\First\\GerberFile\\ALL-2C2316028\\ALL-2C2316028\\gko", "r") as fp:
# # with open(f"C:\\Users\\zhang\\Desktop\\Zou\\Textfle\\jp-1w2448061\\gko","r") as fp:
# # with open(f"C:\\Users\\zhang\\Desktop\\Zou\\Textfle\\gbr.set\\jp-1w2446179\\gko", "r") as fp:
# # with open(f"C:\\Users\\zhang\\Desktop\\Zou\\Textfle\\gbr.set\\jp-2y2446460\\gko", "r") as fp:
# # with open(f"C:\\Users\\zhang\\Desktop\\Zou\\Textfle\\jp-2w2449830\\gko", "r") as fp:
# # with open(f"C:\\Users\\zhang\\Desktop\\Zou\\Textfle\\jp-2w2449815\\gko", "r") as fp:
# with open(f"C:\\Users\\zhang\\Desktop\\Zou\\Textfle\\jp-2w2448167\\gko", "r") as fp:
# # with open(f"C:\\Users\\zhang\\Desktop\\Zou\\Textfle\\gbr.set\\jp-4y2447167\\gko", "r") as fp:
# # with open(f"C:\\Users\\zhang\\Desktop\\Zou\\Textfle\\gbr.set\\all-2w2445718\\gko", "r") as fp:
# # with open(f"C:\\Users\\zhang\\Desktop\\Zou\\Textfle\\jp-2w2446182\\gko", "r") as fp:#jp-1w2448775#jp-1w2449086#jp-1w2449709
# # with open(f"C:\\Users\\ZH\\Desktop\\work\\jp-1w2446179\\gko", "r") as fp:
# # with open(f"C:\\Users\\ZH\\Desktop\\work\\ALL-2W2310019\\gko", "r") as fp:#ALL-2C2312191,ALL-2C2316028,ALL-2C2316029,ALL-2W2116702,ALL-2W2270924#ALL-2W2310017
#     data = fp.read()
#     gerberLayer_gko = gerber.loads(data, 'gko')
#     afew = 0
#
# LinesP = LinesProcessed(gerberLayer_gko)
# LinesP.Processed()
# # print(LinesP.Lines)
# # print(LinesP.NewLineList)
# Line = LinesP.Lines
# # print(Line)
# Node = LinesP.Nodes
# # print((Node))
# bounding_box = gerberLayer_gko.bounding_box
# width = (bounding_box[0][1] - bounding_box[0][0]) * 80
# high = (bounding_box[1][1] - bounding_box[1][0]) * 80
# glutInit()
# glutInitDisplayMode(GLUT_SINGLE | GLUT_RGBA)
# # glutInitWindowSize(int(width), int(high))
# glutInitWindowSize(900, 800)
# glutCreateWindow(b"First")
# gluOrtho2D(bounding_box[0][0] - 0.1, bounding_box[0][1] + 0.1, bounding_box[1][0] - 0.1, bounding_box[1][1] + 0.1)
# # gluOrtho2D(12.5,13, 6.2,7)# 2.559,2.5592, 0.05,0.06 gluOrtho2D(3.44, 3.46, 2.03,2.08)
# glClearColor(0.0, 0.0, 0.0, 0.0)
# glClear(GL_COLOR_BUFFER_BIT)
# glutDisplayFunc(drawFunc)
# glutMainLoop()
