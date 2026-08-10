# Ablations

## Self-consistency term (offline, `scripts/ablation_consistency.py`)

**Question:** does the deterministic `consistency_i` term
(`or_select/consistency.py`) ever actually change which candidate wins,
or is it dead weight in the objective?

**Method:** fully offline, zero new API calls. Each saved
`selection.json` stores the final combined score but not the intermediate
`quality_i`; since the scoring formula is known exactly
(`score_i = w_quality*quality_i + w_confidence*confidence_i +
w_consistency*consistency_i - w_cost*cost_i`), `quality_i` is recoverable
exactly by inversion. Re-solving `select_best` with `consistency=None`
(dropping the term entirely) on the same recovered `quality_i` and saved
`confidence_i`/`cost_i` isolates the term's effect precisely — this is not
an approximation, and the script asserts the reconstructed full-model
winner matches the originally saved winner as a correctness check before
reporting the ablated result.

**Result: 0/5 winners changed.**

| Query | Original winner | Ablated winner | Changed? | `consistency` spread |
|---|---|---|---|---|
| Rent vs. buy | c3 | c3 | no | 0.000 |
| Hamlet summary | c2 | c2 | no | 0.000 |
| Capital of France | c3 | c3 | no | 0.000 |
| Traffic congestion | c1 | c1 | no | 0.000 |
| Berlin Wall year | c0 | c0 | no | 0.000 |

**Why, structurally, not just by chance:** `consistency_spread` — the gap
between the highest and lowest `consistency_i` in a run — was exactly
**0.000 in all 5 cases**. The term can only change a ranking if it
assigns *different* values to different candidates; a constant added to
every candidate's score never changes which one is the argmax. Spread was
zero because every real run collected so far fell into one of two
extremes: either every candidate's text was unique (open-ended queries —
flat `1/N` for everyone) or every candidate's text matched (trivial
closed queries — flat `1.0` for everyone). The term is designed to matter
in the middle case — some candidates cluster into groups of *uneven*
size — which has not occurred once in any live run in this repo.
`tests/test_selection.py`'s
`test_consistency_can_flip_a_close_tie_toward_the_majority_answer` proves
the term *can* change a winner given synthetic data shaped that way; this
ablation shows it has not yet done so on any real data collected.

**Honest interpretation for the paper:** as currently weighted
(`w_consistency=0.3`), this term has been inert in every real test case so
far — not wrong, just untested on the scenario it's built for. Scaling
GSM8K to include harder problems (Task 4) is partly aimed at surfacing
that middle case: a problem hard enough that candidates split into an
uneven majority/minority, rather than uniformly agreeing or uniformly
disagreeing.

## Permutation self-consistency (position-bias correction)

*Pending — needs new live judge calls (forward-only vs. forward+backward)
against already-generated candidate texts. See Task #2.*
