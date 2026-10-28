# Player Manual — Brazil 2026: Four Years to Decide

*A decision-support simulation for "The Vote: Brazil's 2026 Runoff" (companion teaching case).
Play time: roughly 15–20 minutes per candidate.*

## What this is

You are not playing a character. You are a voter trying to decide between two real candidates —
Luiz Inácio Lula da Silva and Flávio Bolsonaro — in Brazil's 2026 presidential runoff. This
simulation lets you step into a hypothetical four-year presidency under *either* candidate's own
filed government programme, make the fiscal choices that programme implies each year, and watch
what happens to five things every voter should care about: the public debt, unemployment, child
mortality, poverty, and inequality (the Gini coefficient).

Every number the simulation shows you is drawn from a real, published, open-source economic model
of Brazil — the same one behind the companion research paper and case document — run forward year
by year. Nothing here is invented for the game. The model is honest about what it doesn't know:
every result is a *range* (a low, a middle, and a high estimate), not a single confident
prediction, because the real economy is uncertain and a model that pretended otherwise would be
lying to you.

**Play it twice** — once as if Lula's programme governs, once as if Flávio's does — before you
answer the case's discussion questions.

## How to play

1. **Choose a candidate.** Lula (PT) or Flávio Bolsonaro (PL). You can replay the whole simulation
   under the other candidate afterwards — in fact, you should, since the case asks you to compare
   both.
2. **Choose your anti-corruption commitment, once, for the whole four years.** Both candidates'
   programmes mention integrity measures. This choice is a *sensitivity test*, not a graded
   promise — neither candidate's own filed programme puts a number on what their anti-fraud
   measures would actually save, so the model treats this as something you're testing, not
   something either candidate has committed to in writing. Choose "commits in practice" or
   "talk only" and move on; you won't be asked again.
3. **Play four rounds, one per year of the term.** Each round, you choose **one** of four fiscal
   paths for that year. The two candidates do **not** share a menu — each one's four choices are
   drawn directly from *that candidate's own* TSE-filed 2026 programme:

   **If you're playing Lula:**
   - **Hold the fiscal rule** — stay on the existing LC 200/2023 constitutional spending-growth
     path. This exactly reproduces the model's own current-law baseline — it's the "do nothing
     differently" reference every result in this game is measured against, for both candidates.
   - **Expand transfers and investment** — grow Bolsa Família, Pé-de-Meia, Farmácia Popular and
     Gás do Povo, while protecting PAC infrastructure investment.
   - **Tax justice revenue** — raise revenue from high incomes and tax expenditures.
   - **Continue the record trend** — keep spending and raising tax revenue at the same pace his
     government actually ran at in 2022–2025.

   **If you're playing Flávio Bolsonaro:**
   - **Light Tesourão cuts** — the lower-intensity version of his administrative/discretionary
     spending-cut package.
   - **Deeper cuts** — the higher-intensity version of the same cut package, reaching further
     into pensions and indexation.
   - **Brasil Mais Barato tax cuts** — cut consumption, fuel/energy, payroll and business-capital
     taxes.
   - **Resume privatisation** — resume the National Privatisation Programme, case by case; sale
     proceeds reduce gross debt.

   Each round's choice is this year's decision only — nothing is locked in for future years, and
   you can choose a different path every year if your strategy changes. Every lever's size and
   composition traces to a specific, cited item in each candidate's own filed programme — nothing
   here is invented for the game.
4. **See the year's results**, then move to the next round. The debt, unemployment, and other
   indicators you see are *cumulative* — last year's choices carry forward into this year's
   starting point, exactly as they would in a real presidency. A big spending choice in year 1
   changes what's possible in year 4.
5. **After year 4, get your score** — a composite number, plus a four-year chart of everything
   that happened along the way. See "Understanding your score" below before you trust it.

## Reading the results

- **Debt/GDP**: the share of everything Brazil produces in a year that its government already
  owes. Rising fast is a warning sign; the model's own companion research found that *interest
  costs*, not any single spending choice, are usually the biggest driver of this number — don't
  expect any one lever to move it dramatically on its own.
- **Unemployment**: how many more or fewer people are out of work than under a current-law,
  no-change baseline.
- **Child mortality**: deaths per 1,000 live births, relative to that same baseline. This responds
  slowly — a cut this year shows up gradually, not all at once, and a later increase takes equally
  long to reverse. The model applies the same sensitivity to increases and cuts in spending, even
  though real-world evidence suggests cuts may hurt more than increases help by the same amount —
  keep that asymmetry in mind when you're judging a "no harm done" result.
- **Poverty**: the share of the population below a defined income line, relative to baseline.
- **Gini**: a standard inequality measure (0 = everyone equal, higher = more unequal), relative to
  baseline.
- **The ranges** (low – middle – high) reflect genuine uncertainty in the underlying economic
  parameters, not a forecast error band. A narrow range means economists broadly agree on the
  size of an effect; a wide one means they don't — both are informative.

## Understanding your score

The final number is expressed in **"percentage points of GDP"** — a common unit everything below
gets converted into so three unlike things can be added together into one headline figure.
**Higher is better.** Zero means your path performed identically to holding the current-law fiscal
rule in every single year — the same "do nothing differently" baseline for both candidates (it's
Lula's own "Hold the fiscal rule" choice, since that's the one that reproduces it exactly). Only
**three** of the simulation's five indicators feed the score:

- **Debt/GDP** — used as-is; it's already measured in the same unit as the score.
- **Unemployment** — converted into a GDP-equivalent using Brazil's own estimated Okun coefficient
  (how much output tends to move for every point unemployment moves).
- **"Value of a life" lever** — the modeled change in infant deaths (the mortality-rate change
  times how many babies are actually born that year) is multiplied by a price-per-death-averted
  you set with a slider, then expressed as a share of GDP.

That slider is not asking you to literally price a child's life. It's a standard economics
technique called a **Value of Statistical Life (VSL)** — used in real cost-benefit analysis by
governments and regulators everywhere — to put a *population-level* change in death risk onto the
same ledger as a fiscal number, so the two can be weighed against each other at all. The R$5.5
million default and the R$2.3M–R$12M range it can move across come from published Brazilian VSL
research (Stivali 2023, IPEA). Move the slider and watch the score's breakdown update — on most
played paths this term stays very small (fractions of a single percentage point of GDP) because
Brazil's own modeled infant-mortality effects are themselves small relative to the size of the
economy. That smallness is a real finding, not a bug: it tells you fiscal choices move the debt and
labour-market numbers far more than they move child mortality in this model.

**Poverty and the Gini coefficient are deliberately left out of the score.** There's no agreed,
sourced way to convert either one into a GDP-equivalent price the way debt, unemployment, and VSL
allow — folding them in would mean inventing a weight exactly where the other three terms don't
need one. They're shown next to the score instead, as indicators you weigh for yourself.

## What this simulation is *not*

- It is **not** a prediction of what will actually happen. It is a disciplined "if this, roughly
  this" exercise built from a real model's own sourced assumptions.
- It does **not** rank the two candidates for you, and it never will. The score at the end tells
  you how *that* four-year path performed against the model's own five indicators — it does not
  tell you how to vote. That's still your decision.
- The anti-corruption lever has **no quantified basis in either candidate's own programme** — it
  exists so you can see how sensitive the other results are to governance quality, not because
  either campaign has told you what their integrity measures are actually worth.
- Flávio's infrastructure plan is mostly financed off-budget (private concessions, PPPs, BNDES)
  in the real-world programme, and the model reflects that — it does **not** carry the
  contingent fiscal risk those structures can create if they go wrong, because that isn't
  quantified anywhere in his filed plan either.
- Neither candidate's programme includes a precisely costed minimum-wage rule change — Flávio's
  "Deeper cuts" option does move pensions and similar benefits as part of its composition, but
  neither programme proposes a new minimum-wage law with enough detail to model.
- "Resume privatisation" only models the debt-reducing side of asset sales (the proceeds). The
  foregone-dividend side (government income lost once a state-owned company is sold) has no
  sourced central estimate in Flávio's filed plan, so it is left at zero rather than guessed —
  this slightly favours that option in the score, and is disclosed here rather than hidden.

## A tip before you start

Since the two candidates don't share a menu, there's no single sequence you can replay identically
for both. Instead, try each candidate's own "steadiest" option every year first (Lula: hold the
fiscal rule; Flávio: light Tesourão cuts) before varying your choices — that isolates how much of
the difference in outcomes comes from each candidate's baseline fiscal philosophy, versus how much
comes from the more aggressive options on their own menu. Both comparisons are useful — the case
asks you to be ready to explain what actually drove your conclusion, not just report a final
number.

*Questions about the model itself, not the game? See the companion research paper and its online
supplementary material in this same repository — the economics behind every lever here is fully
documented and open-source.*
