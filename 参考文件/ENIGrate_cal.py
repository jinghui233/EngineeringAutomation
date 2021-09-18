import cv2
import numpy as np
import os
import gerber

def get_gerber_rate(folderpath,gerberdic: dict):

    gerberLayer = gerber.read(os.path.join(folderpath,'drl'))

    try:
        scale_rate1 = gerberdic['drl'].shape[0] / gerberLayer.size[1]
    except ZeroDivisionError:
        scale_rate1 = 0

    try:
        scale_rate2 = gerberdic['drl'].shape[0] / gerberLayer.size[1]
    except ZeroDivisionError:
        scale_rate2 = 0
    scale_rate= (scale_rate1 + scale_rate2 / 2)

    return scale_rate

def get_c_file(rootDir):
    list_dirs = os.walk(rootDir)
    c_files = []
    d_files = []
    for root, dirs, files in list_dirs:
        for d in dirs:
            d_files.append(str(os.path.join(root, d)))
        for f in files:
            if f.endswith('.png'):
                c_files.append(str(os.path.join(root, f)))
    return d_files, c_files


def AreaRate_cal(binary):
    Area_sum = binary.shape[0] * binary.shape[1] * 255
    binary = np.ravel(binary, order='C')
    Area = np.sum(binary)
    res = Area / (Area_sum + np.exp(-12))
    return res


def imgToBinary(img):
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    binary = cv2.threshold(img, 250, 255, 0)
    # cv2.imshow("binary",binary[1])
    # cv2.waitKey()
    # binary = cv2.threshold(img, 250, 1, 0)
    return binary


def prepareimg(strpath):
    d_files, c_files = get_c_file(strpath)
    gerberdic = dict()
    for i in c_files:
        img = cv2.imread(i)
        filename = [x for x in i.split('\\') if x][-1]
        gerberdic[filename[-7:-4]] = np.zeros_like(img)
    for i in c_files:
        img = cv2.imread(i)
        binary_img = imgToBinary(img)
        if ('gbs' in gerberdic.keys()) & (i.endswith("gbs.png")):
            gerberdic['gbs'] = binary_img[1]
        if ('gts' in gerberdic.keys()) & (i.endswith("gts.png")):
            gerberdic['gts'] = binary_img[1]
        if ('gko' in gerberdic.keys()) & (i.endswith("gko.png")):
            gerberdic['gko'] = binary_img[1]
        if ('gbl' in gerberdic.keys()) & (i.endswith("gbl.png")):
            gerberdic['gbl'] = binary_img[1]
        if ('gtl' in gerberdic.keys()) & (i.endswith("gtl.png")):
            gerberdic['gtl'] = binary_img[1]
        if ('drl' in gerberdic.keys()) & (i.endswith("drl.png")):
            gerberdic['drl'] = binary_img[1]
    return gerberdic


def get_ENIGsurf(gerberdic: dict):
    top_surf = None
    bottom_surf = None

    if ('gtl' in gerberdic.keys()) & ('gbl' in gerberdic.keys()):
        # 一、双面版
        print("双面板")
        # 1.去掉钻孔层，钻孔层没有表面沉金 gts-drl,gbs-drl
        if ('gts' in gerberdic.keys()) & ('drl' in gerberdic.keys()):
            top_surf = gerberdic['gts'] - gerberdic['drl']
            bottom_surf = gerberdic['gbs'] - gerberdic['drl']
        # 2.计算顶部和顶部线路层交集
        if ('gts' in gerberdic.keys()):
            top_surf = cv2.bitwise_and(top_surf, gerberdic['gtl'])
        # 3.计算底部和底部线路层交集
        if ('gbs' in gerberdic.keys()):
            bottom_surf = cv2.bitwise_and(bottom_surf, gerberdic['gbl'])
        return top_surf, bottom_surf
    elif ('gtl' in gerberdic.keys()) & ('gbl' not in gerberdic.keys()):
        # 二、单面顶板
        if ('gts' in gerberdic.keys()) & ('drl' in gerberdic.keys()):
            print("单面顶板")
            # 1.去掉钻孔层，钻孔层没有表面沉金 gts-drl
            top_surf = gerberdic['gts'] - gerberdic['drl']
            # 2.计算顶部和顶部线路层交集
            top_surf = cv2.bitwise_and(top_surf, gerberdic['gtl'])
        return top_surf, bottom_surf
    elif ('gbl' in gerberdic.keys()) & ('gtl' not in gerberdic.keys()):
        # 三、单面底板
        if ('gbs' in gerberdic.keys()) & ('drl' in gerberdic.keys()):
            print("单面底板")
            # 1.去掉钻孔层，钻孔层没有表面沉金 gts-drl
            top_surf = gerberdic['gbs'] - gerberdic['drl']
            # 2.计算顶部和顶部线路层交集
            top_surf = cv2.bitwise_and(top_surf, gerberdic['gbl'])
        return top_surf, bottom_surf
    else:
        # 四、双面无线路
        print("双面无线路")
        return top_surf, bottom_surf


def edge(img):
    canny = cv2.Canny(img, 50, 100)
    return canny


def grommetAreaRate_cal(gerberdic: dict):

    # 金属孔的面积_拿到边缘周长_乘以厚度():
    drl_edgeimg = edge(gerberdic['drl'])
    grommetAreaRate=AreaRate_cal(drl_edgeimg)

    return grommetAreaRate


def ENIG_rate_cal(folderpath):
    # 0.拿到pcb板的各层
    gerberdic = prepareimg(folderpath)


    scale_rate=get_gerber_rate(folderpath,gerberdic)

    # 1.pcb版表面的沉金面积比例计算
    top_surf, bottom_surf = get_ENIGsurf(gerberdic)

    # try:
    #     cv2.imshow("show_top",top_surf)
    #     cv2.waitKey()
    # except:
    #     print("top为空")
    #
    # try:
    #     cv2.imshow("bottom_surf",bottom_surf)
    #     cv2.waitKey()
    # except:
    #     print("bottom为空")

    try:
        top_surf_area = AreaRate_cal(top_surf)
    except AttributeError:
        top_surf_area = 0

    try:
        bottom_surf_area = AreaRate_cal(bottom_surf)
    except AttributeError:
        bottom_surf_area = 0
    surf_area_rate = (top_surf_area + bottom_surf_area) * 100

    # 2.pcb版金属孔沉金比例

    grommetAreaRate = grommetAreaRate_cal(gerberdic) * scale_rate

    # 3.计算总的沉金比率

    ENIG_rate = surf_area_rate + grommetAreaRate

    # print(folderpath,ENIG_rate)
    return np.round(ENIG_rate,2)


def Testdef(imagePath):
    imagePath = imagePath
    groupDirs = os.listdir(imagePath)
    for groupDir in groupDirs:
        orderDirs = os.listdir(f"{imagePath}/{groupDir}")
        for orderDir in orderDirs:
            GERBER_FOLDER = f"{imagePath}/{groupDir}/{orderDir}"
            if not os.path.isdir(GERBER_FOLDER):
                continue
            ENIG_rate_cal(GERBER_FOLDER)

if __name__ == '__main__':

    Testdef(r'C:/Users/qqq/Desktop/PCBImageFile')

