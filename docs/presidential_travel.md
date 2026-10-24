# Presidential-term travel analysis: method

`python -m src.presidential_travel` rebuilds every owned CSV, this method, the report and the offline HTML from local snapshots only.

Terms use the TR3 boundaries. Monthly BCB FDI and export flows are assigned by observation month; September 2016 belongs to Temer. Trips use departure date. Cost records already retain exact-president assignment around the transition. Annual World Bank comparisons use only complete calendar years inside each term.

FDI measures are BCB monthly total and annual-rate average, World Bank FDI/GDP, Brazil's share of world inflows, and world-flow growth. Exports use separate BCB value measures, FUNCEX total/manufactured/basic quantum growth, Brazil's world merchandise-export share and world export growth. No FDI/export composite is calculated.

An export channel is a ComexStat destination at or above US$10 million (US$1 million robustness). A new market is below the threshold at the observed start endpoint and above it at the end; a lost market is the reverse. Concentration is the top-five share and HHI at the endpoint. This is an endpoint definition, not proof that travel opened a market.

Efficiency ratios divide changes in Brazil's world shares or new-market counts by trips, 100 listed days, or—where covered—R$1 million of matched support cost. They are descriptive associations and are ranked separately for FDI and exports. Missing denominators remain missing.

Costs are deflated by monthly IPCA to September 2026 reais. Matched travel-system support, all Presidency CPGF transactions and conservatively identified foreign CPGF transactions remain separate. None is a complete mission bill.
