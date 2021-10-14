import math
import cv2
import numpy as np
import os
import gerber
from gerber.primitives import Circle as gbCircle, Line as gbLine, Rectangle as gbRectangle, Region as gbRegion, Arc as gbArc, Drill as gbDrill, Obround as gbObround, \
    AMGroup as gbAMGroup, Outline as gbOutline
from gerber.am_statements import AMLowerLeftLinePrimitive as gbAMLowerLeftLine, AMCirclePrimitive as gbAMCircle, AMVectorLinePrimitive as gbAMVectorLine


class ImageGenerater:
    def __init__(self, gerbers, ratek=300):
        if 'gko' in gerbers.keys():
            self.ratek = ratek
            self.gerbers = gerbers
            self.gerberLayers = {}
            self.img_layer = {}
            self.__init()

    def __init(self):
        for gerberkey in self.gerbers.keys():
            self.gerberLayers[gerberkey] = gerber.loads(self.gerbers[gerberkey], gerberkey)
            self.gerberLayers[gerberkey].to_inch()
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
        if isinstance(primitive.aperture, gbRectangle):
            dx = primitive.bounding_box_no_aperture[0][1] - primitive.bounding_box_no_aperture[0][0]
            dy = primitive.bounding_box_no_aperture[1][1] - primitive.bounding_box_no_aperture[1][0]
            dx = primitive.aperture.height
            dy = primitive.aperture.width
            ltp1 = self.__p_k_offset_p((primitive.start[0] - primitive.aperture.width / 2, primitive.start[1] - primitive.aperture.height / 2), ratek, offset)  # 左上角
            rbp1 = self.__p_k_offset_p((primitive.start[0] + primitive.aperture.width / 2, primitive.start[1] + primitive.aperture.height / 2), ratek, offset)  # 右下角
            ltp2 = self.__p_k_offset_p((primitive.end[0] - primitive.aperture.width / 2, primitive.end[1] - primitive.aperture.height / 2), ratek, offset)  # 左上角
            rbp2 = self.__p_k_offset_p((primitive.end[0] + primitive.aperture.width / 2, primitive.end[1] + primitive.aperture.height / 2), ratek, offset)  # 右下角
            cv2.rectangle(image, ltp1, rbp1, color, -1)
            cv2.rectangle(image, ltp2, rbp2, color, -1)
            angle = primitive.angle
            r = math.fabs(dx * math.sin(angle) + dy * math.cos(angle)) * ratek
            r = math.ceil(r)  # 半径向上取整
            if r > 0:
                cv2.line(image, start, end, color, r * int(0 == thickness) + thickness)

        if isinstance(primitive.aperture, gbCircle):
            r = primitive.aperture.radius * 2 * ratek  # 获取半径
            r = math.ceil(r)  # 半径向上取整
            if r > 0:
                cv2.line(image, start, end, color, r * int(0 == thickness) + thickness)

    def __DrawAMVectorLine(self, primitive, image, ratek, offset, color):
        start = self.__p_k_offset_p(primitive.start, ratek, offset)  # 获取起点
        end = self.__p_k_offset_p(primitive.end, ratek, offset)  # 获取终点
        r = primitive.width * ratek  # 获取半径
        r = math.ceil(r)  # 半径向上取整
        cv2.line(image, start, end, color, r)

    def __DrawAMLowerLeftLine(self, primitive, image, ratek, offset, color):
        cx = primitive.lower_left[0] + primitive.width / 2
        cy = primitive.lower_left[1] + primitive.height / 2
        rectangle = gbRectangle((cx, cy), primitive.width, primitive.height)
        self.__DrawRectangle(rectangle, image, ratek, offset, color)

    def __DrawAMCircle(self, primitive, image, ratek, offset, color):
        position = self.__p_k_offset_p(primitive.position, ratek, offset)  # 获取圆心
        r = math.ceil(primitive.diameter / 2 * ratek)  # 获取半径
        cv2.circle(image, position, r, color, -1)

    def __DrawRectangle(self, primitive, image, ratek, offset, color):  # 画矩形
        ltp = self.__p_k_offset_p((primitive.bounding_box[0][0], primitive.bounding_box[1][0]), ratek, offset)  # 左上角
        rbp = self.__p_k_offset_p((primitive.bounding_box[0][1], primitive.bounding_box[1][1]), ratek, offset)  # 右下角
        cv2.rectangle(image, ltp, rbp, color, -1)

    def __DrawCircle(self, primitive, image, ratek, offset, color):  # 画圆
        position = self.__p_k_offset_p(primitive.position, ratek, offset)  # 获取圆心
        r = math.ceil(primitive.radius * ratek)  # 获取半径
        cv2.circle(image, position, r, color, -1)

    def __DrawObround(self, primitive, image, ratek, offset, color, linethickness):  # 画椭圆
        self.primitivesTraverse(image, primitive.subshapes, ratek, offset, linethickness)
        # position = self.__p_k_offset_p(primitive.position, ratek, offset)  # 获取圆心
        # width = math.ceil(primitive.width / 2 * ratek)  # 获取长轴
        # height = math.ceil(primitive.height / 2 * ratek)  # 获取短轴
        # cv2.ellipse(image, position, (width, height), 0, 0, 360, color, -1)

    def __DrawDrill(self, primitive, image, ratek, offset, color):  # 画圆
        position = self.__p_k_offset_p(primitive.position, ratek, offset)  # 获取圆心
        r = math.ceil(primitive.radius * 5)  # 获取半径
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

    def __DrawAMGroup(self, primitive, image, ratek, offset, color, linethickness):
        self.primitivesTraverse(image, primitive.stmt.primitives, ratek, (offset[0] - primitive.position[0], offset[1] - primitive.position[1]), linethickness)
        pass

    def __DrawOutLine(self, primitive, image, ratek, offset, color, linethickness):
        # self.primitivesTraverse(image, primitive.primitives, ratek, offset, linethickness)
        bounding_box = primitive.bounding_box
        cx = (bounding_box[0][0] + bounding_box[0][1]) / 2
        cy = (bounding_box[1][0] + bounding_box[1][1]) / 2
        rectangle = gbRectangle((cx, cy), bounding_box[0][1] - bounding_box[0][0], bounding_box[1][1] - bounding_box[1][0])
        self.__DrawRectangle(rectangle, image, ratek, offset, color)

    def __DrawRegion(self, primitive, image, ratek, offset, color):
        points = []
        for primitive2 in primitive.primitives:
            color = 255
            if primitive2.level_polarity == "clear":
                color = 0
            if isinstance(primitive2, gbLine):
                points.append(self.__p_k_offset_p(primitive2.start, ratek, offset))
            elif isinstance(primitive2, gbArc):
                start = ((primitive2.start[0] - offset[0]) * ratek, (primitive2.start[1] - offset[1]) * ratek)
                end = ((primitive2.end[0] - offset[0]) * ratek, (primitive2.end[1] - offset[1]) * ratek)
                center = ((primitive2.center[0] - offset[0]) * ratek, (primitive2.center[1] - offset[1]) * ratek)
                r = primitive2.radius * ratek
                points.extend(self.getpoints(center, r, start, end, primitive2.direction))
        cv2.fillPoly(image, [np.array(points)], color)

    def primitivesTraverse(self, image, primitives, ratek, offset, linethickness):
        if isinstance(primitives, dict):
            primitives = primitives.values()
        for primitive in primitives:
            color = 255
            if hasattr(primitive, 'level_polarity') and primitive.level_polarity == "clear":
                color = 0
            if isinstance(primitive, gbLine):
                self.__DrawLine(primitive, image, ratek, offset, color, linethickness)
            elif isinstance(primitive, gbRectangle):
                self.__DrawRectangle(primitive, image, ratek, offset, color)
            elif isinstance(primitive, gbCircle):
                self.__DrawCircle(primitive, image, ratek, offset, color)
            elif isinstance(primitive, gbDrill):
                self.__DrawDrill(primitive, image, ratek, offset, color)
            elif isinstance(primitive, gbRegion):
                self.__DrawRegion(primitive, image, ratek, offset, color)
            elif isinstance(primitive, gbObround):
                self.__DrawObround(primitive, image, ratek, offset, color, linethickness)
            elif isinstance(primitive, gbAMGroup):
                self.__DrawAMGroup(primitive, image, ratek, offset, color, linethickness)
            elif isinstance(primitive, gbOutline):
                self.__DrawOutLine(primitive, image, ratek, offset, color, linethickness)
            elif isinstance(primitive, gbAMLowerLeftLine):
                self.__DrawAMLowerLeftLine(primitive, image, ratek, offset, color)
            elif isinstance(primitive, gbAMCircle):
                self.__DrawAMCircle(primitive, image, ratek, offset, color)
            elif isinstance(primitive, gbAMVectorLine):
                self.__DrawAMVectorLine(primitive, image, ratek, offset, color)
            else:
                sfe = 0

    def __Draw(self, layerName, linethickness=0):
        gerberLayer = self.gerberLayers[layerName]
        bounds = self.gkobounds
        ratek = self.ratek
        padding = 1
        offset = (self.offset[0] - padding / ratek, self.offset[1] - padding / ratek)
        width, height = math.ceil((bounds[0][1] - bounds[0][0]) * ratek + padding * 2 + 1), math.ceil((bounds[1][1] - bounds[1][0]) * ratek + padding * 2 + 1)
        image = np.zeros((height, width), np.uint8)
        self.primitivesTraverse(image, gerberLayer.primitives, ratek, offset, linethickness)
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
                r = line.radius * 2 * ratek  # 获取半径
                r = math.ceil(r)  # 半径向上取整
                if r > 0:
                    cv2.line(image, start, end, randomColor, r)
                if step:
                    cv2.imshow("test", image)
                    cv2.waitKey(waitKey)
        return image


def dataPrepar(path):
    readlayers = ["gko", "drl", "gbs", "gbo", "gbl", "gts", "gto", "gtl"]
    layers = os.listdir(path)
    gerbers = {}
    for layer in layers:
        if not readlayers.__contains__(layer):
            continue
        with open(f"{path}\\{layer}", "rU") as fp:
            data = fp.read()
            gerbers[layer] = data
    return gerbers


def test1():
    path = "D:\ProjectFile\EngineeringAutomation\GongProcessing\TestDataSet\GerberFile\ALL-1W2308512\jp-2w2282523"
    gerbers = dataPrepar(path)
    gbGenerater = ImageGenerater(gerbers)  # 图片生成器
    imagegko = gbGenerater.getlayerimg2("gko", 1)
    cv2.imshow("test", imagegko)
    cv2.waitKey(-1)
    cv2.imwrite("Debug/gko.png", imagegko)


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
    cv2.namedWindow("test", 0)
    cv2.resizeWindow("test", int(1728 / 100 * 100), int(972 / 100 * 100))
    cv2.moveWindow("test", 0, 0)
    test1()
    print("done!!!!!!!!!!")
