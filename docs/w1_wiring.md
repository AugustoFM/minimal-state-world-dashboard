# W1 Monte Carlo wiring

The optional I1 real-rate profile is applied to every scenario's debt recursion as a common annual offset to the sampled `effective_real_interest_rate`. It is off by default, is zero through 2025, and holds the 2045 value thereafter. A sensitivity run is:

```bash
python -m src.montecarlo --draws 1000 --rate-path i1
```

`run_metadata.json` records `real_rate_path: i1_proposed_offsets`, the 20 annual offsets, `config/i1_proposed.yaml`, and its SHA-256. The Monte Carlo also reports age 0-14, age 65+, and living-with-a-65+-pension/BPC-recipient poverty changes versus S0 for the R$218 and R$759 lines.

For the default-off check, 3-draw summaries were written before and after the change under the system temp directory. The new summary has 2,160 required E3 rows; after removing only those six new indicators, the files are byte-identical with SHA-256 `7e6aa02420f7e05c1700ad306bb7a849ad6e09473c24ad17c80dd4370a7e1068`.

The full suite reached 161 passing tests. Two unrelated `tests/test_microdata.py` cases could not enter pytest setup because Python 3.14/pytest changed their `tmp_path` directory to mode 0700 on Windows and the sandbox then denied access; both test functions passed when run against pre-created system-temp directories, and no assertion failed.
