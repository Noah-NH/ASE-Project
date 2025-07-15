import csv
from typing import Tuple

from classes import *

def read_single_composite_panel_data(loadcase: int, filename) -> dict:
    data = dict()
    with open(filename, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in reader:
            if row and row[0] == 'Elements':
                break
        for row in reader:
            if row and int(row[2]) == loadcase:
                element_id = int(row[0])
                if not element_id in data:
                    data[element_id] = dict()
                data[element_id][int(row[4].removeprefix("Ply  "))] = float(row[5])
    return data

def read_composite_panel_data(loadcase: int, panel_stack: CompositeElement) -> dict[int, CompositeElement]:
    data = dict()

    xx = read_single_composite_panel_data(loadcase, "analysis/Comp-XX.csv")
    yy = read_single_composite_panel_data(loadcase, "analysis/Comp-YY.csv")
    xy = read_single_composite_panel_data(loadcase, "analysis/Comp-XY.csv")

    for id in xx.keys():
        stack = panel_stack.copy_stack(id)
        stack.set_ply_stresses([xx[id], yy[id], xy[id]])
        data[id] = stack

    return data

def read_panel_data(loadcase: int, elements: dict[int, CompositeElement]) -> dict[int, CompositeElement]:
    with open("analysis/Panel-Stress.csv", newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in reader:
            if row and row[0] == 'Elements':
                break
        for row in reader:
            if row and int(row[2]) == loadcase:
                elements[int(row[0])].set_element_stresses(float(row[5]), float(row[7]), float(row[6]))

    return elements

def read_stringer_composite_data(loadcase: int, flange_stack: CompositeElement, web_stack: CompositeElement) -> dict:
    data = dict()
    with open("analysis/Stringer-Strain.csv", newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in reader:
            if row and row[0] == 'Elements':
                break
        for row in reader:
            if row and int(row[2]) == loadcase:
                f = flange_stack.copy_stack()
                f.set_ply_stresses_homogenized(float(row[4]))

                w = web_stack.copy_stack()
                w.set_ply_stresses_homogenized(float(row[4]))

                data[int(row[0])] = (f, w)
    return data

def read_stringer_data(loadcase: int) -> dict[int, OneDElement]:
    data = dict()
    with open("analysis/Stringer-Stress.csv", newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in reader:
            if row and row[0] == 'Elements':
                break
        for row in reader:
            if row and int(row[2]) == loadcase:
                data[int(row[0])] = OneDElement(int(row[0]), float(row[4]))

    return data

def read_project_data(filename) -> Project:
    matrikel = None
    name = ""
    surname = ""
    E11 = 0
    E22 = 0
    G12 = 0
    Scales = []

    with open(filename, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=';', quotechar='|')
        for row in reader:
            if row and row[0] == 'matrikelnr':
                matrikel = int(row[1])
            elif row and row[0] == 'name':
                name = row[1]
            elif row and row[0] == 'surname':
                surname = row[1]
            elif row and row[0] == 'E_11_avg':
                E11 = float(row[1])
            elif row and row[0] == 'E_22_avg':
                E22 = float(row[1])
            elif row and row[0] == 'G_12_avg':
                G12 = float(row[1])
            elif row and row[0] == 'Load scale factor 1':
                Scales.append(float(row[1]))
            elif row and row[0] == 'Load scale factor 2':
                Scales.append(float(row[1]))
            elif row and row[0] == 'Load scale factor 3':
                Scales.append(float(row[1]))

    print(f'Project of {name} {surname}')

    return Project(matrikel, OrthotropicMaterial(E11, E22, G12, 0.33), Scales[0], Scales[1], Scales[2])