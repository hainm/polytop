def write_reddb(mol):
    lines = ['REMARK', *mol.orient_remarks, 'REMARK'] 
    for conf in mol.confs:
        lines.extend(conf.pdb)
        lines.append('TER')
    if not mol.orient_remarks:
        lines.append("REMARK QMRA")
    lines.append('END')

    filename = f'File4REDDB_{mol.name}.pdb'
    with open(filename, 'w') as f:
        f.write('\n'.join(lines))