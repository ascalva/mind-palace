# growth

## 2026-11-06

The question, on the prediction ledger (`dn-prediction-ledger`): can a succession of stakes, each
informed by a forecast, multiply a starting holding by a large factor (ten, say) through many
small decisions rather than one large move, and what does such a path need?

The question in the palace's own terms, which is how it is answered here: a sequence of yes/no
questions, each with a reference probability `r_i` (the baseline the ledger scores arms against),
an arm's forecast `p_i` and an outcome `o_i`; a starting holding `W_0`; and a stake, decided
question by question from what the arm believes, that moves the holding. Does a path to `N × W_0`
exist, and what is it made of?

### The answer

The proportional stake against the reference multiplies the holding by `p_i / r_i` on yes and by
`(1 − p_i) / (1 − r_i)` on no. So

```
log (W_T / W_0) = Σ_i [ o_i log (p_i / r_i) + (1 − o_i) log ((1 − p_i) / (1 − r_i)) ]
```

which is the cumulative difference of log scores between the arm and the reference: exactly the
quantity the ledger already scores (its two mean log scores, summed). A path to `N×` exists iff
that cumulative advantage reaches `log N`. Nothing about any single question has to be large; the
path is a succession of small edges, each one a question the arm read better than the reference.

Proved in `formal/Palace/Growth.lean` (GRW-1 to GRW-6, stated in `docs/LAWS.md` family XIII and
`formal/README.md`; the shapes of GRW-3's domain and GRW-6 follow `lean-ergodicity`, Carrone's
Lean proofs of the Kelly criterion, with our own model and proofs):

- **GRW-1, the identity.** For every sequence the proportional stake's growth is the likelihood
  ratio `Π L(p_i, o_i) / Π L(r_i, o_i)`, and its log the cumulative log-score advantage. Exact.
  The readout computes it (`python -m eval.predictions growth`).
- **GRW-2, the expectation.** With outcome `i` yes with probability `q_i`, the expected log growth
  of question `i` is `KL(q_i ‖ r_i) − KL(q_i ‖ p_i)`: positive iff the forecast is closer to the
  truth than the reference is. The truthful forecast attains `KL(q_i ‖ r_i)`; every other forecast
  strictly less. The edge is calibration, not boldness.
- **GRW-3, optimality.** Among constant fractions `f` of the holding staked on yes at reference
  `r`, the expected log growth under belief `p` is concave in `f`, its derivative vanishes at
  `f* = (p − r) / (1 − r)`, and that fraction is the maximizer; its factors are the proportional
  stake's. The mirror stake on no, at `(r − p) / r`, when `p < r`. `f = 1` is ruin on a single no.
- **GRW-4, the path to `N×`.** `W_T ≥ N W_0` iff the cumulative advantage is at least `log N`. One
  question's advantage is at most `log (1 / m)` for `m` the smallest of `p, 1 − p, r, 1 − r`, so at
  least `log N / log (1 / m)` questions are needed, whatever the luck. With a mean advantage `a > 0`
  per question, the expected cumulative advantage of `T` questions is `T a` (independent outcomes),
  so `log N / a` questions in expectation: at `a = 0.05` nats per question, 47 questions for `10×`.
- **GRW-5, no ruin.** Every factor is positive, so the holding never reaches zero, and `k` adverse
  outcomes in a row multiply it by at least the `k`-th power of the worst factor,
  `min (p / r, (1 − p) / (1 − r))`, itself at least `m`.
- **GRW-6, the time average.** On one question type repeated, its outcomes independent and
  identically distributed, the time-average advantage converges almost surely to the expected one
  (the strong law of large numbers), so a positive expected advantage grows the holding without
  bound almost surely, reaching every `N×`, and a negative one sends it to zero. The stationary
  case; the ledger's questions differ, and the strong law for summands that are not identically
  distributed is the next rung.

### What the proof does and does not say

It says a path exists exactly when the arm's forecasts beat the reference's in cumulative log
score, and it says how long the path is for a given edge. It does not say the arm has an edge:
that is what the pre-registered experiment measures, blinded, at its N. The growth readout is a
thought experiment the scorer computes from the ledger; nothing in the palace stakes anything, and
the readout's primary comparison is withheld before N like the mean. The fractional stakes (half
and a quarter of the proportional one) are reported because a cautious stake is the usual
practice; GRW-1's identity holds at the full stake only, and GRW-5's bound holds for any stake up
to it and not beyond (the attack's control: a doubled stake turns a factor negative).

Open: the reference the ledger scores against is fixed per question; a reference that moves with
the arm's own activity is outside the model.
