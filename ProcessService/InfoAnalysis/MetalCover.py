import cv2
import numpy as np
from ProcessService.SupportFuncs.ImageGenerater import ImageGenerater


class MetalCover:
    def __init__(self, imageGenerater: ImageGenerater):
        self.imageGenerater = imageGenerater
        self.gerberdic: dict = {}
        for key in self.imageGenerater.gerbers.keys():
            self.gerberdic[key] = self.imageGenerater.getlayerimg(key)
        self.ENIG_rate = self.ENIG_rate_cal()

    def __get_gerber_rate(self):

        gerberLayer = self.imageGenerater.gerberLayers["gko"]
        try:
            scale_rate1 = self.gerberdic['gko'].shape[0] / gerberLayer.size[1]
        except ZeroDivisionError:
            scale_rate1 = 0

        try:
            scale_rate2 = self.gerberdic['gko'].shape[1] / gerberLayer.size[0]
        except ZeroDivisionError:
            scale_rate2 = 0
        scale_rate = (scale_rate1 + scale_rate2 / 2)

        return scale_rate

    def __get_ENIGsurf(self):
        top_surf = None
        bottom_surf = None
        if ('gtl' in self.gerberdic.keys()) & ('gbl' in self.gerberdic.keys()):
            # 一、双面版
            # 1.去掉钻孔层，钻孔层没有表面沉金 gts-drl,gbs-drl
            if ('gts' in self.gerberdic.keys()) & ('drl' in self.gerberdic.keys()):
                top_surf = self.gerberdic['gts'] - self.gerberdic['drl']
                bottom_surf = self.gerberdic['gbs'] - self.gerberdic['drl']
            # 2.计算顶部和顶部线路层交集
            if ('gts' in self.gerberdic.keys()):
                top_surf = cv2.bitwise_and(top_surf, self.gerberdic['gtl'])
            # 3.计算底部和底部线路层交集
            if ('gbs' in self.gerberdic.keys()):
                bottom_surf = cv2.bitwise_and(bottom_surf, self.gerberdic['gbl'])
            return top_surf, bottom_surf
        elif ('gtl' in self.gerberdic.keys()) & ('gbl' not in self.gerberdic.keys()):
            # 二、单面顶板
            if ('gts' in self.gerberdic.keys()) & ('drl' in self.gerberdic.keys()):
                # 1.去掉钻孔层，钻孔层没有表面沉金 gts-drl
                top_surf = self.gerberdic['gts'] - self.gerberdic['drl']
                # 2.计算顶部和顶部线路层交集
                top_surf = cv2.bitwise_and(top_surf, self.gerberdic['gtl'])
            return top_surf, bottom_surf
        elif ('gbl' in self.gerberdic.keys()) & ('gtl' not in self.gerberdic.keys()):
            # 三、单面底板
            if ('gbs' in self.gerberdic.keys()) & ('drl' in self.gerberdic.keys()):
                # 1.去掉钻孔层，钻孔层没有表面沉金 gts-drl
                top_surf = self.gerberdic['gbs'] - self.gerberdic['drl']
                # 2.计算顶部和顶部线路层交集
                top_surf = cv2.bitwise_and(top_surf, self.gerberdic['gbl'])
            return top_surf, bottom_surf
        else:
            # 四、双面无线路
            return top_surf, bottom_surf

    def __areaRate_cal(self, binaryImg):
        Area_sum = binaryImg.shape[0] * binaryImg.shape[1] * 255
        binary = np.ravel(binaryImg, order='C')
        Area = np.sum(binary)
        res = Area / (Area_sum + np.exp(-12))
        return res

    def __grommetAreaRate_cal(self):

        # 金属孔的面积_拿到边缘周长_乘以厚度():
        if "drl" in self.gerberdic.keys():
            drl_edgeimg = cv2.Canny(self.gerberdic['drl'], 50, 100)
            grommetAreaRate = self.__areaRate_cal(drl_edgeimg)
        else:
            grommetAreaRate = 0

        return grommetAreaRate

    def ENIG_rate_cal(self):

        scale_rate = self.__get_gerber_rate()

        # 1.pcb版表面的沉金面积比例计算
        top_surf, bottom_surf = self.__get_ENIGsurf()

        try:
            top_surf_area = self.__areaRate_cal(top_surf)
        except AttributeError:
            top_surf_area = 0

        try:
            bottom_surf_area = self.__areaRate_cal(bottom_surf)
        except AttributeError:
            bottom_surf_area = 0
        surf_area_rate = (top_surf_area + bottom_surf_area) * 100

        # 2.pcb版金属孔沉金比例
        grommetAreaRate = self.__grommetAreaRate_cal() * scale_rate

        # 3.计算总的沉金比率
        ENIG_rate = surf_area_rate + grommetAreaRate
        return np.round(ENIG_rate, 2)


if __name__ == '__main__':
    pass
