import cv2, math
from ProcessService.SupportFuncs.AnalyticGeometry import AnalyticGeometry as AGFuncs
import numpy as np
from gerber.primitives import Line as gbLine

cv2.namedWindow("test", 0)
cv2.resizeWindow("test", 1728, 972)
cv2.moveWindow("test", 0, 0)


def getp(x, y):
    return (round(x), round(y))


def PointToLineTest():
    image = np.zeros((1000, 1000, 3), np.uint8)
    lsx, lsy, lex, ley = 200, 500, 800, 500
    px, py = 500, 500
    r = 200
    for i in range(500):
        px = r * math.cos(math.radians(i)) + 200
        py = r * math.sin(math.radians(i)) + 500
        cv2.line(image, getp(lsx, lsy), getp(lex, ley), (255, 0, 0), 3)
        cv2.circle(image, getp(px, py), 10, (255, 0, 0), 2)
        line = gbLine((lsx, lsy), (lex, ley), 0)
        distance, crossPoint, crossDistance, lineLength = AGFuncs.PointToLine(line, (px, py))
        print(crossDistance)
        cv2.line(image, getp(px, py), getp(crossPoint[0], crossPoint[1]), (0, 255, 0), 3)
        cv2.imshow("test", image)
        cv2.waitKey(50)
        image[:, :, :] = 0


def CrossPointTest():
    image = np.zeros((1000, 1000, 3), np.uint8)
    lsx, lsy, lex, ley = 200, 500, 800, 500
    fpx, fpy = 500, 800
    r = 200
    for i in range(250,500):
        px = r * math.cos(math.radians(i)) + 200
        py = r * math.sin(math.radians(i)) + 500
        line1 = gbLine((lsx, lsy), (lex, ley), 0)
        line2 = gbLine((fpx, fpy), (px, py), 0)
        cv2.line(image, getp(lsx, lsy), getp(lex, ley), (255, 0, 0), 3)
        cv2.line(image, getp(fpx, fpy), getp(px, py), (255, 0, 0), 2)
        crossPoint = AGFuncs.get_line_cross_point(line1, line2)
        if crossPoint !=None:
            cv2.circle(image, getp(crossPoint[0], crossPoint[1]), 8, (0, 255, 0), 2)
        cv2.imshow("test", image)
        cv2.waitKey(100)
        image[:, :, :] = 0


CrossPointTest()
