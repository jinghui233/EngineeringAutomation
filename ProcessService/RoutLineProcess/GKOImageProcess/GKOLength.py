import copy
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


class GKOLength:
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
            outer_len = self.calculate_outer_length(self.__img_gko)
            inner_len, area, self.line_dict = self.calculate_inner_length(self.__img_gko, self.__img_drl, l_img)
            sum_len = outer_len + inner_len
            k = self.imageGenerater.k_in_m
            self.solid_len = sum_len * k  # 锣带长度
            self.solid_area = area * k * k  # 板面积
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
        SaveImage(r"../Debug/new_img.png", new_img)
        return max_len

    def calculate_inner_length(self, gko_img, drl_img, gtl_img):
        SaveImage(r"../Debug/gko_img.png", gko_img)
        ret, gko_bin_img = cv2.threshold(gko_img, 250, 1, type=cv2.THRESH_BINARY_INV)
        height, width = gko_img.shape
        gko_area = height * width
        region_num, labels, stats, centroids = cv2.connectedComponentsWithStats(gko_bin_img, connectivity=4)
        draw_label = copy.deepcopy(gko_img)
        for i in range(1, region_num):
            cv2.putText(draw_label, str(i), org=(int(centroids[i][0]), int(centroids[i][1])), fontFace=2, fontScale=3, color=(255), thickness=2)
        labels = np.uint8(labels)

        # outer region
        dilate_img = cv2.dilate(labels, kernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE, ksize=(9, 9), anchor=(-1, -1)))
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
        resize_d_img = cv2.resize(drl_img, dsize=(width, height))
        ret, d_bin_img = cv2.threshold(resize_d_img, 250, 1, type=cv2.THRESH_BINARY)
        invert_d_bin_img = 1 - d_bin_img

        resize_l = cv2.resize(gtl_img, dsize=(width, height))
        ret, l_bin_img = cv2.threshold(resize_l, 250, 1, type=cv2.THRESH_BINARY)
        intersection_kl = labels * l_bin_img * invert_d_bin_img

        hist_l = cv2.calcHist([intersection_kl], [0], None, [region_num], [0, region_num])
        region_area = hist_l[1:]
        cluster_data = region_area.reshape(-1, 1)
        cluster_result = DBSCAN(eps=300, min_samples=1).fit(cluster_data)
        sum_region_area = [0] * (max(cluster_result.labels_) + 1)
        for i in range(1, len(region_area)):
            sum_region_area[cluster_result.labels_[i]] += region_area[i]
        board_region_label = sum_region_area.index(max(sum_region_area))
        board_region_index = []
        for i in range(len(cluster_result.labels_)):
            if cluster_result.labels_[i] == board_region_label:
                board_region_index.append(i + 1)

        # none board region
        none_board_region = set(list(range(1, region_num))).difference(set(board_region_index))
        inner_none_board_region = list(set(none_board_region).difference(set(outer_region_index)))

        # inner none board region length
        height, width = labels.shape
        inner_region_img = np.zeros(shape=(height, width))
        # for i in range(len(inner_none_board_region)):
        #     index = inner_none_board_region[i]
        #     x, y, w, h, area = stats[index]
        #     for row in range(y, y + h):
        #         for col in range(x, x + w):
        #             if labels[row][col] == index:
        #                 inner_region_img[row][col] = 1
        inner_region_img = np.uint8(inner_region_img)
        for i in range(len(inner_none_board_region)):
            index = inner_none_board_region[i]
            mask = cv2.inRange(labels, index, index)
            inner_region_img = cv2.bitwise_or(mask, inner_region_img)
        SaveImage(r"../Debug/inner_region_img.png", inner_region_img)
        ret, inner_region_img = cv2.threshold(inner_region_img, 0, 255, type=cv2.THRESH_BINARY)
        inner_process_img = cv2.dilate(inner_region_img, cv2.getStructuringElement(cv2.MORPH_RECT, ksize=(5, 5)))  # 膨胀腐蚀去掉v割缝
        inner_process_img = cv2.erode(inner_process_img, cv2.getStructuringElement(cv2.MORPH_RECT, ksize=(5, 5)))  # 膨胀腐蚀去掉v割缝
        inner_process_img = np.uint8(inner_process_img)
        inner_process_img = cv2.dilate(inner_process_img, cv2.getStructuringElement(cv2.MORPH_RECT, ksize=(7, 7)))
        SaveImage(r"../Debug/inner_process_img.png", inner_process_img)
        contours, hierarchy = cv2.findContours(inner_process_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        self.contours = contours
        inner_draw_img = np.zeros(shape=labels.shape)
        for i in range(len(contours)):
            cv2.drawContours(inner_draw_img, contours, i, color=(1), thickness=1)
        inner_len = sum(sum(inner_draw_img))

        # ###########################segment line################################################
        SaveImage(r"../Debug/gko_bin_img.png", gko_bin_img * 255)
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
        inner_draw_img = cv2.bitwise_or(inner_draw_img, self.new_img)
        cross_region_points_dilate = cv2.dilate(cross_region_points_img, cv2.getStructuringElement(shape=cv2.MORPH_RECT, ksize=(5, 5)))
        intersection_lp = inner_draw_img * cross_region_points_dilate
        seg_line_img = inner_draw_img - intersection_lp
        SaveImage(r"../Debug/seg_line_img.png", seg_line_img * 255)

        # get line end points
        line_num, line_label_img = cv2.connectedComponents(seg_line_img)
        neighbor_line_img = cv2.filter2D(seg_line_img, -1, kernel=kernel_element)
        ret, end_points_region = cv2.threshold(neighbor_line_img, 1, 0, type=cv2.THRESH_TOZERO_INV)
        end_points_img = end_points_region * line_label_img
        SaveImage(r"../Debug/end_points_img.png", end_points_img * 255)

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

        return inner_len, gko_area, line_dict


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
    gkoLength = GKOLength(imageGenerater)
