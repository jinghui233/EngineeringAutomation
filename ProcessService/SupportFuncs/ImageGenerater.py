import math
import cv2
import numpy as np
import os
import gerber
from gerber.primitives import Circle as gbCircle, Line as gbLine, Rectangle as gbRectangle, Region as gbRegion, Arc as gbArc, Drill as gbDrill


class ImageGenerater:
    def __init__(self, gerbers, ratek=300):
        if 'gko' in gerbers.keys():
            self.ratek = ratek
            self.gerbers = gerbers
            self.gerberLayers = {}
            self.img_layer = {}
            self.__init()

    def __init(self):
        self.sampleLine, self.sampleCircle, self.sampleRect = gbLine((1, 1), (1, 1), 0), gbCircle((1, 1), 1), gbRectangle((1, 1), 1, 1)
        self.sampleArc, self.sampleDrill = gbArc((1, 1), (1, 1), (1, 1), (1, 1), None, None), gbDrill((1, 1), 1)
        self.sampleRegion = gbRegion(None)
        self.gerberLayers["gko"] = gerber.loads(self.gerbers["gko"], "gko")
        self.gkobounds = self.gerberLayers["gko"].bounds
        self.offset = (self.gkobounds[0][0], self.gkobounds[1][0])
        self.width, self.height = self.gkobounds[0][1] - self.gkobounds[0][0], self.gkobounds[1][1] - self.gkobounds[1][0]
        self.k_in_m = 1 / self.ratek * 25.4 / 1000
        self.area_in_m = (self.width * (25.4 / 1000)) * (self.height * (25.4 / 1000))

    def __p_k_offset_p(self, point, ratek, offset):  # 对点坐标应用k值及偏移坐标
        point = (point[0] - offset[0], point[1] - offset[1])  # 偏移
        point = (point[0] * ratek, point[1] * ratek)  # 乘k值
        point = (math.ceil(point[0]), math.ceil(point[1]))  # 向上取整
        return point

    def getlayerimg(self, layername):  # 获取指定层的图片 layername= gko、drl、gts。。。。。。
        if layername not in self.img_layer.keys():
            if layername not in self.gerberLayers.keys():
                if layername not in self.gerbers.keys():
                    return None
                else:
                    self.gerberLayers[layername] = gerber.loads(self.gerbers[layername], layername)
                    if layername == "drl":
                        self.gerberLayers[layername].to_inch()
                    self.img_layer[layername] = self.__Draw(layername)
            else:
                self.img_layer[layername] = self.__Draw(layername)
        return self.img_layer[layername]

    def getlayerimg2(self, layername, gkolinethickness):
        if layername not in self.gerberLayers.keys():
            if layername not in self.gerbers.keys():
                return None
            else:
                self.gerberLayers[layername] = gerber.loads(self.gerbers[layername], layername)
                if layername == "drl":
                    self.gerberLayers[layername].to_inch()
                self.img_layer[layername] = self.__Draw(layername, gkolinethickness)
        else:
            self.img_layer[layername] = self.__Draw(layername, gkolinethickness)
        return self.img_layer[layername]

    def __DrawLine(self, primitive, image, ratek, offset, color, thickness=0):  # 画线
        start = self.__p_k_offset_p(primitive.start, ratek, offset)  # 获取起点
        end = self.__p_k_offset_p(primitive.end, ratek, offset)  # 获取终点
        if type(primitive.aperture) == type(self.sampleRect):
            dx = primitive.bounding_box_no_aperture[0][1] - primitive.bounding_box_no_aperture[0][0]
            dy = primitive.bounding_box_no_aperture[1][1] - primitive.bounding_box_no_aperture[1][0]
            ltp1 = self.__p_k_offset_p((primitive.start[0] - primitive.aperture.width / 2, primitive.start[1] - primitive.aperture.height / 2), ratek, offset)  # 左上角
            rbp1 = self.__p_k_offset_p((primitive.start[0] + primitive.aperture.width / 2, primitive.start[1] + primitive.aperture.height / 2), ratek, offset)  # 右下角
            ltp2 = self.__p_k_offset_p((primitive.end[0] - primitive.aperture.width / 2, primitive.end[1] - primitive.aperture.height / 2), ratek, offset)  # 左上角
            rbp2 = self.__p_k_offset_p((primitive.end[0] + primitive.aperture.width / 2, primitive.end[1] + primitive.aperture.height / 2), ratek, offset)  # 右下角
            cv2.rectangle(image, ltp1, rbp1, color, -1)
            cv2.rectangle(image, ltp2, rbp2, color, -1)
            angle = primitive.angle
            r = dx * math.sin(angle) + dy * math.cos(angle)
            r = math.ceil(r)  # 半径向上取整
            if r > 0:
                cv2.line(image, start, end, color, r * int(0 == thickness) + thickness)

        if type(primitive.aperture) == type(self.sampleCircle):
            r = primitive.aperture.radius * 2 * ratek  # 获取半径
            r = math.ceil(r)  # 半径向上取整
            if r > 0:
                cv2.line(image, start, end, color, r)

    def __DrawRectangle(self, primitive, image, ratek, offset, color):  # 画矩形
        ltp = self.__p_k_offset_p((primitive.bounding_box[0][0], primitive.bounding_box[1][0]), ratek, offset)  # 左上角
        rbp = self.__p_k_offset_p((primitive.bounding_box[0][1], primitive.bounding_box[1][1]), ratek, offset)  # 右下角
        cv2.rectangle(image, ltp, rbp, color, -1)

    def __DrawCircle(self, primitive, image, ratek, offset, color):  # 画圆
        position = self.__p_k_offset_p(primitive.position, ratek, offset)  # 获取圆心
        r = primitive.radius * ratek  # 获取半径
        r = math.ceil(r)  # 半径向上取整
        cv2.circle(image, position, r, color, -1)

    def __DrawDrill(self, primitive, image, ratek, offset, color):  # 画圆
        position = self.__p_k_offset_p(primitive.position, ratek, offset)  # 获取圆心
        r = primitive.radius * 5  # 获取半径
        r = math.ceil(r)  # 半径向上取整
        # r=3
        cv2.circle(image, position, r, color, -1)

    def point_in_box(self, point, box):
        return point[0] >= box[0][0] and point[0] < box[0][1] and point[1] >= box[1][0] and point[1] < box[1][1]

    def getpoints(self, center, r, start, end, direction):
        # ************数据准备*********************
        resultp = []
        start_r, end_r = (int(round(start[0], 0)), int(round(start[1], 0))), (int(round(end[0], 0)), int(round(end[1], 0)))
        resultp.append(start_r)
        if (start_r[0] - end_r[0]) ** 2 + (start_r[1] - end_r[1]) ** 2 < 2:  # 如果起点=终点直接返回
            return resultp  # 如果起点=终点直接返回
        np = -1 if direction == "clockwise" else 1
        # **************计算四个区域******************
        rsin45 = r * 0.707106781
        box_l = ((center[0] - r, center[0] - rsin45), (center[1] - rsin45, center[1] + rsin45))
        box_r = ((center[0] + rsin45, center[0] + r), (center[1] - rsin45, center[1] + rsin45))
        box_t = ((center[0] - rsin45, center[0] + rsin45), (center[1] - r, center[1] - rsin45))
        box_b = ((center[0] - rsin45, center[0] + rsin45), (center[1] + rsin45, center[1] + r))
        box_lrtb = (box_l, box_r, box_t, box_b)
        # ********************循环添加*******************************
        nextPoint, nextPoint_r = start, start_r
        while (nextPoint_r[0] - end_r[0]) ** 2 + (nextPoint_r[1] - end_r[1]) ** 2 > 1:
            newx, newy = nextPoint[0], nextPoint[1]
            if self.point_in_box(nextPoint, box_lrtb[0]):
                newy = nextPoint[1] - np
                if math.pow(newy - center[1], 2) > math.pow(r, 2):
                    return resultp
                newx = center[0] - math.pow((math.pow(r, 2) - math.pow(newy - center[1], 2)), 0.5)
            elif self.point_in_box(nextPoint, box_lrtb[1]):
                newy = nextPoint[1] + np
                if math.pow(newy - center[1], 2) > math.pow(r, 2):
                    return resultp
                newx = center[0] + math.pow((math.pow(r, 2) - math.pow(newy - center[1], 2)), 0.5)
            elif self.point_in_box(nextPoint, box_lrtb[2]):
                newx = nextPoint[0] + np
                if math.pow(newx - center[0], 2) > math.pow(r, 2):
                    return resultp
                newy = center[1] - math.pow((math.pow(r, 2) - math.pow(newx - center[0], 2)), 0.5)
            elif self.point_in_box(nextPoint, box_lrtb[3]):
                newx = nextPoint[0] - np
                if math.pow(newx - center[0], 2) > math.pow(r, 2):
                    return resultp
                newy = center[1] + math.pow((math.pow(r, 2) - math.pow(newx - center[0], 2)), 0.5)
            else:
                return resultp
            nextPoint = (newx, newy)
            nextPoint_r = (int(round(nextPoint[0], 0)), int(round(nextPoint[1], 0)))
            resultp.append(nextPoint_r)
        return resultp

    def __DrawRegion(self, primitive, image, ratek, offset, color):
        points = []
        for primitive2 in primitive.primitives:
            color = 255
            if primitive2.level_polarity == "clear":
                color = 0
            if type(primitive2) == type(self.sampleLine):
                points.append(self.__p_k_offset_p(primitive2.start, ratek, offset))
            elif type(primitive2) == type(self.sampleArc):
                start = ((primitive2.start[0] - offset[0]) * ratek, (primitive2.start[1] - offset[1]) * ratek)
                end = ((primitive2.end[0] - offset[0]) * ratek, (primitive2.end[1] - offset[1]) * ratek)
                center = ((primitive2.center[0] - offset[0]) * ratek, (primitive2.center[1] - offset[1]) * ratek)
                r = primitive2.radius * ratek
                points.extend(self.getpoints(center, r, start, end, primitive2.direction))
        cv2.fillPoly(image, [np.array(points)], color)

    def __Draw(self, layerName, linethickness=0):
        gerberLayer = self.gerberLayers[layerName]
        bounds = self.gkobounds
        ratek = self.ratek
        padding = 1
        offset = (self.offset[0] - padding / ratek, self.offset[1] - padding / ratek)
        width, height = math.ceil((bounds[0][1] - bounds[0][0]) * ratek + padding * 2), math.ceil((bounds[1][1] - bounds[1][0]) * ratek + padding * 2)
        image = np.zeros((height, width), np.uint8)
        for primitive in gerberLayer.primitives:
            color = 255
            if primitive.level_polarity == "clear":
                color = 0
            if type(primitive) == type(self.sampleLine):
                self.__DrawLine(primitive, image, ratek, offset, color, linethickness)
            elif type(primitive) == type(self.sampleRect):
                self.__DrawRectangle(primitive, image, ratek, offset, color)
            elif type(primitive) == type(self.sampleCircle):
                self.__DrawCircle(primitive, image, ratek, offset, color)
            elif type(primitive) == type(self.sampleDrill):
                self.__DrawDrill(primitive, image, ratek, offset, color)
            elif type(primitive) == type(self.sampleRegion):
                self.__DrawRegion(primitive, image, ratek, offset, color)
            else:
                sfe = 0
        return image

    def DrawShow(self, sets, step=True, waitKey=1):
        cv2.namedWindow("test", 0)
        cv2.resizeWindow("test", int(1728 / 100 * 100), int(972 / 100 * 100))
        cv2.moveWindow("test", 0, 0)
        bounds = self.gkobounds
        ratek = self.ratek
        offset = self.offset
        width, height = math.ceil((bounds[0][1] - bounds[0][0]) * ratek + 2), math.ceil((bounds[1][1] - bounds[1][0]) * ratek + 2)
        image = np.zeros((height, width, 3), np.uint8)
        for set in sets:
            randomColor = (np.random.randint(0, 255), np.random.randint(0, 255), np.random.randint(0, 255))
            for line in set.GetLineSet():
                start = self.__p_k_offset_p(line.start, ratek, offset)  # 获取起点
                end = self.__p_k_offset_p(line.end, ratek, offset)  # 获取终点
                if type(line.aperture) == type(self.sampleCircle):
                    r = line.aperture.radius * 2 * ratek  # 获取半径
                    r = math.ceil(r)  # 半径向上取整
                    if r > 0:
                        cv2.line(image, start, end, randomColor, r)
                if step:
                    cv2.imshow("test", image)
                    cv2.waitKey(waitKey)
        return image


def dataPreparation():
    path = 'D:\\ProjectFile\\EngineeringAutomation\\GongProcessing\\TestDataSet\\新建文件夹\\all-2w2283651\\CAM'
    layers = os.listdir(path)
    gerbers = {}
    for layer in layers:
        with open(f"{path}\\{layer}", "rU") as fp:
            data = fp.read()
            gerbers[layer] = data
    return gerbers


def test1():
    gerbers = dataPreparation()  # 准备数据
    gbGenerater = ImageGenerater(gerbers)  # 图片生成器
    imagegko = gbGenerater.getlayerimg("gko")
    cv2.imwrite("Debug/gko.jpg", imagegko)



def test2():
    path = "D:\ProjectFile\EngineeringAutomation\GongProcessing\TestDataSet\GerberFile"
    groupDirs = os.listdir(path)
    for groupDir in groupDirs:
        orderDirs = os.listdir(f"{path}\\{groupDir}")
        for orderDir in orderDirs:
            gblayerfiles = os.listdir(f"{path}\\{groupDir}\\{orderDir}")
            gerbers = {}
            for gblayerfile in gblayerfiles:
                with open(f"{path}\\{groupDir}\\{orderDir}\\{gblayerfile}", "rU") as fp:
                    data = fp.read()
                    gerbers[gblayerfile] = data
            gbGenerater = ImageGenerater(gerbers)  # 图片生成器
            for gblayerfile in gblayerfiles:
                image = gbGenerater.getlayerimg(gblayerfile)
                cv2.imwrite(f"test\\{groupDir}_{orderDir}_{gblayerfile}.jpg", image)


if __name__ == "__main__":
    test1()
    print("done!!!!!!!!!!")