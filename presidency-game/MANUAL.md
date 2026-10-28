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
   paths for that year, grounded directly in what the candidate's own programme says:
   - **Protect services and transfers** — keep pensions, health, education and means-tested
     transfers (like Bolsa Família) at their planned levels, even if that means less room
     elsewhere.
   - **Administrative efficiency** — squeeze administrative and discretionary spending rather
     than services. The model's own evidence says this mostly doesn't cost GDP directly — but it
     isn't a free lunch either; efficiency gains are themselves uncertain, not guaranteed.
   - **Cut subsidies and discretionary spending** — a broader, blunter cut than pure
     administrative efficiency, reaching tax breaks and other current spending too.
   - **Adjust pensions and indexation** — the biggest single lever on the debt, and the one most
     likely to raise poverty and inequality, especially among older households.
   Each round's choice is this year's decision only — nothing is locked in for future years,
   and you can choose a different path every year if your strategy changes.
4. **See the year's results**, then move to the next round. The debt, unemployment, and other
   indicators you see are *cumulative* — last year's choices carry forward into this year's
   starting point, exactly as they would in a real presidency. A big spending choice in year 1
   changes what's possible in year 4.
5. **After year 4, get your score** — a single headline number blending the debt trajectory,
   growth, and the four social indicators, plus a four-year chart of everything that happened
   along the way.

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
- Neither candidate's programme includes a precisely costed minimum-wage rule change — the
  pension/indexation lever moves pensions and similar benefits, but it does not simulate a new
  minimum-wage law, because neither programme proposes one with enough detail to model.

## A tip before you start

Play the *same* sequence of choices (say, protect services every year) under both candidates
first, so you can see how much of the difference in outcomes comes from the two fiscal
philosophies themselves, versus how much comes from your own strategy. Then try varying your own
choices year to year and see how much that changes the final score. Both comparisons are useful —
the case asks you to be ready to explain what actually drove your conclusion, not just report a
final number.

*Questions about the model itself, not the game? See the companion research paper and its online
supplementary material in this same repository — the economics behind every lever here is fully
documented and open-source.*
