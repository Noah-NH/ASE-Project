import numpy as np

import datareader
import export
import os
import subprocess
import configparser
import shutil
from pathlib import Path
from sys import platform
from fem_parser import femreader, femparser, femwriter
from fem_parser.classes import *
from tkinter.filedialog import askdirectory

from classes import *

config = configparser.ConfigParser()
config.read('config.ini')

def find_input_file():
    project_file = ""

    if config.has_section("General"):
        template_dir = config.get("General", "input_directory")
        matrikel = input_with_default("Matrikel", config.get("General", "matrikel"))
    else:
        template_dir = askdirectory(title="Select directory containing input csv files")
        config.add_section("General")
        config.set("General", "input_directory", template_dir)
        matrikel = input("Matrikel: ")

    config.set("General", "matrikel", matrikel)
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

if __name__ == '__main__':
    success = True
    print("ASE Submission 2.1 Script V1")
    print("© Noah Heinzel")

    input_file = find_input_file()
    project = datareader.read_project_data(input_file)

    config.write(open("config.ini", "w"))

    # FEM Preprocessing

    fem = femreader.read_fem("Template.fem")
    data = femparser.parse(fem)

    mat1s: list[Mat1] = data["MAT1"]
    stringer_material: Mat1 = mat1s[0]

    mat8s: list[Mat8] = data["MAT8"]
    panel_material: Mat8 = mat8s[0]
    panel_material.E1 = project.material.E11
    panel_material.E2 = project.material.E22
    panel_material.G12 = project.material.G12

    for loadadd in data["LOADADD"]:
        if loadadd.SID == 5:
            loadadd.S = project.scale1
        elif loadadd.SID == 6:
            loadadd.S = project.scale2
        elif loadadd.SID == 7:
            loadadd.S = project.scale3

    flange_stack: CompositeElement = CompositeElement.create_stack(0, project.material, 0.25, [45, 45, -45, -45, 0, 0, 90, 90, 90, 90, 0, 0, -45, -45, 45, 45])
    web_stack: CompositeElement = CompositeElement.create_stack(0, project.material, 0.25, [-45, -45, 45, 45, 0, 0, 90, 90, 90, 90, 0, 0, 45, 45, -45, -45])
    panel_stack: CompositeElement = CompositeElement.create_stack(0, project.material, 0.552, [45, 45, -45, -45, 0, 0, 90, 90, 90, 90, 0, 0, -45, -45, 45, 45])

    E_stringer = (flange_stack.get_E_x(False) * 70 * 4 + web_stack.get_E_x(True) * 40 * 4) / (110 * 4)
    stringer_material.E = E_stringer

    G_stringer = (flange_stack.get_G(False) * 70 * 4 + web_stack.get_G(True) * 40 * 4) / (110 * 4)
    stringer_material.G = G_stringer

    data["MAT1"] = mat1s
    data["MAT8"] = mat8s

    prn = femparser.print_data(data)

    for key, value in prn.items():
        fem["BULK"][key] = value

    femwriter.print_fem(fem, "analysis/Output.fem")

    # Analysis

    if platform == "win32":
        print("Running solver")
        subprocess.run(["solve.bat"], shell=True)
    else:
        input("Run solver and press ENTER to continue...")

    rf_strength = []
    panel_buckling = []
    stringer_buckling = []
    section_properties = []

    for i in range(3):
        # Reading data
        panel_composite_elements = datareader.read_composite_panel_data(i + 1, panel_stack)
        stringer_stacks = datareader.read_stringer_composite_data(i + 1, flange_stack, web_stack)

        # Writing strength RF
        strength = []
        for ply in panel_composite_elements.get(8).plies:
            ply: Ply
            strength.append([ply.get_RF_FF(), ply.get_RF_IFF()[0], ply.get_RF_IFF()[1], min(ply.get_RF_IFF()[0], ply.get_RF_FF())])

        for ply in stringer_stacks.get(60)[0].plies:
            ply: Ply
            strength.append([ply.get_RF_FF(), ply.get_RF_IFF()[0], ply.get_RF_IFF()[1], min(ply.get_RF_IFF()[0], ply.get_RF_FF())])

        rf_strength.append(strength)

        stringer_elements = datareader.read_stringer_data(i + 1)
        stringers = Stringer.get_stringers(list(stringer_elements.values()), flange_stack, web_stack)

        panel_composite_elements = datareader.read_panel_data(i + 1, panel_composite_elements)
        panels = Panel.get_panels(list(panel_composite_elements.values()))

        sections = CombinedSection.get_combined_sections(stringers, panels)

        panels = Panel.get_panels(list(panel_composite_elements.values()), 6)
        for p in panels:
            p.len_y = 400

        # Panel buckling
        xx = [p.xx for p in panels]
        yy = [p.yy for p in panels]
        xy = [p.xy for p in panels]
        sigma_shear = [p.get_sigma_crit_shear() for p in panels]
        sigma_biax = [p.get_sigma_crit_biax() for p in panels]
        rf_panel_buckling = [p.get_buckling_rf() for p in panels]

        panel_buckling.append([xx, yy, xy, sigma_shear, sigma_biax, rf_panel_buckling])

        # Stringer buckling
        axial = [s.get_axial_stress() for s in sections]
        crip = [s.get_sigma_crip() for s in sections]
        rf_column_buckling = [s.get_buckling_rf() for s in sections]
        stringer_buckling.append([axial, crip, rf_column_buckling])

    section_properties = [sections[0].Eyb1 * 0.9, sections[0].Eyb2 * 0.9, sections[0].Eyb3 * 0.9, sections[0].Eyb4 * 0.9, sections[0].z_EC, sections[0].bending_stiffness * 0.9, sections[0].get_radius_gyration(), sections[0].get_lambda(), sections[0].get_lambda_critical()]

    Path("./submission").mkdir(parents=True, exist_ok=True)
    export.export(flange_stack.get_A(), flange_stack.get_B(), flange_stack.get_D(), rf_strength, panel_buckling, stringer_buckling, section_properties, input_file, f"submission/ASE_Project2025_{project.matrikel}.csv")
    shutil.copy2("analysis/Output.fem", f"submission/ASE_Project2025_SuperPanel_{project.matrikel}.fem")
    print("Submission files can be found in submission folder")

    input("Press ENTER to close...")