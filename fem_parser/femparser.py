import math
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

def print_nastran_float(value: float, field_width: int = 8) -> str:
    """
    Converts a float to a compact Nastran-style float string.
    - Uses fixed-point if it fits
    - Falls back to Nastran-style scientific notation if needed
    - Removes trailing zeros
    - Keeps one digit after the decimal point (e.g. 1.0)
    - Does NOT pad or align the output
    """
    if value == None:
        return ''

    if value == 0.0:
        return '0.0'

    # Try fixed-point formatting first
    for decimals in range(7, -1, -1):
        fixed_str = f"{value:.{decimals}f}"
        if '.' in fixed_str:
            int_part, dec_part = fixed_str.split('.')
            dec_part = dec_part.rstrip('0')
            if dec_part == '':
                dec_part = '0'
            fixed_str = f"{int_part}.{dec_part}"
        if len(fixed_str) <= field_width:
            return fixed_str

    # Fall back to Nastran-style scientific notation
    sci_str = f"{value:.7E}"
    mantissa, exponent = sci_str.split('E')
    exponent = int(exponent)
    sign = '+' if exponent >= 0 else '-'

    # Clean up mantissa
    if '.' in mantissa:
        int_part, dec_part = mantissa.split('.')
        dec_part = dec_part.rstrip('0')
        if dec_part == '':
            dec_part = '0'
        mantissa = f"{int_part}.{dec_part}"

    nastran_str = f"{mantissa}{sign}{abs(exponent)}"

    # Trim mantissa further if needed
    while len(nastran_str) > field_width and '.' in mantissa:
        mantissa = mantissa[:-1]
        if '.' in mantissa:
            int_part, dec_part = mantissa.split('.')
            dec_part = dec_part.rstrip('0')
            if dec_part == '':
                dec_part = '0'
            mantissa = f"{int_part}.{dec_part}"
        nastran_str = f"{mantissa}{sign}{abs(exponent)}"

    return nastran_str

def parse_nastran_integer(s):
    if not s:
        return None
    return int(s)

def print_nastran_integer(value: int) -> str:
    if value == None:
        return ""
    return str(value)

def parse_nastran_string_or_interger(s):
    try:
        return parse_nastran_integer(s)
    except ValueError:
        return s

def print_nastran_string_or_integer(value: int | str) -> str:
    if value == None:
        return ""
    return str(value)

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
                pbarl.NSM = parse_nastran_float(row[max(num_dim - len(dims), 8)])

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

def print_grid(rows: list[Grid]):
    out = []
    for row in rows:
        o1 = [
            print_nastran_integer(row.ID),
            print_nastran_integer(row.CP),
            print_nastran_float(row.X1),
            print_nastran_float(row.X2),
            print_nastran_float(row.X3),
            print_nastran_integer(row.CD),
            print_nastran_integer(row.PS),
            '',
            ''
        ]
        out.append([o1])
    return out

def print_cquad4(rows: list[CQuad4]):
    out = []
    for row in rows:
        # TODO
        o1 = [
            print_nastran_integer(row.EID),
            print_nastran_string_or_integer(row.PID),
            print_nastran_integer(row.G1),
            print_nastran_integer(row.G2),
            print_nastran_integer(row.G3),
            print_nastran_integer(row.G4),
            '',
            print_nastran_float(row.ZOFFS),
            ''
        ]
        out.append([o1])
    return out

def print_cbar(rows: list[CBar]):
    out = []
    for row in rows:
        o1 = [
            print_nastran_integer(row.EID),
            print_nastran_string_or_integer(row.PID),
            print_nastran_integer(row.GA),
            print_nastran_integer(row.GB),
            print_nastran_float(row.X1),
            print_nastran_float(row.X2),
            print_nastran_float(row.X3),
            row.OFFT,
            '+'
        ]
        o2 = [
            print_nastran_integer(row.PA),
            print_nastran_integer(row.PB),
            print_nastran_float(row.W1A),
            print_nastran_float(row.W2A),
            print_nastran_float(row.W3A),
            print_nastran_float(row.W1B),
            print_nastran_float(row.W2B),
            print_nastran_float(row.W3B),
            ''
        ]
        out.append([o1, o2])
    return out

def print_crod(rows: list[CRod]):
    out = []
    for row in rows:
        o1 = [
            print_nastran_integer(row.EID),
            print_nastran_string_or_integer(row.PID),
            print_nastran_integer(row.G1),
            print_nastran_integer(row.G2),
            '',
            '',
            '',
            '',
            ''
        ]
        out.append([o1])
    return out

def print_pshell(rows: list[PShell]):
    out = []
    for row in rows:
        o1 = [
            print_nastran_string_or_integer(row.PID),
            print_nastran_string_or_integer(row.MID1),
            print_nastran_float(row.T),
            print_nastran_string_or_integer(row.MID2),
            print_nastran_float(row.T3),
            print_nastran_string_or_integer(row.MID3),
            print_nastran_float(row.TS),
            print_nastran_float(row.NSM),
            ''
        ]
        out.append([o1])
    return out

def print_pbarl(rows: list[PBarl]):
    out = []
    for row in rows:
        o1 = [
            print_nastran_string_or_integer(row.PID),
            print_nastran_string_or_integer(row.MID),
            row.GROUP,
            row.NAME if row.GROUP == "HYPERBEAM" else row.TYPE,
            print_nastran_integer(row.ND),
            '',
            '',
            '',
            '+'
        ]
        out.append([o1])
        num = row.num_dims(row.TYPE)
        for i in range(math.ceil(num / 8)):
            on = row.DIMS[i : max(i+1, num - i*8)]
            on = [print_nastran_float(a) for a in on]
            if len(on) == 8:
                on.append('+')
            else:
                on.append(print_nastran_float(row.NSM))
            out[-1].append(on)
            while len(on) < 9:
                on.append('')
    return out

def print_data(data: dict):
    output = dict()

    for key, value in data.items():
        if key == "GRID":
            output[key] = print_grid(value)
        elif key == "MAT1":
            pass
        elif key == "CQUAD4":
            output[key] = print_cquad4(value)
        elif key == "CBAR":
            output[key] = print_cbar(value)
        elif key == "CROD":
            output[key] = print_crod(value)
        elif key == "PSHELL":
            output[key] = print_pshell(value)
        elif key == "PBARL":
            output[key] = print_pbarl(value)
    return output