// Four Years to Decide -- front end for the presidency-game data library.
//
// Architecture note: game_data.json precomputes outcomes for complete 4-round
// action sequences only. Round N's outcome is identical across every full
// sequence sharing the same first N actions (the underlying model is a
// forward-only annual recursion -- verified directly against the data before
// writing this file), so a partial choice is looked up by padding the
// undecided remaining rounds with a filler action. This needs no new data: it
// relies on forward-causality, not on guessing future rounds correctly.
//
// Lula and Flávio now have their own distinct, candidate-specific 4-action
// menus (config/programs_2026.yaml), not a shared symmetric one -- so the
// filler action used to pad an unfinished sequence is per candidate, and
// labels/descriptions are read from game_data.json's own sourced
// metadata.action_definitions rather than duplicated here. "Hold the fiscal
// rule" (Lula's current-law action) reproduces Brazil's S0 baseline exactly
// (zero deltas, flat infant mortality -- verified directly against the data),
// so it is used as the single reference path for "vs. doing nothing
// differently" comparisons for BOTH candidates: that baseline is the macro
// model's own status quo, not specific to either candidate's programme.
const FILLER_ACTION_BY_CANDIDATE = { Lula: 'fiscal_rule', Flavio: 'tesourao_light_cuts' };
const REFERENCE_CANDIDATE = 'Lula';
const REFERENCE_SEQUENCE_KEY = 'fiscal_rule+fiscal_rule+fiscal_rule+fiscal_rule';
const PERCENTILE = '50'; // central estimate; p10/p90 shown as the uncertainty range alongside it

// Populated from game_data.json's metadata.action_definitions in init() --
// {candidate: {action_id: {label, blurb}}}. See ACTION_INFO's fill-in below.
const ACTION_INFO = { Lula: null, Flavio: null };

const CANDIDATE_INFO = {
  Lula: {
    name: 'Luiz Inácio Lula da Silva', party: 'PT',
    blurb: 'Four of his own filed programme’s levers: hold the existing spending-growth rule, expand transfers and investment, raise revenue from high incomes and tax expenditures, or continue the pace of his first term.',
  },
  Flavio: {
    name: 'Flávio Bolsonaro', party: 'PL',
    blurb: 'Four of his own filed programme’s levers: light or deeper administrative cuts (the “Tesourão”), tax cuts on consumption and energy, or resumed privatisation.',
  },
};

const INDICATOR_INFO = {
  debt_to_gdp: { label: 'Debt / GDP', unit: '% of GDP', decimals: 1, lowerIsBetter: true, absolute: true },
  unemployment_change: { label: 'Unemployment vs. status quo', unit: 'pp', decimals: 2, lowerIsBetter: true, absolute: false },
  infant_mortality: { label: 'Infant mortality', unit: 'per 1,000 live births', decimals: 2, lowerIsBetter: true, absolute: true },
  poverty_change: { label: 'Poverty vs. status quo', unit: 'pp', decimals: 2, lowerIsBetter: true, absolute: false },
  gini_change: { label: 'Gini vs. status quo', unit: 'points', decimals: 3, lowerIsBetter: true, absolute: false },
};
const INDICATOR_ORDER = ['debt_to_gdp', 'unemployment_change', 'infant_mortality', 'poverty_change', 'gini_change'];

const OKUN_CENTRAL = 0.1878; // src/macro.py: unemployment_change_pp = -okun * gdp_level_vs_s0_pct (Pessoa 2014, central)
const GDP_BRL_MILLION = 12738600; // config/parameters.yaml base_real_gdp.central, 2025 BRL million -- held fixed across the 4 years for this conversion (a disclosed simplification)
const DEFAULT_VSL_BRL_MILLION = 5.5; // IPEA/Stivali (2023) random-effects meta-analysis, central estimate

const App = (() => {
  let DATA = null;
  let hasIntegrityVariants = false;
  const state = { candidate: null, integrity: 'current_controls', actions: [], round: 1 };

  async function init() {
    const res = await fetch('game_data.json');
    DATA = await res.json();
    hasIntegrityVariants = Array.isArray(DATA.metadata && DATA.metadata.integrity_variants_in_library)
      && DATA.metadata.integrity_variants_in_library.length > 1;
    const defs = (DATA.metadata && DATA.metadata.action_definitions) || {};
    for (const cand of ['Lula', 'Flavio']) {
      ACTION_INFO[cand] = {};
      for (const [id, def] of Object.entries(defs[cand] || {})) {
        ACTION_INFO[cand][id] = { label: def.label, blurb: def.description };
      }
    }
    renderCandidates();
    document.querySelectorAll('.toggle-btn[data-choice]').forEach((btn) => {
      btn.onclick = () => setIntegrity(btn.dataset.choice);
    });
  }

  function goStep(name) {
    document.querySelectorAll('section.step').forEach((el) => { el.hidden = el.dataset.step !== name; });
    const order = ['setup', 'round', 'reveal', 'final'];
    const dots = document.querySelectorAll('#progress span');
    const roundOffset = name === 'round' || name === 'reveal' ? state.round : (name === 'final' ? 5 : 0);
    dots.forEach((dot, i) => {
      dot.classList.remove('active', 'done');
      if (i < roundOffset) dot.classList.add('done');
      else if (i === roundOffset) dot.classList.add('active');
    });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function renderCandidates() {
    const grid = document.getElementById('candidate-grid');
    grid.innerHTML = '';
    for (const id of ['Lula', 'Flavio']) {
      const info = CANDIDATE_INFO[id];
      const btn = document.createElement('button');
      btn.className = 'candidate-card';
      btn.innerHTML = `<div class="cand-name">${info.name}</div><div class="cand-party">${info.party}</div><p class="cand-blurb">${info.blurb}</p>`;
      btn.onclick = () => selectCandidate(id, btn);
      grid.appendChild(btn);
    }
  }

  function selectCandidate(id, btnEl) {
    state.candidate = id;
    document.querySelectorAll('.candidate-card').forEach((el) => el.classList.remove('selected'));
    btnEl.classList.add('selected');
    const card = document.getElementById('integrity-card');
    card.hidden = false;
    const sensBtn = document.getElementById('btn-integrity-sensitivity');
    sensBtn.disabled = !hasIntegrityVariants;
    if (!hasIntegrityVariants) sensBtn.title = 'Not yet available in this version of the data library.';
    setIntegrity('current_controls');
    card.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function backToCandidates() {
    document.getElementById('integrity-card').hidden = true;
  }

  function setIntegrity(choice) {
    state.integrity = choice;
    document.querySelectorAll('.toggle-btn').forEach((el) => el.classList.remove('selected'));
    const el = document.getElementById(choice === 'current_controls' ? 'btn-integrity-current' : 'btn-integrity-sensitivity');
    if (el) el.classList.add('selected');
    document.getElementById('btn-start-rounds').disabled = false;
  }

  function startRounds() {
    state.actions = [];
    state.round = 1;
    goStep('round');
    renderRoundActions();
  }

  function renderRoundActions() {
    document.getElementById('round-badge').textContent = `Year ${state.round} of 4`;
    document.getElementById('round-number').textContent = state.round;
    const yearLabel = state.round === 1 ? 'the first year' : `year ${state.round}`;
    document.getElementById('round-sub').textContent = state.round === 1
      ? `Choose the fiscal path for ${CANDIDATE_INFO[state.candidate].name}'s first year in office.`
      : `Last year ended where you saw it. Choose this year's path -- you can change strategy at any point.`;
    const grid = document.getElementById('action-grid');
    grid.innerHTML = '';
    for (const id of Object.keys(ACTION_INFO[state.candidate])) {
      const info = ACTION_INFO[state.candidate][id];
      const btn = document.createElement('button');
      btn.className = 'action-card';
      btn.innerHTML = `<div class="box"></div><div class="txt"><b>${info.label}</b><p>${info.blurb}</p></div>`;
      btn.onclick = () => selectAction(id, btn);
      grid.appendChild(btn);
    }
    document.getElementById('btn-round-continue').disabled = true;
    document.getElementById('btn-round-back').style.visibility = state.round === 1 ? 'hidden' : 'visible';
  }

  function selectAction(id, btnEl) {
    state.pendingAction = id;
    document.querySelectorAll('.action-card').forEach((el) => el.classList.remove('selected'));
    btnEl.classList.add('selected');
    document.getElementById('btn-round-continue').disabled = false;
  }

  function roundBack() {
    if (state.round === 1) { goStep('setup'); return; }
    state.round -= 1;
    state.actions.pop();
    goStep('round');
    renderRoundActions();
    // restore the previous selection visually
    const prevAction = state.actions[state.round - 1];
    if (prevAction) {
      const idx = Object.keys(ACTION_INFO[state.candidate]).indexOf(prevAction);
      const card = document.querySelectorAll('.action-card')[idx];
      if (card) selectAction(prevAction, card);
    }
  }

  function lookupPath(actionsSoFar, candidate) {
    const cand = candidate || state.candidate;
    const filler = FILLER_ACTION_BY_CANDIDATE[cand];
    const padded = actionsSoFar.concat(Array(4 - actionsSoFar.length).fill(filler));
    const key = padded.join('+');
    const byIntegrity = hasIntegrityVariants ? DATA.paths[cand][state.integrity] : DATA.paths[cand];
    return byIntegrity[key];
  }

  // The reference ("vs. doing nothing differently") is always Lula's "hold
  // the fiscal rule" path -- it reproduces the model's own S0 status-quo
  // baseline exactly, which is candidate-agnostic, so the same reference
  // applies whichever candidate you're playing.
  function referencePath() {
    const byIntegrity = hasIntegrityVariants
      ? DATA.paths[REFERENCE_CANDIDATE][state.integrity]
      : DATA.paths[REFERENCE_CANDIDATE];
    return byIntegrity[REFERENCE_SEQUENCE_KEY];
  }

  function fmt(value, decimals) {
    const sign = value > 0 ? '+' : '';
    return sign + value.toFixed(decimals);
  }

  function revealRound() {
    state.actions.push(state.pendingAction);
    const path = lookupPath(state.actions);
    const round = path[PERCENTILE].rounds[state.round - 1];
    const roundLo = path['10'].rounds[state.round - 1];
    const roundHi = path['90'].rounds[state.round - 1];
    const ref = referencePath()[PERCENTILE].rounds[state.round - 1];

    document.getElementById('reveal-title').textContent = `Year ${state.round}: ${ACTION_INFO[state.candidate][state.pendingAction].label}`;
    document.getElementById('reveal-meta').innerHTML = `<b>${CANDIDATE_INFO[state.candidate].name}</b> &middot; ${round.year}`;

    const grid = document.getElementById('reveal-grid');
    grid.innerHTML = '';
    for (const key of INDICATOR_ORDER) {
      const info = INDICATOR_INFO[key];
      const val = round[key];
      const lo = roundLo[key];
      const hi = roundHi[key];
      const deltaVsRef = info.absolute ? (val - ref[key]) : val;
      const isGood = info.lowerIsBetter ? deltaVsRef <= 0 : deltaVsRef >= 0;
      const tile = document.createElement('div');
      tile.className = 'ind-tile';
      const displayVal = info.absolute ? val.toFixed(info.decimals) : fmt(val, info.decimals);
      tile.innerHTML = `
        <div class="label">${info.label}</div>
        <div class="val ${deltaVsRef === 0 ? '' : (isGood ? 'good' : 'bad')}">${displayVal} <span style="font-size:13px;color:var(--muted);">${info.unit}</span></div>
        <div class="range">range across uncertainty: ${lo.toFixed(info.decimals)} to ${hi.toFixed(info.decimals)}</div>
        ${info.absolute ? `<div class="range">vs. holding the current-law fiscal rule: ${fmt(deltaVsRef, info.decimals)} ${info.unit}</div>` : ''}
      `;
      grid.appendChild(tile);
    }
    document.getElementById('btn-reveal-continue').textContent = state.round < 4 ? `Continue to year ${state.round + 1}` : 'See the full four years';
    goStep('reveal');
  }

  function nextRoundOrFinish() {
    if (state.round < 4) {
      state.round += 1;
      goStep('round');
      renderRoundActions();
    } else {
      renderFinal();
      goStep('final');
    }
  }

  function renderFinal() {
    document.getElementById('final-sub').textContent =
      `${CANDIDATE_INFO[state.candidate].name}'s term, as you played it: ${state.actions.map((a) => ACTION_INFO[state.candidate][a].label).join(' → ')}.`;
    renderCharts();
    const slider = document.getElementById('vsl-slider');
    slider.value = DEFAULT_VSL_BRL_MILLION;
    updateScore();
    slider.oninput = updateScore;
  }

  function updateScore() {
    const vslBrlMillion = parseFloat(document.getElementById('vsl-slider').value);
    document.getElementById('vsl-value').textContent = `R$${vslBrlMillion.toFixed(1)}M`;
    const path = lookupPath(state.actions)[PERCENTILE];
    const ref = referencePath()[PERCENTILE];
    const births = (DATA.metadata && DATA.metadata.approx_live_births_by_year) || {};

    let debtTotal = 0, unemploymentTotal = 0, mortalityTotal = 0, totalDeathsDelta = 0;
    for (let i = 0; i < 4; i++) {
      const round = path.rounds[i];
      const refRound = ref.rounds[i];
      const debtDelta = round.debt_to_gdp - refRound.debt_to_gdp;
      const unemploymentGdpEquiv = round.unemployment_change / OKUN_CENTRAL;
      const mortalityDelta = round.infant_mortality - refRound.infant_mortality;
      const birthsThisYear = births[String(round.year)] || births[round.year] || 2700000;
      const deathsDelta = (mortalityDelta / 1000) * birthsThisYear;
      const mortalityCostBrl = deathsDelta * vslBrlMillion; // both in millions of BRL
      const mortalityCostPp = (mortalityCostBrl / GDP_BRL_MILLION) * 100;
      debtTotal += debtDelta;
      unemploymentTotal += unemploymentGdpEquiv;
      mortalityTotal += mortalityCostPp;
      totalDeathsDelta += deathsDelta;
    }
    const costPp = debtTotal + unemploymentTotal + mortalityTotal;
    const score = -costPp; // higher is better, 0 = identical to the protect-everything reference
    const el = document.getElementById('score-value');
    el.textContent = `${score >= 0 ? '+' : ''}${score.toFixed(2)} pp of GDP`;
    el.className = `score-value ${score > 0.01 ? 'good' : (score < -0.01 ? 'bad' : '')}`;

    const breakdown = document.getElementById('score-breakdown');
    if (breakdown) {
      const deathsLabel = totalDeathsDelta >= 0
        ? `~${totalDeathsDelta.toFixed(1)} more infant deaths than the reference path over 4 years`
        : `~${Math.abs(totalDeathsDelta).toFixed(1)} fewer infant deaths than the reference path over 4 years`;
      breakdown.innerHTML = `
        <div>Debt term: ${fmt(-debtTotal, 3)} pp</div>
        <div>Unemployment term (via Okun): ${fmt(-unemploymentTotal, 3)} pp</div>
        <div>Value-of-life term: ${fmt(-mortalityTotal, 4)} pp (${deathsLabel})</div>
      `;
    }
  }

  function sparkline(values, width, height) {
    const min = Math.min(...values, 0);
    const max = Math.max(...values, 0);
    const span = (max - min) || 1;
    const pts = values.map((v, i) => {
      const x = (i / (values.length - 1)) * (width - 8) + 4;
      const y = height - 4 - ((v - min) / span) * (height - 8);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    });
    const zeroY = height - 4 - ((0 - min) / span) * (height - 8);
    return `<svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none">
      <line x1="0" y1="${zeroY.toFixed(1)}" x2="${width}" y2="${zeroY.toFixed(1)}" stroke="var(--line)" stroke-width="1" stroke-dasharray="3,3"/>
      <polyline points="${pts.join(' ')}" fill="none" stroke="var(--accent)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
      ${pts.map((p) => `<circle cx="${p.split(',')[0]}" cy="${p.split(',')[1]}" r="3" fill="var(--accent)"/>`).join('')}
    </svg>`;
  }

  function renderCharts() {
    const path = lookupPath(state.actions)[PERCENTILE];
    const grid = document.getElementById('charts-grid');
    grid.innerHTML = '';
    for (const key of INDICATOR_ORDER) {
      const info = INDICATOR_INFO[key];
      const values = path.rounds.map((r) => r[key]);
      const card = document.createElement('div');
      card.className = 'chart-card';
      const finalDisplay = info.absolute ? values[3].toFixed(info.decimals) : fmt(values[3], info.decimals);
      card.innerHTML = `<div class="chart-label">${info.label}</div>${sparkline(values, 320, 90)}<div class="chart-final">Year 4: ${finalDisplay} ${info.unit}</div>`;
      grid.appendChild(card);
    }
  }

  function resetAll() {
    state.candidate = null; state.actions = []; state.round = 1;
    document.getElementById('integrity-card').hidden = true;
    document.querySelectorAll('.candidate-card').forEach((el) => el.classList.remove('selected'));
    goStep('setup');
  }

  function switchCandidate() {
    const other = state.candidate === 'Lula' ? 'Flavio' : 'Lula';
    resetAll();
    const idx = other === 'Lula' ? 0 : 1;
    const card = document.querySelectorAll('.candidate-card')[idx];
    if (card) selectCandidate(other, card);
  }

  return { goStep, selectCandidate, backToCandidates, setIntegrity, startRounds, selectAction, roundBack, revealRound, nextRoundOrFinish, resetAll, switchCandidate, init };
})();

window.addEventListener('DOMContentLoaded', App.init);
