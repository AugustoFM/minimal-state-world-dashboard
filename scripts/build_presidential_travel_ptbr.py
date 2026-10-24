"""Build a mobile-first Brazilian Portuguese page from the TR3 term dataset (lead developer, 2026-10-22).

Reads data/brazil/presidential_terms.csv (built by `python -m src.presidential_travel`) and writes a fully static,
self-contained page (inline CSS, no JavaScript, no network) to
outputs/presidential_travel/presidential_travel_ptbr_celular.html, which is git-ignored. Static on purpose: phone
file viewers (WhatsApp, Drive, e-mail previews) often do not run JavaScript. Same numbers as the desktop page.
"""
from __future__ import annotations

import html
import math
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/brazil/presidential_terms.csv"
OUT = ROOT / "outputs/presidential_travel/presidential_travel_ptbr_celular.html"

PERIOD_PT = {"FHC I": "1995–1998", "FHC II": "1999–2002", "Lula I": "2003–2006", "Lula II": "2007–2010",
             "Dilma I": "2011–2014", "Dilma II": "2015 – ago/2016", "Temer": "set/2016 – 2018",
             "Bolsonaro": "2019–2022", "Lula III": "2023 – set/2026 (parcial)"}


def _missing(value: object) -> bool:
    return value is None or (isinstance(value, float) and math.isnan(value))


def nf(value: object, decimals: int = 1, scale: float = 1.0, suffix: str = "") -> str:
    """Brazilian number format (1.234,5)."""
    if _missing(value):
        return "sem dado"
    text = f"{float(value) * scale:,.{decimals}f}"
    return text.replace(",", "X").replace(".", ",").replace("X", ".") + suffix


def bars(terms: pd.DataFrame, key: str, decimals: int = 1, scale: float = 1.0, suffix: str = "") -> str:
    values = [None if _missing(v) else float(v) * scale for v in terms[key]]
    top = max([abs(v) for v in values if v is not None] or [1.0]) or 1.0
    rows = []
    for label, value in zip(terms.term, values):
        if value is None:
            track, number = "", "—"
        else:
            width = abs(value) / top * 100
            track = f'<div class="fill{" neg" if value < 0 else ""}" style="width:{width:.1f}%"></div>'
            number = nf(value, decimals, 1.0, suffix)
        rows.append(f'<div class="row"><span>{html.escape(label)}</span><div class="track">{track}</div>'
                    f'<span class="num">{number}</span></div>')
    return '<div class="bars">' + "".join(rows) + "</div>"


def term_card(r: pd.Series, open_: bool) -> str:
    partial = '<p class="note">Mandato em curso: dados parciais até set/2026.</p>' if r.partial_term else ""
    new_names = html.escape(str(r.new_market_names_10m)) if not _missing(r.new_market_names_10m) else "nenhum observado"
    lost_names = html.escape(str(r.lost_market_names_10m)) if not _missing(r.lost_market_names_10m) else "nenhum observado"
    cost = ("sem dados de custo antes de 2014" if _missing(r.matched_cost_brl_2026_09)
            else f"apoio a viagens (piso): R$ {nf(r.matched_cost_brl_2026_09, 2, 1e-6)} mi · cartão da Presidência "
                 f"(contexto): R$ {nf(r.cpgf_all_brl_2026_09, 1, 1e-6)} mi")
    return f"""<details class="card term"{' open' if open_ else ''}>
<summary><b>{html.escape(r.term)}</b> <span class="small">{PERIOD_PT[r.term]}</span></summary>
<div class="grid">
<div class="kpi"><div class="v">US$ {nf(r.fdi_annual_average_usd_m, 1, 1e-3)} bi</div><div class="l">IED por ano · {nf(r.fdi_pct_gdp_average, 2)}% do PIB</div></div>
<div class="kpi"><div class="v">{nf(r.fdi_world_share_average_pct, 2)}%</div><div class="l">do IED mundial (média)</div></div>
<div class="kpi"><div class="v">US$ {nf(r.exports_annual_average_usd_m, 1, 1e-3)} bi</div><div class="l">exportações por ano</div></div>
<div class="kpi"><div class="v">{nf(r.export_world_share_average_pct, 2)}%</div><div class="l">das exportações mundiais</div></div>
<div class="kpi"><div class="v">{nf(r.trips, 0)} viagens</div><div class="l">{nf(r.days_abroad, 0)} dias no exterior (mín.)</div></div>
<div class="kpi"><div class="v">+{nf(r.new_markets_10m, 0)} / −{nf(r.lost_markets_10m, 0)}</div><div class="l">mercados ≥ US$ 10 mi (novos/perdidos)</div></div>
</div>
<p class="small"><b>Volume exportado:</b> {nf(r.export_volume_cagr_pct, 1)}% ao ano · <b>Gastos:</b> {cost}</p>
<p class="small"><b>Novos mercados:</b> {new_names}</p>
<p class="small"><b>Perdidos:</b> {lost_names}</p>
{partial}</details>"""


def cost_table(terms: pd.DataFrame) -> str:
    """One stacked block per term (no sideways scrolling on phones)."""
    blocks = []
    for _, r in terms.iterrows():
        if _missing(r.matched_cost_brl_2026_09) and _missing(r.cpgf_all_brl_2026_09):
            body = '<span class="small">sem dados de custo (registros começam em 2013–2014)</span>'
        else:
            body = (f'<div class="kv"><span>Apoio a viagens (piso)</span><b>R$ {nf(r.matched_cost_brl_2026_09, 2, 1e-6)} mi</b></div>'
                    f'<div class="kv"><span>Cartão da Presidência (contexto)</span><b>R$ {nf(r.cpgf_all_brl_2026_09, 1, 1e-6)} mi</b></div>'
                    f'<div class="kv"><span>dos quais sigiloso</span><b>R$ {nf(r.cpgf_classified_brl_2026_09, 1, 1e-6)} mi</b></div>'
                    f'<div class="kv"><span>Cartão da Vice-Presidência</span><b>R$ {nf(r.cpgf_vice_presidency_brl_2026_09, 1, 1e-6)} mi</b></div>')
        blocks.append(f'<div class="block"><h4>{html.escape(r.term)}</h4>{body}</div>')
    return "".join(blocks)


def efficiency_cost_table(terms: pd.DataFrame) -> str:
    rows = terms[terms.fdi_share_pp_per_cost_m.notna()]
    return "".join(
        f'<div class="block"><h4>{html.escape(r.term)}</h4>'
        f'<div class="kv"><span>IED: p.p. do mundo por R$ mi</span><b>{nf(r.fdi_share_pp_per_cost_m, 3)}</b></div>'
        f'<div class="kv"><span>Exportações: p.p. do mundo por R$ mi</span><b>{nf(r.export_share_pp_per_cost_m, 4)}</b></div></div>'
        for _, r in rows.iterrows()
    )


def build() -> Path:
    terms = pd.read_csv(SOURCE).sort_values("term_order").reset_index(drop=True)
    cards = "".join(term_card(r, i == len(terms) - 1) for i, r in terms.iterrows())
    page = TEMPLATE.format(
        cards=cards,
        fdi_gdp=bars(terms, "fdi_pct_gdp_average", 2, suffix="%"),
        fdi_share=bars(terms, "fdi_world_share_average_pct", 2, suffix="%"),
        exp_value=bars(terms, "exports_annual_average_usd_m", 0, 1e-3),
        exp_share=bars(terms, "export_world_share_average_pct", 2, suffix="%"),
        exp_vol=bars(terms, "export_volume_cagr_pct", 1, suffix="%"),
        new=bars(terms, "new_markets_10m", 0),
        trips=bars(terms, "trips", 0),
        days=bars(terms, "days_abroad", 0),
        eff_fdi=bars(terms, "fdi_share_pp_per_trip", 3),
        eff_exp=bars(terms, "export_share_pp_per_trip", 4),
        eff_mkt=bars(terms, "new_markets_per_trip", 2),
        cost=cost_table(terms),
        eff_cost=efficiency_cost_table(terms),
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(page, encoding="utf-8")
    return OUT


TEMPLATE = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Viagens presidenciais, IED e exportações</title>
<style>
:root{{--bg:#f6f5f2;--card:#fff;--ink:#1d1d1f;--muted:#5f6368;--line:#e3e1dc;--accent:#2f6fb0;--bar:#2f6fb0;--bar2:#b9772f;--gap:#d9d6cf}}
@media (prefers-color-scheme:dark){{:root{{--bg:#141518;--card:#1e2024;--ink:#ececec;--muted:#a3a7ad;--line:#33363c;--accent:#7fb0e6;--bar:#7fb0e6;--bar2:#e0a46a;--gap:#3a3d43}}}}
*{{box-sizing:border-box}}html{{-webkit-text-size-adjust:100%}}
body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}}
main{{max-width:560px;margin:0 auto;padding:0 14px 48px}}
h1{{font-size:21px;line-height:1.2;margin:18px 0 6px}}h2{{font-size:18px;margin:26px 0 8px}}h3{{font-size:15px;margin:0 0 8px}}
.small{{font-size:13px;color:var(--muted)}}.note{{font-size:13px;color:var(--muted);margin:8px 0 0}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:12px;margin:10px 0}}
details.term summary{{min-height:40px;padding:6px 0;font-size:16px;cursor:pointer}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:8px}}
.kpi .v{{font-size:18px;font-weight:650}}.kpi .l{{font-size:12px;color:var(--muted)}}
.row{{display:grid;grid-template-columns:72px 1fr 62px;align-items:center;gap:8px;margin:6px 0;font-size:13px}}
.track{{height:12px;background:var(--gap);border-radius:6px;overflow:hidden}}
.fill{{height:100%;background:var(--bar);border-radius:6px}}.fill.neg{{background:var(--bar2)}}
.num{{text-align:right}}
.scroll{{overflow-x:auto;-webkit-overflow-scrolling:touch}}
table{{border-collapse:collapse;width:100%;font-size:13px}}
th,td{{padding:7px 8px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}}
th:first-child,td:first-child{{text-align:left}}
nav a{{display:inline-block;margin:4px 8px 4px 0;color:var(--accent)}}
.warn{{border-left:4px solid var(--bar2)}}
.block{{border-top:1px solid var(--line);padding:8px 0}}.block h4{{margin:0 0 4px;font-size:14px}}
.kv{{display:flex;justify-content:space-between;gap:10px;font-size:13px;padding:2px 0}}.kv span{{color:var(--muted)}}
</style>
</head>
<body>
<main>
<h1>Mandatos presidenciais: viagens, investimento estrangeiro e exportações</h1>
<p class="small">FHC (1995) a Lula III (set/2026). IED e exportações são sempre medidos separadamente. O contexto mundial acompanha cada número. As comparações são associações, não causalidade.</p>
<nav class="small"><a href="#mandatos">Mandatos</a><a href="#ied">IED</a><a href="#exp">Exportações</a><a href="#mercados">Mercados</a><a href="#viagens">Viagens e gastos</a><a href="#eficiencia">Eficiência</a><a href="#notas">Notas</a></nav>

<h2 id="mandatos">Resumo por mandato</h2>
<p class="small">Toque em um mandato para abrir ou fechar.</p>
{cards}

<h2 id="ied">Investimento estrangeiro direto (IED)</h2>
<div class="card"><h3>IED médio, % do PIB</h3>{fdi_gdp}</div>
<div class="card"><h3>Participação do Brasil no IED mundial (média, %)</h3>{fdi_share}
<p class="note">IED recebido pelo Brasil ÷ IED mundial (Banco Mundial). Oscila muito com o ciclo mundial de investimento.</p></div>

<h2 id="exp">Exportações</h2>
<div class="card"><h3>Exportações por ano, média (US$ bilhões)</h3>{exp_value}
<p class="note">Valores nominais em dólar favorecem os mandatos mais recentes (inflação e preços de commodities). Compare também a participação mundial e o volume.</p></div>
<div class="card"><h3>Participação do Brasil nas exportações mundiais (média, %)</h3>{exp_share}</div>
<div class="card"><h3>Crescimento do volume exportado (% ao ano)</h3>{exp_vol}
<p class="note">Índice de quantum da Funcex (volume, sem efeito de preço). Barras laranja = queda.</p></div>

<h2 id="mercados">Novos mercados de exportação</h2>
<div class="card"><h3>Países que passaram a comprar ≥ US$ 10 milhões por ano</h3>{new}
<p class="note">"Novo" = abaixo do limite no início do mandato e acima no fim. Os nomes dos países estão no resumo de cada mandato. Não atribui a abertura às viagens.</p></div>

<h2 id="viagens">Viagens e gastos</h2>
<div class="card"><h3>Viagens internacionais</h3>{trips}</div>
<div class="card"><h3>Dias no exterior (mínimo)</h3>{days}
<p class="note">Contados pelas datas das paradas listadas; dias de deslocamento podem faltar.</p></div>
<div class="card warn"><h3>Gastos (R$ milhões, preços de set/2026)</h3>
{cost}
<p class="note"><b>Apoio a viagens (piso):</b> diárias, passagens e outros gastos de equipes registrados no sistema de viagens e ligados a uma viagem presidencial; dados só a partir de 2014. Não inclui aviões da FAB nem gastos não discriminados do presidente e da primeira-dama.</p>
<p class="note"><b>Cartão corporativo da Presidência:</b> cerca de 99% é sigiloso (valor e mês são públicos; data e favorecido não). Cobre toda a segurança e logística da Presidência, no Brasil e no exterior, e não pode ser separado em viagem e não viagem: é contexto, não custo de viagem. Vice-Presidência em coluna separada; EBC e Imprensa Nacional excluídas. Dilma I: cartão só de 2013–2014.</p></div>

<h2 id="eficiencia">Eficiência das viagens</h2>
<div class="card warn"><p class="small"><b>Descritivo, não causal.</b> O ciclo mundial e os preços de commodities explicam a maior parte das variações. Cada indicador é ordenado separadamente; não há nota combinada.</p>
<h3>Variação da participação no IED mundial por viagem (p.p.)</h3>{eff_fdi}
<h3 style="margin-top:14px">Variação da participação nas exportações mundiais por viagem (p.p.)</h3>{eff_exp}
<h3 style="margin-top:14px">Novos mercados por viagem</h3>{eff_mkt}
<h3 style="margin-top:14px">Por R$ milhão gasto (só mandatos com dados de custo)</h3>
{eff_cost}
<p class="note">Usa apenas o apoio a viagens (piso). Como o custo está subestimado, os valores por R$ milhão estão superestimados.</p></div>

<h2 id="notas">Notas e limitações</h2>
<div class="card small">
<p>Fontes: listas de viagens presidenciais (Wikipédia; a lista de FHC cita a Biblioteca da Presidência); Portal da Transparência (viagens 2014–2026; cartão 2013–ago/2026); Banco Central (IED, exportações); Funcex (volume); ComexStat/MDIC (exportações por país desde 1997); Banco Mundial (totais mundiais e PIB em dólar).</p>
<p>Valores em dólar são nominais (nenhum deflator dos EUA arquivado); por isso a página privilegia % do PIB e participação mundial. Lula III vai até set/2026 (parcial; médias anualizadas). FHC I usa 1997–1998 para mercados (ComexStat começa em 1997). Contagens de viagens podem diferir de levantamentos da imprensa (ex.: FHC 108 viagens na imprensa; 78 na lista usada).</p>
<p>Análise neutra: as mesmas regras para todos os mandatos.</p>
</div>
</main>
</body>
</html>
"""


if __name__ == "__main__":
    print(build())
