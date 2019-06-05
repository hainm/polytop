from .gamess_io import get_gamess_mep_prefix

def MEP_Calcul(MEPCHR_Calc, molecules, **kwargs):
    if MEPCHR_Calc:
        # log2pdb(); File4REDDB();

        prefix = get_gamess_mep_prefix(**kwargs)

        for i, mol in enumerate(molecules):
            print(f"MEP(s) is/are being computed for molecule {i+1} ...")

            for j, conf in enumerate(mol.conformations):
                print(f'\n\n\tConformation {j+1} ...\t')

                for orientation in conf.orientations:
                    rigid_body_orient(*orientation.atoms, orientation.coords)
                    # write pdb
                
                for rotation in conf.rotations:
                    rigid_body_rotate(*rotation.atoms, rotation.coords)
                
                for translation in conf.translations:
                    # do translate
                
                for k, mode in enumerate(conf.modes):
                    filename = f"JOB2-gam_m{i+1}-{j+1}-{k}"
                    write_gamess_input(filename)
                    # system ("$rungms JOB2-gam_m$NM-$NC-$w $gx $NP > JOB2-gam_m$NM-$NC-$w.log");
					# 		system ("mv $scrpath/JOB2-gam_m$NM-$NC-$w.dat .");

                    # check if 'TERMINATED NORMALLY' or 'TERMINATED -ABNORMALLY-' or 'TERMINATED ABNORMALLY'

