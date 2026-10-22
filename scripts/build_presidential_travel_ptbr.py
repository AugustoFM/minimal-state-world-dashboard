"""Build a mobile-first Brazilian Portuguese page from the TR3 term dataset (lead developer, 2026-10-22).

Reads data/brazil/presidential_terms.csv (built by `python -m src.presidential_travel`) and writes a self-contained
page (inline CSS/JS, no network) to outputs/presidential_travel/presidential_travel_ptbr_celular.html, which is
git-ignored. Same numbers as the desktop page; only language and layout differ.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/brazil/presidential_terms.csv"
OUT = ROOT / "outputs/presidential_travel/presidential_travel_ptbr_celular.html"

TERM_PT = {"FHC I": "FHC I", "FHC II": "FHC II", "Lula I": "Lula I", "Lula II": "Lula II", "Dilma I": "Dilma I",
           "Dilma II": "Dilma II", "Temer": "Temer", "Bolsonaro": "Bolsonaro", "Lula III": "Lula III"}
PERIOD_PT = {"FHC I": "1995–1998", "FHC II": "1999–2002", "Lula I": "2003–2006", "Lula II": "2007–2010",
             "Dilma I": "2011–2014", "Dilma II": "2015 – ago/2016", "Temer": "set/2016 – 2018",
             "Bolsonaro": "2019–2022", "Lula III": "2023 – set/2026 (parcial)"}
COLUMNS = [
    "term", "president", "partial_term", "fdi_total_usd_m", "fdi_annual_average_usd_m", "fdi_pct_gdp_average",
    "fdi_world_share_average_pct", "fdi_world_share_change_pp", "fdi_world_growth_pct", "exports_total_usd_m",
    "exports_annual_average_usd_m", "export_volume_cagr_pct", "manufactured_volume_cagr_pct", "basic_volume_cagr_pct",
    "export_world_share_average_pct", "export_world_share_change_pp", "world_exports_growth_pct",
    "channels_start_10m", "channels_end_10m", "new_markets_10m", "lost_markets_10m", "new_market_names_10m",
    "lost_market_names_10m", "top5_export_share_pct", "trips", "country_visits", "days_abroad",
    "distinct_countries_visited", "matched_cost_brl_2026_09", "cpgf_all_brl_2026_09", "cpgf_classified_brl_2026_09",
    "cpgf_vice_presidency_brl_2026_09", "fdi_share_pp_per_trip", "export_share_pp_per_trip", "new_markets_per_trip",
    "fdi_share_pp_per_100_days", "export_share_pp_per_100_days", "fdi_share_pp_per_cost_m", "export_share_pp_per_cost_m",
]


def _clean(value: object) -> object:
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def build() -> Path:
    terms = pd.read_csv(SOURCE)
    rows = []
    for record in terms[COLUMNS].to_dict(orient="records"):
        record = {k: _clean(v) for k, v in record.items()}
        record["label"] = TERM_PT[record["term"]]
        record["period"] = PERIOD_PT[record["term"]]
        rows.append(record)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(TEMPLATE.replace("__DATA__", json.dumps(rows, ensure_ascii=False)), encoding="utf-8")
    return OUT


TEMPLATE = r"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Viagens presidenciais, IED e exportações</title>
<style>
:root{--bg:#f6f5f2;--card:#fff;--ink:#1d1d1f;--muted:#5f6368;--line:#e3e1dc;--accent:#2f6fb0;--bar:#2f6fb0;--bar2:#b9772f;--gap:#d9d6cf;--sel:#eef3fa}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#141518;--card:#1e2024;--ink:#ececec;--muted:#a3a7ad;--line:#33363c;--accent:#7fb0e6;--bar:#7fb0e6;--bar2:#e0a46a;--gap:#3a3d43;--sel:#22303f}}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:560px;margin:0 auto;padding:0 16px 48px}
header{padding:20px 0 8px}h1{font-size:22px;line-height:1.2;margin:0 0 6px}h2{font-size:18px;margin:26px 0 10px}h3{font-size:15px;margin:0 0 8px}
.small{font-size:13px;color:var(--muted)}.note{font-size:13px;color:var(--muted);margin:8px 0 0}
.chips{position:sticky;top:0;z-index:5;background:var(--bg);display:flex;gap:8px;overflow-x:auto;padding:10px 0;scrollbar-width:none}
.chips::-webkit-scrollbar{display:none}
.chip{flex:0 0 auto;border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:999px;padding:8px 14px;font:inherit;font-size:14px;min-height:40px}
.chip[aria-pressed="true"]{background:var(--accent);color:#fff;border-color:var(--accent)}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px;margin:10px 0}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.kpi .v{font-size:20px;font-weight:650}.kpi .l{font-size:12px;color:var(--muted)}
.bars .row{display:grid;grid-template-columns:78px 1fr 64px;align-items:center;gap:8px;margin:6px 0;font-size:13px}
.bars .row.sel{background:var(--sel);border-radius:8px}
.track{height:12px;background:var(--gap);border-radius:6px;overflow:hidden;position:relative}
.fill{height:100%;background:var(--bar);border-radius:6px}.fill.neg{background:var(--bar2)}
.num{text-align:right;font-variant-numeric:tabular-nums}
.scroll{overflow-x:auto;-webkit-overflow-scrolling:touch}
table{border-collapse:collapse;width:100%;font-size:13px;font-variant-numeric:tabular-nums}
th,td{padding:7px 8px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}
th:first-child,td:first-child{text-align:left;position:sticky;left:0;background:var(--card)}
tr.sel td{background:var(--sel)}
details{margin-top:8px}summary{cursor:pointer;color:var(--accent);min-height:32px}
.warn{border-left:4px solid var(--bar2);padding-left:10px}
</style>
</head>
<body>
<main>
<header>
<h1>Mandatos presidenciais: viagens, investimento estrangeiro e exportações</h1>
<p class="small">FHC (1995) a Lula III (set/2026). IED e exportações são sempre medidos separadamente. O contexto mundial acompanha cada número. As comparações são associações, não causalidade.</p>
</header>
<nav class="chips" id="chips" aria-label="Escolha o mandato"></nav>

<section id="resumo"></section>

<h2>Investimento estrangeiro direto (IED)</h2>
<div class="card"><h3>IED médio, % do PIB</h3><div class="bars" id="b_fdi_gdp"></div></div>
<div class="card"><h3>Participação do Brasil no IED mundial (média, %)</h3><div class="bars" id="b_fdi_share"></div>
<p class="note">Participação = IED recebido pelo Brasil ÷ IED mundial (Banco Mundial). Oscila muito com o ciclo mundial de investimento.</p></div>

<h2>Exportações</h2>
<div class="card"><h3>Exportações por ano, média (US$ bilhões)</h3><div class="bars" id="b_exp_value"></div>
<p class="note">Valores nominais em dólar: o mandato mais recente é favorecido pela inflação e pelos preços de commodities. Veja também a participação mundial e o volume.</p></div>
<div class="card"><h3>Participação do Brasil nas exportações mundiais (média, %)</h3><div class="bars" id="b_exp_share"></div></div>
<div class="card"><h3>Crescimento do volume exportado (% ao ano)</h3><div class="bars" id="b_exp_vol"></div>
<p class="note">Índice de quantum da Funcex (volume, sem efeito de preço).</p></div>

<h2>Novos mercados de exportação</h2>
<div class="card"><h3>Países que passaram a comprar ≥ US$ 10 milhões por ano</h3><div class="bars" id="b_new"></div>
<p class="note">"Novo" = abaixo do limite no início do mandato e acima no fim. Não atribui a abertura às viagens.</p></div>
<div class="card" id="markets"></div>

<h2>Viagens e gastos</h2>
<div class="card"><h3>Viagens internacionais</h3><div class="bars" id="b_trips"></div></div>
<div class="card"><h3>Dias no exterior (mínimo)</h3><div class="bars" id="b_days"></div>
<p class="note">Dias contados pelas datas das paradas listadas; dias de deslocamento podem faltar.</p></div>
<div class="card warn"><h3>Gastos (R$ milhões, preços de set/2026)</h3>
<div class="scroll"><table id="t_cost"></table></div>
<p class="note"><b>Apoio a viagens (piso):</b> diárias, passagens e outros gastos de equipes registrados no sistema de viagens e ligados a uma viagem presidencial; dados só a partir de 2014. Não inclui aviões da FAB nem gastos não discriminados do presidente e da primeira-dama.</p>
<p class="note"><b>Cartão corporativo da Presidência:</b> cerca de 99% é sigiloso (valor e mês são públicos; data e favorecido não). Cobre toda a segurança e logística da Presidência, no Brasil e no exterior, e não pode ser separado em viagem e não viagem: é contexto, não custo de viagem. Vice-Presidência em coluna separada; EBC e Imprensa Nacional excluídas. Dilma I: cartão só de 2013–2014.</p></div>

<h2>Eficiência das viagens</h2>
<div class="card warn"><p class="small"><b>Descritivo, não causal.</b> Mudanças no ciclo mundial e nos preços de commodities explicam a maior parte das variações. Cada indicador é ordenado separadamente; não há nota combinada.</p>
<h3>Variação da participação no IED mundial por viagem (p.p.)</h3><div class="bars" id="b_eff_fdi"></div>
<h3 style="margin-top:14px">Variação da participação nas exportações mundiais por viagem (p.p.)</h3><div class="bars" id="b_eff_exp"></div>
<h3 style="margin-top:14px">Novos mercados por viagem</h3><div class="bars" id="b_eff_mkt"></div>
<details><summary>Por R$ milhão gasto (só mandatos com dados de custo)</summary><div class="scroll"><table id="t_eff_cost"></table></div>
<p class="note">Usa apenas o apoio a viagens (piso). Como o custo está subestimado, os valores por R$ milhão estão superestimados.</p></details></div>

<h2>Notas e limitações</h2>
<div class="card small">
<p>Fontes: listas de viagens presidenciais (Wikipédia, a lista de FHC cita a Biblioteca da Presidência); Portal da Transparência (viagens 2014–2026; cartão 2013–ago/2026); Banco Central (IED, exportações); Funcex (volume); ComexStat/MDIC (exportações por país desde 1997); Banco Mundial (totais mundiais e PIB em dólar).</p>
<p>Valores em dólar são nominais (nenhum deflator dos EUA arquivado); por isso a página privilegia % do PIB e participação mundial. Lula III vai até set/2026 (parcial; médias anualizadas). FHC I usa 1997–1998 para mercados (ComexStat começa em 1997). Contagens de viagens podem diferir de levantamentos da imprensa (ex.: FHC 108 viagens na imprensa; 78 na lista usada).</p>
<p>Análise neutra: as mesmas regras para todos os mandatos.</p>
</div>
</main>
<script>
const D=__DATA__;
let sel=D[D.length-1].term;
const nf=(v,d=1)=>v==null?'sem dado':Number(v).toLocaleString('pt-BR',{minimumFractionDigits:d,maximumFractionDigits:d});
const $=id=>document.getElementById(id);
function bars(id,key,{d=1,scale=1,suffix=''}={}){
  const vals=D.map(r=>r[key]==null?null:r[key]*scale);const max=Math.max(...vals.filter(v=>v!=null).map(Math.abs),1e-9);
  $(id).innerHTML=D.map((r,i)=>{const v=vals[i];const w=v==null?0:Math.abs(v)/max*100;
    return `<div class="row${r.term===sel?' sel':''}"><span>${r.label}</span><div class="track">${v==null?'':`<div class="fill${v<0?' neg':''}" style="width:${w}%"></div>`}</div><span class="num">${v==null?'—':nf(v,d)+suffix}</span></div>`}).join('');
}
function summary(){
  const r=D.find(x=>x.term===sel);
  $('resumo').innerHTML=`<div class="card"><h3>${r.label} · ${r.period}</h3><div class="grid">
  <div class="kpi"><div class="v">US$ ${nf(r.fdi_annual_average_usd_m/1000,1)} bi</div><div class="l">IED por ano · ${nf(r.fdi_pct_gdp_average,2)}% do PIB</div></div>
  <div class="kpi"><div class="v">${nf(r.fdi_world_share_average_pct,2)}%</div><div class="l">do IED mundial (média)</div></div>
  <div class="kpi"><div class="v">US$ ${nf(r.exports_annual_average_usd_m/1000,1)} bi</div><div class="l">exportações por ano</div></div>
  <div class="kpi"><div class="v">${nf(r.export_world_share_average_pct,2)}%</div><div class="l">das exportações mundiais</div></div>
  <div class="kpi"><div class="v">${r.trips??'—'} viagens</div><div class="l">${r.days_abroad??'—'} dias no exterior (mín.)</div></div>
  <div class="kpi"><div class="v">+${r.new_markets_10m??'—'} / −${r.lost_markets_10m??'—'}</div><div class="l">mercados ≥ US$ 10 mi (novos/perdidos)</div></div>
  </div>${r.partial_term?'<p class="note">Mandato em curso: dados parciais até set/2026.</p>':''}</div>`;
}
function tables(){
  const cost=['matched_cost_brl_2026_09','cpgf_all_brl_2026_09','cpgf_classified_brl_2026_09','cpgf_vice_presidency_brl_2026_09'];
  $('t_cost').innerHTML='<thead><tr><th>Mandato</th><th>Apoio a viagens (piso)</th><th>Cartão Presidência</th><th>dos quais sigiloso</th><th>Cartão Vice</th></tr></thead><tbody>'+
   D.map(r=>`<tr class="${r.term===sel?'sel':''}"><td>${r.label}</td>${cost.map(k=>`<td>${r[k]==null?'sem dado':nf(r[k]/1e6,2)}</td>`).join('')}</tr>`).join('')+'</tbody>';
  $('t_eff_cost').innerHTML='<thead><tr><th>Mandato</th><th>IED p.p. por R$ mi</th><th>Export. p.p. por R$ mi</th></tr></thead><tbody>'+
   D.filter(r=>r.fdi_share_pp_per_cost_m!=null).map(r=>`<tr class="${r.term===sel?'sel':''}"><td>${r.label}</td><td>${nf(r.fdi_share_pp_per_cost_m,3)}</td><td>${nf(r.export_share_pp_per_cost_m,4)}</td></tr>`).join('')+'</tbody>';
  const r=D.find(x=>x.term===sel);
  $('markets').innerHTML=`<h3>${r.label}: novos mercados</h3><p class="small">${r.new_market_names_10m||'nenhum observado'}</p><h3>Perdidos</h3><p class="small">${r.lost_market_names_10m||'nenhum observado'}</p>`;
}
function render(){
  $('chips').innerHTML=D.map(r=>`<button class="chip" aria-pressed="${r.term===sel}" data-t="${r.term}">${r.label}</button>`).join('');
  summary();tables();
  bars('b_fdi_gdp','fdi_pct_gdp_average',{d:2,suffix:'%'});bars('b_fdi_share','fdi_world_share_average_pct',{d:2,suffix:'%'});
  bars('b_exp_value','exports_annual_average_usd_m',{d:0,scale:1/1000});bars('b_exp_share','export_world_share_average_pct',{d:2,suffix:'%'});
  bars('b_exp_vol','export_volume_cagr_pct',{d:1,suffix:'%'});bars('b_new','new_markets_10m',{d:0});
  bars('b_trips','trips',{d:0});bars('b_days','days_abroad',{d:0});
  bars('b_eff_fdi','fdi_share_pp_per_trip',{d:3});bars('b_eff_exp','export_share_pp_per_trip',{d:4});bars('b_eff_mkt','new_markets_per_trip',{d:2});
}
document.addEventListener('click',e=>{const b=e.target.closest('.chip');if(b){sel=b.dataset.t;render();b.scrollIntoView({inline:'center',block:'nearest'})}});
render();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    print(build())
