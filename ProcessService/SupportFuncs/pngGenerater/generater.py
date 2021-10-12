import numpy as np
import cv2


def newimage():
    img = np.zeros((256, 256), dtype=np.uint8)
    cv2.rectangle(img, (0, 0), (64, 64), 14, -1)
    cv2.rectangle(img, (64, 0), (128, 64), 16, -1)
    cv2.rectangle(img, (128, 0), (192, 64), 16, -1)
    cv2.rectangle(img, (192, 0), (256, 64), 14, -1)

    cv2.rectangle(img, (0, 64), (64, 128), 10, -1)
    cv2.rectangle(img, (64, 64), (128, 128), 12, -1)
    cv2.rectangle(img, (128, 64), (192, 128), 12, -1)
    cv2.rectangle(img, (192, 64), (256, 128), 10, -1)

    cv2.rectangle(img, (0, 128), (64, 192), 6, -1)
    cv2.rectangle(img, (64, 128), (128, 192), 8, -1)
    cv2.rectangle(img, (128, 128), (192, 192), 8, -1)
    cv2.rectangle(img, (192, 128), (256, 192), 6, -1)

    cv2.rectangle(img, (0, 192), (64, 256), 2, -1)
    cv2.rectangle(img, (64, 192), (128, 256), 4, -1)
    cv2.rectangle(img, (128, 192), (192, 256), 4, -1)
    cv2.rectangle(img, (192, 192), (256, 256), 2, -1)

    for i in range(16):
        cv2.rectangle(img, (124, 16 * i), (132, 16 * i + 16), 16 - i - 1, -1)
    mapdata = ""
    for i in img:
        for j in i:
            print(j)
            mapdata += f",{str(j)}"
    with open(f"m1.txt", 'w') as f:
        f.write(mapdata)
    cv2.imwrite("img.png", img * 15)
    a = 0


if __name__ == "__main__":
    newimage()
