# MPM tunnel in undrained clay (Phase 2, WP3): blocked

- **Plan:** [Phase 2, WP3](../plans/phase2-mpm-face-chamber.md#wp3-undrained-clay-face-about-2-weeks).
- **Code:**
  - [`server/tunnelsim_server/scenes/tunnel_2d.py`](../../server/tunnelsim_server/scenes/tunnel_2d.py), a plane-strain tunnel with a closing ring of segments;
  - [`face_sand.py`](../../server/tunnelsim_server/scenes/face_sand.py) with the kaolin soil;
  - records `t2d_*` and `fc_*` in [`server/results/`](../../server/results/).
- **Status:** **blocked.** The MPM clay tunnel collapses at about half the stability ratio measured by Kimura & Mair (1981), in 2D and 3D alike. Every cause checked so far is ruled out (see below). The London Clay route waits until this is understood.
- **Run on:** 5 Nov 2026

## Data: Kimura & Mair (1981)

The paper is open in the [ISSMGE library](https://www.issmge.org/uploads/publications/1/35/1981_01_0061.pdf). Its numbers are digitised from the scanned Figs 6, 9 and 10 by mapping the axis ticks to pixels, to about ±0.2 in N.

**The tests:**
- kaolin, cu = 26 kPa;
- a 60 mm tunnel at 75 g and 125 g (4.5 m and 7.5 m prototypes), supported by compressed air in a rubber bag;
- N = (σz − σT)/cu, with σz the overburden at the axis.

**The unit weight** is not stated. It comes from pairing Fig. 6 (σT/cu, 2D) with Fig. 10 (N, 2D) at the same C/D: σz/cu = N + σT/cu gives γD/cu ≈ 2.5 at C/D 1.2, 2.0 and 2.8 alike. That is γ ≈ 14.4 kN/m³ at D = 4.5 m.

| Series | C/D | N at collapse |
|---|---|---|
| Plane strain (2D, Fig. 10) | 1.2 / 1.8 / 2.0 / 2.3 / 2.8 | 3.5 / 3.7 / 4.3 / 3.8–4.2 / 4.2 |
| Heading supported to the face, P/D = 0 (Fig. 9) | 1.5 / 3.0 | 7.05 / 9.0 |
| Unlined heading, C/D 3.0 (Fig. 9) | P/D 0.5 / 1.0 / 2.0 / 3.0 | 7.75 / 6.85 / 5.6 / 5.05 |

**Not modelled:** headings with unlined length (P/D > 0). They need pressure on the heading walls, and Newton's colliders cannot apply a traction.

## Results

Rigid-plastic Tresca (friction 0, `yield_stress` = cu). The tunnel wall or face plate is frictionless, as a pressurised bag would be. N is read at 5 % of R (2D) or D (3D) of movement. The pressure keeps falling with further movement and never levels off.

| Case | MPM N | Kimura N | MPM / Kimura |
|---|---|---|---|
| Plane strain, C/D 1.2, D/10 | 2.7 | 3.5 | 0.76 |
| Plane strain, C/D 2.0, D/10 / D/20 / D/30 | 2.1 / 1.9 / 2.8 | 4.3 | 0.44–0.65 |
| Plane strain, C/D 2.8, D/10 | 2.0 | 4.2 | 0.48 |
| Heading at P/D 0, C/D 1.5, D 7.5 m, D/10 | 4.3 | 7.05 | 0.61 |
| Heading at P/D 0, C/D 3.0, D 4.5 m, D/10 | 3.8 | 9.0 | 0.42 |

The MPM clay is about **twice too weak** in plane strain and in 3D alike. The plane-strain values fall below the weightless plasticity lower bound for a circular tunnel, N = 2·ln(2C/D + 1) (Davis et al. 1980), which is about 3.2 at C/D 2.0. A correct rigid-plastic solution cannot do that.

## What has been ruled out

| Suspect | Test | Result |
|---|---|---|
| The cohesion term is scaled wrongly in Newton | Rankine active wall in Tresca clay | Matches theory: K 0.767 against 0.766 (cu/γH 0.06), 0.394 against 0.375–0.473 (0.16) |
| Stress level | The same wall test scaled ×10 (H 20 m) | Still matches: 0.722 and 0.353 |
| Clay leaking past the face plate | Particles behind the plate at the end | About 200 of 181,000 |
| Friction on the shield tube | Tube and plate frictionless | No change (N 2.6 against 3.3 at 5 %) |
| Rate | Retraction 5× slower | Weaker, not stronger |
| Solver convergence | 250 iterations; 4× smaller time step | No change (N 3.1–3.3 at 5 %) |
| Resolution | Plane strain at D/10, D/20, D/30 | N 1.9–2.8, no trend towards 4.3 |
| The yield condition is not enforced | Particle stress with a finite stiffness | √J2 = cu exactly where yielded, never above |

## What points to the cause

The stress check showed two more things:
- **The soil is at yield almost everywhere:** √J2/cu = 0.91 at 3–5 radii from the tunnel.
- **The mean stress is too low:** about 110 kPa around the tunnel, against an overburden of 162 kPa at axis level. At yield (σv − σh ≤ √3·cu) that implies a vertical stress below 140 kPa, short of the weight above. A static solid cannot do that.

So in a cohesive soil at yield over a large region, the solver does not seem to carry the soil's weight as a static stress field. In WP1 the elastic column got σv = γz right, but it never yielded. The sand faces were frictional and mostly not at yield, which may be why the problem is smaller or hidden there.

## Proposed next steps

1. **A weightless plane-strain benchmark.** A shallow tunnel with a surcharge and γ = 0 has closed-form bounds (Davis et al. 1980). It separates a gravity-handling problem from a yield-surface problem.
2. **Equilibrium check.** Integrate the particle stresses across horizontal sections and compare them with the weight above, in the elastic column (WP1) and in the clay slab at yield.
3. **If the solver is at fault:** report it upstream to Newton with a minimal reproduction (only with the maintainers' approval), and keep clay out of the live view until it is fixed.

Until then, WP3 is blocked, and the clay face is not used anywhere.
