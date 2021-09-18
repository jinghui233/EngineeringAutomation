#! /usr/bin/env python
# -*- coding: utf-8 -*-
import numpy as np
import os
from gerber import read
from gerber.render import GerberCairoContext
import cv2
from matplotlib import pyplot as plt
from collections import Counter
from sklearn.cluster import DBSCAN
from collections import Counter
import copy
from skimage import data,color,morphology

np.set_printoptions(precision=4,suppress=True)

def calculate_outer_length():
    gko_img = cv2.imread('gko.png', 0)
    ret, bin_img = cv2.threshold(gko_img, 250, 255, type=cv2.THRESH_BINARY_INV)
    height, width = gko_img.shape
    # cv2.imwrite('temp.jpg',bin_img*255)

    cv2.imwrite('bin.jpg',bin_img)


    expand_bin_img = cv2.copyMakeBorder(bin_img,3,3,3,3,cv2.BORDER_CONSTANT,0)
    new_img = 255 - bin_img
    contours, hierarchy = cv2.findContours(new_img, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    expand_height,expand_width = expand_bin_img.shape

    max_len = 0
    mx_index = 0
    for i in range(len(contours)):
        if len(contours[i])>max_len:
            max_len = len(contours[i])
            max_index = i
    # draw_img = np.zeros(shape=(expand_height,expand_width,3),dtype=np.uint8)
    # cv2.drawContours(draw_img,contours,max_index,color=(1,1,1),thickness=1)
    # cv2.imwrite('draw.jpg',draw_img)
    print('outer length:',max_len)
    return max_len

def calculate_inner_length():
    gko_img = cv2.imread('layer_image/gko.png',0)
    ret,bin_img = cv2.threshold(gko_img,250,1,type=cv2.THRESH_BINARY_INV)
    height,width = gko_img.shape
    gko_area = height * width
    # cv2.imwrite('temp.jpg',bin_7img*255)

    # region_num,labels = cv2.connectedComponents(bin_img)
    region_num,labels,stats,centroids = cv2.connectedComponentsWithStats(bin_img,connectivity=4)
    cv2.imwrite('labels.jpg',labels)
    # plt.imshow(labels)
    # plt.show()
    draw_label = copy.deepcopy(gko_img)
    for i in range(1,region_num):
        cv2.putText(draw_label,str(i),org=(int(centroids[i][0]),int(centroids[i][1])),fontFace=2,fontScale=3,color=(255),thickness=2)
        # cv2.circle(draw_label,center=(int(centroids[i][0]),int(centroids[i][1])),radius=4,color=(255),thickness=2)
    cv2.imwrite('draw_label.jpg',draw_label)
    print('region num:',region_num)
    labels = np.uint8(labels)
    hist,bin_edges = np.histogram(labels,bins=region_num)
    # print(hist)

    #outer region
    dilate_img = cv2.dilate(labels,kernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,ksize=(5,5),anchor=(-1,-1)))
    left_side = dilate_img[0,:]
    right_side = dilate_img[-1,:]
    up_side = dilate_img[:,0]
    bottom_side = dilate_img[:,-1]
    left_conter = Counter(left_side)
    right_conter = Counter(right_side)
    up_conter = Counter(up_side)
    bottom_conter = Counter(bottom_side)
    full_list = list(left_conter.keys()) + list(right_conter.keys()) + list(up_conter.keys()) + list(bottom_conter.keys())
    outer_region_index = set(full_list)
    print('outer region:',outer_region_index)

    #board region
    d_img = cv2.imread('layer_image/drl.png',0)
    resize_d_img = cv2.resize(d_img,dsize=(width,height))
    ret, d_bin_img = cv2.threshold(resize_d_img, 250, 1, type=cv2.THRESH_BINARY)
    invert_d_bin_img = 1 - d_bin_img

    l_img = cv2.imread('layer_image/gtl.png',0)
    resize_l = cv2.resize(l_img,dsize=(width,height))
    ret,l_bin_img = cv2.threshold(resize_l,250,1,type=cv2.THRESH_BINARY)
    intersection_kl = labels * l_bin_img * invert_d_bin_img
    hist_l, bin_edges = np.histogram(intersection_kl, bins=region_num)
    print(hist_l)
    region_area = hist_l[1:-1]
    # print(region_area)
    cluster_data = region_area.reshape(-1,1)
    cluster_result = DBSCAN(eps=300,min_samples=1).fit(cluster_data)
    # print(cluster_result.labels_)
    sum_region_area = [0] * (max(cluster_result.labels_)+1)
    for i in range(1,len(region_area)):
        # print(cluster_result.labels_[i])
        sum_region_area[cluster_result.labels_[i]] += region_area[i]
    # print(sum_region_area)
    board_region_label = sum_region_area.index(max(sum_region_area))
    board_region_index = []
    for i in range(len(cluster_result.labels_)):
        if cluster_result.labels_[i] == board_region_label:
            board_region_index.append(i+1)
    print('board region:',board_region_index)

    # l_rate = hist_l/hist
    # print(l_rate)
    # l_contours,hierarchy = cv2.findContours(l_bin_img,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    # l_contours_img = np.zeros(shape=(height,width))
    # for i in range(len(l_contours)):
    #     cv2.drawContours(l_contours_i\

    # s_img = cv2.imread('layer_image/gts.png', 0)
    # resize_s = cv2.resize(s_img, dsize=(width, height))
    # ret, s_bin_img = cv2.threshold(resize_s, 250, 1, type=cv2.THRESH_BINARY)
    # intersection_ks = labels * s_bin_img
    # hist_s, bin_edges = np.histogram(intersection_ks, bins=num)
    # # print(hist_s)
    # s_rate = hist_s/hist
    # # print(s_rate)
    # s_contours, hierarchy = cv2.findContours(s_bin_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # s_contours_img = np.zeros(shape=(height, width))
    # for i in range(len(s_contours)):
    #     cv2.drawContours(s_contours_img, s_contours, i, color=(1), thickness=1)
    # intersection_kls = labels * s_contours_img
    # contours_hist_s, bin_edges = np.histogram(intersection_kls, bins=num)
    # s_contours_rate = contours_hist_s/hist
    # # print("contours:", contours_hist_s)
    # print(l_rate)
    # print(l_contours_rate)

    # none board region
    none_board_region = set(list(range(1,region_num))).difference(set(board_region_index))
    print('none board region:',none_board_region)
    inner_none_board_region = list(set(none_board_region).difference(set(outer_region_index)))
    print('inner non board region:',inner_none_board_region)

    #inner none board region length
    height,width = labels.shape
    inner_region_img = np.zeros(shape=(height,width))
    # for i in range(height):
    #     for j in range(width):
    #         for target in inner_none_board_region:
    #             if labels[i][j] == target:
    #                 inner_region_img[i][j] = 255
    # stats = list(stats)
    for i in range(len(inner_none_board_region)):
        index = inner_none_board_region[i]
        # print(index)
        x,y,w,h,area = stats[index]
        # inner_region_img[y:(y+h),x:(x+w)] = 1
        for row in range(y,y+h):
            for col in range(x,x+w):
                if labels[row][col] == index:
                    inner_region_img[row][col] = 1
    # inner_region_img = inner_region_img * labels
    ret,inner_region_img = cv2.threshold(inner_region_img,0,255,type=cv2.THRESH_BINARY)
    cv2.imwrite('inner_region.jpg',inner_region_img)

    kernel_element = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,ksize=(5,5),anchor=(-1,-1))
    inner_process_img = cv2.dilate(inner_region_img,kernel=kernel_element)
    inner_process_img = cv2.erode(inner_process_img,kernel=kernel_element)
    cv2.imwrite('inner_process_img.jpg',inner_process_img)
    # tmp_img = 255 - inner_process_img
    # ret,inner_process_img = cv2.threshold(inner_process_img,128,255,type=cv2.THRESH_BINARY)
    inner_process_img = np.uint8(inner_process_img)
    contours, hierarchy = cv2.findContours(inner_process_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # inner_draw_img = copy.deepcopy(labels)
    inner_draw_img = np.zeros(shape=labels.shape)
    for i in range(len(contours)):
        cv2.drawContours(inner_draw_img,contours,i,color=(255),thickness=1)
    cv2.imwrite('inner_draw_img.jpg',inner_draw_img)
    inner_len = sum(sum(inner_draw_img))/255
    print('inner length:',inner_len)
    return inner_len,gko_area

def get_len():
    outer_len = calculate_outer_length()
    inner_len, area = calculate_inner_length()
    sum_len = outer_len + inner_len
    k = 1 / 300 * 25.4 / 1000
    solid_len = sum_len * k
    solid_area = area * k * k
    print(solid_len, solid_area, solid_len / solid_area)

def generate_luodai():
    img = cv2.imread('inner_draw_img.jpg',0)
    ret,bin_img = cv2.threshold(img,100,1,type=cv2.THRESH_BINARY)
    sketech_img = morphology.skeletonize(bin_img)
    # img = img/255
    kernel_element = np.array((
        [1, 1, 1],
        [1, 0, 1],
        [1,1,1]), dtype="float32")

    neighbor_img = cv2.filter2D(sketech_img,-1,kernel_element)
    plt.imshow(neighbor_img)
    plt.show()

if __name__ == '__main__':
    # calculate_inner_length()
    # calculate_outer_length()
    generate_luodai()
