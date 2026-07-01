# McCarthy 2018 原始数据搜索日志

目的：把 Route A 搜索变成有限、可追溯的记录。该日志用于记录 public branch data、initial states、appendix tables、official code、high-resolution figures 或 digitization fallback 的查找过程。当前条目为初始记录，不表示已完成无限搜索。

## Search Template

| search_date | query/source | checked_url_or_resource | target_data | result | useful_for | next_action |
|---|---|---|---|---|---|---|
| YYYY-MM-DD | search query, paper title, repository query, or database source | URL, local file, API endpoint, library record, or repository search page | branch data / initial states / appendix tables / code / high-resolution figure / method detail | found / not found / partial / access issue | Fig. or chapter relevance | follow-up action or stop condition |

## Initial Entries

| search_date | query/source | checked_url_or_resource | target_data | result | useful_for | next_action |
|---|---|---|---|---|---|---|
| 2026-07-01 | Purdue Hammer thesis record | https://hammer.purdue.edu/articles/thesis/Characterization_of_Quasi-Periodic_Orbits_for_Applications_in_the_Sun-Earth_and_Earth-Moon_Systems/7423658 | McCarthy 2018 thesis PDF, supplementary files, branch data, appendix tables | Thesis record / PDF source identified; no machine-readable branch data or official code recorded in current project notes | Primary thesis text, figure intent, equations, terminology, figure classification | Recheck attachments / metadata once; if no supplement exists, mark as negative evidence and proceed to digitization planning |
| 2026-07-01 | Purdue Howell publication page | https://engineering.purdue.edu/people/kathleen.howell.1/Publications/masters.html | Howell group thesis listing, McCarthy thesis mirror, related theses | Useful discovery route; no confirmed McCarthy numerical data table in current project notes | Locating thesis mirrors and predecessor method documents | Recheck for page changes and direct links; record whether McCarthy or Olikara pages expose data beyond PDFs |
| 2026-07-01 | McCarthy 2018 thesis PDF | `C:/Users/wwh20/Desktop/复现论文/2018_McCarthy_拟周期轨道.pdf`; also candidate mirror `https://engineering.purdue.edu/people/kathleen.howell.1/Publications/Masters/2018_McCarthy.pdf` | Figure captions, algorithm descriptions, possible appendix values, high-resolution figure content | Local PDF is available as primary text; no embedded CSV / branch table confirmed in current project notes | Fig. 3.10, Fig. 3.16/3.17, Chapter 4, Chapter 5 interpretation | Inspect appendix / figure pages for digitization targets; do not assume raw data exists |
| 2026-07-01 | McCarthy/Howell 2019 AAS paper | https://engineering.purdue.edu/people/kathleen.howell.1/Publications/Conferences/2019_AAS_McCHow.pdf | Quasi-DRO application data, mapping-time resonance, Chapter 5-style trajectories | Related application paper identified; not a substitute for thesis branch data in current notes | Chapter 5 interpretation; quasi-DRO application context | Use for wording and application motivation only unless explicit numerical tables are found |
| 2026-07-01 | McCarthy/Howell 2021 AAS paper | https://engineering.purdue.edu/people/kathleen.howell.1/Publications/Conferences/2021_AAS_McCHow.pdf | BCR4BP QPO data, later quasi-periodic orbit stability and application material | Related later-model paper identified; not McCarthy 2018 CR3BP quasi-DRO branch data | Chapter 5 / BCR4BP future work framing | Keep as Route B/C reference; do not use it to overwrite thesis targets |
| 2026-07-01 | Olikara/Howell 2010 paper | https://engineering.purdue.edu/people/kathleen.howell.1/Publications/Conferences/2010_AAS_OliHow.pdf | Invariant-curve method details, continuation constraints, predecessor QPO examples | Method source identified; not target quasi-DRO branch data | Fig. 3.16/3.17 formulation audit; Route B method comparison | Extract residual equations / constraints for formulation note if Route B starts |
| 2026-07-01 | JPL periodic orbits API | https://ssd-api.jpl.nasa.gov/doc/periodic_orbits.html | Earth-Moon periodic orbits, halo / DRO baseline states, period and Jacobi checks | API is useful for periodic orbit baselines only; no quasi-periodic torus branch data | Fig. 3.10 periodic seeds; DRO base validation for Fig. 3.16/3.17 | Use for independent periodic-orbit sanity checks; do not treat as McCarthy QPO data |
| 2026-07-01 | GitHub search for McCarthy quasi-periodic orbit data | GitHub queries such as `McCarthy quasi periodic orbit Howell`, `McCarthy Howell quasi-DRO`, `quasi periodic orbit CR3BP McCarthy data` | Official code repository, branch data, reproduction data, third-party implementation | No official McCarthy data repository confirmed in current project notes; third-party QPO repositories must not be treated as original data | Possible method comparison or implementation hints | Run bounded GitHub search and record exact queries / negative evidence before relying on digitization |
| 2026-07-01 | Figure digitization fallback for Fig. 3.16/3.17 | Local PDF figures and `outputs/reference_pages/fig_3_16_reference.png`, `outputs/reference_pages/fig_3_17_reference.png` | Digitized amplitude / rho / Jacobi trends and surface reference points | Fallback route only; digitized curves are lower authority than raw branch data | Fig. 3.16/3.17 trend comparison and proxy-boundary documentation | Use only after Route A raw-data search is bounded; record tool, calibration points, pixel uncertainty, and extracted values |

## Logging Rules

- Record negative evidence explicitly; “not found” is useful when the checked source is central.
- Separate original McCarthy data from related method papers and third-party code.
- Do not upgrade Fig. 3.16/3.17 based only on digitized proxy trends.
- For each future search, include exact query text, date, checked URL/resource, and whether raw data, code, or only paper-level text was found.
- Stop Route A when the main Purdue/Hammer/Howell/AAS/GitHub/API routes are checked and no new source appears, then decide between digitization and Route B.
