import os
from ProcessService.SupportFuncs.ImageGenerater import ImageGenerater
from ProcessService.InfoAnalysis.HoleNum import HoleNum
from ProcessService.InfoAnalysis.MetalCover import MetalCover
from ProcessService.RoutLineProcess.RoutLineProcess import RoutLineProcess


class ProcessService:
    def __init__(self, gerbers):
        self.gerbers = gerbers
        self.__init()

    def __init(self):
        self.imgGrtr = ImageGenerater(self.gerbers)
        self.holes = HoleNum(self.imgGrtr)
        self.metalCover = MetalCover(self.imgGrtr)
        self.routLineProcess = RoutLineProcess(self.imgGrtr)

    def GetInfoAnalysisResult(self):
        imgGrtr = self.imgGrtr
        gkoLength = self.routLineProcess.gkoImageProcess
        holes = self.holes
        resultstr = f"width:{imgGrtr.width * 25.4};height:{imgGrtr.height * 25.4};area:{imgGrtr.area_in_m};holeNum:{holes.holeNum}"
        resultstr = f"{resultstr};solid_len:{gkoLength.solid_len};solid_area:{gkoLength.solid_area};solid_rate:{gkoLength.rate}"
        resultstr = f"{resultstr};metalCover_rate:{self.metalCover.ENIG_rate}"
        return resultstr

    def RoutLine(self):
        return self.routLineProcess.ToGerberFile()


# def dataPrepar():
#     path = "D:\ProjectFile\EngineeringAutomation\GongProcessing\TestDataSet\GerberFile\ALL-1W2308512\ALL-1W2308512"
#     layers = os.listdir(path)
#     gerbers = {}
#     for layer in layers:
#         with open(f"{path}\\{layer}", "rU") as fp:
#             data = fp.read()
#             gerbers[layer] = data
#     return gerbers
#
#
# if __name__ == '__main__':
#     gerbers = dataPrepar()
#     imageGenerater = ImageGenerater(gerbers)
#     gkoLength = GKOLength(imageGenerater)
