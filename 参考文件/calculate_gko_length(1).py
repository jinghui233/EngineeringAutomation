#! /usr/bin/env python
# -*- coding: utf-8 -*-
import numpy as np
import os
# from gerber import read
# from gerber.render import GerberCairoContext
import cv2
from matplotlib import pyplot as plt
from collections import Counter
from sklearn.cluster import DBSCAN
from collections import Counter
import copy
from skimage import data,color,morphology
from DFM_.ImageGenerater import ImageGenerater

np.set_printoptions(precision=4,suppress=True)

def calculate_outer_length(gko_img):
    ret, bin_img = cv2.threshold(gko_img, 250, 255, type=cv2.THRESH_BINARY_INV)
    height, width = gko_img.shape

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

def calculate_inner_length(gko_img,drl_img,gtl_img):
    ret,gko_bin_img = cv2.threshold(gko_img,250,1,type=cv2.THRESH_BINARY_INV)
    height,width = gko_img.shape
    gko_area = height * width
    region_num,labels,stats,centroids = cv2.connectedComponentsWithStats(gko_bin_img,connectivity=4)
    cv2.imwrite('labels.jpg',labels)
    draw_label = copy.deepcopy(gko_img)
    for i in range(1,region_num):
        cv2.putText(draw_label,str(i),org=(int(centroids[i][0]),int(centroids[i][1])),fontFace=2,fontScale=3,color=(255),thickness=2)
    cv2.imwrite('draw_label.jpg',draw_label)
    print('region num:',region_num)
    labels = np.uint8(labels)
    hist,bin_edges = np.histogram(labels,bins=region_num)

    #outer region
    dilate_img = cv2.dilate(labels,kernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,ksize=(9,9),anchor=(-1,-1)))
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
    resize_d_img = cv2.resize(drl_img,dsize=(width,height))
    ret, d_bin_img = cv2.threshold(resize_d_img, 250, 1, type=cv2.THRESH_BINARY)
    invert_d_bin_img = 1 - d_bin_img

    resize_l = cv2.resize(gtl_img,dsize=(width,height))
    ret,l_bin_img = cv2.threshold(resize_l,250,1,type=cv2.THRESH_BINARY)
    intersection_kl = labels * l_bin_img * invert_d_bin_img

    hist_l = cv2.calcHist([intersection_kl], [0], None, [region_num], [0, region_num])
    region_area = hist_l[1:]
    cluster_data = region_area.reshape(-1,1)
    cluster_result = DBSCAN(eps=300,min_samples=1).fit(cluster_data)
    sum_region_area = [0] * (max(cluster_result.labels_)+1)
    for i in range(1,len(region_area)):
        sum_region_area[cluster_result.labels_[i]] += region_area[i]
    board_region_label = sum_region_area.index(max(sum_region_area))
    board_region_index = []
    for i in range(len(cluster_result.labels_)):
        if cluster_result.labels_[i] == board_region_label:
            board_region_index.append(i+1)
    print('board region:',board_region_index)

    # none board region
    none_board_region = set(list(range(1,region_num))).difference(set(board_region_index))
    print('none board region:',none_board_region)
    inner_none_board_region = list(set(none_board_region).difference(set(outer_region_index)))
    print('inner non board region:',inner_none_board_region)

    #inner none board region length
    height,width = labels.shape
    inner_region_img = np.zeros(shape=(height,width))
    for i in range(len(inner_none_board_region)):
        index = inner_none_board_region[i]
        x,y,w,h,area = stats[index]
        for row in range(y,y+h):
            for col in range(x,x+w):
                if labels[row][col] == index:
                    inner_region_img[row][col] = 1
    ret,inner_region_img = cv2.threshold(inner_region_img,0,255,type=cv2.THRESH_BINARY)
    cv2.imwrite('inner_region.jpg',inner_region_img)

    kernel_element = cv2.getStructuringElement(cv2.MORPH_RECT,ksize=(5,5),anchor=(-1,-1))
    inner_process_img = cv2.dilate(inner_region_img,kernel=kernel_element)
    inner_process_img = cv2.erode(inner_process_img,kernel=kernel_element)
    cv2.imwrite('inner_process_img.jpg',inner_process_img)
    inner_process_img = np.uint8(inner_process_img)
    kernel_element1 = cv2.getStructuringElement(cv2.MORPH_RECT, ksize=(7, 7), anchor=(-1, -1))
    inner_process_img = cv2.dilate(inner_process_img,kernel=kernel_element1)
    contours, hierarchy = cv2.findContours(inner_process_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    inner_draw_img = np.zeros(shape=labels.shape)
    for i in range(len(contours)):
        cv2.drawContours(inner_draw_img,contours,i,color=(1),thickness=1)
    cv2.imwrite('inner_draw_img.jpg',inner_draw_img*255)
    inner_len = sum(sum(inner_draw_img))
    print('inner length:',inner_len)

    # ###########################segment line################################################
    gko_bin_img= 1 - gko_bin_img
    sketech_img = morphology.skeletonize(gko_bin_img)
    sketech_img = np.uint8(sketech_img)
    cv2.imwrite("sketech_img.png",sketech_img*100)
    kernel_element = np.array((
        [1, 1, 1],
        [1, 0, 1],
        [1, 1, 1]), dtype="float32")
    neighbor_img = cv2.filter2D(sketech_img, -1, kernel_element)
    neighbor_img = sketech_img * neighbor_img
    cv2.imwrite("neighbor_img.png", neighbor_img * 100)

    ret, cross_region_points_img = cv2.threshold(neighbor_img, 2, 1, cv2.THRESH_BINARY)
    cv2.imwrite('cross_region_points.jpg',cross_region_points_img*255)
    inner_draw_img = np.uint8(inner_draw_img)
    cv2.imwrite('test_inner_draw_img.jpg', inner_draw_img*100)
    dilate_element = cv2.getStructuringElement(shape=cv2.MORPH_RECT,ksize=(5,5))
    cross_region_points_dilate = cv2.dilate(cross_region_points_img,kernel=dilate_element)
    intersection_lp = inner_draw_img * cross_region_points_dilate
    seg_line_img = inner_draw_img - intersection_lp
    cv2.imwrite('seg_line_img.jpg',seg_line_img*255)

    #get line end points
    line_num, line_label_img = cv2.connectedComponents(seg_line_img)
    neighbor_line_img = cv2.filter2D(seg_line_img, -1, kernel=kernel_element)
    ret, end_points_region = cv2.threshold(neighbor_line_img, 1, 0, type=cv2.THRESH_TOZERO_INV)
    plt.imshow(end_points_region)
    plt.show()
    end_points_img = end_points_region * line_label_img
    cv2.imwrite('end_points_img.jpg', end_points_img * 255)

    line_dict = {}
    height, width = end_points_img.shape
    for i in range(height):
        for j in range(width):
            if end_points_img[i][j] > 0:
                print(i,j,end_points_img[i][j])
                line_dict[end_points_img[i][j]] = []

    for i in range(height):
        for j in range(width):
            if end_points_img[i][j] > 0:
                line_dict[end_points_img[i][j]].append([i, j])

    return inner_len,gko_area,line_dict

def get_len():
    outer_len = calculate_outer_length()
    inner_len, area = calculate_inner_length()
    sum_len = outer_len + inner_len
    k = 1 / 300 * 25.4 / 1000
    solid_len = sum_len * k
    solid_area = area * k * k
    print(solid_len, solid_area, solid_len / solid_area)

def generate_luodai(gko_img):
    ret,gko_bin_img = cv2.threshold(gko_img,100,1,type=cv2.THRESH_BINARY)
    sketech_img = morphology.skeletonize(gko_bin_img)
    sketech_img = np.uint8(sketech_img)
    # img = img/255
    kernel_element = np.array((
        [1, 1, 1],
        [1, 0, 1],
        [1,1,1]), dtype="float32")
    neighbor_img = cv2.filter2D(sketech_img,-1,kernel_element)
    neighbor_img = sketech_img * neighbor_img
    # Key points
    ret,neighbor_bin_img = cv2.threshold(neighbor_img,2,1,cv2.THRESH_BINARY)
    seg_line_img = cv2.absdiff(sketech_img,neighbor_bin_img)
    seg_line_img = seg_line_img
    region_num, labels, stats, centroids = cv2.connectedComponentsWithStats(seg_line_img, connectivity=8)

if __name__ == '__main__':
    folderpath = r'C:\Users\qqq\Desktop\08-20\jp-2w2282523\CAM'
    layers = os.listdir(folderpath)
    gerbers = {}
    for layer in layers:
        with open(f"{folderpath}\\{layer}") as fp:
            data = fp.read()
            gerbers[layer] = data
    # 生成图片
    gbGenerater = ImageGenerater(gerbers)
    gko_img = gbGenerater.getlayerimg("gko")
    cv2.imwrite("gko_img.png",gko_img)
    drl_img = gbGenerater.getlayerimg("drl")
    cv2.imwrite("drl_img.png", drl_img)
    gtl_img = gbGenerater.getlayerimg("gtl")
    cv2.imwrite("gtl_img.png", gtl_img)
    inner_len,gko_area,line_dict = calculate_inner_length(gko_img,drl_img,gtl_img)
    calculate_outer_length(gko_img)
    generate_luodai(gko_img)
