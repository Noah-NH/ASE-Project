import numpy as np
from classes import *

def to_array(p):
    return np.array([p.X1, p.X2, p.X3])

def triangle_area(a, b, c):
    u = b - a
    v = c - a
    cross = np.cross(u, v)
    return 0.5 * np.linalg.norm(cross)

def area_of_quadrilateral_3d(p1, p2, p3, p4):
    a = to_array(p1)
    b = to_array(p2)
    c = to_array(p3)
    d = to_array(p4)

    area1 = triangle_area(a, b, c)
    area2 = triangle_area(a, c, d)

    return area1 + area2

def get_length(p1, p2):
    a = to_array(p1)
    b = to_array(p2)

    u = b - a
    return np.linalg.norm(u)