%Mem=96MB 
%NProc=1 

#P HF/6-31G* SCF(Conver=6) NoSymm Test 
   Pop=mk IOp(6/33=2) GFInput GFPrint 

Molecular Electrostatic Potential Dimethylalanine-dipeptide_(extended) 

0 1 
  C       -0.86694979      1.24250682      0.02893622
  H       -0.32518511      2.15261039     -0.19727073
  H       -1.67453659      1.11588992     -0.67993808
  H       -1.30504412      1.33276313      1.01702940
  C        0.00000000      0.00000000      0.00000000
  O       -0.49569409     -1.09849770      0.00047583
  N        1.32810345      0.22787467     -0.00468733
  H        1.66583153      1.16449328     -0.00297799
  C        2.36696008     -0.78994773      0.00165610
  C        2.27919390     -1.65987976     -1.26491234
  H        1.31200117     -2.13866417     -1.30444646
  H        2.40292560     -1.04903519     -2.15267315
  H        3.04170986     -2.43145678     -1.27293030
  C        2.27767363     -1.64817797      1.27615208
  H        3.04162274     -2.41814389      1.29299717
  H        2.39871190     -1.02889339      2.15848035
  H        1.31118566     -2.12827467      1.31814944
  C        3.69201415     -0.00000000      0.00000000
  O        3.71372021      1.20523375      0.00000000
  N        4.82425759     -0.72397275     -0.00031988
  H        4.77792065     -1.71439442     -0.00177528
  C        6.12518971     -0.08649987     -0.00146326
  H        6.25181527      0.53220172     -0.88034765
  H        6.25142927      0.53538763      0.87517870
  H        6.88403781     -0.85701024      0.00011732



