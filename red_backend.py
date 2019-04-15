import warnings
import numpy as np

def rotate_x(x, y, z, coords):
    hypotenuse = np.sqrt(y**2 + z**2)
    adjacent = abs(y)
    angle = np.cos(hypotenuse/adjacent)

    if z >= 0:
        if y < 0:
            angle = np.pi - angle
    else:
        if y >= 0:
            angle = 2 * np.pi - angle
        else:
            angle = np.pi + angle

    cos_angle = np.cos(angle)
    sin_angle = np.sin(angle)
    # y = z*sin(angle) + y*cos(angle)
    coords[:, 1] = coords[:, 2] * sin_angle + coords[:, 1] * cos_angle
    # z = z*cos(angle) + y*sin(angle)
    coords[:, 2] = coords[:, 2] * cos_angle + coords[:, 1] * sin_angle

def rotate_z(x, y, z, coords):
    hxpotenuse = np.sqrt(x**2 + y**2)
    adjacent = abs(x)
    angle = np.cos(hxpotenuse/adjacent)

    if y >= 0:
        if x < 0:
            angle = np.pi - angle
    else:
        if x >= 0:
            angle = 2 * np.pi - angle
        else:
            angle = np.pi + angle

    cos_angle = np.cos(angle)
    sin_angle = np.sin(angle)
    # x = y*sin(angle) + x*cos(angle)
    coords[:, 0] = coords[:, 0] * cos_angle + coords[:, 1] * sin_angle
    # y = y*cos(angle) + x*sin(angle)
    coords[:, 1] = coords[:, 0] * cos_angle - coords[:, 1] * sin_angle

def rigid_body_orient(i1, i2, i3, coords):
    # warn on alignment
    if atoms_aligned(i1, i2, i3, coords):
        warnings.warn(f'In REMARK ORIENT, atoms {i1+1} {i2+1} {i3+1} are aligned')

    # translate so atom i1 is at the origin
    coords -= coords[i1]

    # rotate around atom i2 (x, z) then atom i3
    rotate_x(*coords[i2], coords)
    rotate_z(*coords[i2], coords)
    rotate_x(*coords[i3], coords)

def rigid_body_rotate(i1, i2, i3, coords):
    # warn on alignment
    if atoms_aligned(i1, i2, i3, coords):
        warnings.warn(f'In REMARK ROTATE, atoms {i1+1} {i2+1} {i3+1} are aligned')

    # translate so atom i1 is at the origin
    vec = coords[i1][:]
    coords -= vec

    # rotate around atom i2 (x, z) then atom i3
    rotate_x(*coords[i2], coords)
    rotate_z(*coords[i2], coords)
    rotate_x(*coords[i3], coords)

    # translate back
    coords += vec

def atoms_aligned(i1, i2, i3, coords):
    """ verif_align """
    v1 = coords[i1] - coords[i2]
    v2 = coords[i2] - coords[i3]

    # avoid div by 0 error
    v1[v1 == 0] = 1e-6
    coef = v2/v1
    if coef[0] == coef[1] and coef[1] == coef[2]:
        return True
    return False

def Log2pdb():
    pass

def gen_gamess_mep_prefix(charge, multiplicity, test_l4a, pcgvar, n_proc, chr_type, title, debug=False):
    # defaults
    scf_typ = "UHF"
    coord = ""
    conv = "CONV=1.0E-06"
    memddi = "MEMDDI=0"
    proc = ""
    basis = "N31"
    ngauss = "6"
    ndfunc = "NDFUNC=1"
    ptsel = 'CONNOLY'

    if multiplicity == 1:
        scf_typ = "RHF"

    if test_l4a:
        if pcgvar:
            coord = "D5=.T."
        else:
            coord = "ISPHER=1"

    if pcgvar:
        conv = "NCONV=6"
        memddi = ""
        if n_proc > 1:
            proc="\n $P2P     P2P=.T. DLB=.T.                              $END"
    
    if chr_type.type == 'ESP' and chr_type.coeff == 2:
        basis = 'STO'
        ngauss = '3'
        ndfunc = ''
    
    if chr_type.symbol == 'C':
        ptsel = 'CHELPG'

    if debug:
        conv[-1] = "1"
        basis = "STO"
        ngauss = "2"
        ndfunc = ""

    prefix = f"""! Single point to get MEP - Input generated by R.E.D.-III in Python
!
 $CONTRL ICHARG={charge} MULT={multiplicity} RUNTYP=ENERGY MOLPLT=.T.
         MPLEVL=0 UNITS=ANGS MAXIT=200 EXETYP=RUN
         SCFTYP={scf_typ}
         {coord} COORD=UNIQUE                         $END
 $SCF    DIRSCF=.T. {conv}                       $END
 $SYSTEM TIMLIM=5000 MWORDS=32 {memddi}                $END {proc}
 $BASIS  GBASIS={basis} NGAUSS={ngauss} {ndfunc}                         $END
 $GUESS GUESS=HUCKEL                                  $END
! CHELPG/CONNOLLY CHARGES
 $ELPOT  IEPOT=1 WHERE=PDC OUTPUT=BOTH                 $END
 $PDC    PTSEL={ptsel} CONSTR=NONE                    $END
 $DATA
 {title}
 C1
"""
    return prefix
    

def write_file(filename):
    pass

def MEP_Calcul(MEPCHR_Calc, molecules, **kwargs):
    if MEPCHR_Calc:
        # log2pdb(); File4REDDB();

        prefix = gen_gamess_mep_prefix(**kwargs)

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
                    