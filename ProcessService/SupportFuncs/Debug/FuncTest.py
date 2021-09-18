import cv2
import numpy as np
import math


class FuncTest:
    def point_in_box(self, point, box):
        return point[0] >= box[0][0] and point[0] < box[0][1] and point[1] >= box[1][0] and point[1] < box[1][1]

    def getpoints(self, center, r, start, end, direction, image):
        # ************数据准备*********************
        resultp = []
        start_r, end_r = (int(round(start[0], 0)), int(round(start[1], 0))), (int(round(end[0], 0)), int(round(end[1], 0)))
        resultp.append(start_r)
        if start_r == end_r:  # 如果起点=终点直接返回
            return resultp  # 如果起点=终点直接返回
        np = 1 if direction == "clockwise" else -1
        # **************计算四个区域******************
        rsin45 = r * 0.707106781
        box_l = ((center[0] - r, center[0] - rsin45), (center[1] - rsin45, center[1] + rsin45))
        box_r = ((center[0] + rsin45, center[0] + r), (center[1] - rsin45, center[1] + rsin45))
        box_t = ((center[0] - rsin45, center[0] + rsin45), (center[1] - r, center[1] - rsin45))
        box_b = ((center[0] - rsin45, center[0] + rsin45), (center[1] + rsin45, center[1] + r))
        box_lrtb = (box_l, box_r, box_t, box_b)
        cv2.circle(image, (int(round(center[0], 0)), int(round(center[1], 0))), int(r), 255, 1)
        cv2.rectangle(image, (int(round(box_l[0][0], 0)), int(round(box_l[1][0], 0))), (int(round(box_l[0][1], 0)), int(round(box_l[1][1], 0))), 255, 1)
        cv2.rectangle(image, (int(round(box_r[0][0], 0)), int(round(box_r[1][0], 0))), (int(round(box_r[0][1], 0)), int(round(box_r[1][1], 0))), 255, 1)
        cv2.rectangle(image, (int(round(box_t[0][0], 0)), int(round(box_t[1][0], 0))), (int(round(box_t[0][1], 0)), int(round(box_t[1][1], 0))), 255, 1)
        cv2.rectangle(image, (int(round(box_b[0][0], 0)), int(round(box_b[1][0], 0))), (int(round(box_b[0][1], 0)), int(round(box_b[1][1], 0))), 255, 1)
        # ********************循环添加*******************************
        nextPoint, nextPoint_r = start, start_r
        while (nextPoint_r[0] - end_r[0]) ** 2 + (nextPoint_r[1] - end_r[1]) ** 2 > 1:
            newx, newy = nextPoint[0], nextPoint[1]
            if self.point_in_box(nextPoint, box_lrtb[0]):
                newy = nextPoint[1] - np
                newx = center[0] - math.pow((math.pow(r, 2) - math.pow(newy - center[1], 2)), 0.5)
            elif self.point_in_box(nextPoint, box_lrtb[1]):
                newy = nextPoint[1] + np
                newx = center[0] + math.pow((math.pow(r, 2) - math.pow(newy - center[1], 2)), 0.5)
            elif self.point_in_box(nextPoint, box_lrtb[2]):
                newx = nextPoint[0] + np
                newy = center[1] - math.pow((math.pow(r, 2) - math.pow(newx - center[0], 2)), 0.5)
            elif self.point_in_box(nextPoint, box_lrtb[3]):
                newx = nextPoint[0] - np
                newy = center[1] + math.pow((math.pow(r, 2) - math.pow(newx - center[0], 2)), 0.5)
            else:
                return resultp
            nextPoint = (newx, newy)
            nextPoint_r = (int(round(nextPoint[0], 0)), int(round(nextPoint[1], 0)))
            resultp.append(nextPoint_r)
            cv2.circle(image, nextPoint_r, 1, 255, 1)
            cv2.imshow("test", image)
            cv2.waitKey(1)
        return resultp


if __name__ == '__main__':
    ftest = FuncTest()
    image = np.zeros((2000, 2000), np.uint8)
    center = (1413.92, 559.2564)
    r = 0.7936000000000831
    start = (1413.1263999999999, 559.2564)
    end = (1413.7400000000002, 560.0292)
    direction = "clockwise1"
    points = ftest.getpoints(center, r, start, end, direction, image)
    points = np.array(points)
    cv2.fillPoly(image, [points], 255)
    cv2.imshow("test", image)
    cv2.waitKey(-1)
