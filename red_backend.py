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