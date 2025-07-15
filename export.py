import csv

def export(A, B, D, rf_strength, panel_buckling, stringer_buckling, section_properties, file_in, file_out) -> None:
    rows = []
    with open(file_in, newline='', mode='r') as csvfile:
        reader = csv.reader(csvfile, delimiter=';', quotechar='|')
        for row in reader:
            rows.append(row)

    for i, row in enumerate(rows):
        if i in range(16, 19):
            row[0] = str(A[i - 16][0])
            row[1] = str(A[i - 16][1])
            row[2] = str(A[i - 16][2])
        elif i in range(20, 23):
            row[0] = str(B[i - 20][0])
            row[1] = str(B[i - 20][1])
            row[2] = str(B[i - 20][2])
        elif i in range(24, 27):
            row[0] = str(D[i - 24][0])
            row[1] = str(D[i - 24][1])
            row[2] = str(D[i - 24][2])
        elif i in range(31, 63):
            row[1] = str(rf_strength[0][i - 31][0])
            row[2] = str(rf_strength[0][i - 31][1])
            row[3] = str(rf_strength[0][i - 31][2])
            row[4] = str(rf_strength[0][i - 31][3])

            row[7] = str(rf_strength[1][i - 31][0])
            row[8] = str(rf_strength[1][i - 31][1])
            row[9] = str(rf_strength[1][i - 31][2])
            row[10] = str(rf_strength[1][i - 31][3])

            row[13] = str(rf_strength[2][i - 31][0])
            row[14] = str(rf_strength[2][i - 31][1])
            row[15] = str(rf_strength[2][i - 31][2])
            row[16] = str(rf_strength[2][i - 31][3])
        elif i in range(68, 73):
            row[1] = str(panel_buckling[0][0][i - 68])
            row[2] = str(panel_buckling[0][1][i - 68])
            row[3] = str(panel_buckling[0][2][i - 68])
            row[4] = str(panel_buckling[0][3][i - 68])
            row[5] = str(panel_buckling[0][4][i - 68])
            row[6] = str(panel_buckling[0][5][i - 68])

            row[9] = str(panel_buckling[1][0][i - 68])
            row[10] = str(panel_buckling[1][1][i - 68])
            row[11] = str(panel_buckling[1][2][i - 68])
            row[12] = str(panel_buckling[1][3][i - 68])
            row[13] = str(panel_buckling[1][4][i - 68])
            row[14] = str(panel_buckling[1][5][i - 68])

            row[17] = str(panel_buckling[2][0][i - 68])
            row[18] = str(panel_buckling[2][1][i - 68])
            row[19] = str(panel_buckling[2][2][i - 68])
            row[20] = str(panel_buckling[2][3][i - 68])
            row[21] = str(panel_buckling[2][4][i - 68])
            row[22] = str(panel_buckling[2][5][i - 68])

        elif i in range(77, 81):
            row[1] = str(stringer_buckling[0][0][i - 77])
            row[2] = str(stringer_buckling[0][1][i - 77])
            row[3] = str(stringer_buckling[0][2][i - 77])

            row[6] = str(stringer_buckling[1][0][i - 77])
            row[7] = str(stringer_buckling[1][1][i - 77])
            row[8] = str(stringer_buckling[1][2][i - 77])

            row[11] = str(stringer_buckling[2][0][i - 77])
            row[12] = str(stringer_buckling[2][1][i - 77])
            row[13] = str(stringer_buckling[2][2][i - 77])
        elif i in range(84, 88):
            row[1] = section_properties[0]
            row[2] = section_properties[1]
            row[3] = section_properties[2]
            row[4] = section_properties[3]
            row[5] = section_properties[4]
            row[6] = section_properties[5]
            row[7] = section_properties[6]
            row[8] = section_properties[7]
            row[9] = section_properties[8]

    with open(file_out, 'w', encoding="utf-8", newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=';', quotechar='|')
        writer.writerows(rows)