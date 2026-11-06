# Release 1 audit

- **Run on:** 6 Nov 2026, on main after `7153858`
- **Scope:** every tracked file (345), the six demos, the model library, the presets, the scenarios and the documentation
- **Questions:**
  1. Is anything from the owner's system, or derived from it, in the repository?
  2. Does every value carry a source or an assumed label?
  3. Is cited data quoted only as numbers, with a link to an open source?

## Result

No finding is open. Five were found; four are fixed in the commit that adds this note, and one is accepted as it is.

| # | Finding | Fix |
|---|---|---|
| F1 | The EPB and Mixshield pages credited the building data as "(all OGL)" only. The Open Government Licence asks for the attribution statements, and the Thames river level from the Environment Agency had none | The pages now carry "Contains OS data © Crown copyright and database right 2026", the Environment Agency and Historic England statements, and the Environment Agency statement for the river level |
| F2 | The SEM page used BGS boreholes without the BGS attribution statement | "Open Government Licence v3.0; contains British Geological Survey materials © UKRI 2026" added |
| F3 | One preset value had no source: drill & blast `pull_fraction` 0.90–0.95, from search snippets only | Set to null with the reason. The code does not use it: pull comes from the drilled depth and the empty-hole design |
| F4 | About 20 cited works had no URL or DOI anywhere in the repository, among them the CSM disc-cutter model and the Hoek–Brown references | DOIs checked in Crossref for Anagnostou & Kovári 1996, Davis et al. 1980, Hoek & Diederichs 2006, Carranza-Torres & Fairhurst 2000, Merritt & Mair 2006 and 2008, Yeh 1997 (year corrected from 1996). Open copies linked for Rostami 1997 (thesis), Hoek et al. 2002 (authors' pre-print), EFNARC 2005 (free download), Mair, Taylor & Burland 1996 and Mair 1997 on the demo pages. Works with no open copy are marked "not openly published": Rostami & Ozdemir 1993, Farrokh 2013, Johnson 2014, Roby & Willis 2014, McMillan et al. 2022. Mueller-Kirchenbauer 1977, Krause 1987, Mair 1989 and Cunningham 1987 are cited through the open sources that give their relations |
| F5 | About 69 background works in the [research survey](research/research-survey.md) have no link of their own; the survey ends with a list of the source URLs it used | Accepted: the survey is background reading, not a model input |

## What was checked and passed

- **Owner's system:** no private paths, credentials, VPN files, SP200 data or `knowledge/private` content in any tracked file. The only company references are the intended public credits (initiator and maintainer). Server run records hold only the GPU name, load and driver, library versions and the git commit.
- **Third-party files:** none are redistributed. Tracked binaries are our own renders and one recorded MPM run. The scenario files carry open data under their licences (BGS, OS, Environment Agency and Historic England under the OGL; the OpenStreetMap line under the ODbL), with the licence text in each file.
- **Presets:** 80 fields in `models/presets/machine-classes.json`. Each has a source, or is null with a reason (6 are null); 7 values are marked unverified (secondary source). Every source key resolves to an entry with a URL or DOI.
- **Demo settings:** every numeric setting in the demos' configuration blocks carries a comment, meant to give its source or an "assumed" label (see Limits).
- **Quotations:** no passage of a source is reproduced; values are quoted as numbers with a link.

## Limits of this audit

- The comment check confirms that each demo setting has a comment, not that the comment names the right source. The [realism checklists](realism/) cover that per demo.
- Citations were found by an author–year pattern, so a work cited in another form could be missed.
- Licence terms were read for the data the repository carries. The licences of sources quoted only as numbers with a link (for example CC BY-NC-ND articles) were not re-checked one by one.
