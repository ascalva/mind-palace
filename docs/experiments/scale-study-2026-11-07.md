# Scale study: where the macro quantities of a citation graph stop fluctuating

Date 2026-11-07. Code in `eval/scale/`, tests in `tests/unit/test_scale_study.py`, the article in
`papers/2026-11-07-scale-study/`. The data stays outside the repository. The small result tables
are in `docs/experiments/scale-study-2026-11-07/` (`cuts.csv`, `boot.csv`, `hodge.csv`,
`core_cuts.csv`, `core_boot.csv`, `corpus.csv`).

## Question

A companion note proves that a macro observable's time average needs a window of many relaxation
times 1/gamma, that a k-mode macro model holds only after a time set by the eigengap, and cites
the theorem that normalized-Laplacian eigenvalues of random graphs concentrate once degrees exceed
about log N. This note measures where those thresholds fall on a real growing graph.

## Data

- Source: OpenAlex (CC0), `api.openalex.org/works`, fetched 2026-11-07.
- Field: the concept **Complex network** (`C34947359`, about 47,700 works in OpenAlex's count).
  Chosen because it is a coherent field with a short, dense history (it starts in 1998), small
  enough to fetch in minutes and large enough to reach N above 30,000.
- Nodes: works with a publication date. Edges: references from one work of the set to another work
  of the set (references to works outside the field are dropped). Edge time is the citing work's
  publication date. 47,546 works and 327,978 in-field citations were stored (the API's count was
  47,683; the 137 missing are works that changed between the count and the page requests).
- Download: 293 gzip pages (200 works each), 31 MB; with the derived `edges.csv`, `works.csv` and
  the result CSVs, 41 MB in total under `~/datasets/openalex/complex-network/`. The cap was 2 GB.
- Deviation from the brief: cursor paging past the first page requires an API key, and obtaining a
  key needs an account tied to an email address, which this run did not create. The fetcher cuts
  the field into date ranges of at most 9,000 works (halving a range until it fits) and pages each
  with `page=`. Requests were sequential with a 0.5 s pause, a descriptive User-Agent that names
  the project, backoff on errors, and resume by skipping stored files.
- Coverage caveat: the volume jumps in the last two years (1,205 works dated 2024, 3,795 dated
  2025, 7,575 dated 2026), which is an indexing effect and not growth of the field. Cuts after
  2024 are listed but not interpreted.

## Method

- Cuts: yearly at 31 December from 1995 to 2024, plus 2025-12-31 and 2026-11-07. At each cut the
  graph is the edges with time at or before the cut, symmetrized, loops and duplicates removed,
  largest connected component kept (`eval/scale/graphs.py`).
- Spectrum: the 20 smallest eigenvalues of the normalized Laplacian L = I - D^(-1/2) A D^(-1/2).
  Dense `eigvalsh` up to 500 nodes. Above that `scipy.sparse.linalg.eigsh` in shift-invert mode,
  sigma = -0.01, which = 'LM', tol = 1e-8, with a sparse LU of L + 0.01 I under a minimum-degree
  ordering (`MMD_AT_PLUS_A`) passed as `OPinv`. The default ordering took 162 s at N = 21,681 and
  the minimum-degree ordering about 10 s. LOBPCG was not used. ARPACK can miss repeated
  eigenvalues (a cycle's); the tests use a path above the dense limit for that reason. The smallest
  gap among lambda_3 to lambda_20 over the cuts above 500 nodes was 1.5e-6, so near-repeated
  eigenvalues occur and the tail of the 20 is less reliable than lambda_2 and the first gaps.
- gamma = lambda_2. The eigengap gap_k = lambda_(k+1) - lambda_k, so gap_1 = gamma; the table
  reports widths of gap_1 to gap_4.
- Bootstrap, at each cut: node subsampling at fractions 0.25, 0.4, 0.55, 0.7, 0.85 (induced
  subgraph, then largest component) and edge resampling (m edges drawn with replacement, then
  largest component), 20 replicates each. The width is (q97.5 - q2.5) / |median| over replicates.
  The scale of a row is the mean N of its replicates. Bootstrap was run for cuts up to N = 25,000;
  later cuts have point estimates only.
- Crossing: N* is the smallest scale from which the width is at or below 10% at every larger scale
  that was measured (`eval.scale.study.crossing`).
- k-cores: the same measures on the largest component of the k-core of each cut (k = 3, 6, 10, 15),
  with every replicate reduced to its own k-core, because the concentration theorem needs minimum
  degree of order log N and the full graph always has degree-one nodes.
- Relaxation and window: 1/gamma in walk steps. For a reversible chain with spectral gap gamma
  the asymptotic variance of a time average of g is at most 2 Var_pi(g)/gamma (the eigenvalue
  factor (1+mu)/(1-mu) is at most 2/gamma for mu at most 1 - gamma), so a relative standard error
  eps with relative standard deviation 1 needs T = 2/(gamma eps^2) steps. At eps = 0.1 that is
  200/gamma. The companion note's SCL-1 statement was not available to this branch; this is the
  standard bound it should agree with.
- Hodge split: the flow on a canonical edge is +1 or -1 along the citation (citing to cited), 0 for
  a mutual pair. On the clique complex (all triangles of the symmetrized graph) the flow is
  projected by LSMR (tolerance 1e-8) onto the gradient space and onto the curl space; harmonic is
  the remainder. Energies are fractions of the squared norm. Bootstrap: 6 replicates for node 0.7
  and for edge resampling.

## Results

### 1. Cuts

| cut | N | edges | mean deg | min deg | mean deg / ln N | gamma | 1/gamma | window, 10% |
|---|---|---|---|---|---|---|---|---|
| 1999-12-31 | 15 | 17 | 2.27 | 1 | 0.84 | 0.1102 | 9.1 | 1815 |
| 2000-12-30 | 43 | 114 | 5.30 | 1 | 1.41 | 0.2827 | 3.5 | 707 |
| 2001-12-30 | 161 | 624 | 7.75 | 1 | 1.53 | 0.0152 | 65.6 | 13118 |
| 2002-12-31 | 305 | 1993 | 13.07 | 1 | 2.28 | 0.0521 | 19.2 | 3838 |
| 2003-12-31 | 533 | 3958 | 14.85 | 1 | 2.37 | 0.0544 | 18.4 | 3678 |
| 2004-12-30 | 917 | 7059 | 15.40 | 1 | 2.26 | 0.0760 | 13.2 | 2632 |
| 2005-12-31 | 1404 | 11438 | 16.29 | 1 | 2.25 | 0.0972 | 10.3 | 2058 |
| 2006-12-31 | 2076 | 17843 | 17.19 | 1 | 2.25 | 0.1153 | 8.7 | 1734 |
| 2007-12-31 | 2876 | 26380 | 18.34 | 1 | 2.30 | 0.1189 | 8.4 | 1682 |
| 2008-12-30 | 3878 | 36102 | 18.62 | 1 | 2.25 | 0.1496 | 6.7 | 1337 |
| 2009-12-30 | 5066 | 47090 | 18.59 | 1 | 2.18 | 0.0073 | 136.3 | 27252 |
| 2010-12-31 | 6239 | 57846 | 18.54 | 1 | 2.12 | 0.0115 | 87.3 | 17459 |
| 2011-12-31 | 7549 | 70504 | 18.68 | 1 | 2.09 | 0.0102 | 97.7 | 19539 |
| 2012-12-30 | 8995 | 83621 | 18.59 | 1 | 2.04 | 0.0075 | 133.8 | 26764 |
| 2013-12-31 | 10591 | 99645 | 18.82 | 1 | 2.03 | 0.0084 | 118.8 | 23753 |
| 2014-12-31 | 12375 | 116883 | 18.89 | 1 | 2.00 | 0.0048 | 210.2 | 42037 |
| 2015-12-31 | 14152 | 135141 | 19.10 | 1 | 2.00 | 0.0046 | 218.6 | 43722 |
| 2016-12-30 | 15853 | 153465 | 19.36 | 1 | 2.00 | 0.0076 | 132.4 | 26488 |
| 2017-12-30 | 17619 | 171927 | 19.52 | 1 | 2.00 | 0.0085 | 117.9 | 23571 |
| 2018-12-31 | 19487 | 194588 | 19.97 | 1 | 2.02 | 0.0081 | 123.0 | 24593 |
| 2019-12-31 | 21407 | 215687 | 20.15 | 1 | 2.02 | 0.0077 | 129.6 | 25911 |
| 2020-12-30 | 23210 | 234961 | 20.25 | 1 | 2.01 | 0.0075 | 133.4 | 26674 |
| 2021-12-31 | 24926 | 254123 | 20.39 | 1 | 2.01 | 0.0074 | 135.6 | 27111 |
| 2022-12-31 | 26434 | 270944 | 20.50 | 1 | 2.01 | 0.0077 | 129.0 | 25808 |
| 2023-12-31 | 27910 | 286751 | 20.55 | 1 | 2.01 | 0.0081 | 124.2 | 24834 |
| 2024-12-30 | 28773 | 296244 | 20.59 | 1 | 2.01 | 0.0094 | 105.9 | 21174 |
| 2025-12-31 | 30584 | 309659 | 20.25 | 1 | 1.96 | 0.0089 | 112.0 | 22396 |
| 2026-11-07 | 33342 | 327510 | 19.65 | 1 | 1.89 | 0.0089 | 112.0 | 22395 |

Mean degree stays at about twice ln N from 2002 onward, and the minimum degree is 1 at every cut.

### 2. Stability of gamma on the whole component

| statistic | scheme | N* (width stays at or below 10% from here up) | mean deg / ln N there |
|---|---|---|---|
| width_gamma | node | never | |
| width_gamma | edge | never | |
| width_gap1 | node | never | |
| width_gap1 | edge | never | |
| width_gap2 | node | never | |
| width_gap2 | edge | never | |
| width_gap3 | node | never | |
| width_gap3 | edge | never | |
| width_gap4 | node | never | |
| width_gap4 | edge | never | |

No width of gamma or of the first eigengaps reaches 10% at any scale up to N = 25,000, under
either scheme. Pooled medians of the width of gamma (binned by half decades of N):

| scheme | N (geometric mean) | mean deg / ln N | median width_gamma | points |
|---|---|---|---|---|
| node | 7 | 0.98 | 1.302 | 14 |
| node | 18 | 1.06 | 1.375 | 5 |
| node | 61 | 1.22 | 1.462 | 6 |
| node | 189 | 1.44 | 2.058 | 10 |
| node | 581 | 1.47 | 1.528 | 12 |
| node | 1789 | 1.24 | 1.324 | 23 |
| node | 5503 | 1.28 | 4.216 | 36 |
| node | 13782 | 1.57 | 1.966 | 18 |
| edge | 8 | 0.90 | 1.559 | 5 |
| edge | 38 | 1.05 | 0.489 | 1 |
| edge | 191 | 1.41 | 4.091 | 2 |
| edge | 648 | 1.59 | 1.195 | 2 |
| edge | 1926 | 1.52 | 0.848 | 3 |
| edge | 5794 | 1.43 | 5.996 | 5 |
| edge | 16361 | 1.33 | 1.330 | 9 |

The same for gap_2:

| scheme | N (geometric mean) | mean deg / ln N | median width_gap2 | points |
|---|---|---|---|---|
| node | 7 | 0.98 | 1.006 | 14 |
| node | 18 | 1.06 | 1.937 | 5 |
| node | 61 | 1.22 | 2.217 | 6 |
| node | 189 | 1.44 | 2.495 | 10 |
| node | 581 | 1.47 | 2.827 | 12 |
| node | 1789 | 1.24 | 3.395 | 23 |
| node | 5503 | 1.28 | 2.799 | 36 |
| node | 13782 | 1.57 | 3.064 | 18 |
| edge | 8 | 0.90 | 1.959 | 5 |
| edge | 38 | 1.05 | 2.300 | 1 |
| edge | 191 | 1.41 | 2.701 | 2 |
| edge | 648 | 1.59 | 2.549 | 2 |
| edge | 1926 | 1.52 | 3.107 | 3 |
| edge | 5794 | 1.43 | 2.043 | 5 |
| edge | 16361 | 1.33 | 1.687 | 9 |

The widths are not small and do not fall with N. The cause is visible in the point estimates: gamma
falls from 0.150 (2008, N = 3,878) to 0.0073 (2009, N = 5,066), and stays near 0.005 to 0.010
afterwards. At the 2009 cut a sweep cut on the Fiedler vector finds a set of 42 nodes joined to
the rest by a single edge (conductance 0.008, volume 121). At the 2026 cut the sweep finds a set of
7 nodes joined by one edge. The gap is set by small groups hanging on a single citation. Whether
such a group is present in a resampled graph varies from replicate to replicate, so the interval
of gamma spans an order of magnitude. The mean degree over ln N is about 2 or more through 2024, so the mean
degree is not the quantity that matters; the minimum degree is 1, which is 0.1 to 0.3 of ln N.

### 3. Stability of gamma on the k-core

Point estimates and widths for selected cuts (all cuts are in `core_cuts.csv` and `core_boot.csv`;
`n/a` marks cuts above the bootstrap size limit of 15,000, and `nan` a resampled graph whose k-core
was empty):

| cut | k | N | min deg | mean deg / ln N | gamma | 1/gamma | width, edge | width, node 0.85 | width, node 0.5 |
|---|---|---|---|---|---|---|---|---|---|
| 2003-12-31 | 3 | 405 | 3 | 3.10 | 0.3714 | 2.7 | 0.109 | 0.210 | 0.361 |
| 2003-12-31 | 6 | 313 | 6 | 3.78 | 0.3867 | 2.6 | 0.125 | 0.271 | 0.374 |
| 2003-12-31 | 10 | 221 | 10 | 4.57 | 0.4284 | 2.3 | 0.189 | 0.190 | 0.104 |
| 2003-12-31 | 15 | 98 | 15 | 5.73 | 0.5301 | 1.9 | nan | 0.061 | nan |
| 2006-12-30 | 3 | 1734 | 3 | 2.69 | 0.2971 | 3.4 | 0.215 | 0.658 | 0.691 |
| 2006-12-30 | 6 | 1375 | 6 | 3.21 | 0.3120 | 3.2 | 0.094 | 0.150 | 0.573 |
| 2006-12-30 | 10 | 917 | 10 | 4.03 | 0.3482 | 2.9 | 0.175 | 0.163 | 0.527 |
| 2006-12-30 | 15 | 430 | 15 | 5.24 | 0.4092 | 2.4 | nan | 0.285 | nan |
| 2009-12-30 | 3 | 4320 | 3 | 2.55 | 0.0221 | 45.2 | 0.548 | 6.211 | 0.542 |
| 2009-12-30 | 6 | 3424 | 6 | 3.05 | 0.2145 | 4.7 | 0.061 | 0.267 | 0.460 |
| 2009-12-30 | 10 | 2390 | 10 | 3.75 | 0.2255 | 4.4 | 0.116 | 0.269 | 0.619 |
| 2009-12-30 | 15 | 1222 | 15 | 4.84 | 0.2762 | 3.6 | nan | 0.280 | nan |
| 2012-12-30 | 3 | 7665 | 3 | 2.38 | 0.0373 | 26.8 | 0.744 | 2.088 | 0.877 |
| 2012-12-30 | 6 | 6010 | 6 | 2.88 | 0.1665 | 6.0 | 0.045 | 0.219 | 0.569 |
| 2012-12-30 | 10 | 4090 | 10 | 3.59 | 0.1732 | 5.8 | 0.075 | 0.269 | 0.438 |
| 2012-12-30 | 15 | 2232 | 15 | 4.57 | 0.1892 | 5.3 | nan | 0.232 | nan |
| 2015-12-31 | 3 | 12115 | 3 | 2.32 | 0.0098 | 102.5 | 8.566 | 1.337 | 1.357 |
| 2015-12-31 | 6 | 9528 | 6 | 2.80 | 0.1464 | 6.8 | 0.032 | 0.232 | 0.500 |
| 2015-12-31 | 10 | 6599 | 10 | 3.47 | 0.1524 | 6.6 | 0.062 | 0.220 | 0.477 |
| 2015-12-31 | 15 | 3720 | 15 | 4.38 | 0.1646 | 6.1 | 0.109 | 0.230 | nan |
| 2018-12-31 | 3 | 16820 | 3 | 2.33 | 0.0143 | 69.8 | n/a | n/a | n/a |
| 2018-12-31 | 6 | 13372 | 6 | 2.79 | 0.1323 | 7.6 | 0.036 | 0.197 | 0.476 |
| 2018-12-31 | 10 | 9405 | 10 | 3.45 | 0.1382 | 7.2 | 0.064 | 0.135 | 0.551 |
| 2018-12-31 | 15 | 5297 | 15 | 4.40 | 0.1524 | 6.6 | 0.072 | 0.286 | 1.069 |
| 2021-12-30 | 3 | 21596 | 3 | 2.31 | 0.0133 | 75.2 | n/a | n/a | n/a |
| 2021-12-30 | 6 | 17371 | 6 | 2.74 | 0.1277 | 7.8 | n/a | n/a | n/a |
| 2021-12-30 | 10 | 12268 | 10 | 3.38 | 0.1320 | 7.6 | 0.048 | 0.227 | 0.575 |
| 2021-12-30 | 15 | 7064 | 15 | 4.28 | 0.1490 | 6.7 | 0.053 | 0.166 | 0.943 |
| 2026-11-07 | 3 | 28184 | 3 | 2.22 | 0.0131 | 76.2 | n/a | n/a | n/a |
| 2026-11-07 | 6 | 22229 | 6 | 2.67 | 0.1262 | 7.9 | n/a | n/a | n/a |
| 2026-11-07 | 10 | 15545 | 10 | 3.30 | 0.1309 | 7.6 | n/a | n/a | n/a |
| 2026-11-07 | 15 | 8929 | 15 | 4.19 | 0.1490 | 6.7 | 0.066 | 0.248 | 0.765 |

| k | scheme | N* (width of gamma stays at or below 10%) | min deg / ln N* | mean deg / ln N there |
|---|---|---|---|---|
| 3 | edge | never | | |
| 3 | node 0.85 | never | | |
| 3 | node 0.5 | never | | |
| 6 | edge | 1002 | 0.87 | 2.48 |
| 6 | node 0.85 | never | | |
| 6 | node 0.5 | never | | |
| 10 | edge | 1816 | 1.33 | 3.04 |
| 10 | node 0.85 | never | | |
| 10 | node 0.5 | never | | |
| 15 | edge | 1380 | 2.07 | 4.25 |
| 15 | node 0.85 | never | | |
| 15 | node 0.5 | never | | |

For k = 6 and edge resampling the width of gamma is at or below 10% from N* = 1,002 (minimum degree
over ln N = 0.87); for k = 10 from 1,816 (1.33). Edge resampling at k = 3 never gets there, because a
3-core still contains weakly attached groups (gamma = 0.01 to 0.04 from 2009 on, against 0.12 to
0.15 for the 6-core and 10-core). Node subsampling stays at 15% to 60% for every k, because an
induced subgraph on a sampled node set is a different graph, not a perturbation of the same one.
The reading: with minimum degree at least about ln N (k = 6 at N near 1,000, k = 10 at N near
2,000) the spectral gap of edge-resampled graphs concentrates at the 10% level; without it, no
scale tested works. The 10% crossing is a few times ln N in mean degree (2.5 to 3.0 times) and
close to 1 times ln N in minimum degree.

### 4. Relaxation time and windows

Whole component, N above 5,000: gamma between 0.0046 and 0.0115, so 1/gamma between 87 and 219
steps, and a window for 10% precision of 17,000 to 44,000 steps (the 2026 cut: gamma = 0.0089,
1/gamma = 112, window 22,395, against N = 33,342). The window is of the order of N: a walk must
cross the graph about once to average an observable to 10%. The 6-core: gamma = 0.126 to 0.21,
1/gamma = 5 to 8, window 950 to 2,000 steps. The 10-core: gamma = 0.13 to 0.22 and window 900 to 1,500 steps. The relaxation time of the whole component grew by an order
of magnitude when the first weakly attached group appeared (2009); that of the cores did not.

### 5. Hodge split of the citation flow

| cut | N | triangles | gradient | curl | harmonic | width grad (node 0.7 / edge) | width curl | width harm |
|---|---|---|---|---|---|---|---|---|
| 2000-12-30 | 43 | 105 | 0.839 | 0.153 | 0.008 | 0.047 / 0.065 | 0.352 / 0.236 | 2.431 / 0.599 |
| 2001-12-30 | 161 | 955 | 0.850 | 0.148 | 0.002 | 0.042 / 0.082 | 0.312 / 0.216 | 4.920 / 0.725 |
| 2002-12-31 | 305 | 5464 | 0.814 | 0.184 | 0.002 | 0.032 / 0.049 | 0.160 / 0.108 | 0.917 / 0.447 |
| 2003-12-31 | 533 | 12390 | 0.812 | 0.186 | 0.002 | 0.019 / 0.035 | 0.102 / 0.102 | 1.840 / 0.273 |
| 2004-12-30 | 917 | 21500 | 0.816 | 0.181 | 0.003 | 0.017 / 0.020 | 0.113 / 0.063 | 0.978 / 0.328 |
| 2005-12-31 | 1404 | 34811 | 0.818 | 0.179 | 0.004 | 0.010 / 0.021 | 0.112 / 0.079 | 1.798 / 0.342 |
| 2006-12-31 | 2076 | 54570 | 0.819 | 0.177 | 0.004 | 0.008 / 0.012 | 0.023 / 0.039 | 0.613 / 0.100 |
| 2007-12-31 | 2876 | 82488 | 0.822 | 0.173 | 0.004 | 0.012 / 0.008 | 0.018 / 0.028 | 0.978 / 0.083 |
| 2008-12-30 | 3878 | 112784 | 0.825 | 0.170 | 0.005 | 0.012 / 0.006 | 0.049 / 0.020 | 1.473 / 0.088 |
| 2009-12-30 | 5066 | 143703 | 0.826 | 0.169 | 0.005 | 0.006 / 0.006 | 0.047 / 0.019 | 0.659 / 0.077 |
| 2010-12-31 | 6239 | 173279 | 0.826 | 0.168 | 0.006 | 0.006 / 0.010 | 0.054 / 0.031 | 0.802 / 0.084 |
| 2011-12-31 | 7549 | 209149 | 0.826 | 0.167 | 0.007 | 0.011 / 0.009 | 0.042 / 0.022 | 0.834 / 0.072 |
| 2012-12-30 | 8995 | 240783 | 0.826 | 0.166 | 0.008 | 0.005 / 0.007 | 0.033 / 0.017 | 0.307 / 0.039 |
| 2013-12-31 | 10591 | 282316 | 0.825 | 0.166 | 0.009 | 0.008 / 0.004 | 0.053 / 0.017 | 0.597 / 0.069 |
| 2014-12-31 | 12375 | 325206 | 0.823 | 0.166 | 0.010 | 0.003 / 0.006 | 0.046 / 0.021 | 0.479 / 0.051 |
| 2015-12-31 | 14152 | 371682 | 0.821 | 0.167 | 0.011 | 0.006 / 0.003 | 0.029 / 0.007 | 0.492 / 0.056 |
| 2016-12-30 | 15853 | 419628 | 0.819 | 0.168 | 0.013 | 0.005 / 0.007 | 0.038 / 0.022 | 0.602 / 0.029 |
| 2017-12-30 | 17619 | 463437 | 0.817 | 0.170 | 0.014 | 0.005 / 0.004 | 0.043 / 0.013 | 0.343 / 0.022 |
| 2018-12-31 | 19487 | 529135 | 0.815 | 0.170 | 0.015 | 0.006 / 0.007 | 0.050 / 0.021 | 0.499 / 0.032 |
| 2019-12-31 | 21407 | 576527 | 0.813 | 0.171 | 0.016 | 0.007 / 0.003 | 0.039 / 0.013 | 0.208 / 0.041 |
| 2020-12-30 | 23210 | 617016 | 0.811 | 0.172 | 0.018 | 0.003 / 0.004 | 0.054 / 0.013 | 0.353 / 0.020 |
| 2021-12-31 | 24926 | 660537 | 0.808 | 0.173 | 0.019 | 0.006 / 0.005 | 0.039 / 0.020 | 0.278 / 0.023 |
| 2022-12-31 | 26434 | 696613 | 0.806 | 0.174 | 0.020 | n/a | n/a | n/a |
| 2023-12-31 | 27910 | 728786 | 0.803 | 0.175 | 0.022 | n/a | n/a | n/a |
| 2024-12-30 | 28773 | 746742 | 0.801 | 0.176 | 0.023 | n/a | n/a | n/a |
| 2025-12-31 | 30584 | 767752 | 0.800 | 0.176 | 0.024 | n/a | n/a | n/a |
| 2026-11-07 | 33342 | 792324 | 0.798 | 0.175 | 0.027 | n/a | n/a | n/a |

| energy | scheme | N* (width stays at or below 10% from here up) |
|---|---|---|
| gradient | node | 7 |
| gradient | edge | 36 |
| curl | node | 1402 |
| curl | edge | 856 |
| harmonic | node | never |
| harmonic | edge | 2744 |

The split settles early and stays put. The gradient part is 0.80 to 0.83 of the energy from 2000
onward, the curl part 0.15 to 0.18, the harmonic part under 0.03 (rising slowly from 0.002 to 0.027
as the graph grows). Widths of the gradient fraction are under 10% from the smallest sizes; of the
curl fraction from N of about 900 to 1,400; of the harmonic fraction from N of about 2,700 under
edge resampling (never under node 0.7 within the range, where its width falls to 0.2 to 0.3 near
20,000). The flow quantities concentrate at scales one to two decades below gamma's.
The gradient part dominates because most citations point from newer to older works; the potential
is close to a time order.

### 6. The private-corpus contrast

A synthetic graph with 38 nodes and 20 edges in one generation (18 parent nodes, 20 child nodes,
each child with one edge to a uniformly drawn parent; nothing private was read). Over 200 draws
(`corpus.csv`):

| quantity | median (range) |
|---|---|
| components that have an edge | 12 (8 to 16) |
| largest component, nodes | 4 (3 to 6) |
| largest component, edges | 3 (2 to 5) |
| minimum degree | 1 |
| mean degree over ln N of the largest component | 1.08 (0.93 to 1.21) |
| gamma of the largest component | 1.0 (a star) |
| gamma of the whole graph | 0 (a forest with 38 - 20 = 18 components) |

The graph is a forest of stars. It has 18 components, so eigenvalue 0 has multiplicity 18, the
spectral gap is 0, and the relaxation time and every window are infinite: a walk never leaves its
component, so no macro observable averages over the corpus at any length. The largest component
(3 to 6 nodes) is below the smallest scale at which the real data's eigenvalues were computed
(N = 11), has minimum degree 1, and has a degenerate gamma (a star's value 1). Only 11 of 200 draws
have a component of at least 6 nodes, and those have width 0 for the same reason.

For scale, two connected 38-node graphs (`python -m eval.scale.corpus --references`, 200 edge
resamples each):

| graph | edges | min degree | mean degree / ln N | gamma | window, 10% | width of gamma |
|---|---|---|---|---|---|---|
| random recursive tree | 37 | 1 | 0.54 | 0.026 | 7,800 steps | 271% |
| tree plus random edges to mean degree 2 ln N | 138 | 3 | 2.00 | 0.43 | 465 steps | 47% |

Against the thresholds measured here: the corpus is far below N* (about 1,000 for a 6-core at the
10% level), far below minimum degree of order ln N (1 against 3.6), and the window is infinite. Even
the denser connected reference at N = 38 has a 47% interval, so connecting the corpus and giving it
degree 2 ln N would still leave it well under the scale of the measured crossing.

## Limits of this study

- One field, one source. Citations are time-oriented and strongly acyclic; a version chain, a
  hyperlink graph or a corpus of notes will differ. The optional Wikipedia sample was not done.
- OpenAlex reference lists are incomplete for older works, and the in-field restriction removes
  edges to outside works, which produces the degree-one nodes. The minimum-degree result is partly
  a property of this truncation.
- The symmetrization discards direction for the spectrum; the walk whose relaxation time is
  reported is the undirected one.
- Node subsampling and edge resampling are not the same experiment as drawing a fresh graph from
  the same law. The widths measure sensitivity to deletion, not sampling error of an unknown
  population. The bootstrap used 20 replicates (6 for the Hodge split), which makes the 2.5% and
  97.5% quantiles coarse; the crossings are read from pooled points and are indicative to about
  a factor of two in N.
- The required window uses relative standard deviation 1 for the observable; it scales with the
  square of the actual value.
- The 10% crossing is of a stricter form (stays below at every larger scale) than the first
  dip below 10%; the CSVs allow the other reading.

## Reproduce

```
uv run python -m eval.scale.fetch_openalex --concept C34947359 --out ~/datasets/openalex/complex-network
uv run python -m eval.scale.openalex_edges ~/datasets/openalex/complex-network
uv run python -m eval.scale.study ~/datasets/openalex/complex-network/edges.csv \
    ~/datasets/openalex/complex-network/study --first 9495 --last 20100 --step 365.25 \
    --extra 20453 20764 --reps 20 --hodge-reps 6 --max-boot-n 25000
uv run python -m eval.scale.study ... --first 11321 --last 20100 --step 365.25 \
    --extra 20453 20764 --reps 20 --cores 3 6 10 15 --max-boot-n 15000
uv run python -m eval.scale.report ~/datasets/openalex/complex-network/study
uv run python -m eval.scale.corpus > corpus.csv
uv run python -m eval.scale.corpus --references
```

Seed 0 for the study. The raw pages are the API's responses of 2026-11-07; OpenAlex changes over
time, so a rerun will differ in the last digits of N.
