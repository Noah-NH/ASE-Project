import csv

def export(mass: float, rf_strength: list[list[float]], panel_buckling: list[list[list[float]]], stringer_buckling: list[list[list[float]]], section_properties: list[list[float]], file_in, file_out) -> None:
    rows = []
    with open(file_in, newline='', mode='r') as csvfile:
        reader = csv.reader(csvfile, delimiter=';', quotechar='|')
        for row in reader:
            rows.append(row)

    for i, row in enumerate(rows):
        # TODO Mass
        if i == 15: row[1] = str(mass)
        elif i in range(21, 51):
            row[1] = str(rf_strength[0][i - 21])
            row[4] = str(rf_strength[1][i - 21])
            row[7] = str(rf_strength[2][i - 21])
        elif i in range(51, 78):
            row[1] = str(rf_strength[0][i - 21])
            row[4] = str(rf_strength[1][i - 21])
            row[7] = str(rf_strength[2][i - 21])
        elif i in range(83, 88):
            # LC1
            row[1] = str(panel_buckling[0][0][i - 83])
            row[2] = str(panel_buckling[0][1][i - 83])
            row[3] = str(panel_buckling[0][2][i - 83])
            row[4] = str(panel_buckling[0][3][i - 83])
            row[5] = str(panel_buckling[0][4][i - 83])
            row[6] = str(panel_buckling[0][5][i - 83])

            # LC2
            row[9] = str(panel_buckling[1][0][i - 83])
            row[10] = str(panel_buckling[1][1][i - 83])
            row[11] = str(panel_buckling[1][2][i - 83])
            row[12] = str(panel_buckling[1][3][i - 83])
            row[13] = str(panel_buckling[1][4][i - 83])
            row[14] = str(panel_buckling[1][5][i - 83])

            # LC3
            row[17] = str(panel_buckling[2][0][i - 83])
            row[18] = str(panel_buckling[2][1][i - 83])
            row[19] = str(panel_buckling[2][2][i - 83])
            row[20] = str(panel_buckling[2][3][i - 83])
            row[21] = str(panel_buckling[2][4][i - 83])
            row[22] = str(panel_buckling[2][5][i - 83])

        elif i in range(92, 96):
            row[1] = str(stringer_buckling[0][0][i - 92])
            row[2] = str(stringer_buckling[0][1][i - 92])
            row[3] = str(stringer_buckling[0][2][i - 92])

            row[6] = str(stringer_buckling[1][0][i - 92])
            row[7] = str(stringer_buckling[1][1][i - 92])
            row[8] = str(stringer_buckling[1][2][i - 92])

            row[11] = str(stringer_buckling[2][0][i - 92])
            row[12] = str(stringer_buckling[2][1][i - 92])
            row[13] = str(stringer_buckling[2][2][i - 92])

        elif i in range(99, 103):
            row[1] = str(section_properties[0][i - 99])
            row[2] = str(section_properties[1][i - 99])
            row[3] = str(section_properties[2][i - 99])
            row[4] = str(section_properties[3][i - 99])

    with open(file_out, 'w', encoding="utf-8", newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=';', quotechar='|')
        writer.writerows(rows)