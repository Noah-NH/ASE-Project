import datareader
import export
import argparse
from fem_parser import femreader, femparser, geometry
from fem_parser.classes import *
from tkinter.filedialog import askopenfilename, asksaveasfilename

from classes import *

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    #parser.
    parser.add_argument('-n', '--nogui', default=False, action='store_true', help="run without GUI", dest='nogui')
    parser.add_argument('--input', type=str, help='Path to input project csv file')
    parser.add_argument('--stringer', type=str, help='Path to stringer stress csv file')
    parser.add_argument('--panel', type=str, help='Path to panel stress csv file')
    parser.add_argument('--fem', type=str, help='Path to fem file')

    parser.add_argument('--output', type=str, help='Path to output csv file')
    args = parser.parse_args()
    if not args.nogui:
        input_file = askopenfilename(title='Choose Input csv', filetypes=[('CSV Files', '*.csv')])
        stringer_file = askopenfilename(title='Choose Stringer csv', filetypes=[('CSV Files', '*.csv')])
        panel_file = askopenfilename(title='Choose Panel csv', filetypes=[('CSV Files', '*.csv')])
        fem_file = askopenfilename(title='Choose Input fem', filetypes=[('Optistruct FEM files', '*.fem')])
        output_file = asksaveasfilename(title='Choose Output location', filetypes=[('CSV Files', '*.csv')])
    else:
        if not (args.input and args.stringer and args.panel and args.fem and args.output):
            parser.error("When using --nogui, the input and output files must be specified")
        input_file = None
        stringer_file = None
        panel_file = None
        fem_file = None
        output_file = None

    project = datareader.read_project_data(input_file)

    fem = femreader.read_fem(fem_file)
    data = femparser.parse(fem)

    materials: list[Mat1] = data["MAT1"]
    if materials[0].E != project.material.e_modulus: RuntimeWarning("Different E-values detected!")

    grid: list[Grid] = data["GRID"]

    shell_properties: list[PShell] = data["PSHELL"]
    bar_properties: list[PBarl] = data["PBARL"]

    quads: list[CQuad4] = data["CQUAD4"]
    bars: list[CBar] = data["CBAR"]

    mass = 0
    stringer_sections = []

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
            stringer_sections.append(HatSection(prop.DIMS[0], prop.DIMS[1], prop.DIMS[2], prop.DIMS[3]))
        else:
            RuntimeWarning("Not implemented yet!")

    rf_strength = []
    panel_buckling = []
    stringer_buckling = []
    section_properties = []

    for i in range(3):
        # Reading data
        stringer_elements = datareader.read_stringer_data(i+1, stringer_file)
        panel_elements = datareader.read_panel_data(i + 1, panel_file)

        # Writing strength RF
        rf_strength.append([el.get_strength_rf(project.material.ultimate_strength) for el in panel_elements] + [el.get_strength_rf(project.material.ultimate_strength) for el in stringer_elements])

        # Averaging elements
        stringers = Stringer.get_stringers(stringer_elements, project.material, stringer_sections)
        panels = Panel.get_panels(panel_elements, project.material)
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

    print(output_file)

    export.export(mass, rf_strength, panel_buckling, stringer_buckling, section_properties, input_file, output_file)
