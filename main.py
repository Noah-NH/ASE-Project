import datareader
import export
import os
from fem_parser import femreader, femparser, geometry, femwriter
from fem_parser.classes import *
from tkinter.filedialog import askdirectory

from classes import *

def find_input_file():
    template_dir = askdirectory()

    project_file = ""

    matrikel = input("Matrikel: ")
    matrikel = matrikel.removeprefix("0")

    for file in os.listdir(template_dir):
        if file.endswith(f"{matrikel}.csv"):
            project_file = file
            break

    if not project_file:
        print("Matrikel not found")
        exit(0)

    return template_dir + "/" + project_file

def input_with_default(query, default):
    return input(f"{query} [{default}]: ").strip() or default

def dimension_input():
    p1 = float(input_with_default("Thickness panel 1", "4.0"))
    p2 = float(input_with_default("Thickness panel 2", "4.0"))
    p3 = float(input_with_default("Thickness panel 3", "4.0"))
    p4 = float(input_with_default("Thickness panel 4", "4.0"))
    p5 = float(input_with_default("Thickness panel 5", "4.0"))

    s1 = list(map(float, input_with_default("Stringer 1 Dimensions", "25.0 2.0 20.0 15.0").split(" ")))
    s2 = list(map(float, input_with_default("Stringer 2 Dimensions", "25.0 2.0 20.0 15.0").split(" ")))
    s3 = list(map(float, input_with_default("Stringer 3 Dimensions", "25.0 2.0 20.0 15.0").split(" ")))
    s4 = list(map(float, input_with_default("Stringer 4 Dimensions", "25.0 2.0 20.0 15.0").split(" ")))
    s5 = list(map(float, input_with_default("Stringer 5 Dimensions", "25.0 2.0 20.0 15.0").split(" ")))

    return [p1, p2, p3, p4, p5, p5, p4, p3, p2, p1], [s1, s2, s3, s4, s5, s4, s3, s2, s1]

if __name__ == '__main__':
    print("ASE Submission 1.2 Script V2")
    print("© Noah Heinzel")

    input_file = find_input_file()
    project = datareader.read_project_data(input_file)

    # FEM Preprocessing

    fem = femreader.read_fem("Template.fem")
    data = femparser.parse(fem)

    materials: list[Mat1] = data["MAT1"]
    material: Mat1 = materials[0]
    material.E = project.material.e_modulus

    for loadadd in data["LOADADD"]:
        if loadadd.SID == 5:
            loadadd.S = project.scale1
        elif loadadd.SID == 6:
            loadadd.S = project.scale2
        elif loadadd.SID == 7:
            loadadd.S = project.scale3

    for a in data["LOADADD"]:
        print(a.S)

    input_dimensions = dimension_input()

    grid: list[Grid] = data["GRID"]

    shell_properties: list[PShell] = data["PSHELL"]
    bar_properties: list[PBarl] = data["PBARL"]

    quads: list[CQuad4] = data["CQUAD4"]
    bars: list[CBar] = data["CBAR"]

    mass = 0
    shell_dimensions = []
    stringer_sections = []
    stringer_dimensions = []

    for i, prop in enumerate(shell_properties):
        prop.T = input_dimensions[0][i]
        shell_dimensions.append([prop.T, prop.T / 2])
        shell_properties[i] = prop

    for quad in quads:
        prop = [e for e in shell_properties if e.PID == quad.PID][0]
        thickness = prop.T

        material = [e for e in materials if e.MID == prop.MID1][0]
        density = material.RHO

        g1 = [e for e in grid if e.ID == quad.G1][0]
        g2 = [e for e in grid if e.ID == quad.G2][0]
        g3 = [e for e in grid if e.ID == quad.G3][0]
        g4 = [e for e in grid if e.ID == quad.G4][0]

        area = geometry.area_of_quadrilateral_3d(g1, g2, g3, g4)

        m = area * thickness * density * 1000
        mass += m

        quad.ZOFFS = thickness / 2

    for i, prop in enumerate(bar_properties):
        if prop.TYPE == "HAT":
            prop.DIMS = input_dimensions[1][i]
            bar_properties[i] = prop
            section = HatSection(prop.DIMS[0], prop.DIMS[1], prop.DIMS[2], prop.DIMS[3])
            stringer_sections.append(section)
            stringer_dimensions.append([prop.DIMS[0], prop.DIMS[1], prop.DIMS[2], prop.DIMS[3], -section.z_centroid])
        else:
            RuntimeWarning("Not implemented yet!")

    for bar in bars:
        prop = [e for e in bar_properties if e.PID == bar.PID][0]
        area = prop.get_area()

        g1 = [e for e in grid if e.ID == bar.GA][0]
        g2 = [e for e in grid if e.ID == bar.GB][0]

        length = geometry.get_length(g1, g2)

        material = [e for e in materials if e.MID == prop.MID][0]
        density = material.RHO

        m = area * length * density * 1000
        mass += m

        if prop.TYPE == "HAT":
            section = HatSection(prop.DIMS[0], prop.DIMS[1], prop.DIMS[2], prop.DIMS[3])

            bar.W3A = -section.z_centroid
            bar.W3B = -section.z_centroid
        else:
            RuntimeWarning("Not implemented yet!")

    data["MAT1"] = materials
    data["PBARL"] = bar_properties
    data["PSHELL"] = shell_properties
    data["CQUAD4"] = quads
    data["CBAR"] = bars

    prn = femparser.print_data(data)

    for key, value in prn.items():
        fem["BULK"][key] = value

    femwriter.print_fem(fem, "analysis/Output.fem")

    rf_strength = []
    panel_buckling = []
    stringer_buckling = []
    section_properties = []

    for i in range(3):
        # Reading data
        stringer_elements = datareader.read_stringer_data(i+1, "analysis/Stringer.csv")
        panel_elements = datareader.read_panel_data(i+1, "analysis/Panel.csv")

        # Writing strength RF
        rf_strength.append([el.get_strength_rf(project.material.ultimate_strength) for el in panel_elements] + [el.get_strength_rf(project.material.ultimate_strength) for el in stringer_elements])

        # Averaging elements
        stringers = Stringer.get_stringers(stringer_elements, project.material, stringer_sections)

        panels = Panel.get_panels(panel_elements, shell_dimensions, project.material)
        sections = CombinedSection.get_combined_sections(stringers, panels)

        # Panel buckling
        xx = [p.xx for p in panels]
        yy = [p.yy for p in panels]
        xy = [p.xy for p in panels]
        k_shear = [p.get_k_shear() for p in panels]
        k_biax = [p.get_k_biax() for p in panels]
        rf_panel_buckling = [p.get_buckling_rf() for p in panels]

        panel_buckling.append([xx, yy, xy, k_shear, k_biax, rf_panel_buckling])

        # Stringer buckling
        axial = [s.get_axial_stress() for s in sections]
        crip = [s.get_sigma_crip() for s in sections]
        rf_column_buckling = [s.get_buckling_rf() for s in sections]

        stringer_buckling.append([axial, crip, rf_column_buckling])

        # Cross-section properties
        second_moment = [s.second_moment_area for s in sections]
        r = [s.get_radius_gyration() for s in sections]
        lamda = [s.get_lambda() for s in sections]
        lamda_crit = [s.get_lambda_critical() for s in sections]

        section_properties = [second_moment, r, lamda, lamda_crit]

    export.export(shell_dimensions, stringer_dimensions, mass, rf_strength, panel_buckling, stringer_buckling, section_properties, input_file, "analysis/Result.csv")
