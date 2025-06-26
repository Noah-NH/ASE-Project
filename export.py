import csv

def export(shell_dimension: list[list[float]], stringer_dimension: list[list[float]],mass: float, rf_strength: list[list[float]], panel_buckling: list[list[list[float]]], stringer_buckling: list[list[list[float]]], section_properties: list[list[float]], file_in, file_out) -> None:
    rows = []
    with open(file_in, newline='', mode='r') as csvfile:
        reader = csv.reader(csvfile, delimiter=';', quotechar='|')
        for row in reader:
            rows.append(row)

    for i, row in enumerate(rows):
        if i in range(17, 22):
            row[1] = str(shell_dimension[i - 17][0])
            row[2] = str(shell_dimension[i - 17][1])
        elif i in range(24, 29):
            row[1] = str(stringer_dimension[i - 24][0])
            row[2] = str(stringer_dimension[i - 24][1])
            row[3] = str(stringer_dimension[i - 24][2])
            row[4] = str(stringer_dimension[i - 24][3])
            row[5] = str(stringer_dimension[i - 24][4])
        elif i == 30: row[1] = str(mass)
        elif i in range(36, 93):
            row[1] = str(rf_strength[0][i - 36])
            row[4] = str(rf_strength[1][i - 36])
            row[7] = str(rf_strength[2][i - 36])
        elif i in range(98, 103):
            # LC1
            row[1] = str(panel_buckling[0][0][i - 98])
            row[2] = str(panel_buckling[0][1][i - 98])
            row[3] = str(panel_buckling[0][2][i - 98])
            row[4] = str(panel_buckling[0][3][i - 98])
            row[5] = str(panel_buckling[0][4][i - 98])
            row[6] = str(panel_buckling[0][5][i - 98])

            # LC2
            row[9] = str(panel_buckling[1][0][i - 98])
            row[10] = str(panel_buckling[1][1][i - 98])
            row[11] = str(panel_buckling[1][2][i - 98])
            row[12] = str(panel_buckling[1][3][i - 98])
            row[13] = str(panel_buckling[1][4][i - 98])
            row[14] = str(panel_buckling[1][5][i - 98])

            # LC3
            row[17] = str(panel_buckling[2][0][i - 98])
            row[18] = str(panel_buckling[2][1][i - 98])
            row[19] = str(panel_buckling[2][2][i - 98])
            row[20] = str(panel_buckling[2][3][i - 98])
            row[21] = str(panel_buckling[2][4][i - 98])
            row[22] = str(panel_buckling[2][5][i - 98])

        elif i in range(107, 112):
            row[1] = str(stringer_buckling[0][0][i - 107])
            row[2] = str(stringer_buckling[0][1][i - 107])
            row[3] = str(stringer_buckling[0][2][i - 107])

            row[6] = str(stringer_buckling[1][0][i - 107])
            row[7] = str(stringer_buckling[1][1][i - 107])
            row[8] = str(stringer_buckling[1][2][i - 107])

            row[11] = str(stringer_buckling[2][0][i - 107])
            row[12] = str(stringer_buckling[2][1][i - 107])
            row[13] = str(stringer_buckling[2][2][i - 107])

        elif i in range(115, 120):
            row[1] = str(section_properties[0][i - 114])
            row[2] = str(section_properties[1][i - 114])
            row[3] = str(section_properties[2][i - 114])
            row[4] = str(section_properties[3][i - 114])

    with open(file_out, 'w', encoding="utf-8", newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=';', quotechar='|')
        writer.writerows(rows)