import re
import numpy as np

def read_bulk_cleanuptext(text_lines, line_limit):
    """
    Clean up the input text (bulk data)

    Args:
        text_lines (list of str): Lines from the input file
        line_limit (int): Max number of characters per line

    Returns:
        text_lines (list of str): Cleaned-up lines, each line is exactly line_limit characters
        text_lines_char (str): Combined character version (with fixed width)
        pos_endbulk (int): Index where ENDDATA line is found
        pos_beginbulk (int): Index where BEGIN BULK line is found
    """
    # Remove empty lines (only whitespace)
    text_lines = [line for line in text_lines if line.strip()]

    # Remove comment lines that start with '$'
    text_lines = [line for line in text_lines if not line.lstrip().startswith('$')]

    # Strip leading/trailing spaces
    text_lines = [line.strip() for line in text_lines]

    # Find position of 'ENDDATA' and 'BEGIN BULK'
    pos_endbulk = next((i for i, line in enumerate(text_lines) if line.strip().startswith('ENDDATA')), -1)
    pos_beginbulk = next((i for i, line in enumerate(text_lines) if line.strip().startswith('BEGIN BULK')), -1)

    # Create fixed-width lines (pad with spaces or raise error if too long)
    for i, line in enumerate(text_lines):
        if len(line) > line_limit:
            raise ValueError(f"Maximum characters in bulk data exceeded by: {len(line) - line_limit}")
        elif len(line) < line_limit:
            text_lines[i] = line + ' ' * (line_limit - len(line))

    # Create text_lines_char as a single string with fixed-width lines
    text_lines_char = "\n".join(text_lines)

    return text_lines, text_lines_char, pos_endbulk, pos_beginbulk

def get_line_information_in_text(text, common_spacing=' '):
    """
    Splits a string based on a given spacing pattern (e.g., whitespace),
    returns a list of non-empty substrings with delimiters removed.

    Args:
        text (str): Input string to process.
        common_spacing (str): Delimiter string to split on.

    Returns:
        list of str: Cleaned substrings (no delimiters).
    """
    # Find all split points (similar to strfind + [1, length(text)])
    split_indices = [0] + [m.start() for m in re.finditer(re.escape(common_spacing), text)] + [len(text)]

    # Build substrings between split points
    substrings = []
    for i in range(len(split_indices) - 1):
        start = split_indices[i]
        end = split_indices[i+1]
        fragment = text[start:end]
        # Remove all instances of common_spacing
        cleaned = fragment.replace(common_spacing, '')
        if cleaned:
            substrings.append(cleaned)

    return substrings


def read_bulk_organize_cells(output, text_lines, text_lines_char, pos_beginbulk, pos_endbulk,
                             line_limit, line_spacing):
    """
    Organizes the bulk data section of a FEM file.

    Args:
        output (dict): Existing output structure, may contain SUBCASE info
        text_lines (list of str): Lines from the file
        text_lines_char (str): Fixed-width version of the lines
        pos_beginbulk (int): Index of BEGIN BULK
        pos_endbulk (int): Index of ENDDATA
        line_limit (int): Max line length
        line_spacing (int): Field width (typically 8 or 16)

    Returns:
        dict: Updated output structure with parsed BULK data
    """

    # Extract the bulk section
    text_lines_bulk = text_lines[pos_beginbulk + 1:pos_endbulk + 1]
    char_text_lines_bulk = text_lines_char.split('\n')[pos_beginbulk + 1:pos_endbulk + 1]

    # Detect unstructured control cards (with commas)
    unstruc_control_log = [',' in line for line in char_text_lines_bulk]
    if any(unstruc_control_log):
        control_cards = [line.strip() for i, line in enumerate(text_lines_bulk) if unstruc_control_log[i]]
        output.setdefault('BULK', {})['CONTROL_CARDS'] = control_cards
        # Remove them from the bulk lines
        text_lines_bulk = [line for i, line in enumerate(text_lines_bulk) if not unstruc_control_log[i]]
        char_text_lines_bulk = [line for i, line in enumerate(char_text_lines_bulk) if not unstruc_control_log[i]]

    # Identify continuation lines
    first_chars = [line[0] if line else ' ' for line in char_text_lines_bulk]
    pos_plus = [char == '+' for char in first_chars]
    pos_orig = [not p for p in pos_plus]

    idx_total = list(range(len(pos_plus)))
    idx_orig = [i for i, is_orig in zip(idx_total, pos_orig) if is_orig]
    diffs = np.diff(idx_orig)

    # Link lines into original cards
    ids_link = [(idx_orig[i], idx_orig[i] + diffs[i] - 1)
                for i in range(len(diffs)) if diffs[i] != 1]
    ids_nolnk = [idx_orig[i] for i in range(len(diffs)) if diffs[i] == 1]

    cell_array_nolnk = [text_lines_bulk[i] for i in ids_nolnk]
    new_cells2 = []

    for start, end in ids_link:
        new_cells2.append(''.join(text_lines_bulk[start:end+1]))

    # Combine one-liners and merged multi-line cards
    new_cells3 = cell_array_nolnk + new_cells2

    # Split lines into field arrays
    text_split2 = []
    for line in new_cells3:
        # Chop into fixed-width fields
        chunks = [line[i:i+line_spacing] for i in range(0, len(line), line_spacing)]
        chunks = [chunk.strip() for chunk in chunks]
        if len(chunks) % (line_limit // line_spacing) != 0:
            continue  # Skip malformed lines
        n_rows = len(chunks) // (line_limit // line_spacing)
        reshaped = [chunks[i * (line_limit // line_spacing):(i + 1) * (line_limit // line_spacing)]
                    for i in range(n_rows)]
        text_split2.append(reshaped)

    # Extract unique card names (first field)
    card_names = [row[0][0] for row in text_split2 if row and row[0]]
    unique_names = sorted(set(card_names))

    output.setdefault('BULK', {})
    for name in unique_names:
        grouped_cards = [card for card, card_name in zip(text_split2, card_names) if card_name == name]
        # Remove the name field (first column)
        trimmed_cards = [np.array(card)[:, 1:].tolist() for card in grouped_cards]
        output['BULK'][name] = trimmed_cards

    return output

def read_fem(filename):
    line_limit = 80
    line_spacing = 8

    with open(filename) as file:
        text_lines = file.readlines()

        (text_lines, text_lines_char, pos_endbulk, pos_beginbulk) = read_bulk_cleanuptext(text_lines, line_limit)

        output = dict()
        output['SUBCASE'] = []

        def set_output_subcase(i, name, value):
            try:
                output['SUBCASE'][i][name] = value
            except IndexError:
                for _ in range(i - len(output['SUBCASE']) + 1):
                    output['SUBCASE'].append(None)
                output['SUBCASE'][i] = {name: value}

        subcase_trigger = 0
        io_count = 0

        # Process INPUTIO, SUBCASES and OBJECTIVES
        for jiu in range(pos_beginbulk):
            text = text_lines[jiu]

            if text.startswith('SUBCASE') or text.startswith(' SUBCASE'):
                subcase_trigger += 1

            if subcase_trigger == 0 or text.startswith('DESOBJ('):
                io_count += 1
                output['IO'] = [text.strip()]

            # SUBCASE DATA ENTRIES
            if subcase_trigger != 0 and not (text.startswith('SUBCASE') or text.startswith(' SUBCASE')):
                tmp_ar = get_line_information_in_text(text, ' ')
                if len(tmp_ar) > 1:
                    subcase_sub_name = tmp_ar[0]
                    subcase_sub_value = tmp_ar[-1]
                    # Store in latest subcase dict
                    set_output_subcase(subcase_trigger - 1, subcase_sub_name, subcase_sub_value)

        output = read_bulk_organize_cells(output, text_lines, text_lines_char, pos_beginbulk, pos_endbulk, line_limit, line_spacing)

    return output
