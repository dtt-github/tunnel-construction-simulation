# Model catalogue

Implemented models. Each source file states its references, equations and units; this page is the index.

| Model | Python | JS | References | Validated against |
|---|---|---|---|---|
| CSM disc cutter: forces, penetration from thrust, ROP, torque (T ≈ 0.3·D·N·Fr), power, torque limit | `models/py/tunnelsim_models/csm.py` | `models/js/csm.js` | Rostami & Ozdemir (1993), Rostami (1997) | Hand calculation for a 19″ disc (p = 5 mm, UCS 150, BTS 10 → Ft ≈ 201 kN, RC ≈ 0.10). Field validation pending (Yinsong dataset) |
| Generalised Hoek–Brown (mb, s, a, σcm), rock-mass modulus | `hoek_brown.py` | `hoek_brown.js` | Hoek, Carranza-Torres & Corkum (2002); Hoek & Diederichs (2006) | Hand calculation (GSI 50, mi 10); intact limit GSI 100 → s = 1 |
| Gaussian settlement trough, horizontal displacement, longitudinal profile, Burland categories | `settlement.py` | `settlement.js` | Peck (1969); O'Reilly & New (1982); Attewell & Woodman (1982); Burland (1995) | Hand calculation (D 6 m, z0 20 m, VL 1 % → Smax 11.3 mm); numerical integration equals Vs |

## Default parameter sources

- [research/research-survey.md](research/research-survey.md): models, ranges, datasets, standards (with verification tags).
- [research/industry-survey.md](research/industry-survey.md): manufacturer spec numbers, such as disc cutter ratings of 267 kN (17″) and 311 kN (19″/20″), published machine power and torque, and world-record advance rates by diameter class.
