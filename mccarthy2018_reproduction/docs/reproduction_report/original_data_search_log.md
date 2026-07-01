# McCarthy 2018 Original Data Search Log

Purpose: record the bounded Route A search for public McCarthy 2018 quasi-DRO
branch data, initial states, appendix tables, official code, and digitization
fallback sources. Negative evidence is recorded explicitly. Related papers and
third-party code are not treated as McCarthy original data.

Search date for this Route A pass: 2026-07-01.

## Search Records

| search_date | query/source | checked_url_or_resource | target_data | result | useful_for | next_action |
|---|---|---|---|---|---|---|
| 2026-07-01 | Purdue Hammer thesis record | https://hammer.purdue.edu/articles/thesis/Characterization_of_Quasi-Periodic_Orbits_for_Applications_in_the_Sun-Earth_and_Earth-Moon_Systems/7423658 | supplementary files, attachments, metadata, raw branch data, code | partial: thesis landing page found; page exposes one 14.12 MB thesis download and thesis metadata; no visible supplementary branch data or code | primary thesis source, figure captions, method wording | verify through Figshare API metadata |
| 2026-07-01 | Purdue Hammer / Figshare API metadata | https://api.figshare.com/v2/articles/7423658 | machine-readable file list, related materials, linked files, folder structure | not found: API lists only `thesisMcCarthySubmit.pdf` with MD5 `639af424a0993034c429cc4bec7790ae`; `folder_structure`, `references`, and `related_materials` are empty; `has_linked_file=false` | strong negative evidence for public supplementary files attached to the Hammer record | stop Hammer attachment search unless a new version appears |
| 2026-07-01 | Purdue Howell conference publications page | https://engineering.purdue.edu/people/kathleen.howell.1/Publications/conferences.html | McCarthy AAS papers, presentation, data links | partial: page now renders as a compact publication archive notice; search results and direct links still expose AAS PDFs, but no data-table links were found | related paper discovery | use direct Purdue PDF links for specific papers; do not infer data availability |
| 2026-07-01 | Purdue Howell McCarthy thesis mirror | https://engineering.purdue.edu/people/kathleen.howell.1/Publications/Masters/2018_McCarthy.pdf | thesis mirror, possible high-resolution PDF | access issue: direct Purdue mirror redirects to the Howell landing page / site-under-construction response in the current browser check | redundant thesis source only | rely on Hammer/local PDF; recheck later only if Hammer becomes unavailable |
| 2026-07-01 | McCarthy 2018 local thesis PDF | `../2018_McCarthy_拟周期轨道.pdf` | appendix tables, initial states, branch values, figure captions, coordinate ranges | partial: local PDF is available; text extraction reports 137 pages; no `Appendix` text hit; no embedded CSV or appendix branch table found in this bounded pass; Fig. 3.16/Fig. 3.17 captions and axes are usable for digitization | primary figure and method reference | use Fig. 3.17 for bounded 2D digitization; do not treat it as raw branch data |
| 2026-07-01 | McCarthy and Howell 2019 AAS paper | https://engineering.purdue.edu/people/kathleen.howell.1/Publications/Conferences/2019_AAS_McCHow.pdf | quasi-DRO branch data, mapping-time data, trajectory design data | partial: paper discusses quasi-DRO eclipse avoidance, insertion angles, epochs, ephemeris transition, and application figures; no thesis Fig. 3.16/3.17 branch table or official data file found | Chapter 5 interpretation and qualitative quasi-DRO application context | keep as related context only |
| 2026-07-01 | McCarthy and Howell 2021 AAS paper | https://engineering.purdue.edu/people/kathleen.howell.1/Publications/Conferences/2021_AAS_McCHow.pdf | BCR4BP QPO data, later branch conventions, BCR4BP continuation details | partial: paper exposes BCR4BP formulation details and notes that free variables/constraints are summarized by McCarthy; it cites the 2018 thesis but does not expose McCarthy 2018 CR3BP quasi-DRO branch data | later-model method context and Route B notes | do not use for Fig. 3.16/3.17 raw-data substitution |
| 2026-07-01 | McCarthy and Howell 2022 AAS paper | https://engineering.purdue.edu/people/kathleen.howell.1/Publications/Conferences/2022_AAS_MccHow.pdf | quasi-periodic application data, transfer examples, branch conventions | partial: related application paper found; no public McCarthy 2018 quasi-DRO branch data or official code found in this bounded pass | Chapter 5 and later application framing | keep as background; do not upgrade Chapter 3 figures |
| 2026-07-01 | McCarthy 2021 journal article | https://www.sciopen.com/article/10.1007/s42064-020-0094-5 | cislunar quasi-periodic trajectory design data | partial: article record/abstract confirms quasi-periodic orbit application scope; no raw branch package found | peer-reviewed wording for applications | use only for context |
| 2026-07-01 | Olikara and Howell 2010 AAS paper | https://engineering.purdue.edu/people/kathleen.howell.1/Publications/Conferences/2010_AAS_OliHow.pdf | invariant-curve residual equations, continuation constraints, curve discretization details | partial: method paper found and useful for formulation audit; it is not McCarthy quasi-DRO branch data | Route B method note, residual/constraint comparison | extract equations only if Route B starts |
| 2026-07-01 | Olikara Purdue thesis record | https://docs.lib.purdue.edu/dissertations/AAI1489526/ | predecessor invariant torus thesis, discretization and continuation details | partial: thesis record/abstract found; describes discretized PDE plus constraints, continuation, fixed-Jacobi families; no McCarthy raw branch data | method provenance for invariant tori | use as method background only |
| 2026-07-01 | Olikara later thesis PDF | https://hanspeterschaub.info/Papers/grads/ZubinOlikara.pdf | collocation methods and heteroclinic connections | partial: related method thesis found; not McCarthy data | Route B formulation replacement references | use for method comparison only |
| 2026-07-01 | JPL periodic orbits API documentation | https://ssd-api.jpl.nasa.gov/doc/periodic_orbits.html | periodic orbit baseline, DRO initial conditions, Jacobi/period checks | partial: API provides periodic-orbit initial conditions, Jacobi, period, and stability fields; no quasi-periodic torus branch data | independent periodic DRO/halo baseline checks | use for periodic baseline only, not McCarthy quasi-periodic branch data |
| 2026-07-01 | GitHub API search: `McCarthy quasi periodic orbit Howell` | https://api.github.com/search/repositories?q=McCarthy%20quasi%20periodic%20orbit%20Howell | official code, branch data, third-party implementation | not found: `total_count=0` | negative evidence for public official repo | stop this exact query |
| 2026-07-01 | GitHub API search: `McCarthy Howell quasi-DRO` | https://api.github.com/search/repositories?q=McCarthy%20Howell%20quasi-DRO | official code, branch data, third-party implementation | not found: `total_count=0` | negative evidence for public official repo | stop this exact query |
| 2026-07-01 | GitHub API search: `quasi periodic orbit CR3BP McCarthy` | https://api.github.com/search/repositories?q=quasi%20periodic%20orbit%20CR3BP%20McCarthy | official code, branch data, third-party implementation | not found: `total_count=0` | negative evidence for public official repo | stop this exact query |
| 2026-07-01 | GitHub API search: `McCarthy 2018 quasi periodic orbit data` | https://api.github.com/search/repositories?q=McCarthy%202018%20quasi%20periodic%20orbit%20data | official code, branch data, third-party implementation | not found: `total_count=0` | negative evidence for public official repo | stop this exact query |
| 2026-07-01 | GitHub API search: `Olikara Howell invariant tori code` | https://api.github.com/search/repositories?q=Olikara%20Howell%20invariant%20tori%20code | official Olikara/Howell implementation | not found: `total_count=0` | negative evidence for public predecessor code through this query | stop this exact query |
| 2026-07-01 | GitHub API search: `quasi-DRO fixed mapping time data` | https://api.github.com/search/repositories?q=quasi-DRO%20fixed%20mapping%20time%20data | quasi-DRO branch data or fixed-mapping implementation | not found: `total_count=0` | negative evidence for public branch-data repo | stop this exact query |
| 2026-07-01 | General web search for third-party QPO repositories | https://github.com/dlujan17/QPOs | third-party implementation | partial: `dlujan17/QPOs` exists and describes code to compute quasi-periodic orbits in Julia/MATLAB/Python; it is not McCarthy official code and no McCarthy branch data were identified | possible method comparison only | do not cite as original data |
| 2026-07-01 | Fig. 3.17 digitization fallback | `outputs/reference_pages/fig_3_17_reference.png` | digitized rho-amplitude and rho-Jacobi trend points | found as fallback: 871x407 reference image supports traceable 2D color-threshold digitization; axis/pixel calibration is recorded separately | bounded comparison against accepted corrected branch | use only as lower-authority reference trend |
| 2026-07-01 | Fig. 3.16 digitization feasibility | `outputs/reference_pages/fig_3_16_reference.png` | 3D torus surface coordinates | not suitable: static perspective 3D rendering cannot provide precise 3D coordinates without camera/model metadata; only qualitative annotations are defensible | feasibility note and limited annotations | do not fabricate 3D data |

## Route A Search Conclusion

The bounded Route A search did not find McCarthy 2018 original quasi-DRO branch
data, initial states, appendix tables, thesis-specific supplementary files, or
official code. The strongest negative evidence is the Purdue Hammer/Figshare API
record: it lists only the thesis PDF and no related files or linked material.
Purdue/Howell pages and related AAS/journal papers provide useful context and
method references, but they do not expose Fig. 3.16/Fig. 3.17 raw branch data.
The JPL API remains useful for periodic-orbit baselines only. GitHub API
searches for the required queries returned zero repository matches; the one
general third-party QPO repository found by web search is not McCarthy original
data.

Therefore Fig. 3.17 digitization is a lower-authority reference-trend fallback,
not a replacement for raw branch data. Fig. 3.16 is not suitable for precise 3D
digitization from the static image. Neither digitized trend points nor Fig. 3.16
annotations upgrade Fig. 3.16/Fig. 3.17 from partial physical-consistency
baseline to full numerical reproduction.
