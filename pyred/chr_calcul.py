import re
import subprocess
import numpy as np

PUNCH_PATTERN = re.compile(
    r'\s+\d+\s+\d+\s+(\-\d|\d)\.\d+\s+(\-\d|\d)\.\d+\s+')


def run_resp_job(input_no, name, extension=""):
    """ Run resp in the system """
    suffix = f'{name}{extension}'
    rinput = f'input{input_no}_{suffix}'
    routput = f'output{input_no}_{suffix}'
    punch = f'punch{input_no}_{suffix}'

    espot = f'espot_{suffix}'
    qwts = f'qwts_{suffix}'
    esout = f'esout_{suffix}'

    qqout = f'qout{input_no-1}_{suffix}'
    qtout = f'qout{input_no}_{suffix}'

    subprocess.run(['resp', '-0', '-i', rinput, '-o', routput, '-p', punch,
                    '-e', espot, '-q', qqout, '-t', qtout, '-w', qwts, '-s',
                    esout], stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL)


def run_resp_1(mol):
    run_resp_job(1, mol.name, '')
    run_resp_job(1, mol.name, '.sm')


def run_resp_2(mol):
    run_resp_1(mol)
    run_resp_job(2, mol.name, '')
    run_resp_job(2, mol.name, '.sm')


def run_resp_3(mol):
    run_resp_1(mol)
    create_punch_files(mol)


def charges_from_punch(filename):
    charges = []
    with open(filename, 'r') as f:
        for line in f:
            if re.match(PUNCH_PATTERN, line):
                subbed = re.sub(r'\s+', ':', line)
                try:
                    ch = subbed.split(':')[4]
                except IndexError:
                    raise ValueError('No charge found; job failed.'
                                     f' See {filename}')
                if 'nan' in ch or '*' in ch:
                    raise ValueError('At least one charge invalid.'
                                     f' See {filename}')
                charges.append(float(ch))
    return charges


def write_intra_equivalences_all(mol_temps, mols, ref_atoms):
    conf_lines = []
    if any(x == 0 for y in mol_temps for x in y):
        conf_lines.append(INPUT_INTER_REMARK)
    for m, mol in enumerate(mols):
        temps = mol_temps[m]
        ref_atom = 1 + sum(ref_atoms[:m])
        for i, temp in enumerate(temps, 1):
            if temp == 0:
                conf_lines.append(f'  {mol.n_structures:3d}')
                conf_line = ''
                for j in range(1, mol.n_structures+1):
                    conf_line += f'  {j+ref_atom-1:3d}  {i:3d}'
                    # new line every 8th step
                    if j and not j % 8 and not j == mol.n_structures:
                        conf_line += '\n'
                conf_line += '\n'
                conf_lines.append(conf_line)
    return conf_lines


# def write_inter_equivalences(constraints, temps, ref_atoms):
#     lines = []
#     for constr in constraints:
#         nmol = len(constr.molecules)
#         for imeq in constr.atoms:
#             lines.append(f'  {nmol: 3d}')
#             conf_line = ''
#             for i, mol in enumerate(constr.molecules, 1):
#                 ref_atom = 1 + sum(ref_atoms[:mol])
#                 conf_line += f'  {ref_atom: 3d}  {imeq: 3d}'
#                 if i and not i % 8:
#                     conf_line += '\n'
#             lines.append(conf_line)
#             lines.append('')
#     if lines:
#         lines[0] += INPUT_MEQA_REMARK
#     if not any(x == 0 for y in x for x in temps):
#         lines.insert(0, '\n')
#     lines.append("\n\n\n\n\n\n")
#     return lines


# def write_inter_equivalences_2(constraints, temps, ref_atoms):
#     lines = []
#     if not any(x == 0 for y in x for x in temps):
#         lines.append('\n')
#     for constr in constraints:
#         nmol = len(constr.molecules)
#         for imeq in constr.atoms:
#             conf_line = ''
#             i = 0
#             for mol in constr.molecules:
#                 temp = temps[mol][imeq]
#                 if temp == 0:
#                     ref_atom = 1 + sum(ref_atoms[:mol])
#                     conf_line += f'  {ref_atom: 3d}  {imeq: 3d}'
#                     i += 1
#                     # newline for every 8th
#                     if i and not i % 8:
#                         conf_line += '\n'
#                         i = 0

#             if conf_line:
#                 # only on first mol where temp == 0
#                 lines.append(f'  {nmol: 3d}')
#             lines.append(conf_line)
#             lines.append('')
#     if lines:
#         lines[0] += INPUT_MEQA_REMARK
#     if not any(x == 0 for y in x for x in temps):
#         lines.insert(0, '\n')
#     lines.append("\n\n\n\n\n\n")
#     return lines


# def same_number_with_T(atom, mol):
#     """If another atom has the same number and its name ends with T"""
#     for other in mol.atoms:
#         if atom.resp_number == other.resp_number:
#             if other.resp_name[-1] == 'T':
#                 return True
#     return False


# def get_resp_1_temps(_, i, atom, mol):
#     """ Get temp values for RESP-A1, RESP-C1, DEBUG"""
#     temp1 = temp2 = temp3 = temp4 = 0

#     for j, other in enumerate(mol.atoms[:i], 1):
#         if atom.full_resp_name == other.full_resp_name:
#             if (atom.resp_name[-1] == 'T' or same_number_with_T(atom, mol)):
#                 temp1 = 0
#                 temp2 = j
#                 temp3 = 0
#                 temp4 = j
#             else:
#                 temp1 = j
#                 temp2 = -1
#                 temp3 = j
#                 temp4 = -1
#             break

#     for constr in mol.constraints:
#         if i in constr.atoms:
#             temp4 = -1
#             break

#     return temp1, temp2, temp3, temp4


# def get_resp_2_temps(_, i, atom, mol):
#     """Get temp values for RESP-A2, RESP-C2, ESP-A1, ESP-A2"""
#     temp1 = temp2 = temp3 = temp4 = 0
#     for j, other in enumerate(mol.atoms[:i], 1):
#         if atom.full_resp_name == other.full_resp_name:
#             temp1 = j
#             temp3 = j

#             if same_number_with_T(atom, mol):
#                 temp2 = j
#                 temp4 = j
#             else:
#                 temp2 = -1
#                 temp4 = -1
#             break

#     for constr in mol.constraints:
#         if i in constr.atoms:
#             temp4 = -1
#             break

#     return temp1, temp2, temp3, temp4


# def get_esp_2_temps(i, atom, mol):
#     """Get temp values for ESP-A2, ESP-C2"""
#     temp1 = temp2 = temp3 = temp4 = 0

#     for j, other in enumerate(mol.atoms[:i], 1):
#         if atom.full_resp_name == other.full_resp_name:
#             if same_number_with_T(atom, mol):
#                 temp2 = j
#                 temp4 = j
#             else:
#                 temp2 = -1
#                 temp4 = -1

#             if any(j-1 in constr.atoms for constr in mol.constraints):
#                 temp3 = j
#             break

#     for constr in mol.constraints:
#         if i in constr.atoms:
#             temp4 = -1
#             break

#     return temp1, temp2, temp3, temp4
