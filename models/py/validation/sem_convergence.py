"""Check the ground-response chain (Hoek-Brown -> equivalent Mohr-Coulomb -> Duncan Fama ground reaction ->
Vlachopoulos & Diederichs LDP) against measured convergence in a weak-rock tunnel.

Data (CC BY 4.0): 14 monitored sections of a hydropower headrace tunnel in weak flysch, central Albania, Tables 5 and 9
of Terron-Almenara & Panthi (2025), Rock Mech Rock Eng 58:8111-8143, doi:10.1007/s00603-025-04545-1, as transcribed
in the data package of Zhang et al. (2026), Zenodo, doi:10.5281/zenodo.23040284 (downloaded on first run into
validation/.cache/, not committed).

Set-up, following the package's field_case.py: in-situ stress P0 = 0.025 z MPa (the source's relation), m_i 7
(siltstone-dominated flysch), Poisson's ratio 0.3, rock-mass modulus and sigma_ci from Table 9 of the source. The
reading is the wall-to-wall convergence from the installation of the station at distance L behind the face to the end
of monitoring; about one third of the deformation in this flysch is time-dependent (source, section 3.6), so the
time-independent part is taken as 2/3 to 1 of the reading. The installed support capacity p_i is Table 9's; how much
of it was mobilised is not measured. For each section the script back-calculates the support pressure the model needs
to reproduce the reading and compares it with p_i.

Run:  uv run python validation/sem_convergence.py      (prints a Markdown summary)
"""
from __future__ import annotations

import csv
import io
import statistics as st
import sys
import urllib.request
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from tunnelsim_models.ground_response import equivalent_mohr_coulomb, ground_reaction, ldp, pressure_for_displacement  # noqa: E402
from tunnelsim_models.hoek_brown import hoek_brown  # noqa: E402

CACHE = HERE / ".cache"
URL = "https://zenodo.org/api/records/23040284/files/convergence_identifiability_data.zip/content"
MI, NU, EI = 7.0, 0.3, 20000.0  # E_i only for the Hoek-Diederichs comparison (source prior 15-25 GPa)


def tables() -> tuple[list[dict], dict]:
    CACHE.mkdir(exist_ok=True)
    p = CACHE / "convergence_identifiability_data.zip"
    if not p.exists():
        req = urllib.request.Request(URL, headers={"User-Agent": "tunnel-construction-simulation validation"})
        with urllib.request.urlopen(req, timeout=120) as r:
            p.write_bytes(r.read())
    z = zipfile.ZipFile(p)
    base = "convergence_identifiability_data/data/field_case/"
    t5 = list(csv.DictReader(io.TextIOWrapper(z.open(base + "table5_convergence.csv"), encoding="utf-8")))
    t9 = {r["chainage"]: r for r in csv.DictReader(io.TextIOWrapper(z.open(base + "table9_ccm_results.csv"), encoding="utf-8"))}
    return t5, t9


def sections() -> list[dict]:
    t5, t9 = tables()
    out = []
    for r in t5:
        q = t9[r["chainage"]]
        p0 = 0.025 * float(r["rock_cover_m"])
        a, length, gsi = float(r["tunnel_radius_RT_m"]), float(r["L_m"]), float(r["GSI"])
        e, sci, pi = float(q["Erm_MPa"]), float(q["weighted_sigma_ci_MPa"]), float(q["support_pressure_pi_MPa"])
        mc = equivalent_mohr_coulomb(gsi, MI, sci, EI, p0)
        free = ground_reaction(p0, 0.0, a, e, NU, mc.phi_deg, mc.c)
        before = free.u * ldp(length, a, free.r_p)  # released before the station was installed
        reading = float(r["measured_convergence_mm"]) / 2000  # radial, m
        need = [pressure_for_displacement(before + k * reading, p0, a, e, NU, mc.phi_deg, mc.c) for k in (1.0, 2 / 3)]
        out.append({"chainage": r["chainage"], "class": r["GSI_flysch_class_or_BIM"], "gsi": gsi, "p0": p0, "L": length,
                    "reading_mm": reading * 1000, "phi": mc.phi_deg, "c": mc.c, "rp": free.r_p / a, "u_free_mm": free.u * 1000,
                    "after_station_mm": (free.u - before) * 1000, "p_installed": pi, "p_need": need,
                    "e_source": e, "e_hd2006": hoek_brown(gsi, MI, sci, 0.0, EI).e_rm})
    return out


if __name__ == "__main__":
    rows = sections()
    print("| Section | Class | GSI | P0 MPa | Reading (radial) mm | Unsupported after the station mm | R_p / a | Support needed MPa | Installed MPa | Share mobilised |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        lo, hi = r["p_need"][0], r["p_need"][1]
        print(f"| {r['chainage']} | {r['class']} | {r['gsi']:.0f} | {r['p0']:.2f} | {r['reading_mm']:.0f} | {r['after_station_mm']:.0f} | {r['rp']:.2f} | "
              f"{lo:.2f}–{hi:.2f} | {r['p_installed']:.1f} | {lo / r['p_installed']:.0%}–{hi / r['p_installed']:.0%} |")
    nb = [r for r in rows if r["class"] != "BIM"]
    print(f"\nFlysch sections (no block-in-matrix), n = {len(nb)}: support needed / installed, median "
          f"{st.median(r['p_need'][0] / r['p_installed'] for r in nb):.2f} (all deformation time-independent) to "
          f"{st.median(r['p_need'][1] / r['p_installed'] for r in nb):.2f} (one third time-dependent); maximum "
          f"{max(r['p_need'][1] / r['p_installed'] for r in rows):.2f}.")
    print(f"Unsupported convergence after the station / reading, median {st.median(r['after_station_mm'] / r['reading_mm'] for r in nb):.2f}.")
    print(f"Hoek-Diederichs (2006) modulus with E_i 20 GPa / source modulus, median {st.median(r['e_hd2006'] / r['e_source'] for r in rows):.2f}.")
