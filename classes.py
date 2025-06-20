from abc import abstractmethod, ABC

import numpy as np

class Material(object):
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

class TwoDElement(object):
    id: int
    xx: float
    yy: float
    xy: float
    mises: float

    def __init__(self, id, xx, yy, xy):
        self.id = id
        self.xx = xx
        self.yy = yy
        self.xy = xy
        self.mises = np.sqrt(np.square(self.xx) + np.square(self.yy) - self.xx * self.yy + 3 * np.square(self.xy))

    def get_strength_rf(self, ultimate_strength, SF=1.5):
        return np.abs(ultimate_strength / (self.mises * SF))

    def __str__(self):
        return f'ID: {self.id}, XX: {self.xx}, YY: {self.yy}, XY: {self.xy}, MISES: {self.mises}'

class Panel(object):
    id: int
    xx: float = 0
    yy: float = 0
    xy: float = 0
    len_x: float = 750
    len_y: float = 200
    thickness: float
    material: Material
    elements: list[TwoDElement]

    def __init__(self, elements: list[TwoDElement], id: int, thickness: float, material: Material):
        self.id = id
        self.elements = elements
        for element in elements:
            self.xx += element.xx
            self.yy += element.yy
            self.xy += element.xy
        self.xy /= len(self.elements)
        self.xx /= len(self.elements)
        self.yy /= len(self.elements)

        self.thickness = thickness
        self.material = material

    def get_k_biax(self):
        # TODO Hardcoded orientation
        alpha = self.len_x / self.len_y
        beta = self.yy / self.xx
        all_k = []
        for m in range(1, 11):
            for n in range(1, 11):
                all_k.append(np.square(np.square(m) + np.square(n * alpha)) / (np.square(alpha) * (np.square(m) + beta * np.square(n * alpha))))

        k = min(e for e in all_k if e > 0)
        return k

    def get_k_shear(self):
        alpha = self.len_x / self.len_y
        return 4 + 5.34 / np.square(alpha) if alpha < 1 else 5.34 + 4 / np.square(alpha)

    def get_sigma_e(self):
        return self.material.b_basis * np.square(np.pi)/(12 * (1 - np.square(self.material.poisson))) * np.square(self.thickness / self.len_y)

    def get_buckling_rf(self, SF=1.5):
        sigma_crit_biax = self.get_k_biax() * self.get_sigma_e()
        rf_biax = np.abs(sigma_crit_biax / (self.xx * SF))

        sigma_crit_shear = self.get_k_shear() * self.get_sigma_e()
        rf_shear = np.abs(sigma_crit_shear / (self.xy * SF))

        return 1 / (1/rf_biax + np.square(1 / rf_shear))


    @staticmethod
    def get_panels(elements: list[TwoDElement], material: Material, bin_size: int = 3):
        if len(elements) % bin_size != 0:
            RuntimeError("Invalid number of elements/ bin size")
            return
        out = []
        for i in range(len(elements) // bin_size):
            # TODO Hardcoded thickness
            out.append(Panel(elements[i*3:i*3+bin_size], i, 4, material))
        return out


    def __str__(self):
        return f'ID: {self.id}, XX: {self.xx}, YY: {self.yy}, XY: {self.xy}'

class CrossSection(object):
    z_centroid: float
    area: float
    second_moment_area: float

    def __init__(self, z_centroid=0, area=0):
        self.z_centroid = z_centroid
        self.area = area

    @abstractmethod
    def get_sigma_crip(self, material: Material):
        pass

class HatSection(CrossSection):
    dim1: float
    dim2: float
    dim3: float
    dim4: float

    def compute_properties(self):
        h1 = self.dim2
        h2 = self.dim1
        h3 = self.dim2

        b1 = self.dim4
        b2 = self.dim2
        b3 = (self.dim3 - 2 * self.dim2)

        a1 = h1 * b1
        a2 = h2 * b2
        a3 = h3 * b3
        a4 = a2
        a5 = a1

        self.area = a1 + a2 + a3 + a4 + a5

        z1 = self.dim2 / 2
        z2 = self.dim1 / 2
        z3 = self.dim1 - self.dim2 / 2
        z4 = z2
        z5 = z1

        self.z_centroid = (z1 * a1 + z2 * a2 + z3 * a3 + z4 * a4 + z5 * a5) / self.area

        i1 = (h1 ** 3 * b1) / 12
        i2 = (h2 ** 3 * b2) / 12
        i3 = (h3 ** 3 * b3) / 12
        i4 = i2
        i5 = i1

        self.second_moment_area = (i1 + np.square(z1 - self.z_centroid) * a1 +
                                   i2 + np.square(z2 - self.z_centroid) * a2 +
                                   i3 + np.square(z3 - self.z_centroid) * a3 +
                                   i4 + np.square(z4 - self.z_centroid) * a4 +
                                   i5 + np.square(z5 - self.z_centroid) * a5)


    def __init__(self, dim1: float, dim2: float, dim3: float, dim4: float):
        super().__init__()
        self.dim1 = dim1
        self.dim2 = dim2
        self.dim3 = dim3
        self.dim4 = dim4
        self.compute_properties()

    @staticmethod
    def _get_alpha(x):
        if x > 1.633:
            return 0.69 / (x ** 0.75)
        elif x > 1.095:
            return 0.78 / x
        elif x >= 0.4:
            return 1.4 - 0.628 * x
        else:
            RuntimeError("Invalid alpha value (no crippling possible)")

    def get_sigma_crip(self, material: Material):
        a1 = self.dim1
        a2 = self.dim3

        t = self.dim2

        b1 = a1 - t
        b2 = a2 - t

        k1 = 3.6
        k2 = 3.6

        x1 = b1/t * np.sqrt(material.yield_strength/(k1 * material.b_basis))
        x2 = b2/t * np.sqrt(material.yield_strength/(k2 * material.b_basis))

        alpha1 = self._get_alpha(x1)
        alpha2 = self._get_alpha(x2)

        sigma1 = alpha1 * material.yield_strength
        sigma2 = alpha2 * material.yield_strength

        sigma_crip_avg = (sigma1 * 2 * b1 * t + sigma2 * b2 * t) / (2 * b1 * t + b2 * t)
        return min(sigma_crip_avg, material.yield_strength)


class OneDElement(object):
    id: int
    axial: float

    def __init__(self, id: int, axial: float):
        self.id = id
        self.axial = axial

    def get_strength_rf(self, ultimate_strength, SF=1.5):
        return np.abs(ultimate_strength / (self.axial * SF))

class Stringer(object):
    id: int
    axial: float = 0
    section: CrossSection

    def __init__(self, elements: list[OneDElement], id: int, material: Material, section: CrossSection):
        self.id = id
        self.elements = elements
        for element in elements:
            self.axial += element.axial
        self.axial /= len(elements)

        self.material = material
        self.section = section

    @staticmethod
    def get_stringers(elements: list[OneDElement], material: Material, sections: list[CrossSection], bin_size: int = 3):
        if len(elements) % bin_size != 0:
            RuntimeError("Invalid number of elements/ bin size")
            return
        out = []
        for i in range(len(elements) // bin_size):
            out.append(Stringer(elements[i * 3:i * 3 + bin_size], i, material, sections[i]))
        return out

class CombinedSection(CrossSection):
    id: int
    stringer: Stringer
    panel1: Panel
    panel2: Panel
    material: Material

    def compute_properties(self):
        area_panel1 = self.panel1.thickness * self.panel1.len_y / 2
        area_panel2 = self.panel2.thickness * self.panel2.len_y / 2

        self.area = area_panel1 + area_panel2 + self.stringer.section.area

        z1 = -self.panel1.thickness / 2
        z2 = -self.panel2.thickness / 2

        self.z_centroid = (z1 * area_panel1 + z2 * area_panel2 + self.stringer.section.z_centroid * self.stringer.section.area) / self.area

        i_panel1 = (self.panel1.thickness ** 3 * (self.panel1.len_y / 2)) / 12
        i_panel2 = (self.panel2.thickness ** 3 * (self.panel2.len_y / 2)) / 12

        self.second_moment_area = (i_panel1 + np.square(z1 - self.z_centroid) * area_panel1 +
                                   i_panel2 + np.square(z2 - self.z_centroid) * area_panel2 +
                                   self.stringer.section.second_moment_area + np.square(self.stringer.section.z_centroid - self.z_centroid) * self.stringer.section.area)

    def __init__(self, stringer: Stringer, panel1: Panel, panel2: Panel):
        super().__init__()
        self.id = stringer.id
        self.material = stringer.material
        self.stringer = stringer
        self.panel1 = panel1
        self.panel2 = panel2
        self.compute_properties()

    def get_axial_stress(self):
        area_panel1 = self.panel1.thickness * self.panel1.len_y / 2
        area_panel2 = self.panel2.thickness * self.panel2.len_y / 2

        return (self.panel1.xx * area_panel1 + self.panel2.xx * area_panel2 + self.stringer.axial * self.stringer.section.area) / self.area

    def get_radius_gyration(self):
        return np.sqrt(self.second_moment_area / self.area)

    def get_lambda(self, c: int = 1):
        return c * self.panel1.len_x / self.get_radius_gyration()

    def get_sigma_crip(self, material: Material = None):
        return self.stringer.section.get_sigma_crip(self.material)

    def get_lambda_critical(self):
        return np.sqrt(2 * np.square(np.pi) * self.material.b_basis / self.get_sigma_crip())

    def get_sigma_euler(self):
        return np.square(np.pi / self.get_lambda()) * self.material.b_basis

    def get_sigma_euler_johnson(self):
        crip = self.get_sigma_crip()
        return np.abs(crip - np.square(crip * self.get_lambda() / (2 * np.pi)) / self.material.b_basis)

    def get_sigma_critical(self):
        return min(self.get_sigma_crip(), self.get_sigma_euler(), self.get_sigma_euler_johnson())

    def get_buckling_rf(self, SF=1.5):
        return np.abs(self.get_sigma_critical() / (SF * self.get_axial_stress()))



    @staticmethod
    def get_combined_sections(stringers: list[Stringer], panels: list[Panel]):
        if len(stringers) + 1 != len(panels):
            RuntimeError("Invalid stringer/ panel data")
            return
        out: list[CombinedSection] = []
        for i in range(len(stringers)):
            out.append(CombinedSection(stringers[i], panels[i], panels[i+1]))
        return out

class Project(object):
    matrikel: int
    material: Material
    scale1: float
    scale2: float
    scale3: float

    def __init__(self, matrikel, material, scale1, scale2, scale3):
        self.matrikel = matrikel
        self.material = material
        self.scale1 = scale1
        self.scale2 = scale2
        self.scale3 = scale3
