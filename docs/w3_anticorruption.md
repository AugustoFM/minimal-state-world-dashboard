# W3 anti-corruption sensitivity

## Interpretation

W3 is an off-by-default sensitivity, not a ranking of candidates or recent governments. The WGI and CPI series in `docs/governance.md` cannot distinguish recent administrations within their measurement uncertainty. W3 instead asks the same conditional question of each programme: **what if its stated anti-corruption measures deliver effects of the size represented by the common evidence-based/assumption ranges?** Every effect-size draw is shared between the programmes on random stream `[seed, 8]`.

Use `--anti-corruption {none,lula,flavio,both}`. The default is `none`. `--anti-corruption-mapping programme` activates only the text-mapped channels below; `full` activates all four channels for each selected programme and is the symmetric procurement add-on. Selecting W3 also loads the P1 programme scenarios. Policy effects begin in 2027, the first year of the 2027-2030 term; pre-2027 G2 events are never removed.

## Programme-text mapping

The quotations are from the TSE-filed PDFs archived in `data/raw/brazil/programs_2026/`. Page numbers are the printed PDF page numbers.

### Lula (PT)

- Leakage/effective services: “Vamos aprofundar a participação. o controle social nas políticas públicas e continuaremos realizando conferências para implantar e aprimorar políticas e programas sob responsabilidade federal.” (p. 15.) On the budget, “As emendas impositivas e o orçamento secreto são práticas que mudaram as relações entre o Executivo e o Legislativo, sequestram o orçamento público, dispersam os recursos e reduzem a eficiência alocativa.” (pp. 15-16.)
- Leakage and lower major-scandal probability: “Vamos dar sequência às medidas de controle e integridade da administração pública e ao combate à corrupção. O Plano de Integridade e Combate à Corrupção 2025–2027 representa um avanço institucional que será aprofundado, fortalecendo a prevenção, a investigação e a responsabilização de corruptos e corruptores, inclusive os do andar de cima, com pleno respeito à independência das instituições.” (p. 18.)
- Leakage/transparency: “O Portal da Transparência receberá investimentos para evoluir para uma plataforma inteligente baseada em dados abertos e inteligência artificial. Fortaleceremos ainda mais organismos como a Ouvidoria-Geral da União” (p. 18.)

These statements map to channels 1 and 4. They do not quantify either effect.

### Flávio Bolsonaro (PL)

- General direction: “Tesouraço nos gastos públicas: equilíbrio fiscal, reforma do Estado, combate à corrupção e menos impostos.” (p. 12.)
- Leakage/transparency: “daremos mais transparência, controle e rastreabilidade às emendas parlamentares, priorizando sua alocação em políticas públicas prioritárias do Plano Plurianual, aprovado pelo parlamento.” (p. 69.) The programme also proposes “uma agenda permanente de transparência e avaliação de políticas públicas, identificando quem são os beneficiários de cada programa e medindo o impacto real de cada gasto.” (p. 71.)
- Lower major-scandal probability: “Nas empresas públicas, essa proteção tem nome: a Lei das Estatais, de 2016, criada depois da Lava Jato para blindar as estatais da indicação política, com exigência de qualificação técnica e quarentena para quem vem de campanha eleitoral. Tentaram enfraquecê-la; nós vamos fortalecê-la.” (p. 70.) It also says: “Vamos blindar os fundos de pensão das estatais da indicação política, porque a aposentadoria do trabalhador não pode virar cofre de projeto de poder.” (p. 70.)
- INSS income protection: “Reeditaremos um pacote antifraude na Previdência, nos moldes do que fizemos em 2019, e não pouparemos esforços para coibir qualquer nova tentativa de roubar o dinheiro de quem já deu sua contribuição ao país.” (p. 72.) For payroll loans: “Vamos mudar a governança do consignado para que a fraude não se repita, revendo quem opera esses descontos e como são autorizados, com mais transparência” (p. 72.)

These statements map to channels 1, 3 and 4. They do not quantify any effect.

Neither programme quantifies procurement savings, so channel 2 is excluded from `programme` mapping and is available symmetrically through `full` mapping only.

## Evidence and mechanics

| Channel | Common draw | Evidence/status | Model effect and reported attribution |
|---|---:|---|---|
| 1. Leakage reduction | triangular(0.08, 0.25, 0.50) fraction of leakage removed | Low: Avis, Ferraz & Finan (JPE, 2018), a past random CGU audit reduced future measured corruption by 8% across 1,949 municipalities. Mode is a choice; high is the existing “leakage halved” sensitivity. | Gross spending is unchanged. Lower leakage raises effective health and education services. W3 reports the service gain, infant-mortality and life-expectancy contributions, the direct health-output contribution, and schooling contribution. |
| 2. Procurement savings | triangular(0, 0.01, 0.03) of purchases | Weak evidence. A 2007 federal report stated 12.7% electronic-auction price savings against reference prices; case studies do not identify a government-wide causal effect. The wide W3 range is a modelling choice. | The 2024 central-government goods-and-services total is R$82.26544bn, 0.6983928% of 2024 GDP. Savings ramp from zero in 2026 to full in 2030 and enter as positive non-tax revenue. There is no household incidence, multiplier, or service loss. |
| 3. INSS fraud protection | triangular(R$0, R$0.5bn, R$1.0bn) per year | The 2019-2024 associative-deduction fraud took retirees’ money, not Treasury money. CGU/PF estimated R$6.3bn; the CPMI majority report used R$3.3bn; associative deductions ended by law in November 2025. The annual range is a choice. | The amount is spread equally across weighted retirement/pension recipients aged 65+ in C3. It changes pensioner income and poverty among older people but has no fiscal effect. |
| 4. Lower major-scandal probability | triangular(0, 0.25, 0.50) proportional probability reduction | Judgment, not a causal estimate. | For each draw, G2 first creates one event sequence and magnitudes. W3 draws one uniform per event and keeps the event when `u >= q`; the same thinning is reused for every enabled programme scenario, preserving pairing. The avoided GDP loss is reported separately. |

The procurement base is the sum of 2024 rows labelled `GASTO - USO DE BENS E SERVICOS` in `data/raw/brazil/education/tesouro_cofog_gc_2010_2024_aggregated.csv.gz`, divided by 2024 current-price GDP from IBGE SIDRA table 1846. Parameter values, derivations and the same page-specific quotations are machine-readable in `config/w3_anticorruption.yaml`.

## Outputs and limitations

W3 adds `anticorruption_leakage_contribution_*`, `anticorruption_fiscal_saving_pp_gdp`, `anticorruption_scandal_gdp_contribution_pct`, and `anticorruption_pensioner_income_change_pct`. Existing health, feedback, external-GDP/debt and C3 poverty indicators also change, but only for programme rows with the relevant channel switched on. Channel contributions are zero where a channel is not mapped; C3 outputs are missing outside the default variant, as before.

The mapping from qualitative programme language to model mechanisms is judgment. The 25% leakage mode, procurement range, INSS annual range, and scandal-probability reduction are partly or wholly assumptions; no programme supplies them. Procurement reference-price savings may not be realised fiscal savings. Protected retiree income is not a recovered Treasury transfer. Event thinning represents institutional prevention, not concealment or delayed discovery. The optional long-run CPI association remains disabled and is not part of W3 because its scale input is still marked `to_verify`.
