# Ground response against measured convergence in weak rock

- **Script:** [`models/py/validation/sem_convergence.py`](../../models/py/validation/sem_convergence.py). It downloads the data package on first run into a local cache that is not committed, then prints the table below.
- **Models:** [Hoek–Brown](../MODELS.md#hoekbrown-rock-mass), [ground response](../MODELS.md#ground-response-and-squeezing), which the [SEM demo](../realism/sem-heading.md) uses.
- **Run on:** 5 Nov 2026

## Data

The sections come from a hydropower headrace tunnel in weak flysch in central Albania, drilled and blasted with sprayed-concrete support. There are 14 monitored sections:

- GSI 25–35;
- rock cover 226–285 m;
- radius about 3 m;
- convergence read from a station installed 0.5–5 m behind the face, for 132–382 days.

They are Tables 5 and 9 of Terron-Almenara & Panthi (2025), *Rock Mechanics and Rock Engineering* 58:8111–8143, [doi:10.1007/s00603-025-04545-1](https://doi.org/10.1007/s00603-025-04545-1) (open access, CC BY 4.0). The transcription used here is in the data package of Zhang et al. (2026), [doi:10.5281/zenodo.23040284](https://doi.org/10.5281/zenodo.23040284) (CC BY 4.0).

**Set-up** (as in the package's own analysis):

- in-situ stress 0.025 MPa per metre of cover (the source's relation);
- mᵢ 7 for this siltstone-dominated flysch and Poisson's ratio 0.3;
- rock-mass modulus and σci from the source's Table 9;
- the model chain is Hoek–Brown, then equivalent Mohr–Coulomb at the in-situ stress, then the Duncan Fama ground reaction, then the Vlachopoulos & Diederichs longitudinal displacement profile.

**Reading the measurements:**

- The reading is the convergence after the station was installed, so the model's quantity is the wall displacement still to come at distance L behind the face.
- About a third of the deformation in this flysch is time-dependent (source, section 3.6). The time-independent part of each reading is therefore taken as two-thirds to all of it.
- The installed support capacity is known (1.4–2.0 MPa, Table 9), but how much of it was mobilised was not measured. So the check asks what support pressure the model needs to reproduce each reading, and whether that is within the installed capacity.

## Results

| Section | Class | GSI | P0 (MPa) | Reading, radial (mm) | Model, unsupported after the station (mm) | R_p / a | Support needed (MPa) | Installed (MPa) | Share mobilised |
|---|---|---|---|---|---|---|---|---|---|
| 7+029 | X | 25 | 5.65 | 17 | 26 | 2.41 | 0.13–0.24 | 2.0 | 6–12 % |
| 7+064 | X | 25 | 5.95 | 16 | 32 | 2.43 | 0.28–0.42 | 2.0 | 14–21 % |
| 7+092 | X | 25 | 6.25 | 15 | 25 | 2.45 | 0.14–0.24 | 1.6 | 9–15 % |
| 7+136 | VI | 35 | 6.78 | 10 | 15 | 1.96 | 0.17–0.34 | 1.6 | 11–21 % |
| 7+168 | VIII | 27 | 7.00 | 16 | 56 | 2.55 | 0.64–0.81 | 1.6 | 40–51 % |
| 7+194 | X | 25 | 7.03 | 9 | 21 | 2.41 | 0.22–0.29 | 1.6 | 14–18 % |
| 7+218 | X | 25 | 6.98 | 12 | 29 | 2.61 | 0.29–0.39 | 1.6 | 18–24 % |
| 7+266 | VIII | 35 | 6.93 | 6 | 14 | 2.02 | 0.42–0.59 | 1.4 | 30–42 % |
| 7+291 | VIII | 30 | 6.88 | 9 | 17 | 2.23 | 0.22–0.34 | 2.0 | 11–17 % |
| 7+316 | VIII | 30 | 6.78 | 8 | 13 | 2.05 | 0.19–0.32 | 1.6 | 12–20 % |
| 7+342 | VIII | 32 | 6.98 | 8 | 9 | 2.21 | 0.02–0.09 | 2.0 | 1–5 % |
| 7+423 | BIM | 35 | 7.10 | 3 | 8 | 1.77 | 0.37–0.49 | 1.6 | 23–31 % |
| 7+455 | BIM | 33 | 7.12 | 4 | 10 | 1.96 | 0.32–0.43 | 1.6 | 20–27 % |
| 7+531 | X | 25 | 6.25 | 23 | 24 | 2.50 | 0.02–0.12 | 1.4 | 1–8 % |

**What this shows:**

- **Consistent with the field data:**
  - Unsupported, the model gives a median 1.77× the measured convergence after the station.
  - Every reading is reproduced with a support pressure inside the installed capacity: 1–51 % of it, median 11–19 % in the flysch sections.
  - The plastic zone comes out at 1.8–2.6 radii.
- **Not a tight test:** the reading cannot separate the rock-mass stiffness from the share of support mobilised. The package's article draws the same conclusion about identifiability. So this check confirms the order of magnitude, not a calibrated value.
- **Rock-mass modulus:** the source's back-analysed values are higher than the Hoek–Diederichs (2006) estimate with Eᵢ 20 GPa that the demos use. The Hoek–Diederichs value is a median 0.64 of the source's. With it, our predicted displacements would be larger.
- **Time:** the data hold one reading per section, not a time series. So the Sulem convergence law and its time parameters in the SEM demo are not tested here.

## Consequences

- **No defaults change.** The ground-response chain is consistent with this tunnel.
- **Still open for the SEM demo:**
  - convergence time series from a site in comparable rock, to test the Sulem law;
  - a measured share of support mobilisation, for example from lining strain gauges, to test the lining interaction.
