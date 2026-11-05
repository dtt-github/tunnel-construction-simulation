#!/bin/sh
# WP0b re-baseline: the key WP1-WP3 runs with the new packing defaults (radius 0.7 h, cohesion and stiffness divided by
# the packing). Records go to results/*_r07.json beside the WP0-WP3 records they repeat.
set -e
cd "$(dirname "$0")/.."
R() { name=$1; shift; .venv-server/bin/python -m tunnelsim_server.runner "$@" --name "${name}_r07" > /dev/null 2>&1 && echo "done $name"; }
R rankine_mu0.5592_v0.1 rankine
R rankine_mu0.35_v0.1 rankine --mu 0.35
R rankine_mu0.75_v0.1 rankine --mu 0.75
R rankine_phi34_psi10_v0.1 rankine --phi 34 --psi 10
R k0_phi34_E5e6 k0 --E 5e6
R collapse_B00 collapse --run B00
R collapse_G00 collapse --run G00
R fs_idinger_c0.5_d10 face_sand --cover 0.5
R fs_idinger_c1.0_d10 face_sand --cover 1.0
R fs_idinger_c1.5_d10 face_sand --cover 1.5
R fs_idinger_c1.0_d20 face_sand --cover 1.0 --vpd 20
R fs_wang33_c0.5_d10 face_sand --soil wang33 --cover 0.5
R fs_wang33_c1.0_d10 face_sand --soil wang33 --cover 1.0
R fs_wang33_c2.0_d10 face_sand --soil wang33 --cover 2.0
R fsb_idinger_c0.5_d10_psi4.7 face_sand --cover 0.5 --psi 4.7
R fsb_idinger_c1.0_d10_psi4.7 face_sand --cover 1.0 --psi 4.7
R fsb_idinger_c1.5_d10_psi4.7 face_sand --cover 1.5 --psi 4.7
R fsb_idinger_c1.0_d10_tc face_sand --cover 1.0 --match triaxial
R fs_idinger_c1.0_d10_servo12 face_sand --control pressure --target-kpa 12
R fs_idinger_c1.0_d10_servo6 face_sand --control pressure --target-kpa 6
R t2d_kaolin_c1.2_d10 tunnel_2d --cover 1.2
R t2d_kaolin_c2.0_d10 tunnel_2d --cover 2.0
R t2d_kaolin_c2.8_d10 tunnel_2d --cover 2.8
R t2d_kaolin_c2.0_d20 tunnel_2d --cover 2.0 --vpd 20
R fc_kaolin_c1.5_D7.5_d10 face_sand --soil kaolin --cover 1.5 --diameter 7.5 --retract 0.3
R fc_kaolin_c3.0_D4.5_d10 face_sand --soil kaolin --cover 3.0 --diameter 4.5 --retract 0.3
echo all done
