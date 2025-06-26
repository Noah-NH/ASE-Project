import csv
from classes import *

def read_panel_data(loadcase: int, filename) -> list[TwoDElement]:
    data = []
    with open(filename, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in reader:
            if row and row[0] == 'Elements':
                break
        for row in reader:
            if row and int(row[2]) == loadcase:
                data.append(TwoDElement(int(row[0]), float(row[5]), float(row[7]), float(row[6])))

    return data

def read_stringer_data(loadcase: int, filename) -> list[OneDElement]:
    data = []
    with open(filename, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in reader:
            if row and row[0] == 'Elements':
                break
        for row in reader:
            if row and int(row[2]) == loadcase:
                data.append(OneDElement(int(row[0]), float(row[4])))

    return data

def read_project_data(filename) -> Project:
    matrikel = None,
    E = 0
    B = 0
    Yield = 0
    Ultimate = 0
    Scales = []
    limit_mass = 0

    with open(filename, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=';', quotechar='|')
        for row in reader:
            if row and row[0] == 'matrikelnr':
                matrikel = int(row[1])
            elif row and row[0] == 'E-modulus_avg':
                E = float(row[1])
            elif row and row[0] == 'E-modulus_B-basis':
                B = float(row[1])
            elif row and row[0] == 'Yield strength (t/c)':
                Yield = float(row[1])
            elif row and row[0] == 'Ultimate strength (t/c)':
                Ultimate = float(row[1])
            elif row and row[0] == 'Load scale factor 1':
                Scales.append(float(row[1]))
            elif row and row[0] == 'Load scale factor 2':
                Scales.append(float(row[1]))
            elif row and row[0] == 'Load scale factor 3':
                Scales.append(float(row[1]))
            elif row and row[0] == 'limit model mass (skin and stringer) [kg]':
                limit_mass = float(row[1])

    print(f'Matrikelnr: {matrikel}')

    return Project(matrikel, Material(E, B, Yield, Ultimate), Scales[0], Scales[1], Scales[2], limit_mass)