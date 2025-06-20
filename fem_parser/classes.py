import enum


class Grid(object):
    ID: int
    CP: int
    X1: float
    X2: float
    X3: float
    CD: int
    PS: int

    def __init__(self, ID, CP, X1, X2, X3, CD, PS):
        self.ID = ID
        self.CP = CP
        self.X1 = X1
        self.X2 = X2
        self.X3 = X3
        self.CD = CD
        self.PS = PS

class Mat1(object):
    MID: int
    E: float
    G: float
    NU: float
    RHO: float
    A: float
    TREF: float
    GE: float
    ST:float
    SC: float
    SS: float

    def __init__(self, MID, E, G, NU, RHO, A, TREF, GE, ST, SC, SS):
        self.MID = MID
        self.E = E
        self.G = G
        self.NU = NU
        self.RHO = RHO
        self.A = A
        self.TREF = TREF
        self.GE = GE
        self.ST = ST
        self.SC = SC
        self.SS = SS

class CQuad4(object):
    EID: int
    PID: str | int
    G1: int
    G2: int
    G3: int
    G4: int
    Theta: float
    MCID: int
    ZOFFS: float

    def __init__(self, EID, PID, G1, G2, G3, G4, Theta, MCID, ZOFFS):
        self.EID = EID
        self.PID = PID
        self.G1 = G1
        self.G2 = G2
        self.G3 = G3
        self.G4 = G4
        self.Theta = Theta
        self.MCID = MCID
        self.ZOFFS = ZOFFS

class CBar(object):
    EID: int
    PID: str | int
    GA: int
    GB: int
    G0: int
    X1: float
    X2: float
    X3: float
    OFFT: str
    PA: int
    PB: int
    W1A: float
    W2A: float
    W3A: float
    W1B: float
    W2B: float
    W3B: float

    def __init__(self, EID, PID, GA, GB, G0, X1, X2, X3, OFFT, PA, PB, W1A, W2A, W3A, W1B, W2B, W3B):
        self.EID = EID
        self.PID = PID
        self.GA = GA
        self.GB = GB
        self.G0 = G0
        self.X1 = X1
        self.X2 = X2
        self.X3 = X3
        self.OFFT = OFFT
        self.PA = PA
        self.PB = PB
        self.W1A = W1A
        self.W2A = W2A
        self.W3A = W3A
        self.W1B = W1B
        self.W2B = W2B
        self.W3B = W3B

class CRod(object):
    EID: int
    PID: str | int
    G1: int
    G2: int

    def __init__(self, EID, PID, G1, G2):
        self.EID = EID
        self.PID = PID
        self.G1 = G1
        self.G2 = G2

class PShell(object):
    PID: str | int
    MID1: str | int
    T: float
    MID2: str | int
    T3: float
    MID3: str | int
    TS: float
    NSM: float

    def __init__(self, PID, MID1, T, MID2, T3, MID3, TS, NSM):
        self.PID = PID
        self.MID1 = MID1
        self.T = T
        self.MID2 = MID2
        self.T3 = T3
        self.MID3 = MID3
        self.TS = TS
        self.NSM = NSM

class PBarl(object):
    PID: str | int
    MID: str | int
    GROUP: str
    NAME: str
    TYPE: str
    ND: int
    DIMS: list[float]
    NSM: float

    def __init__(self, PID, MID, GROUP, NAMEoTYPE, ND, DIMS, NSM):
        self.PID = PID
        self.MID = MID
        self.GROUP = GROUP
        if GROUP == "HYPERBEAM": self.NAME = NAMEoTYPE
        else: self.TYPE = NAMEoTYPE
        self.ND = ND
        self.DIMS = DIMS
        self.NSM = NSM

    def get_area(self):
        area = 0.0
        if self.TYPE == "HAT":
            h1 = self.DIMS[1]
            h2 = self.DIMS[0]
            h3 = self.DIMS[1]

            b1 = self.DIMS[3]
            b2 = self.DIMS[1]
            b3 = (self.DIMS[2] - 2 * self.DIMS[1])

            a1 = h1 * b1
            a2 = h2 * b2
            a3 = h3 * b3
            a4 = a2
            a5 = a1

            area = a1 + a2 + a3 + a4 + a5
        else:
            RuntimeError("Not implemented.")

        return area

    @staticmethod
    def num_dims(type):
        if type == "HAT":
            return 4
        else:
            RuntimeError("Not implemented")