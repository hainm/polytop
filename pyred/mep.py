import re
import logging
from .gamess_io import get_gamess_mep_prefix
from .reddb import write_reddb

logger = logging.getLogger(__name__)
abnormal_termination = re.compile('TERMINATED -?ABNORMALLY-?', flags=re.I)
normal_termination = re.compile('TERMINATED NORMALLY', flags=re.I)


class JobFailureError(Exception):
    """Raise when QM job fails"""

# def write_reddb(mol):
#     lines = ['REMARK', *mol.transform_remarks, 'REMARK']
#     for conf in mol.confs:
#         lines.extend(conf.pdb)
#         lines.append('TER')
#     if not mol.orient_remarks:
#         lines.append("REMARK QMRA")
#     lines.append('END')

#     filename = f'File4REDDB_{mol.name}.pdb'
#     with open(filename, 'w') as f:
#         f.write('\n'.join(lines))


def MEP_Calcul(molecules, **kwargs):
    for i, mol in enumerate(molecules, 1):
        prefix = get_gamess_mep_prefix(**kwargs)  # title = mol.name
        # write_reddb(mol)

        filenames = write_gamess_mep(mol)
        for file in filenames:
            run_gamess(file, verify=True)


def write_gamess_mep(mol):
    n = 1
    prefix = get_gamess_mep_prefix(mol)
    elements, numbers = mol.atom_elements, mol.atom_atomic_numbers
    atoms = [f'{el:2} {z:4.1f}' for el, z in zip(elements, numbers)]
    filenames = []

    for c, conf_coords in enumerate(mol.coords, 1):
        filebase = f'mep-{mol.name}-conf{c:02d}'

        for ijk in mol.transforms['REORIENT']:
            xyz = conf_coords.copy()
            rigid_body_orient(*ijk, xyz)
            filename = f'{filebase}-{n:02d}.inp'
            write_gamess_input(filename, prefix, atoms, xyz)
            filenames.append(filename)
            n += 1

        for ijk in mol.transforms['ROTATE']:
            xyz = conf_coords.copy()
            rigid_body_rotate(*ijk, xyz)
            filename = f'{filebase}-{n:02d}.inp'
            write_gamess_input(filename, prefix, atoms, xyz)
            filenames.append(filename)
            n += 1

        for coords in mol.transforms['TRANSLATE']:
            xyz = conf_coords.copy() + coords
            filename = f'{filebase}-{n:02d}.inp'
            write_gamess_input(filename, prefix, atoms, xyz)
            filenames.append(filename)
            n += 1

    log.info(f'Wrote GAMESS MEP files for molecule {mol.name}')
    return filenames


def write_gamess_input(filename, prefix, atoms, xyz):
    lines = [prefix]
    for a, (x, y, z) in zip(atoms, xyz):
        lines.append(f'{a} {x:12.9f} {y:12.9f} {z:12.9f}')
    lines.append(' $END\n')
    with open(filename, 'w') as f:
        f.write('\n'.join(lines))
    logger.debug(f'Wrote {filename}')
