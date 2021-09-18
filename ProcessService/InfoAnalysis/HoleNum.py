import math
import gerber
from gerber.primitives import Line as gbLine
from ProcessService.SupportFuncs.ImageGenerater import ImageGenerater


class HoleNum:
    def __init__(self, imageGenerater: ImageGenerater):
        self.imageGenerater = imageGenerater
        if "drl" in imageGenerater.gerbers.keys():
            if "drl"not in imageGenerater.gerberLayers.keys():
                imageGenerater.gerberLayers["drl"]= gerber.loads(imageGenerater.gerbers["drl"], "drl")
            self.drlLayer = imageGenerater.gerberLayers["drl"]
            self.calcHoleNum()
            self.width, self.height = imageGenerater.width, imageGenerater.height
            k = 1 / self.imageGenerater.ratek * 25.4 / 1000
            self.holeNum = self.circleNum + self.spLineNum  # 孔数量
            self.holeDensity = self.holeNum / (self.width * self.height * k * k)  # 孔密度
        else:
            self.holeNum = 0  # 孔数量
            self.holeDensity = 0  # 孔密度

    def calcHoleNum(self):
        self.circleNum = 0
        self.lineNum = 0
        self.spLineNum = 0
        for primitive in self.drlLayer.primitives:
            if type(self.imageGenerater.sampleLine) == type(primitive):
                self.lineNum += 1
                self.spLineNum += self.SplitLineToCircles(primitive)
            if type(self.imageGenerater.sampleCircle) == type(primitive):
                self.circleNum += 1

    def SplitLineToCircles(self, gbLine: gbLine):
        start, end, r = gbLine.start, gbLine.end, gbLine.aperture.radius
        lineLen = pow((pow(start[0] - end[0], 2) + pow(start[1] - end[1], 2)), 0.5)
        hole_L = math.sqrt(math.pow(r, 2) - math.pow(r - 0.0172, 2)) * 2
        return math.ceil(math.fabs(math.floor(-lineLen / hole_L)) + 1)


if __name__ == "__main__":
    GerberSingleFilePath = f"D:\ProjectFile\EngineeringAutomation\HoleDensity\ok"
    gerberLayerdrl = gerber.read(f"{GerberSingleFilePath}\drl")
    gerberLayergko = gerber.read(f"{GerberSingleFilePath}\gko")
    gerberLayerdrl.to_metric()
    gerberLayergko.to_metric()
    holes = HoleNum(gerberLayerdrl)
    holeNum = holes.holeNum  # 孔数量
    holeDensity = holeNum / (holes.width * holes.height)  # 孔密度
