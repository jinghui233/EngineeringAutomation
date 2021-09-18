import numpy as np
from scipy import spatial



class maxdis_point:
    def __init__(self,pts):
        self.pts=pts

    def getPoints_maxdis(self):


        # two points which are fruthest apart will occur as vertices of the convex hull
        candidates = self.pts[spatial.ConvexHull(self.pts).vertices]

        # get distances between each pair of candidate points
        dist_mat = spatial.distance_matrix(candidates, candidates)

        # get indices of candidates that are furthest apart
        i, j = np.unravel_index(dist_mat.argmax(), dist_mat.shape)

        return candidates[i], candidates[j]



if __name__ == '__main__':
    # test points
    pts = np.random.rand(100, 2)
    print(pts)
    print(pts.shape)
    get_maxpoints_obj=maxdis_point(pts)
    pt1,pt2=get_maxpoints_obj.getPoints_maxdis()

    print(pt1,pt2)