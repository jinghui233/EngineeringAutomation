import copy
import math
import time
from collections import Counter
import os
import cv2
import numpy as np
from sklearn.cluster import DBSCAN
from ProcessService.SupportFuncs.ImageGenerater import ImageGenerater
from skimage import morphology
from scipy import spatial


def SaveImage(path, image):
    cv2.imwrite(path, image)


def ShowImage(image):
    if __name__ == '__main__':
        cv2.imshow("test", image)
        cv2.waitKey(-1)


class GKOLength:
    def __init__(self, imageGenerater: ImageGenerater):
        self.imageGenerater = imageGenerater
        self.__init()

    def __init(self):
        self.__img_gko = self.imageGenerater.getlayerimg2("gko", 1)
        img_drl = self.imageGenerater.getlayerimg("drl")
        img_gtl = self.imageGenerater.getlayerimg("gtl")
        img_gbl = self.imageGenerater.getlayerimg("gbl")
        l_img = np.zeros(shape=self.__img_gko.shape, dtype=np.uint8)
        if img_gtl is not None:
            l_img = cv2.bitwise_or(l_img, img_gtl)
        if img_gbl is not None:
            l_img = cv2.bitwise_or(l_img, img_gbl)
        outer_len = self.calculate_outer_length(self.__img_gko)
        inner_len, self.line_dict = self.calculate_inner_length(self.__img_gko, l_img)
        sum_len = outer_len + inner_len
        k = self.imageGenerater.k_in_m
        self.solid_len = sum_len * k  # 锣带长度
        self.solid_area = self.imageGenerater.width * self.imageGenerater.height * k * k  # 板面积
        self.rate = self.solid_len / self.solid_area

    def calculate_outer_length(self, gko_img):
        ret, bin_img = cv2.threshold(gko_img, 250, 255, type=cv2.THRESH_BINARY_INV)
        height, width = gko_img.shape

        expand_bin_img = cv2.copyMakeBorder(bin_img, 3, 3, 3, 3, cv2.BORDER_CONSTANT, 0)
        new_img = 255 - bin_img
        contours, hierarchy = cv2.findContours(new_img, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
        expand_height, expand_width = expand_bin_img.shape

        max_len = 0
        max_index = 0
        for i in range(len(contours)):
            if len(contours[i]) > max_len:
                max_len = len(contours[i])
                max_index = i
        new_img[:, :] = 0
        cv2.drawContours(new_img, contours, max_index, color=255, thickness=-1)
        new_img = cv2.erode(new_img, cv2.getStructuringElement(cv2.MORPH_RECT, ksize=(7, 7)))
        new_img = cv2.dilate(new_img, cv2.getStructuringElement(cv2.MORPH_RECT, ksize=(7, 7)))
        contours, hierarchy = cv2.findContours(new_img, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
        new_img[:, :] = 0
        cv2.drawContours(new_img, contours, 0, color=255, thickness=1)
        self.new_img = np.uint8(new_img / 255)
        SaveImage(r"Debug\new_img.png", new_img)
        return max_len

    def calculate_inner_length(self, gko_img, l_img):
        SaveImage(r"Debug\gko_img.png", gko_img)
        ret, gko_bin_img = cv2.threshold(gko_img, 250, 1, type=cv2.THRESH_BINARY_INV)
        region_num, labels, stats, centroids = cv2.connectedComponentsWithStats(gko_bin_img, connectivity=4)
        labels = np.uint8(labels)

        # outer region
        dilate_img = cv2.dilate(labels, kernel=cv2.getStructuringElement(cv2.MORPH_RECT, ksize=(9, 9)))
        SaveImage(r"Debug\dilate_img.png", dilate_img)

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
        ret, l_bin_img = cv2.threshold(l_img, 250, 1, type=cv2.THRESH_BINARY)
        intersection_kl = labels * l_bin_img
        SaveImage(r"Debug\intersection_kl.png", intersection_kl)
        hist_l = cv2.calcHist([intersection_kl], [0], None, [region_num], [0, region_num])
        board_region_index = np.nonzero(hist_l)[0]
        # none board region
        none_board_region = set(list(range(1, region_num))).difference(set(board_region_index))
        inner_none_board_region = list(set(none_board_region).difference(set(outer_region_index)))
        # inner none board region length
        height, width = labels.shape
        inner_region_img = np.zeros(shape=(height, width), dtype=np.uint8)
        for i in range(len(inner_none_board_region)):
            index = inner_none_board_region[i]
            mask = cv2.inRange(labels, index, index)
            inner_region_img = cv2.bitwise_or(mask, inner_region_img)
        SaveImage(r"Debug\inner_region_img.png", inner_region_img)
        ret, inner_region_img = cv2.threshold(inner_region_img, 0, 255, type=cv2.THRESH_BINARY)

        inner_process_img = cv2.dilate(inner_region_img, cv2.getStructuringElement(cv2.MORPH_RECT, ksize=(5, 5)))
        inner_process_img = cv2.erode(inner_process_img, cv2.getStructuringElement(cv2.MORPH_RECT, ksize=(5, 5)))
        inner_process_img = cv2.dilate(inner_process_img, cv2.getStructuringElement(cv2.MORPH_RECT, ksize=(7, 7)))
        SaveImage(r"Debug\inner_process_img.png", inner_process_img)
        contours, hierarchy = cv2.findContours(inner_process_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        self.contours = contours
        inner_draw_img = np.zeros(shape=labels.shape)
        for i in range(len(contours)):
            cv2.drawContours(inner_draw_img, contours, i, color=(1), thickness=1)
        inner_len = sum(sum(inner_draw_img))

        # ###########################segment line################################################
        gko_bin_img = 1 - gko_bin_img
        sketech_img = morphology.skeletonize(gko_bin_img)
        SaveImage(r"Debug\sketech_img.png", sketech_img * 255)
        sketech_img = np.uint8(sketech_img)
        kernel_element = np.array((
            [1, 1, 1],
            [1, 0, 1],
            [1, 1, 1]), dtype="float32")
        neighbor_img = cv2.filter2D(sketech_img, -1, kernel_element)
        SaveImage(r"Debug\neighbor_img.png", neighbor_img * 255)
        neighbor_img = sketech_img * neighbor_img
        # SaveImage(r"Debug\neighbor_img.png", neighbor_img * 255)
        ret, cross_region_points_img = cv2.threshold(neighbor_img, 2, 1, cv2.THRESH_BINARY)
        SaveImage(r"Debug\cross_region_points_img.png", cross_region_points_img * 255)
        inner_draw_img = np.uint8(inner_draw_img)
        inner_draw_img = cv2.bitwise_or(inner_draw_img, self.new_img)
        SaveImage(r"Debug\inner_draw_img.png", inner_draw_img * 255)
        cross_region_points_dilate = cv2.dilate(cross_region_points_img, cv2.getStructuringElement(shape=cv2.MORPH_RECT, ksize=(7, 7)))
        SaveImage(r"Debug\cross_region_points_dilate.png", cross_region_points_dilate * 255)
        intersection_lp = inner_draw_img * cross_region_points_dilate
        SaveImage(r"Debug\intersection_lp.png", intersection_lp * 255)
        seg_line_img = inner_draw_img - intersection_lp
        SaveImage(r"Debug\seg_line_img.png", seg_line_img * 255)

        # get line end points
        line_num, line_label_img = cv2.connectedComponents(seg_line_img)
        SaveImage(r"Debug\line_label_img.png", line_label_img)
        neighbor_line_img = cv2.filter2D(seg_line_img, -1, kernel=kernel_element)
        SaveImage(r"Debug\neighbor_line_img.png", neighbor_line_img * 64)
        ret, end_points_region = cv2.threshold(neighbor_line_img, 1, 0, type=cv2.THRESH_TOZERO_INV)
        SaveImage(r"Debug\end_points_region.png", end_points_region * 255)
        cross_region_points_dilate = cv2.dilate(cross_region_points_dilate, cv2.getStructuringElement(shape=cv2.MORPH_RECT, ksize=(3, 3)))
        end_points_img = cross_region_points_dilate * line_label_img
        SaveImage(r"Debug\end_points_img.png", end_points_img * 255)

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
        for key in line_dict.keys():
            pointPair = line_dict[key]
            if pointPair.__len__() > 2:
                firstp = pointPair[0]
                lastp = None
                maxlen = 0
                for p in pointPair:
                    curlen = math.fabs(firstp[0] - p[0]) + math.fabs(firstp[1] - p[1])
                    if curlen > maxlen:
                        maxlen = curlen
                        lastp = p
                line_dict[key] = []
                line_dict[key].append(firstp)
                line_dict[key].append(lastp)
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
    t = time.time()
    gkoLength = GKOLength(imageGenerater)
    print(f'coast:{time.time() - t:.4f}s')
