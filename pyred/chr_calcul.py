import re
import subprocess
import numpy as np

PUNCH_PATTERN = re.compile(
    r'\s+\d+\s+\d+\s+(\-\d|\d)\.\d+\s+(\-\d|\d)\.\d+\s+')

INPUT_INTER_REMARK = "                    Inter-'molecular' charge equivalencing (i.e. for orientations, conformations or different molecules)"
INPUT_INTRA_REMARK = "                    Intra and/or inter-molecular charge constraints for atom or group of atoms"
INPUT_MEQA_REMARK = "               Inter-'molecular' charge equivalencing (i. e. for different molecules)"


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


def write_intra_constraints(constraints=None, ref_atom=1):
    if not constraints:
        return []
    lines = []
    conf_line = ''
    for constr in constraints:
        n_atoms = len(constr.atoms)
        lines.append(f'  {n_atoms} {constr.charge:> 4.2f}')

        for i, atom in enumerate(constr.atoms):
            conf_line += f'  {ref_atom:>3d}  {atom:>3d}'
            if i and not i % 8 and not i == n_atoms:
                conf_line += '\n'
    lines.append(conf_line)
    return [INPUT_INTRA_REMARK] + lines


def write_inter_constraints(constraints=None, ref_atoms=[]):
    if not constraints:
        return []
    lines = []
    conf_line = ''
    for constr in constraints:
        ref_atom1 = 1 + sum(ref_atoms[:constr.mol1])
        ref_atom2 = 1 + sum(ref_atoms[:constr.mol2])
        lines.append(f'  {constr.n_atoms} {constr.charge:> 4.2f}')

        for i, atom in enumerate(constr.atoms1):
            conf_line += f'  {ref_atom1:>3d}  {atom:>3d}'
            if i and not i % 8:
                conf_line += '\n'
        for j, atom in enumerate(constr.atoms2, i+1):
            conf_line += f'  {ref_atom2:>3d}  {atom:>3d}'
            if i and not i % 8:
                conf_line += '\n'
    lines.append(conf_line)
    return lines


def write_intra_charge(temps, mol, ref_atom=1):
    conf_lines = []
    if any(x == 0 for x in temps):
        conf_lines.append(INPUT_INTER_REMARK)
    for i, temp in enumerate(temps, 1):
        if temp == 0:
            conf_lines.append(f'  {mol.n_structures:3d}')
            conf_line = ''
            for j in enumerate(mol.n_structures, 1):
                conf_line += f'  {j+ref_atom-1:3d}  {i:3d}'
                if j and not j % 8:  # new line every 8th step
                    conf_line += '\n'
            conf_lines.append(conf_line)

    conf_lines.append('\n\n\n\n\n')
    return conf_lines


def write_inter_equiv(constraints, temps, ref_atoms):
    lines = []
    # if constraints:
    #     constr = constraints.pop()
    #     nmol = len(constraints[0].atoms)
    #     lines.append(INPUT_MEQA_REMARK.format(nmol=nmol))

    for constr in constraints:
        nmol = len(constr.molecules)
        for imeq in constr.atoms:
            lines.append(f'  {nmol: 3d}')
            conf_line = ''
            for i, mol in enumerate(constr.molecules, 1):
                ref_atom = 1 + sum(ref_atoms[:mol])
                conf_line += f'  {ref_atom: 3d}  {imeq: 3d}'
                if i and not i % 8:
                    conf_line += '\n'
            lines.append(conf_line)
            lines.append('')
    lines[0] += INPUT_MEQA_REMARK
    lines.append("\n\n\n\n\n\n")
    return lines


def same_number_with_T(atom, mol):
    """If another atom has the same number and its name ends with T"""
    for other in mol.atoms:
        if atom.resp_number == other.resp_number:
            if other.resp_name[-1] == 'T':
                return True
    return False


def get_resp_1_temps(i, atom, mol):
    """ Get temp values for RESP-A1, RESP-C1, DEBUG"""
    temp1 = temp2 = temp3 = temp4 = 0

    for j, other in enumerate(mol.atoms[:i], 1):
        if atom.full_resp_name == other.full_resp_name:
            if (atom.resp_name[-1] == 'T' or same_number_with_T(atom, mol)):
                temp1 = 0
                temp2 = j
                temp3 = 0
                temp4 = j
            else:
                temp1 = j
                temp2 = -1
                temp3 = j
                temp4 = -1
            break

    for constr in mol.constraints:
        if i in constr.atoms:
            temp4 = -1
            break

    return temp1, temp2, temp3, temp4


def get_resp_2_temps(i, atom, mol):
    """Get temp values for RESP-A2, RESP-C2, ESP-A1, ESP-A2"""
    temp1 = temp2 = temp3 = temp4 = 0
    for j, other in enumerate(mol.atoms[:i], 1):
        if atom.full_resp_name == other.full_resp_name:
            temp1 = j
            temp3 = j

            if same_number_with_T(atom, mol):
                temp2 = j
                temp4 = j
            else:
                temp2 = -1
                temp4 = -1
            break

    for constr in mol.constraints:
        if i in constr.atoms:
            temp4 = -1
            break

    return temp1, temp2, temp3, temp4


def get_esp_2_temps(i, atom, mol):
    """Get temp values for ESP-A2, ESP-C2"""
    temp1 = temp2 = temp3 = temp4 = 0

    for j, other in enumerate(mol.atoms[:i], 1):
        if atom.full_resp_name == other.full_resp_name:
            if same_number_with_T(atom, mol):
                temp2 = j
                temp4 = j
            else:
                temp2 = -1
                temp4 = -1

            if any(j-1 in constr.atoms for constr in mol.constraints):
                temp3 = j
            break

    for constr in mol.constraints:
        if i in constr.atoms:
            temp4 = -1
            break

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
