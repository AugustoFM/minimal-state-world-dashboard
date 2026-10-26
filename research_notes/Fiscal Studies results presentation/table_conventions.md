# Fiscal Studies Table Conventions for Monte Carlo / Distributional Output

**Methodological note on access:** Wiley Online Library blocks automated fetches of *Fiscal Studies* (403/429 errors on every direct attempt), so paywalled journal PDFs could not be read directly in this session. Where a free IFS/IZA working-paper "twin" existed, its PDF was downloaded and converted to text with `pdftotext -layout`, then inspected line-by-line — this gives verified, quoted table content. Where no free twin was found, findings are explicitly marked as abstract-level or as drawn from closely related IFS house-style documents (same authors, same TAXBEN microsimulation model, same "Notes:/Source:" footnote convention) rather than from the *Fiscal Studies* article itself. This distinction is flagged in every finding below.

Directly verified primary source: **O'Donoghue, C., Sologon, D.M., Kyzyma, I. and McHale, J. (2020), "Modelling the Distributional Impact of the COVID-19 Crisis," *Fiscal Studies*, 41(2), pp. 321–336**, DOI 10.1111/1475-5890.12231 — confirmed published in *Fiscal Studies*; full text read via its free IZA working-paper twin, Discussion Paper 13235 (https://www.iza.org/publications/dp/13235), PDF at the paper's distribution mirror, text-extracted and read directly (tables quoted below).

Stylistic-proxy sources (NOT themselves *Fiscal Studies* journal articles, but produced by the same IFS research group, using the same microsimulation model (TAXBEN) and the same footnote/table house style that IFS authors carry into their *Fiscal Studies* articles — used here only to characterize layout conventions, clearly labeled as such):
- Brewer, M., Browne, J. and Joyce, R. (2011), *Child and Working-age Poverty from 2010 to 2020*, IFS Commentary C121 (https://www.ifs.org.uk/sites/default/files/output_url_files/comm121.pdf) — full text read directly.
- Adam, S. and Browne, J. (2010), *Redistribution, Work Incentives and Thirty Years of UK Tax and Benefit Reform*, IFS Working Paper 10/24 (https://ifs.org.uk/sites/default/files/output_url_files/wp1024.pdf) — full text read directly; publication status in the *Fiscal Studies* journal could not be confirmed (see Gaps), so this is treated as an IFS working paper only, not a confirmed journal twin.

Confirmed-but-unread journal citations (bibliographic details verified; tables not accessible this session):
- Brewer, M., Browne, J. and Jin, W. (2012), "Universal Credit: A Preliminary Analysis of its Impact on Incomes and Work Incentives," *Fiscal Studies*, 33(1), pp. 39–71, DOI 10.1111/j.1475-5890.2012.00152.x.
- Balladares, S. and García-Miralles, E., "Fiscal Drag with Microsimulation: Evidence from Spanish Tax Records," *Fiscal Studies*, EarlyView (2025/26); free working-paper twin IEB Working Paper 2025/08 exists but returned HTTP 429/404 on every fetch attempt in this session.

---

## When presenting p10/p50/p90-style output, are percentiles separate columns, a single "p50 [p10,p90]" cell, or separate rows?

### Takeaway
In every table actually viewed, the IFS/Fiscal-Studies convention is **scenarios or time periods as rows**, with the distributional dimension (deciles, income-level breakdowns, or inequality measures) broken out as **separate labeled rows or row-blocks**, not as a single bracketed "median [low, high]" cell and not normally as columns-per-percentile for policy-scenario comparisons. Where deciles ARE the object of analysis (as opposed to scenario uncertainty), deciles run down the first column as rows, with income/outcome measures as the column headers.

### Cited Findings
- In O'Donoghue et al. (2020, *Fiscal Studies* 41(2)), Table 9 ("Distributional characteristics of income before and during crisis") is laid out with **"Decile" as the leftmost row label (1 through 10, plus a "Total" row)**, and columns for each income concept ("Market income / Gross income / Disposable income / Disposable income* / Benefits / Taxes / Housing and work expenses") repeated for "Before Crisis" and "During crisis" — i.e., deciles are rows, income concepts are column groups, and the two time periods are nested column sub-groups. — [IZA DP13235 PDF text, p.14, Table 9]
- In the same paper, Table 10 ("Change in distributional characteristics of income before and during crisis") again has deciles 1–10 as rows and income-concept columns, with an added bottom row "% change" that is the Total row expressed as a percentage rather than a level. — [IZA DP13235 PDF text, p.15, Table 10]
- Table 15 ("Gini coefficient before and during crisis") in the same paper uses **income concepts as columns** ("Market income / Gross income / Disposable income / Disposable income*") and **"Before Crisis" / "During crisis" / "Change" as stacked rows** underneath a single "Gini" row label — i.e. three percentile/summary-statistic-like rows stacked per column, not separate columns per statistic. — [IZA DP13235 PDF text, p.19, Table 15]
- In the IFS Commentary C121 (Brewer, Browne and Joyce, 2011), the poverty-projection tables (3.1–3.10) put **years (or named scenarios) as rows** and **demographic group × (Millions, %) pairs as column groups**, with a final "Real annual median income growth (%)" column — e.g. Table 3.7 has row labels "2015", "2020:", then indented sub-rows "Baseline", "High earnings growth", "100,000 fall in no. of workless households", etc. — [IFS Commentary C121 PDF text, p.18, Table 3.7]
- No table viewed in either source used a single composite cell format like "18.3 [17.5, 20.0]" to show a central estimate with a low/high range; every uncertainty or scenario comparison used separate rows (scenarios) or separate tables (sensitivity analysis), never bracketed interval notation inside one cell. — [IZA DP13235 and IFS Commentary C121 PDF text, all tables reviewed]

### Inferences
- For the target paper's p10/median/p90 Monte Carlo output, the house convention most consistent with these examples would be: **scenarios (baseline, moderate/ambitious reduction, moderate/ambitious expansion) as rows**, and if percentiles are shown at all per scenario, they would most likely appear as **three separate numeric sub-columns or a compact "median (p10–p90)" prose aside rather than a bracket inside a single cell**, since none of the tables viewed used bracket notation. A simpler and more consistent-with-house-style option is to show the median as the primary cell value and relegate p10/p90 to a lighter-weight secondary row or an explicit separate "range" column, following the Table 15 pattern of stacking "Before/During/Change" as rows under one column header.

### Gaps
- No table found in this research actually reports Monte Carlo percentiles (p10/p50/p90) in the strict sense used in the target paper — IFS/*Fiscal Studies* tables viewed show scenario sensitivity (discrete named scenarios) or empirical deciles of a cross-sectional distribution, not simulation-based percentile bands of a single scalar outcome over repeated draws. This is a genuine gap: no Fiscal Studies table with "10th percentile / median / 90th percentile" column or row triplet was located and confirmed in this session.

---

## How many scenarios and horizons do they typically show in one table before splitting into multiple tables or moving detail to an appendix?

### Takeaway
IFS/Fiscal-Studies-style tables tend to keep a **single structural dimension (e.g., either scenarios OR years) compact — around 3–9 rows** — and push additional structural splits (e.g., before-housing-costs vs. after-housing-costs, or relative vs. absolute poverty) into **separate, parallel tables** (e.g. Tables 3.7/3.8/3.9/3.10) rather than cramming multiple dimensions into one table; true sensitivity/robustness variants are isolated into a distinct later section ("4. Sensitivities") with its own small tables.

### Cited Findings
- IFS Commentary C121's main projection table (Table 3.7) has 9 scenario rows (2015 baseline-year row, "2020:" header row, then 8 named 2020 scenarios: Baseline, High earnings growth, four workless-household variants, Non-take-up of UC halved, Full take-up of UC, Without UC) and the authors still split BHC and AHC, and relative vs. absolute poverty, into four separate but parallel tables (3.7, 3.8, 3.9, 3.10) rather than merging them. — [IFS Commentary C121 PDF text, pp.18–21, Tables 3.7–3.10]
- The explicit sensitivity analysis is deferred to a later, separate chapter ("4. Sensitivities") with its own much smaller tables (Table 4.1 has 2 scenario rows — Progressive/Regressive; Tables 4.2 and 4.3 have 5 scenario rows — Baseline, High employment and earnings, Low employment and earnings, Progressive earnings growth, Regressive earnings growth), each restricted to a single year (2015) rather than showing multiple horizons at once. — [IFS Commentary C121 PDF text, pp.27–29, Tables 4.1–4.3]
- Table 3.1 (the baseline year-by-year table) shows 6 years as rows (2008–2013) in one table, split into two row-blocks ("before housing costs" / "after housing costs") rather than adding housing-cost basis as a further column dimension. — [IFS Commentary C121 PDF text, p.10, Table 3.1]
- O'Donoghue et al. (2020, *Fiscal Studies*) keeps each table to one outcome/time slice: Table 9 shows deciles × two time points (before/during crisis) for multiple income concepts; Table 15 condenses the inequality analysis into one compact table with 4 income-concept columns and 3 rows, rather than a sprawling multi-panel table. — [IZA DP13235 PDF text, pp.14,19, Tables 9 and 15]

### Inferences
- A workable rule of thumb consistent with these examples: keep any one table to roughly **one cross-cutting dimension at "full" granularity (e.g., all scenarios, or all deciles) times one or two other dimensions shown as column headers**, and if a third structural split is needed (e.g., both BHC/AHC and relative/absolute poverty, as in C121), produce **parallel sister tables** rather than one giant table. For the target paper with 5 scenarios × 4 horizons × 3 percentiles, this suggests either (a) one table per horizon with scenarios as rows and percentiles as columns, or (b) one table per outcome variable with scenario×horizon as rows and percentile columns — not a single table trying to show all three dimensions plus all outcome variables at once.

### Gaps
- Could not confirm a hard numeric cutoff (e.g., "no more than N rows") that *Fiscal Studies*' style guide enforces; this is inferred from table practice in two IFS-house documents, not from an explicit style guide. The target paper's structure (2 reduction scenarios + 2 expansion scenarios + baseline, across 4 horizons, for 3 outcome variables) is larger than any single table seen in this research, which — by the pattern above — argues for splitting by outcome variable or by horizon rather than one mega-table.

---

## Do they use bold, shading, or other visual emphasis for headline rows/columns (e.g. median or baseline scenario)?

### Takeaway
Text-only extraction cannot reliably confirm bold/shading, but the one visual cue consistently recoverable from the text layer is that **the baseline/central scenario is given a distinct row label ("Baseline", "Central scenario") positioned first among the alternative-scenario rows**, directly below the relevant year header, functioning as a visual/structural anchor even if true bold/shading cannot be confirmed from plain text.

### Cited Findings
- In IFS Commentary C121, Table 3.3 uses the row label "Central scenario" immediately under the current year, and Table 3.7 uses "Baseline" immediately under "2020:" as the first scenario row before the alternative scenarios — in both cases placed first in the scenario block, a conventional "anchor row" position regardless of literal bolding. — [IFS Commentary C121 PDF text, p.13 and p.18, Tables 3.3 and 3.7]
- In Table 4.2, the row order is "Baseline" first, then "High employment and earnings", "Low employment and earnings", "Progressive earnings growth", "Regressive earnings growth" — again baseline-first ordering. — [IFS Commentary C121 PDF text, p.28, Table 4.2]
- The PDF font metadata for the Adam & Browne IFS working paper (WP10/24) shows headings/table captions set in a distinct font ("Cisalpin LT Std, Bold") from body text (Cambria), consistent with table titles (not necessarily specific rows) being bolded; this is a structural/metadata-level observation, not a direct view of the rendered page. — [WebFetch metadata extraction of ifs.org.uk/sites/default/files/output_url_files/wp1024.pdf]

### Inferences
- Because the research tooling available in this session can only reliably extract text, not rendered visual styling (color, shading, boldface), this question cannot be answered with full confidence from primary sources. Based on general familiarity with how Wiley/IFS output renders (table titles bold, column headers bold, data cells plain), it is reasonable to expect that *Fiscal Studies* follows the common academic-journal norm of **bolding table titles and column headers only**, not data rows — but this is an inference about general Wiley house style, not a verified observation of a specific *Fiscal Studies* table in this session.

### Gaps
- No direct visual (rendered/rasterized) inspection of an actual *Fiscal Studies* table was possible in this session (PDF rendering tools were unavailable; only text extraction via `pdftotext -layout` succeeded). This is the single biggest gap in this research: **whether the journal uses bold/shading for baseline rows, median columns, or headline results is not confirmed one way or the other** and should be checked by a human directly viewing a recent PDF issue of the journal, or treated as "unknown — use plain structural anchoring (ordering, row labels) rather than relying on visual bold/shading" as a conservative design choice.

---

## How do they handle unit labeling (percentage points vs percent vs levels) in table headers vs footnotes?

### Takeaway
Units are placed **in the column header itself** (e.g., "%", "Millions", "(%)", "€ per month per adult equivalent" in the table title) rather than relegated to a footnote; footnotes are reserved for definitions of composite/derived variables (e.g., what "Disposable income*" means) and for data/methodology sourcing, not for basic unit disclosure.

### Cited Findings
- IFS Commentary C121's poverty tables header each relevant column pair directly as "Millions" and "%" (e.g. "Children [Millions] [%]"), and the final column is explicitly labeled "Real annual median income growth (%)" in the column header itself — no separate footnote is needed to say the final column is a percentage. — [IFS Commentary C121 PDF text, pp.10,18, Tables 3.1, 3.7]
- The table title itself sometimes carries the unit when the whole table is in one unit, e.g. Table 10's title is "Change in distributional characteristics of income before and during crisis (€ per month per adult equivalent)" — the unit sits in parentheses in the title line, not in a footnote. — [IZA DP13235 PDF text, p.15, Table 10]
- Footnotes are used instead for defining composite variables and flagging what differs from the simple reading of the column header: "Note: Disposable income* stands for household equivalized disposable income adjusted for housing, work related expenses and capital losses. Deciles in the first column are defined within the distribution of household equivalized disposable income adjusted for housing, work related expenses and capital losses. The last line shows the percentage change in each type of income during the crisis compared to the pre-crisis level." — [IZA DP13235 PDF text, p.15, Table 10 notes]
- IFS Commentary C121 footnotes define the poverty line and the accounting period rather than units: "Notes: Poverty line is 60% of median income. Years refer to financial years." — [IFS Commentary C121 PDF text, p.10, Table 3.1 notes]

### Inferences
- The target paper's tables (percentage-point changes in Gini/poverty rate vs. levels of debt/GDP) should follow this pattern: put "(percentage points)" or "(% of GDP)" directly in the column header or in the table title's parenthetical, and reserve footnotes for defining any adjusted/composite measure (e.g., "Gini coefficient change" meaning change relative to the no-reform baseline) and for the data/model source line, not for stating the basic unit.

### Gaps
- None significant for this question — the pattern was consistent and corroborated across both sources reviewed.

---

## Do they include notes/footnotes explaining methodology, data sources, or caveats, and how long are they typically?

### Takeaway
Every table reviewed carries a **two-line footnote block**: a short "Notes:" line (1–3 sentences, defining the poverty line, rounding, scope exclusions, or composite-variable definitions) immediately followed by a separate "Source:" line (1 sentence, naming the data set and the microsimulation model/method) — footnotes are terse, not multi-paragraph, with deeper methodological explanation left to the main text (often cross-referenced, e.g. "the `scenarios' are defined in the text").

### Cited Findings
- Standard two-line pattern: "Notes: Poverty line is 60% of median income. Years refer to financial years. / Source: Authors' calculations based on Family Resources Survey, 2008–09, using TAXBEN and assumptions specified in the text." — [IFS Commentary C121 PDF text, p.10, Table 3.1]
- When a table repeats an already-stated note, IFS abbreviates rather than restating it in full: "Note: As Table 4.2. / Source: As Table 4.2." — [IFS Commentary C121 PDF text, p.29, Table 4.3]
- Minimal, pointer-style notes are acceptable rather than exhaustive explanation: "Note: The `scenarios' are defined in the text." — [IFS Commentary C121 PDF text, p.28, Table 4.2]
- In the Adam & Browne IFS working paper, footnotes define sample scope and technical exclusions tersely, e.g.: "Notes: Calculations for personal direct and indirect taxes and benefits only: excludes [business taxes]" and "Note: Figures may not sum due to rounding." and "Note: Gini coefficients are for post-tax income, after direct and indirect personal taxes [...]" each followed by a one-line "Source: Authors' calculations using the IFS tax and benefit micro-simulation model, [dataset]." — [IFS WP10/24 PDF text, lines ~298–1113]
- In O'Donoghue et al. (2020, *Fiscal Studies*), the note under the Gini table (Table 15) is a single sentence: "Note: Disposable income* stands for household equivalized disposable income adjusted for housing, work related expenses and capital losses." — [IZA DP13235 PDF text, p.19, Table 15]

### Inferences
- For the target paper, footnotes should stay short: one line defining any derived/adjusted variable (e.g. what "ambitious expansion scenario" or "Gini coefficient change" precisely means, if not obvious from the column header) plus one line citing the data/model source (e.g., the specific Monte Carlo microsimulation model and number of draws) — following the terse "Notes:/Source:" two-liner rather than a long caveats paragraph. Deeper caveats (e.g., limitations of the Monte Carlo approach) belong in the main text, with the table footnote at most pointing back to it ("see Section X" / "scenarios are defined in the text").

### Gaps
- None significant — this pattern was highly consistent across both sources, though it is worth noting both exemplars are IFS-authored; whether non-IFS authors publishing in *Fiscal Studies* (e.g., the Balladares & García-Miralles Spanish fiscal-drag paper, or other non-UK contributors) follow an identical terse two-line convention could not be confirmed, since that paper's PDF could not be retrieved in this session (HTTP 429 then 404 on the two available mirrors).

---

## Do they ever combine a "baseline" and "difference from baseline" column/row in the same table, and if so how is that laid out?

### Takeaway
Yes — the clearest confirmed example lays this out as **stacked rows under each column header: "Before Crisis" (baseline level), "During crisis" (level), "Change" (the difference)** — i.e., baseline and difference share the same column (same unit/variable), distinguished by row label, rather than baseline and difference appearing in adjacent columns.

### Cited Findings
- Table 15 in O'Donoghue et al. (2020, *Fiscal Studies*) is headed by column labels "Market income / Gross income / Disposable income / Disposable income*", and under each, three stacked rows appear in order: "Before Crisis" (e.g. 0.499), "During crisis" (e.g. 0.578), "Change" (e.g. 0.079) — the difference-from-baseline value sits directly beneath the two levels it was computed from, in the same column. This exact row-stacking repeats for the "Redistribution" panel below it (Benefits/Taxes/Work-related and housing costs columns, with Before Crisis / During crisis / Change rows). — [IZA DP13235 PDF text, p.19, Table 15]
- Table 10 in the same paper is explicitly a "Change" table (title: "Change in distributional characteristics of income before and during crisis"), paired with the preceding Table 9, which gives the "Before Crisis" and "During crisis" levels — here the baseline/level table and the difference table are two separate, adjacent tables (9 then 10) rather than one combined table, which is the alternative layout pattern observed. — [IZA DP13235 PDF text, pp.14–15, Tables 9 and 10]
- In IFS Commentary C121's scenario tables (e.g. Table 3.7), each alternative scenario row shows the scenario's own level (e.g. a poverty rate of 18.2% under "100,000 fall in no. of workless households"), and the reader is expected to subtract the adjacent "Baseline" row's value to get the difference — i.e., **no explicit "difference from baseline" column is printed**; the comparison is left implicit, to be computed by the reader or discussed in prose in the surrounding text (e.g. "relative child poverty would increase by a further 300,000... between 2013 and 2015"). — [IFS Commentary C121 PDF text, pp.13,18, Tables 3.3, 3.7 and surrounding prose]

### Inferences
- Two distinct, both IFS/Fiscal-Studies-attested layouts exist: (1) a **compact single table** with baseline/during/change as stacked rows under shared column headers (Table 15 pattern) — best when there are few row-levels and few columns; and (2) **two parallel tables**, one of levels and one of differences (Tables 9/10 pattern) — best when there are many rows (e.g. deciles) and the paired table would otherwise be unwieldy. For the target paper's scenario-by-horizon structure, the Table 15 "stacked rows" pattern (baseline level, scenario level, and an explicit "difference" row, all under the same outcome-variable column) is probably the better fit, since the scenario-vs-baseline comparison is a key number readers will want without doing arithmetic — unlike the IFS Commentary tables, which leave the subtraction implicit and explain it only in prose.

### Gaps
- Did not find a confirmed *Fiscal Studies* (or twin) table that shows baseline and difference **side-by-side as adjacent columns** (e.g., "Baseline" column next to a "Δ vs baseline" column) — only the stacked-rows pattern and the separate-tables pattern were directly observed. It remains unconfirmed whether a column-pair layout is ever used in the journal; this should be treated as an open design choice rather than a confirmed convention either way.

---

## Additional general/background facts (not tied to one key question)

### Cited Findings
- *Fiscal Studies* is a quarterly, peer-reviewed economics journal published by Wiley on behalf of the Institute for Fiscal Studies (IFS); it is hybrid open access (authors may pay for individual-article open access, otherwise content is subscription-only), which is why most full-text retrieval attempts in this session returned HTTP 403. — [Fiscal Studies - Wikipedia](https://en.wikipedia.org/wiki/Fiscal_Studies)
- A 2026-volume *Fiscal Studies* article, "Fiscal drag with microsimulation: evidence from Spanish tax records" (Balladares & García-Miralles), confirms the journal continues to publish microsimulation/counterfactual-simulation papers with distributional (by income source and by position in the income distribution) results as of 2025/26 — directly relevant to the target paper's genre, but its tables could not be retrieved in this session (two working-paper mirror URLs returned HTTP 429 and 404 respectively). — [IEB Working Paper 2025/08 listing](https://ideas.repec.org/p/ieb/wpaper/doc2025-08.html)

### Gaps
- A plausible close genre-match, Ball, Creedy and Scobie's non-parametric stochastic fiscal-projection modelling for New Zealand, was traced to the *Australian Economic Review* (2016, vol. 49(1), pp. 59–76), **not** *Fiscal Studies* — flagged explicitly so it is not mistaken for a *Fiscal Studies* example; its NZ Treasury working-paper twin (WP 15/10) was located but not read in this session, so it is not included as evidence above.
- This session could not confirm whether genuine Monte-Carlo-percentile (p10/p50/p90, in the repeated-random-draw sense) tables exist anywhere in the *Fiscal Studies* back-catalogue; all confirmed/viewed examples use discrete named scenarios or empirical sample deciles rather than simulated percentile bands. A dedicated follow-up search specifically for *Fiscal Studies* articles on long-run debt sustainability, demographic/ageing fiscal projections, or defined-contribution pension outcomes (genres where Monte Carlo percentile fan charts are more standard, per OBR and EU Commission practice) would be needed to close this gap, ideally with direct Wiley Online Library access rather than general web search.
