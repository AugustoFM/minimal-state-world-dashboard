# Fiscal Studies Figure Conventions for Simulation/Projection and Policy-Scenario Results

**Methodological note on access:** Fiscal Studies (Wiley/IFS) articles are paywalled on Wiley Online Library, and the Wiley abstract pages returned HTTP 403 to automated fetches in this research session. For several articles I could only retrieve bibliographic metadata and abstracts (via RePEc/IDEAS, IZA, or institutional repositories), not the rendered figures themselves — this is flagged explicitly below wherever a description is inferred rather than directly viewed. Free full-text "twin" working papers (the pre-publication version hosted by the authors' home institution) were fetched as PDFs, but the automated PDF-reading tool could only extract binary/structural metadata (fonts, page count, embedded image objects), not legible figure captions or chart contents, for the two PDFs attempted. No figure was directly viewed in this research session. All findings below are therefore sourced from abstracts, RePEc summaries, and journal-adjacent descriptions, not from inspecting rendered charts.

## Do Fiscal Studies papers use fan charts, shaded percentile-band ribbons, box plots, or simple line charts with error bars for uncertainty? Which is most common?

### Takeaway
The clearest confirmed example of probabilistic/uncertainty visualization in Fiscal Studies is a fan-chart methodology paper (Cronin and Dowd, 2013); for the journal's more numerous microsimulation/distributional papers, no direct evidence of fan charts, box plots, or error bars was found — these appear to more often report point estimates (e.g., Gini coefficients, income changes by group) without visualized uncertainty bands, based on the abstracts available. This is a significant gap: the dominant uncertainty-visualization convention across the broader Fiscal Studies corpus could not be established with confidence in this session.

### Cited Findings
- David Cronin and Kevin Dowd, "Fiscal Fan Charts: A Tool for Assessing Member States' (Likely?) Compliance with EU Fiscal Rules," *Fiscal Studies*, Institute for Fiscal Studies, vol. 34, pp. 517–534, December 2013, sets out a method for constructing fan charts of government deficit and debt ratios over a five-year medium-term horizon, using a stochastic model of real GDP passed through the fiscal arithmetic (dynamic deficit-debt relationship) — [IDEAS/RePEc record](https://ideas.repec.org/a/ifs/fistud/v34y2013ip517-534.html)
- The same paper produces two sets of fan charts for Ireland: a baseline set (no fiscal policy response, "a standard assumption for fan charts") based on the 2011 Stability/Convergence Programme Update, and a second set showing how the probability range of outcomes shifts if fiscal policy tightens in 2013–2015 — [IDEAS/RePEc record](https://ideas.repec.org/a/ifs/fistud/v34y2013ip517-534.html); free working-paper twin: Cronin and Dowd, Central Bank of Ireland Research Technical Paper 15/RT/11 (2011) — [PDF](https://centralbank.ie/docs/default-source/publications/research-technical-papers/research-technical-paper-15rt11.pdf?sfvrsn=8)
- The UK Office for Budget Responsibility (not a Fiscal Studies article, but the standard reference method the journal's fan-chart papers draw on) describes its fan-chart approach as generating thousands of simulated scenarios from randomly selected historical shocks, with the central line as the median and each band representing 10 percentage points of cumulative probability (so the two innermost bands together span an 80% range) — [OBR, "Using stochastic simulations to produce fan charts"](https://obr.uk/box/using-stochastic-simulations-to-produce-fan-charts/)
- O'Donoghue, Sologon, Kyzyma and McHale, "Modelling the Distributional Impact of the COVID-19 Crisis," *Fiscal Studies*, vol. 41, no. 2, pp. 321–336 (2020), is a calibrated tax-benefit microsimulation of Ireland combining real-time "nowcasting" with a household income generation model; its headline results are reported as point-estimate changes in the Gini coefficient and income-distribution percentile comparisons rather than as described uncertainty bands, based on the abstract — [IZA DP 13235 abstract](https://www.iza.org/publications/dp/13235) (full text: [docs.iza.org/dp13235.pdf](https://docs.iza.org/dp13235.pdf); figures not legible to the automated extraction used here)

### Inferences
- The one confirmed instance of genuine stochastic-uncertainty visualization in Fiscal Studies (Cronin and Dowd 2013) is a fan chart specifically built for debt/deficit sustainability analysis under EU fiscal rules — the same subject matter as the user's Brazil debt-sustainability model — suggesting fan charts are an established, citable convention in this journal specifically for debt/GDP-type trajectories, even if not necessarily the dominant chart type across the whole journal.
- Because most of the other Fiscal Studies simulation papers identified in this research are static/comparative-statics microsimulation (tax-benefit, pension, labour-supply) rather than Monte Carlo stochastic simulation, they are less likely to need percentile-band or fan-chart treatments at all — uncertainty in those papers is more often a methodological discussion (standard errors, sensitivity checks reported in tables) than a visualized band. This cannot be confirmed without direct figure access.

### Gaps
- Could not directly view any figure (fan chart, box plot, line+error-bar, or otherwise) in this session — all descriptions are at the abstract/methods level. The specific visual design of the Cronin and Dowd fan charts (color palette, number of bands, single vs. multi-panel) could not be confirmed; the working-paper PDF's figure pages were present (one full-page JPEG image object detected) but not legible to the automated PDF-text extraction tool used.
- Could not establish whether box plots or line-plus-error-bar charts appear anywhere in the Fiscal Studies corpus — no article using either was found.
- Could not determine the relative frequency of fan charts vs. other uncertainty treatments across the journal's full back catalogue; this would require systematic review of many more full-text articles than the ~15-query budget for this research task allowed.

## How do Fiscal Studies papers compare multiple policy scenarios visually (grouped bars by horizon, multi-line charts, small-multiple grids)?

### Takeaway
No Fiscal Studies figure showing multi-scenario comparison was directly viewed; the one confirmed case (Cronin and Dowd 2013) compares exactly two scenarios (baseline vs. a fiscal-tightening scenario) as two separate fan-chart sets rather than as overlaid lines or grouped bars, which is suggestive but not sufficient to generalize.

### Cited Findings
- Cronin and Dowd (2013) present their policy comparison as two distinct sets of fan charts — one for the no-policy-response baseline, one for a 2013–2015 fiscal-tightening scenario — described in the abstract as separate chart sets rather than a single overlaid chart — [IDEAS/RePEc record](https://ideas.repec.org/a/ifs/fistud/v34y2013ip517-534.html)
- Blundell, Crawford, French and Tetlow, "Comparing Retirement Wealth Trajectories on Both Sides of the Pond," *Fiscal Studies*, vol. 37, pp. 105–130 (2015/16), is confirmed as a Fiscal Studies article structured around a cross-country (UK vs. US) comparison of retirement wealth trajectories, implying some form of multi-series trajectory visualization, but the figure format itself could not be retrieved in this session — [RePEc citation found via search](https://ideas.repec.org) (bibliographic detail only; direct record URL not captured)

### Inferences
- Given that Cronin and Dowd treat two policy scenarios as two parallel sets of charts (not one overlaid chart), small-multiple/panel-grid layouts (one scenario per panel, consistent axes) appear to be at least one convention used for scenario comparison in this journal — but this is inferred from a single article's abstract description, not confirmed by viewing the actual layout.

### Gaps
- No direct evidence found for grouped bar charts by horizon, multi-line overlay charts, or small-multiple grids specifically in a Fiscal Studies article — this entire question could not be answered with confidence from the sources accessed.
- Could not confirm how many scenarios (beyond Cronin and Dowd's two) a typical Fiscal Studies simulation paper compares, or whether scenario count correlates with a specific chart form.

## What are typical figure design conventions (color palette, panel layout, axis labeling, legend placement, caption length/content)?

### Takeaway
No specific, confirmed design convention (palette, legend placement, caption wording) could be verified for any Fiscal Studies figure in this session — every attempt to retrieve actual rendered figures or their captions (via Wiley abstract pages, via PDF text extraction of working-paper twins) was blocked or returned unreadable binary content. This is the weakest-evidenced section of this research and should be treated as a near-total gap.

### Cited Findings
- None retrievable. The Wiley Online Library abstract page for the O'Donoghue et al. (2020) COVID-19 article returned HTTP 403 Forbidden to the automated fetch tool, preventing any check of figure thumbnails or caption text — [attempted URL](https://onlinelibrary.wiley.com/doi/10.1111/1475-5890.12231)
- The working-paper twin PDF of Cronin and Dowd's fan-chart paper (Central Bank of Ireland RT 15/RT/11) was fetched successfully as a binary file (28 pages, A4, LaTeX/Computer Modern fonts, containing at least one embedded full-page JPEG image object), confirming the document exists and contains at least one image/figure, but the automated tool could not extract caption text, axis labels, legend placement, or color information from it — [PDF](https://centralbank.ie/docs/default-source/publications/research-technical-papers/research-technical-paper-15rt11.pdf?sfvrsn=8)

### Inferences
- None can be responsibly drawn — any claim about Fiscal Studies caption length, palette choice, or legend placement would be speculation not grounded in a viewed source.

### Gaps
- Color palette conventions (categorical vs. sequential): not established.
- Panel/subplot layout conventions (e.g., 2×2 grids for multiple outcome variables): not established, beyond the weak inference above that Cronin and Dowd use separate chart sets per scenario.
- Axis labeling style: not established.
- Legend placement: not established.
- Caption length and content (bare label vs. one-sentence takeaway): not established. This would require either (a) access to a non-paywalled Fiscal Studies PDF with machine-readable text, (b) a vision-capable tool to read figure images directly, or (c) manual inspection by the user/report-writer of a Fiscal Studies PDF they can access (e.g., via institutional subscription), which this research agent did not have.
- **Recommended next step for the report writer or user:** if institutional access to Wiley Online Library is available, manually opening 2–3 recent Fiscal Studies microsimulation articles (e.g., the COVID-19 paper, the Spanish fiscal-drag paper if/when published in the journal, or the retirement-wealth comparison paper) and inspecting Figures 1–2 directly would close this gap quickly; it could not be closed via web search/fetch tools alone in this session.

## Do Fiscal Studies papers use distinctive chart types (spaghetti plot of simulated paths, tornado/sensitivity chart, waterfall decomposition)?

### Takeaway
Fan charts are the one confirmed distinctive uncertainty-chart type found in a Fiscal Studies article (Cronin and Dowd, 2013); no evidence of spaghetti plots, tornado charts, or waterfall charts was found in or attributed to any Fiscal Studies article in this session.

### Cited Findings
- Cronin and Dowd (2013), *Fiscal Studies* 34: 517–534, is confirmed to use fan charts (described above) — [IDEAS/RePEc record](https://ideas.repec.org/a/ifs/fistud/v34y2013ip517-534.html)
- The OBR (a UK body closely linked to the Fiscal Studies/IFS ecosystem methodologically, though not itself the journal) explicitly frames its fan-chart method as "widely used in the academic literature and by other organisations, including the IMF," and runs "thousands of scenarios driven by randomly selected shocks ... typical of those experienced in the past" — i.e., the fan chart is built from an underlying ensemble of simulated paths, conceptually adjacent to a spaghetti plot, but the OBR's own published output is the fan chart (percentile ribbon), not the raw spaghetti of individual paths — [OBR box](https://obr.uk/box/using-stochastic-simulations-to-produce-fan-charts/)

### Inferences
- Because Cronin and Dowd's method (like the OBR's) is explicitly a Monte-Carlo-style stochastic simulation condensed into percentile bands, it is reasonable to infer that Fiscal Studies/IFS-adjacent authors in this sub-literature prefer the condensed fan-chart presentation over showing raw individual simulated trajectories (a "spaghetti plot"), since both the journal article and its methodological reference point describe the output as bands/fans, not raw paths — but this was not directly confirmed by viewing a figure.

### Gaps
- No tornado/sensitivity chart or waterfall chart was found attributed to any Fiscal Studies article; absence of evidence here is weak (limited search budget), not proof of absence.
- Could not confirm whether any Fiscal Studies paper shows a literal "spaghetti plot" of many individual simulated paths (as opposed to condensed percentile bands) — this remains an open question.

## Roughly how many figures does a typical Fiscal Studies empirical/simulation paper include, and how are they split between main text and appendix?

### Takeaway
No source found in this session reported figure counts for any specific Fiscal Studies article, so this question could not be answered even approximately.

### Cited Findings
- None found with figure counts specified.

### Inferences
- None can be responsibly drawn from available evidence.

### Gaps
- Complete gap. None of the RePEc/IDEAS bibliographic records, abstracts, or the one working-paper PDF successfully inspected (page count 28, but that is total document length including text, references, and appendices, not a figure count) gave a figure count. Answering this would require opening full-text PDFs of several Fiscal Studies articles directly (blocked by paywall/403 in this session) or a vision-capable review of the working-paper twins already identified (Cronin and Dowd 2013 twin PDF, and the O'Donoghue et al. 2020 twin PDF at https://docs.iza.org/dp13235.pdf, both saved locally during this session but not machine-readable by the text-extraction tool used).

## Additional candidate Fiscal Studies articles identified (bibliographic confirmation only, content/figures not verified)

These titles were confirmed as Fiscal Studies journal publications via search but could not be examined further within the tool budget for this task. They are listed as leads for further research (by the report writer or with direct journal access), not as sources for any claim above:
- Kornstad and Thoresen, on Norwegian family policy combining labour-supply and childcare microsimulation, *Fiscal Studies* (2006) — identified only via a secondary summary in search results, original citation not independently verified.
- A 2008 *Fiscal Studies* article (vol. 29, pp. 285–325) on lone parents' labour supply, combining microsimulation and quasi-experimental evaluation of financial incentives — title and exact authorship not captured; flagged as unverified.
- Creedy, Herault and Kalb, "Abolishing the tax-free threshold in Australia: simulating alternative reforms," associated with *Fiscal Studies* (2009) per a University of Melbourne repository record — not independently verified against the Wiley record.
- Balladares and García-Miralles, "Fiscal Drag with Microsimulation: Evidence from Spanish Tax Records" — confirmed as IEB Working Paper 2025/08 ([PDF](https://diposit.ub.edu/dspace/bitstream/2445/223025/1/IEB25-08_Balladares%2bGraciaMiralles.pdf)); a RePEc snippet referenced a "Fiscal Studies, Volume 47, Issue 2 (2026)" listing with the same title, but this was not independently confirmed to be the same, published-in-journal version — treat as unverified/possibly-forthcoming.

## Overall assessment for the report writer

This research was substantially hampered by (a) Fiscal Studies being paywalled on Wiley with abstract pages returning 403 to automated fetching, and (b) the available PDF-reading tool being able to extract only structural/binary metadata (fonts, page counts, embedded image object types) rather than legible text or visual figure content from the two working-paper-twin PDFs retrieved. As a result, this note can confirm that fan charts are an established, citable Fiscal Studies convention for debt/deficit sustainability analysis (Cronin and Dowd, 2013) — directly relevant and usable for benchmarking the user's Brazil debt-sustainability Monte Carlo paper — but cannot confirm specific design details (palette, legend placement, caption style, figure counts, scenario-comparison chart form for non-fan-chart papers). For a benchmarking exercise this thorough, the user or report-writer would benefit from either (1) direct institutional access to the 2–3 specific DOIs identified here, or (2) a follow-up research pass using a vision-capable tool against the two already-downloaded working-paper PDFs (saved locally at the paths noted above during this session) or freshly downloaded Wiley PDFs, to actually view and describe the figures.
