import copy
import math
from collections import Counter
import os
import cv2
import numpy as np
from sklearn.cluster import DBSCAN
from ProcessService.SupportFuncs.ImageGenerater import ImageGenerater
from skimage import morphology
from scipy import spatial


def SaveImage(path, image):
    # if not __name__ == '__main__':
    cv2.imwrite(path, image)


def ShowImage(image):
    if __name__ == '__main__':
        cv2.imshow("test", image)
        cv2.waitKey(-1)


class GKOImageProcess:
    def __init__(self, imageGenerater: ImageGenerater):
        self.imageGenerater = imageGenerater
        self.__init()

    def __init(self):
        self.__img_gko = self.imageGenerater.getlayerimg2("gko", 1)
        self.__img_drl = self.imageGenerater.getlayerimg("drl")
        self.__img_gtl = self.imageGenerater.getlayerimg("gtl")
        self.__img_gbl = self.imageGenerater.getlayerimg("gbl")
        l_img = None
        if self.__img_gbl is not None:
            l_img = self.__img_gbl
        if self.__img_gtl is not None:
            if l_img is not None:
                l_img = cv2.bitwise_or(self.__img_gtl, self.__img_gbl)
            else:
                l_img = self.__img_gtl
        if l_img is None:
            self.solid_len = 0  # 锣带长度
            self.solid_area = 0  # 板面积
            self.rate = 0
        else:
            outer_len, outer_full_image, outer_image = self.calc_outer_contour(self.__img_gko)
            rows, cols = self.calc_v_cut(self.__img_gko, outer_full_image)
            inner_region_img, self.nolineBorderstat = self.find_border_index(self.__img_gko, self.__img_drl, l_img, rows, cols)
            inner_len, self.line_dict = self.calc_endPoints(inner_region_img, outer_image, self.__img_gko)

    def calc_outer_contour(self, gko_img):
        ret, bin_img = cv2.threshold(gko_img, 250, 255, type=cv2.THRESH_BINARY_INV)

        outer_image = 255 - bin_img
        contours, hierarchy = cv2.findContours(outer_image, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)

        max_len = 0
        max_index = 0
        for i in range(len(contours)):
            if len(contours[i]) > max_len:
                max_len = len(contours[i])
                max_index = i
        outer_image[:, :] = 0
        cv2.drawContours(outer_image, contours, max_index, color=255, thickness=-1)
        outer_image = cv2.erode(outer_image, cv2.getStructuringElement(cv2.MORPH_RECT, ksize=(7, 7)))
        outer_image = cv2.dilate(outer_image, cv2.getStructuringElement(cv2.MORPH_RECT, ksize=(7, 7)))
        contours, hierarchy = cv2.findContours(outer_image, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
        outer_image[:, :] = 0
        cv2.drawContours(outer_image, contours, 0, color=255, thickness=1)
        SaveImage(r"Debug/outer_image.png", outer_image)  # 外轮廓图片
        expanded_outer_image = cv2.copyMakeBorder(outer_image, 1, 1, 1, 1, cv2.BORDER_CONSTANT, 0)
        cv2.floodFill(expanded_outer_image, None, (0, 0), 255)
        outer_full_image = cv2.bitwise_not(expanded_outer_image)
        outer_full_image = outer_full_image[1:-1, 1:-1]
        outer_full_image = cv2.dilate(outer_full_image, cv2.getStructuringElement(cv2.MORPH_RECT, ksize=(3, 3)))
        SaveImage(r"Debug/outer_full_image.png", outer_full_image)  # 外轮廓填充图片
        return max_len, np.uint8(outer_full_image / 255), np.uint8(outer_image / 255)

    def calc_v_cut(self, gko_img, outer_full_image):
        _, gko_bin_img = cv2.threshold(gko_img, 250, 1, cv2.THRESH_BINARY)
        rows = []
        for rowindex in range(gko_bin_img.shape[0]):
            gko_sum = gko_bin_img[rowindex, :].sum()
            outer_full_sum = outer_full_image[rowindex, :].sum()
            if gko_sum >= outer_full_sum and gko_sum != 0:
                rows.append(rowindex)
        cols = []
        for colindex in range(gko_bin_img.shape[1]):
            gko_sum = gko_bin_img[:, colindex].sum()
            outer_full_sum = outer_full_image[:, colindex].sum()
            if gko_sum >= outer_full_sum and gko_sum != 0:
                cols.append(colindex)
        return rows, cols

    def find_border_index(self, gko_img, drl_img, gtl_img, rows, cols):
        SaveImage(r"Debug/gko_img.png", gko_img)
        ret, gko_bin_img = cv2.threshold(gko_img, 250, 1, type=cv2.THRESH_BINARY_INV)
        height, width = gko_img.shape
        gko_area = height * width
        region_num, labels, stats, centroids = cv2.connectedComponentsWithStats(gko_bin_img, connectivity=4)
        labels = np.uint8(labels)
        SaveImage(r"Debug/labels.png", labels)
        # outer region
        dilate_img = cv2.dilate(labels, kernel=cv2.getStructuringElement(cv2.MORPH_RECT, ksize=(9, 9)))
        left_side = dilate_img[0, :]
        right_side = dilate_img[-1, :]
        up_side = dilate_img[:, 0]
        bottom_side = dilate_img[:, -1]
        left_conter = Counter(left_side)
        right_conter = Counter(right_side)
        up_conter = Counter(up_side)
        bottom_conter = Counter(bottom_side)
        full_list = list(left_conter.keys()) + list(right_conter.keys()) + list(up_conter.keys()) + list(bottom_conter.keys())
        outer_region_index = set(full_list)

        # board region
        ret, d_bin_img = cv2.threshold(drl_img, 250, 1, type=cv2.THRESH_BINARY)
        invert_d_bin_img = 1 - d_bin_img

        ret, l_bin_img = cv2.threshold(gtl_img, 250, 1, type=cv2.THRESH_BINARY)
        intersection_kl = labels * l_bin_img * invert_d_bin_img

        hist_l = cv2.calcHist([intersection_kl], [0], None, [region_num], [0, region_num])
        linerRegionIndex = list(np.where(hist_l > 0)[0])
        linerRegionIndex.remove(0)
        nolinerBorderRegionIndex = []
        rows, cols = np.array(rows), np.array(cols)
        for statindex in range(len(stats)):
            stat = stats[statindex]
            if math.fabs(stat[4] - stat[2] * stat[3]) < 10:  # 判断是矩形
                sx, sy, ex, ey = stat[0], stat[1], stat[0] + stat[2], stat[1] + stat[3]
                dsx = abs(cols - sx).min()
                dsy = abs(rows - sy).min()
                dex = abs(cols - ex).min()
                dey = abs(rows - ey).min()
                if dsx + dsy + dex + dey < 5:
                    nolinerBorderRegionIndex.append(statindex)
        nolinerBorderRegionIndex.extend(full_list)
        nolinerBorderRegionIndex = list(set(nolinerBorderRegionIndex))  # 废料边的index
        linerRegionIndex.extend(nolinerBorderRegionIndex)
        linerRegionIndex = list(set(linerRegionIndex))
        inner_none_board_region = list(set(list(range(1, region_num))).difference(set(linerRegionIndex)))
        height, width = labels.shape
        inner_region_img = np.zeros(shape=(height, width), dtype=np.uint8)
        for i in range(len(inner_none_board_region)):
            index = inner_none_board_region[i]
            mask = cv2.inRange(labels, int(index), int(index))
            inner_region_img = cv2.bitwise_or(mask, inner_region_img)
        SaveImage(r"Debug/inner_region_img.png", inner_region_img)
        return inner_region_img, stats[nolinerBorderRegionIndex]

    def calc_endPoints(self, inner_region_img, outer_image, gko_img):
        ret, gko_bin_img = cv2.threshold(gko_img, 250, 1, type=cv2.THRESH_BINARY_INV)
        SaveImage(r"Debug\gko_bin_img.png", gko_bin_img * 255)
        inner_process_img = cv2.dilate(inner_region_img, cv2.getStructuringElement(cv2.MORPH_RECT, ksize=(5, 5)))  # 膨胀腐蚀去掉v割缝
        inner_process_img = cv2.erode(inner_process_img, cv2.getStructuringElement(cv2.MORPH_RECT, ksize=(5, 5)))  # 膨胀腐蚀去掉v割缝
        inner_process_img = np.uint8(inner_process_img)
        inner_process_img = cv2.dilate(inner_process_img, cv2.getStructuringElement(cv2.MORPH_RECT, ksize=(7, 7)))
        SaveImage(r"Debug\inner_process_img.png", inner_process_img)
        contours, hierarchy = cv2.findContours(inner_process_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        self.contours = contours
        inner_draw_img = np.zeros(shape=inner_region_img.shape)
        for i in range(len(contours)):
            cv2.drawContours(inner_draw_img, contours, i, color=(1), thickness=1)
        inner_len = sum(sum(inner_draw_img))

        # ###########################segment line################################################
        gko_bin_img = 1 - gko_bin_img
        sketech_img = morphology.skeletonize(gko_bin_img)
        sketech_img = np.uint8(sketech_img)
        kernel_element = np.array((
            [1, 1, 1],
            [1, 0, 1],
            [1, 1, 1]), dtype="float32")
        neighbor_img = cv2.filter2D(sketech_img, -1, kernel_element)
        neighbor_img = sketech_img * neighbor_img

        ret, cross_region_points_img = cv2.threshold(neighbor_img, 2, 1, cv2.THRESH_BINARY)
        inner_draw_img = np.uint8(inner_draw_img)
        inner_draw_img = cv2.bitwise_or(inner_draw_img, outer_image)
        cross_region_points_dilate = cv2.dilate(cross_region_points_img, cv2.getStructuringElement(shape=cv2.MORPH_RECT, ksize=(5, 5)))
        intersection_lp = inner_draw_img * cross_region_points_dilate
        seg_line_img = inner_draw_img - intersection_lp
        SaveImage(r"Debug/seg_line_img.png", seg_line_img * 255)

        # get line end points
        line_num, line_label_img = cv2.connectedComponents(seg_line_img)
        neighbor_line_img = cv2.filter2D(seg_line_img, -1, kernel=kernel_element)
        ret, end_points_region = cv2.threshold(neighbor_line_img, 1, 0, type=cv2.THRESH_TOZERO_INV)
        end_points_img = end_points_region * line_label_img
        SaveImage(r"Debug/end_points_img.png", end_points_img * 255)

        line_dict = {}
        height, width = end_points_img.shape
        for i in range(height):
            for j in range(width):
                if end_points_img[i][j] > 0:
                    # print(i, j, end_points_img[i][j])
                    line_dict[end_points_img[i][j]] = []

        for i in range(height):
            for j in range(width):
                if end_points_img[i][j] > 0:
                    line_dict[end_points_img[i][j]].append([j, i])

        return inner_len, line_dict


def dataPreparation():
    path = "D:\ProjectFile\EngineeringAutomation\GongProcessing\TestDataSet\GerberFile\ALL-1W2308512\JP-1W2310736"
    layers = os.listdir(path)
    gerbers = {}
    for layer in layers:
        with open(f"{path}\\{layer}", "rU") as fp:
            data = fp.read()
            gerbers[layer.lower()] = data
    return gerbers


if __name__ == '__main__':
    gerbers = dataPreparation()
    imageGenerater = ImageGenerater(gerbers)
    gkoLength = GKOImageProcess(imageGenerater)
