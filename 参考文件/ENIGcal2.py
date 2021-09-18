import cv2
import numpy as np
import os
import gerber
from DFM_.ImageGenerater import Generater


class EnigRate:
    def __init__(self, folderpath):
        self.folderpath = folderpath
        self.gerberdic: dict = {}

    def __get_gerber_rate(self):

        gerberLayer = gerber.read(os.path.join(self.folderpath, 'drl'))

        try:
            scale_rate1 = self.gerberdic['drl'].shape[0] / gerberLayer.size[1]
        except ZeroDivisionError:
            scale_rate1 = 0

        try:
            scale_rate2 = self.gerberdic['drl'].shape[1] / gerberLayer.size[0]
        except ZeroDivisionError:
            scale_rate2 = 0
        scale_rate = (scale_rate1 + scale_rate2 / 2)

        return scale_rate

    def __dataPreparation(self):
        '''
        :return: 文件夹下的每一个Gerber子文件：比如drl、gts...
        '''
        layers = os.listdir(self.folderpath)
        gerbers = {}
        for layer in layers:
            with open(f"{self.folderpath}\\{layer}", "rU") as fp:
                data = fp.read()
                gerbers[layer] = data
        return gerbers

    def __gerberImage(self):
        # 准备数据
        gerbers = self.__dataPreparation()
        # 生成图片
        gbGenerater = Generater(gerbers)
        imagegko = gbGenerater.getlayerimg("gko")
        self.gerberdic['gko'] = imagegko[1]
        imagegbs = gbGenerater.getlayerimg("gbs")
        self.gerberdic['gbs'] = imagegbs[1]
        imagegts = gbGenerater.getlayerimg("gts")
        self.gerberdic['gts'] = imagegts[1]
        imagegbl = gbGenerater.getlayerimg("gbl")
        self.gerberdic['gbl'] = imagegbl[1]
        imagegtl = gbGenerater.getlayerimg("gtl")
        self.gerberdic['gtl'] = imagegtl[1]
        imagedrl = gbGenerater.getlayerimg("drl")
        self.gerberdic['drl'] = imagedrl[1]

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
        drl_edgeimg = cv2.Canny(self.gerberdic['drl'], 50, 100)
        grommetAreaRate = self.__areaRate_cal(drl_edgeimg)

        return grommetAreaRate

    def ENIG_rate_cal(self):
        self.__dataPreparation()
        self.__gerberImage()

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
    EnigRateobj = EnigRate(r'C:\Users\qqq\Desktop\TestDataSet\GerberFile\ALL-1W2308512\ALL-1W2308512')
    ENIG_rate = EnigRateobj.ENIG_rate_cal()
