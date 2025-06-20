import re

from fem_parser.classes import *

def parse_nastran_float(s):
    """
    Converts NASTRAN-style float strings like '2.7-9' to proper Python float.
    """
    if not s:
        return None

    if not isinstance(s, str):
        return float(s)  # Already a number

    # Match floats like 2.7-9 or -1.23+5
    match = re.match(r'^([+-]?\d*\.?\d+)([+-]\d+)$', s.strip())
    if match:
        base, exponent = match.groups()
        return float(f"{base}e{exponent}")
    else:
        return float(s)  # Regular float string

def parse_nastran_integer(s):
    if not s:
        return None
    return int(s)

def parse_nastran_string_or_interger(s):
    try:
        return parse_nastran_integer(s)
    except ValueError:
        return s

def parse_grid(rows):
    out = []
    for row in rows:
        row = row[0]
        grid = Grid(
            parse_nastran_integer(row[0]),
            parse_nastran_integer(row[1]),
            parse_nastran_float(row[2]),
            parse_nastran_float(row[3]),
            parse_nastran_float(row[4]),
            parse_nastran_integer(row[5]),
            parse_nastran_integer(row[6])
        )
        out.append(grid)
    return out

def parse_mat1(rows):
    out = []
    for r in rows:
        row = r[0]
        mat1 = Mat1(
            parse_nastran_integer(row[0]),
            parse_nastran_float(row[1]),
            parse_nastran_float(row[2]),
            parse_nastran_float(row[3]),
            parse_nastran_float(row[4]),
            parse_nastran_float(row[5]),
            parse_nastran_float(row[6]),
            parse_nastran_float(row[7]),
            None,
            None,
            None,
        )
        if row[-1] == '+':
            row = r[1]
            mat1.ST = parse_nastran_float(row[0])
            mat1.SC = parse_nastran_float(row[1])
            mat1.SS = parse_nastran_float(row[2])

        out.append(mat1)
    return out

def parse_cquad4(rows):
    out = []
    for r in rows:
        row = r[0]
        # TODO
        cquad = CQuad4(
            parse_nastran_integer(row[0]),
            parse_nastran_string_or_interger(row[1]),
            parse_nastran_integer(row[2]),
            parse_nastran_integer(row[3]),
            parse_nastran_integer(row[4]),
            parse_nastran_integer(row[5]),
            None,
            None,
            parse_nastran_float(row[7])
        )
        out.append(cquad)
    return out


def parse_cbar(rows):
    out = []
    for r in rows:
        row = r[0]
        cbar = CBar(
            parse_nastran_integer(row[0]),
            parse_nastran_string_or_interger(row[1]),
            parse_nastran_integer(row[2]),
            parse_nastran_integer(row[3]),
            None,
            parse_nastran_float(row[4]),
            parse_nastran_float(row[5]),
            parse_nastran_float(row[6]),
            row[7],
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None
        )
        if row[-1] == '+':
            row = r[1]
            cbar.PA = parse_nastran_integer(row[0])
            cbar.PB = parse_nastran_integer(row[1])
            cbar.W1A = parse_nastran_float(row[2])
            cbar.W2A = parse_nastran_float(row[3])
            cbar.W3A = parse_nastran_float(row[4])
            cbar.W1B = parse_nastran_float(row[5])
            cbar.W2B = parse_nastran_float(row[6])
            cbar.W3B = parse_nastran_float(row[7])

        out.append(cbar)
    return out

def parse_crod(rows):
    out = []
    for r in rows:
        row = r[0]
        crod = CRod(
            parse_nastran_integer(row[0]),
            parse_nastran_string_or_interger(row[1]),
            parse_nastran_integer(row[2]),
            parse_nastran_integer(row[3])
        )
        out.append(crod)
    return out


def parse_pshell(rows):
    out = []
    for r in rows:
        row = r[0]
        pshell = PShell(
            parse_nastran_string_or_interger(row[0]),
            parse_nastran_string_or_interger(row[1]),
            parse_nastran_float(row[2]),
            parse_nastran_string_or_interger(row[3]),
            parse_nastran_float(row[4]),
            parse_nastran_string_or_interger(row[5]),
            parse_nastran_float(row[6]),
            parse_nastran_float(row[7]),
        )
        if row[-1] == '+':
            RuntimeWarning("PSHELL Overflow")
        out.append(pshell)
    return out

def parse_pbarl(rows):
    out = []
    for r in rows:
        row = r[0]
        pbarl = PBarl(
            parse_nastran_string_or_interger(row[0]),
            parse_nastran_string_or_interger(row[1]),
            row[2],
            row[3],
            parse_nastran_integer(row[4]),
            [],
            None
        )
        dims = []
        num_dim = PBarl.num_dims(row[3])
        while row[-1] == '+':
            row = r[len(dims)+1]
            for j in range(min(num_dim - len(dims), 8)):
                dims.append(parse_nastran_float(row[j]))
            if len(dims) == num_dim:
                pbarl.DIMS = dims
                pbarl.NSM = row[max(num_dim - len(dims), 8)]

        out.append(pbarl)
    return out

def parse(data: dict):
    bulk = data['BULK']
    output = dict()

    for key, value in bulk.items():
        if key == "GRID":
            output[key] = parse_grid(value)
        elif key == "MAT1":
            output[key] = parse_mat1(value)
        elif key == "CQUAD4":
            output[key] = parse_cquad4(value)
        elif key == "CBAR":
            output[key] = parse_cbar(value)
        elif key == "CROD":
            output[key] = parse_crod(value)
        elif key == "PSHELL":
            output[key] = parse_pshell(value)
        elif key == "PBARL":
            output[key] = parse_pbarl(value)


    return output