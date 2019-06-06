import re
import subprocess
import numpy as np

PUNCH_PATTERN = re.compile(
    r'\s+\d+\s+\d+\s+(\-\d|\d)\.\d+\s+(\-\d|\d)\.\d+\s+')

INPUT_INTER_REMARK = "                    Inter-'molecular' charge equivalencing (i.e. for orientations, conformations or different molecules)"
INPUT_INTRA_REMARK = "                    Intra and/or inter-molecular charge constraints for atom or group of atoms"


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
                    raise ValueError('At least one charge equals zero!'
                                     f' See {filename}')
                charges.append(float(ch))
    return charges


def gen_punch(mol, charges, atom_name_indices, filename):
    lines = ["     Averaged ESP charges from punch1",
             "  Z     Equiv.    q(opt)	Rounding-Off"]

    for i, (z, name) in enumerate(zip(mol.atomic_Z, mol.resp_atom_names)):
        indices = atom_name_indices.get(name, [i])
        equiv_charges = charges[indices]
        avg = np.mean(equiv_charges)
        j = indices[0]+1  # serial of first match
        lines.append(f"{z:<2d}     {j:<2d}     {avg:<8.7f}  {avg:<5.4f}")

    with open(filename, 'w') as f:
        f.write('\n'.join(lines))


def create_punch_files(mol):
    indices = name_to_indices(mol)

    try:
        charges = charges_from_punch(f'punch1_{mol.name}')
        gen_punch(mol, charges, indices, f'punch2_{mol.name}')
    except FileNotFoundError:
        pass

    try:
        charges = charges_from_punch(f'punch1_{mol.name}.sm')
        if mol.intra_constraints:
            gen_punch(mol, charges, {}, f'punch2_{mol.name}.sm')
        else:
            gen_punch(mol, charges, indices, f'punch2_{mol.name}.sm')
    except FileNotFoundError:
        pass


def name_to_indices(mol):
    indices = {}
    for i, name in enumerate(mol.resp_atom_names):
        if name in indices:
            indices[name].append(i)
        else:
            indices[name] = [i]
    return indices


def input_intra(mol):
    lines = []
    conf_line = ''
    for constr in mol.constraints:
        n_atoms = len(constr.atoms)
        lines.append('')
        # TODO: is this what %3f means??
        lines.append(f'  {n_atoms} {constr.charge: 3.2f}')

        for i, atom in enumerate(constr.atoms):
            conf_line += f'    1  {atom:3d}'
            if i and not i % 8 and not i == n_atoms:
                conf_line += '\n'
    lines.append(conf_line)
    if mol.n_structures > 1:
        lines = [INPUT_INTRA_REMARK] + lines
    return lines


def input_inter(atom_line_templates, temps, n_confmodes):
    templates = []
    atom_lines = []
    conf_lines = []
    for x, temp in zip(atom_line_templates, temps):
        templates.append(x.format(temp=temp))

    atom_lines = templates * n_confmodes

    if any(x == 0 for x in temps):
        conf_lines.append(INPUT_INTER_REMARK)
        for i in range(1, len(temps)+1):
            if temps[i-1] == 0:
                conf_lines.append(f'  {n_confmodes:3d}')
                conf_line = ''
                for j in range(1, n_confmodes):
                    conf_line += f'  {j:3d}  {i:3d}'
                    if j and not j % 8:
                        conf_line += '\n'
                conf_line += f'  {j:3d}  {i:3d}'
                conf_lines.append(conf_line)

    conf_lines.append('\n\n\n\n\n')
    return atom_lines[2:], conf_lines  # extra 1.0\n mol.title in atom_lines


def resp_2_temps(i, mol):
    temp1 = temp2 = temp3 = temp4 = 0

    flag = False
    for constr in mol.constraints:
        if i in constr.atoms:
            temp4 = -1
    else:
        flag = True

    i_name = mol.resp_atom_names[i]
    i_number = mol.resp_atom_numbers[i]
    if i_name != 'T':
        for j, j_name in enumerate(mol.resp_atom_names[:i], 1):
            if i_name == j_name:
                temp1 = j
                temp2 = j
                temp3 = j
                temp4 = j
                break

        for j, j_number in enumerate(mol.resp_atom_numbers):
            if i_number == j_number:
                if mol.resp_atom_names[j][-1] == 'T':
                    break
        else:
            temp2 = -1
            temp4 = -1

    else:
        for j, j_name in enumerate(mol.resp_atom_names[:i], 1):
            if i_name == j_name:
                temp2 = j
                temp4 = j
                break

    if not flag:
        temp4 = -1

    return temp1, temp2, temp3, temp4


def resp_1_temps(i, mol):
    temp1 = temp2 = temp3 = temp4 = 0

    flag = False
    for constr in mol.constraints:
        if i in constr.atoms:
            temp4 = -1
    else:
        flag = True

    i_name = mol.resp_atom_names[i]
    i_number = mol.resp_atom_numbers[i]
    for j, j_name in enumerate(mol.resp_atom_names[:i], 1):
        if i_name == j_name:
            temp1 = j
            temp2 = j
            temp3 = j
            temp4 = j
            break

    for j, j_number in enumerate(mol.resp_atom_numbers):
        if i_number == j_number:
            if mol.resp_atom_names[j][-1] == 'T':
                break
    else:
        temp2 = -1
        temp4 = -1

    if not flag:
        temp4 = -1

    return temp1, temp2, temp3, temp4


def esp_temps(i, mol):
    temp1 = temp2 = temp3 = temp4 = 0

    flag = False
    for constr in mol.constraints:
        if i in constr.atoms:
            temp4 = -1
    else:
        flag = True

    i_name = mol.resp_atom_names[i]
    i_number = mol.resp_atom_numbers[i]
    for j, j_name in enumerate(mol.resp_atom_names[:i], 1):
        if i_name == j_name:
            temp2 = j
            temp3 = j
            temp4 = j
            break

    for j, j_number in enumerate(mol.resp_atom_numbers):
        if i_number == j_number:
            if mol.resp_atom_names[j][-1] == 'T':
                break
    else:
        temp2 = -1
        temp4 = -1

    if not flag:
        temp4 = -1
        temp3 = 0

    return temp1, temp2, temp3, temp4


def CHR_Calcul(MEPCHR_Calc, Re_Fit, CHR_TYP, molecules):
    if MEPCHR_Calc and not Re_Fit:
        for mol in molecules:
            make_espot(mol)
            input_gene(CHR_TYP, mol)

    elif Re_Fit:
        pass
        # check for espot files

    for i, mol in enumerate(molecules, 1):
        print(f"The {CHR_TYP} charges are being derived for molecule {i} ...")
        run_resp(1, mol.name)
        run_resp(1, mol.name, '.sm')

        if CHR_TYP in {'RESP-A1', 'RESP-C1'}:
            run_resp(2, mol.name)
            run_resp(2, mol.name, '.sm')

        if CHR_TYP in {'ESP-A2', 'ESP-C2'}:
            create_punch_files(mol)

        # create mol files?
