import numpy as np
import cv2
from matplotlib import pyplot as plt


class Line_endpoint():
    def __init__(self, x1, y1, x2, y2):
        self.Aline = []
        self.start = (x1, y1)
        self.end = (x2, y2)
        self.Aline.append(self.start)
        self.Aline.append(self.end)


class getLine_endpoint():
    def __init__(self, gko_img):
        self.gko_img = gko_img
        self.imgList = []

    def imgprecess(self):
        ret, gko_bin_img = cv2.threshold(self.gko_img, 250, 255, type=cv2.THRESH_BINARY)
        region_num, labels, stats, centroids = cv2.connectedComponentsWithStats(gko_bin_img, connectivity=4)
        labels = np.uint8(labels)
        hist, bin_edges = np.histogram(labels, bins=region_num)
        lable_area = hist
        for i in range(1, region_num):
            copy_gko_binimg = np.zeros((self.gko_img.shape[0], self.gko_img.shape[1], 1), np.uint8)
            mask = i == labels
            if lable_area[i] < 10:
                continue
            else:
                copy_gko_binimg[:, :][mask] = 255
            # Detecting corners
            gray = copy_gko_binimg
            corners = cv2.goodFeaturesToTrack(gray, 35, 0.05, 10)
            print(corners)
            for pt in corners:
                print(pt)
                b = np.random.randint(0, 256 + 1)
                g = np.random.randint(0, 256 + 1)
                r = np.random.randint(0, 256 + 1)
                x = np.int32(pt[0][0])
                y = np.int32(pt[0][1])
                cv2.circle(copy_gko_binimg, (x, y), 5, (int(b), int(g), int(r)), 2)
            cv2.imshow("test", copy_gko_binimg)
            cv2.waitKey()
            Aline = np.int32([corners[0], corners[1]])
            Aline = np.reshape(Aline, (1, -1))
            AlineObj = Line_endpoint(Aline[0][0], Aline[0][1], Aline[0][2], Aline[0][3])
            self.imgList.append(AlineObj)

        return self.imgList


if __name__ == '__main__':
    gko_img = cv2.imread('seg_line_img.jpg', 0)
    get_pointObj = getLine_endpoint(gko_img)
    imgLinePoint = get_pointObj.imgprecess()
    for i in imgLinePoint:
        print(i.Aline)
