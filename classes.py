import copy

import numpy as np

class IsotropicMaterial(object):
    e_modulus: float
    b_basis: float
    yield_strength: float
    ultimate_strength: float
    poisson: float = 0.34

    def __init__(self, e_modulus: float, b_value: float, yield_strength: float, ultimate_strength: float):
        self.e_modulus = e_modulus
        self.b_basis = b_value
        self.yield_strength = yield_strength
        self.ultimate_strength = ultimate_strength

class OrthotropicMaterial(object):
    E11: float
    E22: float
    G12: float
    Nu12: float
    Nu21: float

    R_IIt: float = 3050
    R_IIc: float = 1500
    R_Tt: float = 300
    R_Tc: float = 50
    R_TII: float = 100

    def __init__(self, E11: float, E22: float, G12: float, Nu12: float = 0.34):
        self.E11 = E11
        self.E22 = E22
        self.G12 = G12
        self.Nu12 = Nu12
        self.Nu21 = Nu12 * (E22 / E11)

class Ply(object):
    material: OrthotropicMaterial
    angle: float
    thickness: float
    Q11: float
    Q12: float
    Q22: float
    Q66: float
    
    Q11_bar: float
    Q12_bar: float
    Q22_bar: float
    Q16_bar: float
    Q26_bar: float
    Q66_bar: float

    sigma1: float
    sigma2: float
    tau12: float

    def sin(self):
        sin = np.sin(self.angle)
        return 0 if np.isclose(sin, 0, atol=1e-6) else sin
    
    def cos(self):
        cos = np.cos(self.angle)
        return 0 if np.isclose(cos, 0, atol=1e-6) else cos

    def compute_properties(self):
        self.Q11 = self.material.E11 / (1 - self.material.Nu12 * self.material.Nu21)
        self.Q22 = self.material.E22 / (1 - self.material.Nu12 * self.material.Nu21)
        self.Q12 = self.material.Nu12 * self.material.E22 / (1 - self.material.Nu12 * self.material.Nu21)
        self.Q66 = self.material.G12

        self.Q11_bar = self.Q11* np.power(self.cos(), 4) + 2 * (self.Q12 + 2*self.Q66) * np.power(self.sin() * self.cos(), 2) + self.Q22 * np.power(self.sin(), 4)
        self.Q12_bar = (self.Q11+ self.Q22 - 4*self.Q66) * np.power(self.sin() * self.cos(), 2) + self.Q12 * (np.power(self.sin(), 4) + np.power(self.cos(), 4))
        self.Q22_bar = self.Q11* np.power(self.sin(), 4) + 2 * (self.Q12 + 2*self.Q66) * np.power(self.sin() * self.cos(), 2) + self.Q22 * np.power(self.cos(), 4)
        self.Q16_bar = (self.Q11- self.Q12 - 2*self.Q66) * self.sin() * np.power(self.cos(), 3) + (self.Q12 - self.Q22 + 2*self.Q66) * self.cos() * np.power(self.sin(), 3)
        self.Q26_bar = (self.Q11- self.Q12 - 2*self.Q66) * self.cos() * np.power(self.sin(), 3) + (self.Q12 - self.Q22 + 2*self.Q66) * self.sin() * np.power(self.cos(), 3)
        self.Q66_bar = (self.Q11+ self.Q22 - 2*self.Q12 - 2*self.Q66) * np.power(self.sin() * self.cos(), 2) + self.Q66 * (np.power(self.sin(), 4) + np.power(self.cos(), 4))

    def __init__(self, material: OrthotropicMaterial, angle: float, thickness: float):
        self.material = material
        self.angle = np.deg2rad(angle)
        self.thickness = thickness

        self.compute_properties()

    def get_RF_FF(self):
        if self.sigma1 > 0:
            return self.material.R_IIt / (1.5 * self.sigma1)
        else:
            return -self.material.R_IIc / (1.5 * self.sigma1)

    def get_RF_IFF(self):
        sigma2 = self.sigma2 * 1.5
        tau21 = self.tau12 * 1.5

        R = self.material.R_Tc / (2 * (1 + 0.25))
        tau21c = self.material.R_TII * np.sqrt(1 + 2 * 0.25)

        if sigma2 >= 0:
            f = np.sqrt(np.square(tau21 / self.material.R_TII) + np.square(1 - 0.25 * self.material.R_Tt / self.material.R_TII) * np.square(sigma2 / self.material.R_Tt)) + 0.25 * sigma2 / self.material.R_TII
            mode = "A"
        elif np.abs(sigma2 / tau21) <= R / np.abs(tau21c):
            f = (np.sqrt(np.square(tau21) + np.square(0.25 * sigma2)) + 0.25 * sigma2) / self.material.R_TII
            mode = "B"
        elif np.abs(tau21 / sigma2) <= np.abs(tau21c) / R:
            f = -(np.square(tau21 / (2 * self.material.R_TII * (1 + 0.25))) + np.square(sigma2 / self.material.R_Tc)) * self.material.R_Tc / sigma2
            mode = "C"
        else:
            f = 0
            mode = "Error"

        return 1 / f, mode


class CompositeElement(object):
    id: int
    plies: list[Ply]

    stress_x: float
    stress_y: float
    stress_xy: float

    def get_thickness(self):
        return np.sum([ply.thickness for ply in self.plies])

    def get_A(self):
        zk = -self.get_thickness() / 2
        A = np.array([0, 0, 0, 0, 0, 0])
        for ply in self.plies:
            zkp1 = zk + ply.thickness
            dz = zkp1 - zk
            Ak = np.array([
                ply.Q11_bar * dz,
                ply.Q12_bar * dz,
                ply.Q22_bar * dz,
                ply.Q16_bar * dz,
                ply.Q26_bar * dz,
                ply.Q66_bar * dz,
            ])
            A = np.add(A, Ak)

            zk = zkp1
        return np.array([[A[0], A[1], A[3]], [A[1], A[2], A[4]], [A[3], A[4], A[5]]])

    def get_B(self):
        zk = -self.get_thickness() / 2
        B = np.array([0, 0, 0, 0, 0, 0])
        for ply in self.plies:
            zkp1 = zk + ply.thickness
            dz = (np.power(zkp1, 2) - np.power(zk, 2)) / 2
            Bk = np.array([
                ply.Q11_bar * dz,
                ply.Q12_bar * dz,
                ply.Q22_bar * dz,
                ply.Q16_bar * dz,
                ply.Q26_bar * dz,
                ply.Q66_bar * dz,
            ])
            B = np.add(B, Bk)
            B = np.round(B, 10)

            zk = zkp1
        return np.array([[B[0], B[1], B[3]], [B[1], B[2], B[4]], [B[3], B[4], B[5]]])

    def get_D(self):
        zk = -self.get_thickness() / 2
        D = np.array([0, 0, 0, 0, 0, 0])
        for ply in self.plies:
            zkp1 = zk + ply.thickness
            dz = (np.power(zkp1, 3) - np.power(zk, 3)) / 3
            Dk = np.array([
                ply.Q11_bar * dz,
                ply.Q12_bar * dz,
                ply.Q22_bar * dz,
                ply.Q16_bar * dz,
                ply.Q26_bar * dz,
                ply.Q66_bar * dz,
            ])
            D = np.add(D, Dk)

            zk = zkp1
        return np.array([[D[0], D[1], D[3]], [D[1], D[2], D[4]], [D[3], D[4], D[5]]])

    def get_E_x(self, free_lat_def: bool):
        if free_lat_def:
            return 1 / (np.linalg.inv(self.get_A())[0][0] * self.get_thickness())
        else:
            return self.get_A()[0][0] / self.get_thickness()

    def get_E_b_x(self, free_lat_def: bool):
        if free_lat_def:
            return 12 / (np.linalg.inv(self.get_D())[0][0] * np.power(self.get_thickness(), 3))
        else:
            return 12 * self.get_D()[0][0] / np.power(self.get_thickness(), 3)

    def get_E_y(self, free_lat_def: bool):
        if free_lat_def:
            return 1 / (np.linalg.inv(self.get_A())[1][1] * self.get_thickness())
        else:
            return self.get_A()[1][1] * self.get_thickness()

    def get_E_b_y(self, free_lat_def: bool):
        if free_lat_def:
            return 12 / (np.linalg.inv(self.get_D())[1][1] * np.power(self.get_thickness(), 3))
        else:
            return 12 * self.get_D()[1][1] / np.power(self.get_thickness(), 3)

    def get_G(self, free_lat_def: bool):
        if free_lat_def:
            return 1 / (np.linalg.inv(self.get_A())[2][2] * self.get_thickness())
        else:
            return self.get_A()[2][2] / self.get_thickness()

    def get_G_b(self, free_lat_def: bool):
        if free_lat_def:
            return 12 / (np.linalg.inv(self.get_D())[2][2] * np.power(self.get_thickness(), 3))
        else:
            return 12 * self.get_D()[2][2] / np.power(self.get_thickness(), 3)

    def __init__(self, id: int, plies: list[Ply]):
        self.id = id
        self.plies = plies

    def set_ply_stresses(self, stresses):
        for i, ply in enumerate(self.plies):
            ply.sigma1 = stresses[0][i + 1]
            ply.sigma2 = stresses[1][i + 1]
            ply.tau12 = stresses[2][i + 1]

    def set_ply_stresses_homogenized(self, strain):
        for i, ply in enumerate(self.plies):
            epsilon1 = strain * np.square(ply.cos())
            epsilon2 = strain * np.square(ply.sin())
            gamma12 = -2 * strain * ply.cos() * ply.sin()

            ply.sigma1 = ply.Q11 * epsilon1 + ply.Q12 * epsilon2
            ply.sigma2 = ply.Q12 * epsilon1 + ply.Q22 * epsilon2
            ply.tau12 = ply.Q66 * gamma12

    def set_element_stresses(self, stress_x, stress_y, stress_xy):
        self.stress_x = stress_x
        self.stress_y = stress_y
        self.stress_xy = stress_xy

    def copy_stack(self, id = None):
        stack = copy.deepcopy(self)
        if id is not None:
            stack.id = id
        return stack

    @staticmethod
    def create_stack(id: int, material: OrthotropicMaterial, ply_thickness: float, angles: list[float]):
        plies = []
        for angle in angles:
            plies.append(Ply(material, angle, ply_thickness))
        return CompositeElement(id, plies)

class Panel(object):
    id: int
    xx: float = 0
    yy: float = 0
    xy: float = 0
    len_x: float = 750
    len_y: float = 200
    thickness: float
    elements: list[CompositeElement]

    def __init__(self, elements: list[CompositeElement], id: int, thickness: float):
        self.id = id
        self.elements = elements
        for element in elements:
            self.xx += element.stress_x
            self.yy += element.stress_y
            self.xy += element.stress_xy
        self.xy /= len(self.elements)
        self.xx /= len(self.elements)
        self.yy /= len(self.elements)

        self.thickness = thickness

    def get_sigma_crit_biax(self):
        # TODO Hardcoded orientation
        alpha = self.len_x / self.len_y
        beta = self.yy / self.xx
        D = self.elements[0].get_D() * 0.9
        all = []
        for m in range(1, 11):
            for n in range(1, 11):
                sig = np.square(np.pi / self.len_y) / self.thickness * (D[0][0] * np.power(m/alpha, 4) + 2 * (D[0][1] + D[2][2]) * np.square(m * n / alpha) + D[1][1] * np.power(n, 4)) / (np.square(m/alpha) + beta * np.square(n))
                all.append(sig)

        return min(e for e in all if e > 0)

    def get_sigma_crit_shear(self):
        D = self.elements[0].get_D() * 0.9

        delta = np.sqrt(D[0][0] * D[1][1]) / (D[0][1] + 2*D[2][2])

        if delta >= 1:
            return 4 / (self.thickness * np.square(self.len_y)) * (np.power(D[0][0] * np.power(D[1][1], 3), 1/4) * (8.12 + 5.05 / delta))

        else:
            return 4 / (self.thickness * np.square(self.len_y)) * (np.sqrt(D[1][1] * (D[0][1] + 2*D[2][2])) * (11.7 + 0.532 * delta + 0.938 * np.square(delta)))

    def get_buckling_rf(self, SF=1.5):
        sigma_crit_biax = self.get_sigma_crit_biax()
        rf_biax = np.abs(sigma_crit_biax / (self.xx * SF))

        sigma_crit_shear = self.get_sigma_crit_shear()
        rf_shear = np.abs(sigma_crit_shear / (self.xy * SF))

        return 1 / (1/rf_biax + np.square(1 / rf_shear))

    @staticmethod
    def get_panels(elements: list, bin_size: int = 3):
        if len(elements) % bin_size != 0:
            RuntimeError("Invalid number of elements/ bin size")
            return
        out = []
        for i in range(len(elements) // bin_size):
            out.append(Panel(elements[i*3:i*3+bin_size], i, 8.832))
        return out

    def __str__(self):
        return f'ID: {self.id}, XX: {self.xx}, YY: {self.yy}, XY: {self.xy}'

class CrossSection(object):
    z_EC: float
    area: float
    second_moment_area: float

    E_x: float
    E_b_x: float
    G: float

    E_b_y: float

    def __init__(self, z_EC=0.0, area=0.0):
        self.z_EC = z_EC
        self.area = area

    def get_sigma_crip(self):
        pass

class CompositeTSection(CrossSection):
    dim1: float
    dim2: float
    dim3: float
    dim4: float

    flange: CompositeElement
    web: CompositeElement

    elements: list[CrossSection] = []

    def compute_properties(self):
        b1 = self.dim1
        b2 = self.dim4

        h1 = self.dim3
        h2 = self.dim2 - self.dim3

        a1 = b1 * h1
        a2 = b2 * h2

        self.area = a1 + a2

        self.E_x = (self.flange.get_E_x(False) * a1 + self.web.get_E_x(True) * a2) / self.area
        self.G = (self.flange.get_G(False) * a1 + self.web.get_G(True) * a2) / self.area

        zc1 = h1 / 2
        zc2 = h1 + h2 / 2

        self.z_EC = (self.flange.get_E_x(False) * a1 * zc1 + self.web.get_E_x(True) * a2 * zc2) /(self.flange.get_E_x(False) * a1 + self.web.get_E_x(True) * a2)

        i1 = b1 * np.power(h1, 3) / 12
        i2 = b2 * np.power(h2, 3) / 12

        e1 = CrossSection(z_EC=zc1, area=a1)
        e1.second_moment_area = i1
        e1.E_x = self.flange.get_E_x(False)
        e1.E_b_x = self.flange.get_E_b_x(False)
        e1.E_b_y = self.flange.get_E_b_x(False)
        e1.G = self.flange.get_G(False)

        e2 = CrossSection(z_EC=zc2, area=a2)
        e2.second_moment_area = i2
        e2.E_x = self.web.get_E_x(True)
        e2.E_b_x = self.web.get_E_b_x(True)
        e2.E_b_y = e2.E_x
        e2.G = self.web.get_G(True)

        self.elements.append(e1)
        self.elements.append(e2)

    def __init__(self, dim1: float, dim2: float, dim3: float, dim4: float, flange: CompositeElement, web: CompositeElement):
        super().__init__()
        self.dim1 = dim1
        self.dim2 = dim2
        self.dim3 = dim3
        self.dim4 = dim4

        self.flange = flange
        self.web = web

        self.compute_properties()

    def get_sigma_crip(self):
        a11 = self.dim1 / 2
        a12 = self.dim2
        t1 = self.dim3
        t2 = self.dim4

        b12 = a12 - t1/2 * (2 - 0.5 * t2/t1)

        return 650 * 1.63 / np.power(b12/t2, 0.717)

class OneDElement(object):
    id: int
    axial: float

    def __init__(self, id: int, axial: float):
        self.id = id
        self.axial = axial

class Stringer(object):
    id: int
    axial: float = 0
    section: CompositeTSection

    def __init__(self, elements: list[OneDElement], id: int, flange: CompositeElement, web: CompositeElement):
        self.id = id
        self.elements = elements
        for element in elements:
            self.axial += element.axial
        self.axial /= len(elements)

        self.section = CompositeTSection(70, 44, 4, 4, flange, web)

    @staticmethod
    def get_stringers(elements: list[OneDElement], flange: CompositeElement, web: CompositeElement, bin_size: int = 3):
        if len(elements) % bin_size != 0:
            RuntimeError("Invalid number of elements/ bin size")
            return
        out = []
        for i in range(len(elements) // bin_size):
            out.append(Stringer(elements[i * 3:i * 3 + bin_size], i, flange, web))
        return out

class CombinedSection(CrossSection):
    id: int
    stringer: Stringer
    panel1: Panel
    panel2: Panel
    bending_stiffness: float
    Eyb1: float
    Eyb2: float
    Eyb3: float
    Eyb4: float

    def compute_properties(self):
        b3 = self.panel1.len_y
        h3 = self.panel1.thickness
        b4 = self.panel2.len_y
        h4 = self.panel2.thickness

        a1 = self.stringer.section.elements[0].area
        a2 = self.stringer.section.elements[1].area
        a3 = b3 * h3
        a4 = b4 * h4

        E1 = self.stringer.section.elements[0].E_x
        E2 = self.stringer.section.elements[1].E_x
        E3 = self.panel1.elements[0].get_E_x(False)
        E4 = self.panel2.elements[0].get_E_x(False)

        self.Eyb1 = self.stringer.section.elements[0].E_b_y
        self.Eyb2 = self.stringer.section.elements[1].E_b_y
        self.Eyb3 = self.panel1.elements[0].get_E_b_x(False)
        self.Eyb4 = self.panel2.elements[0].get_E_b_x(False)

        self.area = a1 + a2 + a3 + a4

        zc1 = self.stringer.section.elements[0].z_EC
        zc2 = self.stringer.section.elements[1].z_EC
        zc3 = -self.panel1.thickness / 2
        zc4 = -self.panel2.thickness / 2

        self.E_x = (a3 * E3 + a4 * E4 + self.stringer.section.area * self.stringer.section.E_x) / self.area

        self.z_EC = (zc1 * E1 * a1 + zc2 * E2 * a2 + zc3 * E3 * a3 + zc4 * E4 * a4) / (E1 * a1 + E2 * a2 + E3 * a3 + E4 * a4)

        i1 = self.stringer.section.elements[0].second_moment_area
        i2 = self.stringer.section.elements[1].second_moment_area
        i3 = b3 * np.power(h3, 3) / 12
        i4 = b4 * np.power(h4, 3) / 12

        s1 = np.square(zc1 - self.z_EC) * a1
        s2 = np.square(zc2 - self.z_EC) * a2
        s3 = np.square(zc3 - self.z_EC) * a3
        s4 = np.square(zc4 - self.z_EC) * a4

        self.second_moment_area = i1 + s1 + i2 + s2 + i3 + s3 + i4 + s4

        self.bending_stiffness = self.Eyb1 * i1 + E1 * s1 + self.Eyb2 * i2 + E2 * s2 + self.Eyb3 * i3 + E3 * s3 + self.Eyb4 * i4 + E4 * s4

        self.E_b_y = self.bending_stiffness / self.second_moment_area

    def __init__(self, stringer: Stringer, panel1: Panel, panel2: Panel):
        super().__init__()
        self.id = stringer.id
        self.stringer = stringer
        self.panel1 = panel1
        self.panel2 = panel2
        self.compute_properties()

    def get_axial_stress(self):
        area_panel1 = self.panel1.thickness * self.panel1.len_y
        area_panel2 = self.panel2.thickness * self.panel2.len_y

        return (self.panel1.xx * area_panel1 + self.panel2.xx * area_panel2 + self.stringer.axial * self.stringer.section.area) / self.area

    def get_radius_gyration(self):
        return np.sqrt(self.second_moment_area / self.area)

    def get_lambda(self, c: int = 1):
        return c * self.panel1.len_x / self.get_radius_gyration()

    def get_sigma_crip(self):
        return self.stringer.section.get_sigma_crip()

    def get_lambda_critical(self):
        return np.sqrt(2 * np.square(np.pi) * self.E_b_y * 0.9 / self.get_sigma_crip())

    def get_sigma_euler(self):
        return np.square(np.pi / self.get_lambda()) * self.E_b_y * 0.9

    def get_sigma_euler_johnson(self):
        crip = self.get_sigma_crip()
        return np.abs(crip - np.square(crip * self.get_lambda() / (2 * np.pi)) / (self.E_b_y * 0.9))

    def get_sigma_critical(self):
        sigma = self.get_sigma_euler() if self.get_lambda() > self.get_lambda_critical() else self.get_sigma_euler_johnson()
        return min(self.get_sigma_crip(), sigma)

    def get_buckling_rf(self, SF=1.5):
        return np.abs(self.get_sigma_critical() / (SF * self.get_axial_stress()))

    @staticmethod
    def get_combined_sections(stringers: list[Stringer], panels: list[Panel]):
        if len(stringers) * 2 + 2 != len(panels):
            RuntimeError("Invalid stringer/ panel data")
            return
        out: list[CombinedSection] = []
        for i in range(len(stringers)):
            out.append(CombinedSection(stringers[i], panels[2*i + 1], panels[2*i + 2]))
        return out

class Project(object):
    matrikel: int
    material: OrthotropicMaterial
    scale1: float
    scale2: float
    scale3: float

    def __init__(self, matrikel, material, scale1, scale2, scale3):
        self.matrikel = matrikel
        self.material = material
        self.scale1 = scale1
        self.scale2 = scale2
        self.scale3 = scale3
