# [1.16.0](https://github.com/ascalva/mind-palace/compare/v1.15.0...v1.16.0) (2026-07-22)


### Bug Fixes

* **bp-092:** write_scope core/provenance.py → core/kernel/provenance.py (K1 relocation) ([dcd79c6](https://github.com/ascalva/mind-palace/commit/dcd79c63948de22a98ac44b2dc855c28314ad40b))
* **docs:** repoint mkdocs API refs to core.kernel.* after K1/K3 relocation ([98bc7b2](https://github.com/ascalva/mind-palace/commit/98bc7b2ffd1ff76fac4a2f791ac1700a3c7293f3))


### Features

* **board:** scripts/board.py — the derived tracks x phases view + tests ([1d8169b](https://github.com/ascalva/mind-palace/commit/1d8169b424815916fa8f274cf3b1db1eabdef298))
* **templates:** add track: coordinate + resume-brief deskchecks-owed line ([9c676cc](https://github.com/ascalva/mind-palace/commit/9c676cc1f65b002e40056d9297b5473f9de19ebe))
* **tracks:** author the eight track manifests (docs/tracks/<slug>.md) ([5a603f9](https://github.com/ascalva/mind-palace/commit/5a603f92344298379d25d8554384d170a198d812))
* **workflow:** surface owed deskchecks in the brief + /triage ([d113d8a](https://github.com/ascalva/mind-palace/commit/d113d8aa95a5f3e64d8c0b76b9363cfe844abd60))

# [1.15.0](https://github.com/ascalva/mind-palace/compare/v1.14.0...v1.15.0) (2026-07-21)


### Bug Fixes

* **bp-072:** satisfy ruff + mypy CI gates (lint/type only, no behavior change) ([dde9dba](https://github.com/ascalva/mind-palace/commit/dde9dba2edcc571b5f86f35096df7d53bf923fe0))
* **bp-077:** renumber the book's finding 0116->0117 (0116 taken by the exhaust-write conflict on main); retarget 4 book refs ([d201911](https://github.com/ascalva/mind-palace/commit/d201911324d00dd69dbb1ea9d1d725f0bd95b2bc))
* **bp-078:** make plane verifier OS-portable — CI was red since the seal (finding-0124) ([ebce282](https://github.com/ascalva/mind-palace/commit/ebce2826ba123f145b2ed5946a9e25890a010069))
* **cockpit:** force umask 002 in the ouroboros-work launch (sudo resets it to 022) ([681b187](https://github.com/ascalva/mind-palace/commit/681b1872888e7a54ca977253f9b06fe2e41df2aa))
* **cockpit:** pin reading-room session to opus[1m] router default ([f41dbd1](https://github.com/ascalva/mind-palace/commit/f41dbd19d7e0493acc80c8829d32f7f21194cd6d))
* **cockpit:** quote opus[1m] so zsh doesn't glob-expand the model pin ([e8a278e](https://github.com/ascalva/mind-palace/commit/e8a278e7e878f798d277faa9f8b891ce1ba8e8cc))
* **exhaust_report:** add repo-root sys.path bootstrap so the CLI actually runs (finding-0118) ([f5f46d9](https://github.com/ascalva/mind-palace/commit/f5f46d9c657109c2d6b8ccfca8fd82f39373242a))


### Features

* **agentic-loop:** AL-1 — three actor profiles + the zone-boundary lattice law (G-D) ([9774bd7](https://github.com/ascalva/mind-palace/commit/9774bd7fe351053c930c8a2988435e57eb817d24))
* **agentic-loop:** AL-3 — exhaust⊂dialogue excluded refinement + origin(e) view (bp-088) ([9e9555f](https://github.com/ascalva/mind-palace/commit/9e9555f657b5fa9362445f92898a9dc1026525b2))
* **bp-072:** owner cockpit — docket + readmap + bless CLI + tmux reading room ([d0a5623](https://github.com/ascalva/mind-palace/commit/d0a5623c7bd683ff9375cad6285ef274a8788ac0))
* **bp-074:** stop-audit clause (e) — the session-handoff gate ([5e816e6](https://github.com/ascalva/mind-palace/commit/5e816e6aea65125be83dd0ad72aedee1f47c66dc))
* **bp-075:** pin the [exhaust] config root in defaults.toml ([d29672c](https://github.com/ascalva/mind-palace/commit/d29672ccf08dd0a70ead00309ea8062764c3be1a))
* **bp-075:** surface the [exhaust] config root via ExhaustConfig ([0338200](https://github.com/ascalva/mind-palace/commit/0338200776aaa6b2ca215826a754bc841c538da0))
* **bp-075:** the ingest-invariant test and the report writer ([2068410](https://github.com/ascalva/mind-palace/commit/2068410e2740a96fa8a2d9d8b528db104945c10a))
* **bp-078:** cockpit launches the orchestrator as ouroboros-work ([a4ea16f](https://github.com/ascalva/mind-palace/commit/a4ea16fe1eaddb0ec873392112a5f7281a050f32))
* **bp-078:** core-egress pf anchor (block ouroboros off-host, lo0 carve-out) ([ebe99bf](https://github.com/ascalva/mind-palace/commit/ebe99bf7946d5170bfb6f3756b6c5dd1a839567a)), closes [#2](https://github.com/ascalva/mind-palace/issues/2)
* **bp-078:** domain/user-aware Launcher + ouroboros daemon plist + [planes] ([c6c72da](https://github.com/ascalva/mind-palace/commit/c6c72da5677b5a52e4caa0d06d76aa2876fa1daa))
* **bp-078:** read-only four-plane verifier + per-plane self-configuring ratchets ([194ecf6](https://github.com/ascalva/mind-palace/commit/194ecf6f40a36e45f13ee62c75fd2bf12d9a17ba))
* **bp-079:** DreamCharter dispatch record + materialization boundary ([fc25809](https://github.com/ascalva/mind-palace/commit/fc25809c8b280d0c82460cee231e12a458d85656))
* **bp-080:** D-1 ARROW-READ census — reader + panel lens behind R&D flag ([beae067](https://github.com/ascalva/mind-palace/commit/beae0675950bb30a8164dcc457fce8fc038e6e0e))
* **bp-081:** H-0 + H-1 — the HYPOTHETICAL stratum and its staging substrate ([8f70eca](https://github.com/ascalva/mind-palace/commit/8f70ecaa3fe1c2aff8030b67202669cbded502b5)), closes [trou#tier](https://github.com/trou/issues/tier)
* **bp-082:** H-2 influence v1 + the conditioning law (Items 11-13) ([e50bb32](https://github.com/ascalva/mind-palace/commit/e50bb326f1a61f46e04bb2cf7da3ec0be27171db))
* **cockpit:** <leader>dr docket-refresh binding in the desk nvim ([9710854](https://github.com/ascalva/mind-palace/commit/97108549365660159eee910153bc895e3fe46edf))
* **cockpit:** orchestrator-launch wrapper — inject ouroboros-work's OAuth token + silent SSH signing ([0a3d32a](https://github.com/ascalva/mind-palace/commit/0a3d32af3d0ff7d2460dfc3880a3d2151ca561b8)), closes [#10](https://github.com/ascalva/mind-palace/issues/10)
* **cockpit:** PLANE=ascalva toggle — fable escape hatch for design/gate panes ([eb7a577](https://github.com/ascalva/mind-palace/commit/eb7a57739d8eca349e9b56a70a344d3c14c9b442))
* **cockpit:** swap PLANE default to ascalva — fable-first, isolation opt-in ([f294c3e](https://github.com/ascalva/mind-palace/commit/f294c3e07da0e14b01d047db292134f8fb4cf53a))
* **cockpit:** vim-nav pane bindings + reload runtime settings on join ([bd1cb21](https://github.com/ascalva/mind-palace/commit/bd1cb21221a6118459f2a81c4c41cab775fc8485))
* **docket:** group the render by owner action — bless / ratify / answer sections ([43d1f27](https://github.com/ascalva/mind-palace/commit/43d1f27d66e2dae7af17ae35568d345dd27f0545))
* **docket:** in-view key legend in the footer (gf is plain gf — no leader) ([3b68cd5](https://github.com/ascalva/mind-palace/commit/3b68cd5b63e2f0779450f1d0a697a1539f86b510))
* **fiber-geometry:** G-A — the read-only measure-first survey M1-M8 (bp-085) ([978b073](https://github.com/ascalva/mind-palace/commit/978b07352e656a2fcdc08265fe2e46f7af8f9c72))
* **inner-outer-core:** M0 — born-green inner-ring map + fixed-point ratchet (bp-083) ([33d6929](https://github.com/ascalva/mind-palace/commit/33d692923793eebe8abc5a82809dfe9742e1a278))
* **inner-outer-core:** S1 — temporal math↔persistence splits, INNER 30→37 (bp-089) ([d8d9d09](https://github.com/ascalva/mind-palace/commit/d8d9d09f836a64faa2a67b8a54b0918869829806))
* **palace:** queue subcommand — read-only overview of waiting jobs by kind ([57b2b01](https://github.com/ascalva/mind-palace/commit/57b2b01561a5f4364ae4c9a0cefb9fe05559a1ab))
* **statusline:** full-telemetry plane-aware statusLine ([a95986d](https://github.com/ascalva/mind-palace/commit/a95986dd573bf1c4f36f7668bf1aba127c49a141))

# [1.14.0](https://github.com/ascalva/mind-palace/compare/v1.13.0...v1.14.0) (2026-07-19)


### Bug Fixes

* **bp-073:** type-gate — mypy Tier-2 floor (object-typed rows + σ* None narrowing) ([c8802c5](https://github.com/ascalva/mind-palace/commit/c8802c5caec9255957fdfe24df12a8253b55aa1a))


### Features

* **bp-073:** Phase Δ connectivity re-measure — assemble + oq-0031 verdict (eval-side) ([6741fcf](https://github.com/ascalva/mind-palace/commit/6741fcf4a2a77200f16bd00cad3a8d4148c1a438))

# [1.13.0](https://github.com/ascalva/mind-palace/compare/v1.12.0...v1.13.0) (2026-07-19)


### Features

* **bp-071:** the chat↔code↔doc integrator — store, resolver, wiring, instruments ([2cfa0c0](https://github.com/ascalva/mind-palace/commit/2cfa0c0f320ffd30b201c6e99e1542dd4c677f67))

# [1.12.0](https://github.com/ascalva/mind-palace/compare/v1.11.0...v1.12.0) (2026-07-19)


### Bug Fixes

* **bp-046:** make shipped-manifest test registry-faithful — resolves finding-0088 ([fd0f5ff](https://github.com/ascalva/mind-palace/commit/fd0f5ff4f2c6ed7dc5d798d78758f085ccbcac92))
* **bp-065:** audit — restore module-top MirrorGraph imports in both wrappers (exact move fidelity) ([f44cf1f](https://github.com/ascalva/mind-palace/commit/f44cf1f2821f1f112a0e7e9658496fbcef317aa9))
* **ci:** deselect the intentional-red ratchet in the CI ratchet job (finding-0105 decision-A, CI half) ([5943622](https://github.com/ascalva/mind-palace/commit/5943622aeb58014a91f16cb76c1ead6261fad503))
* **ci:** repair pre-existing red CI jobs — ruff, mypy baseline, gitleaks, config Tier-2 ([c9171d4](https://github.com/ascalva/mind-palace/commit/c9171d44f3d6141cfa86330e8958869d9c3c472c))
* **core:** stop spine g2 from cycling on shared attestation hashes ([14b3140](https://github.com/ascalva/mind-palace/commit/14b31407f3ff5e094201cc1e5a5d237fbad2c410))
* **graduate-skill:** forbid inline write_scope comments + retrofit test-path pre-widen (finding-0085a) ([b65cc3f](https://github.com/ascalva/mind-palace/commit/b65cc3f51ea370ad40bc81c10c3d9f6f9c7aa64f))
* **ops:** deploy gate deselects the one intentional-red ratchet (finding-0105) ([fdfaac1](https://github.com/ascalva/mind-palace/commit/fdfaac11033356bd0d1bf5f5130e10b0e756be9d))


### Features

* **bp-046:** register dream_rnd_sigma lever + widen _config_fingerprint over the registry ([72ce216](https://github.com/ascalva/mind-palace/commit/72ce21681bdc82da49ff6d537a69d5931560bcd0))
* **bp-049:** the deterministic model-free sweep engine (E3a-1b, Items 13+14) ([21efcdf](https://github.com/ascalva/mind-palace/commit/21efcdf93b34e50be493d3e91af508a8ddadeb78))
* **bp-050:** add the σ-fibers consumer (FB-1) ([69e673f](https://github.com/ascalva/mind-palace/commit/69e673f3ea101bdb3db77dec6bfb36deab94983f))
* **bp-057:** add F9-validated σ-gate surfacing tiers ([02388fd](https://github.com/ascalva/mind-palace/commit/02388fd3f761f966780002992d2b88237e590fb4))
* **bp-059:** CN-2 σ*/MST — the abstraction ultrametric via one max spanning tree per certified cut ([67b373d](https://github.com/ascalva/mind-palace/commit/67b373df8bfa34d101a806f01aff9433e7e37e90))
* **bp-063:** item 1 — the OBSERVED-only chatlog store, utterance grain ([bfb53b2](https://github.com/ascalva/mind-palace/commit/bfb53b29870e8dc5b5573af54978b8163ba9c479))
* **bp-063:** items 2-3 — the chat sensor pipeline (retain-raw-first, tool-strip, fail-closed secret guard) ([7cc0975](https://github.com/ascalva/mind-palace/commit/7cc0975ab72db95961086386fa2d45f2a572d281)), closes [#10](https://github.com/ascalva/mind-palace/issues/10)
* **bp-065:** item 1 — σ*/MST math re-homed to core/graph, connectivity thins to the instrument ([2e362e9](https://github.com/ascalva/mind-palace/commit/2e362e9142ee40353ca0d7ea1ce38664b3a53955))
* **bp-065:** item 2 — conductance math re-homed to core/graph on core/complex's Laplacian ([53289bf](https://github.com/ascalva/mind-palace/commit/53289bf0161972a00e360a9e6665aa9e8930d082))
* **bp-068:** wire the chat sensor to RUN — chat ingests (110 sessions live); ratchet held 19 ([2093c69](https://github.com/ascalva/mind-palace/commit/2093c69249f9791a3b149668c9edb90cd9a4f56c))
* **chat-sensor:** bp-069 Item 1 — L0 growth-aware, torn-line tolerant, total accounting ([c5d8bbf](https://github.com/ascalva/mind-palace/commit/c5d8bbf362cf1b32b120c000374968a14b33325d))
* **chat-sensor:** bp-069 Item 2 — real-time trigger (DirectoryWatcher + multi-watcher launcher + [chat]) ([2821a53](https://github.com/ascalva/mind-palace/commit/2821a53dd297ad2bc1fbd4797c4c538c093383da))
* **chat-sensor:** bp-069 Item 3 — L1 action log + the born scope + D2 conformance ([632fa6f](https://github.com/ascalva/mind-palace/commit/632fa6fdaf7a2390ed7b390db6aaceb9ecf46747))
* **core:** add GC-1 derived causal event spine (read-side) ([6f49f5f](https://github.com/ascalva/mind-palace/commit/6f49f5f2b4478ed5073ad30e98a940bc633412ef))
* **core:** add GC-2 clock maps p_κ + N_s to the spine ([6e66961](https://github.com/ascalva/mind-palace/commit/6e66961c670235c98173c579e848176a2c3c6a37))
* **core:** add GC-3 certified quiescent cuts to the spine ([a6cb902](https://github.com/ascalva/mind-palace/commit/a6cb902e89765f7312f50e34519379dfcb386051)), closes [trou#quiescent](https://github.com/trou/issues/quiescent)
* **core:** add Res[T] result grade beside Inv/Rate (Rule SCALE) ([a649abd](https://github.com/ascalva/mind-palace/commit/a649abd485737d36a715c0e8460df6269575a2c9))
* **core:** add RotationReport harmonic-subspace rotation to TemporalView ([4ee0078](https://github.com/ascalva/mind-palace/commit/4ee007833c51ab041de4363ff11cf994de733c8a))
* **core:** add velocity_view alive/stale harmonic-velocity discriminator ([ad949dc](https://github.com/ascalva/mind-palace/commit/ad949dc7a7a7d4f5b9b1e7dc419a3cee75ce7800))
* **core:** bp-070 Phase Α scope tooling — DIALOGUE+fiber-C, agent layer, composed graph ([5d19a9a](https://github.com/ascalva/mind-palace/commit/5d19a9acef81c744c3f01f00d1a840109ddb015e))
* **core:** complete cross-clock T-meet via an injectable clock atlas ([5d27f2f](https://github.com/ascalva/mind-palace/commit/5d27f2f75c4764d0a67775af421098dd86683264))
* **core:** wire the chat clock — chatlog as observed-stratum g1 chains (CS-4) ([c3fef76](https://github.com/ascalva/mind-palace/commit/c3fef7616b351cfe28a43862709cda407b5e79e9))
* **dreaming:** the run ledger + shadow runner + trough job (bp-043, E2) ([196e5fc](https://github.com/ascalva/mind-palace/commit/196e5fc09699830217af567cb7a0778cf8d1740a))
* **dreaming:** wire SnapshotStore into build_dreamer (bp-045, E5(A2)) ([92b8874](https://github.com/ascalva/mind-palace/commit/92b887497f77b025689ec3a56ad5723630a559c7))
* **eval:** register sigma_persistence.* + structural_axes.* rows ([9031376](https://github.com/ascalva/mind-palace/commit/90313769e59f1c9fbaf188e2ff20ba9b87a4ecd9))
* **eval:** the eval-results store + metric registry (bp-042, E1 keystone) ([4bb201b](https://github.com/ascalva/mind-palace/commit/4bb201b73becd2282f5b7be1e9156ac63749fde4))
* **eval:** tuning manifest model + loader + resolved fingerprint (bp-047 Item 15) ([351dc6d](https://github.com/ascalva/mind-palace/commit/351dc6dc907424e3f9cea52b9a37c13d669bd397))
* **harness:** pure terminal sparkline (bp-044 Item 8, E4) ([b0331dd](https://github.com/ascalva/mind-palace/commit/b0331dd7c4a3b4c6e5deaf088ba829787c1e253b))
* **harness:** the report generator — markdown/JSON, drift study, A/B, cost appendix (bp-044 Item 9, E4) ([a6a4adb](https://github.com/ascalva/mind-palace/commit/a6a4adb816b011b0ee0067e457eedd2624ff1a95))
* **probes:** E6 Item 18 — theory-probe candidate recorder (annex-grounded) ([80c01e2](https://github.com/ascalva/mind-palace/commit/80c01e2ef448a432a0e83a6cb93ef25a4d6a10a5))
* **review:** E6 Item 17 — the model-free review REPL (signed keystroke verdicts) ([33250a3](https://github.com/ascalva/mind-palace/commit/33250a3796870f6a4813675f997f88bdd8f157b3))
* **scripts:** tune.py — the attended tuning CLI over the §14 gate (bp-047 Item 16) ([73873eb](https://github.com/ascalva/mind-palace/commit/73873eb90db56cc4f880829ac86d2089433c4908))
* **telemetry:** additive harness_cost ledger, SCHEMA_VERSION 2->3 (bp-044 Item 10, E4) ([3185d44](https://github.com/ascalva/mind-palace/commit/3185d44a0490c386793c4777e37d9a8a381a6b65))

# [1.11.0](https://github.com/ascalva/Mind-Palace/compare/v1.10.0...v1.11.0) (2026-07-15)


### Bug Fixes

* **pages:** drop the dead edge.monitor docs stub — unbreak the mkdocs build ([af64031](https://github.com/ascalva/Mind-Palace/commit/af64031db4a9f2a923eca4b6e8ce93a1d4bdf639))


### Features

* **bp-035:** ReferenceView — the deterministic reference read surface (§2.3) ([1585150](https://github.com/ascalva/Mind-Palace/commit/158515084892236743a9eeb39c5756dee7960c10))
* **bp-037:** TemporalView — the temporal algebra's first live consumer (β₁ threads) ([1a7be36](https://github.com/ascalva/Mind-Palace/commit/1a7be36da7f4f5d755fea327116279d559ee67cf))
* **bp-038:** two-snapshot ‖[d,τ]‖ citation-coherence — the algebra fully wired ([d915e85](https://github.com/ascalva/Mind-Palace/commit/d915e850d8723c330c6318e813bb1d515e61e7d8)), closes [#1](https://github.com/ascalva/Mind-Palace/issues/1)
* **scope:** req() retrofit on the five Views + Inv/Rate markers (bp-039 Items 3-4) ([f9897b5](https://github.com/ascalva/Mind-Palace/commit/f9897b5044f8c2b8b02e7e2db1838c3552bbe38d))
* **scope:** the CQ-scope algebra + laws (bp-039 Items 1-2) ([0ae9070](https://github.com/ascalva/Mind-Palace/commit/0ae90705a34925ccf9bac5a3eb17aa9ebd075720)), closes [#6](https://github.com/ascalva/Mind-Palace/issues/6)

# [1.10.0](https://github.com/ascalva/Mind-Palace/compare/v1.9.0...v1.10.0) (2026-07-15)


### Features

* **bp-030:** lifecycle control (down/up/restart) + enriched status [Items 1,3] ([7542062](https://github.com/ascalva/Mind-Palace/commit/7542062bf43a6cf5009eb2296e05e8a954f11eb4))
* **bp-030:** remove the dead edge monitor [Item 2] — bp-030 COMPLETE ([f53730a](https://github.com/ascalva/Mind-Palace/commit/f53730a554a5ab10747c5a6d04e71838cf1cdf9d))

# [1.9.0](https://github.com/ascalva/Mind-Palace/compare/v1.8.0...v1.9.0) (2026-07-14)


### Features

* **bp-036:** body-only embeddings — strip key:: props from the shared derivation (Items 13/14) ([1d731d8](https://github.com/ascalva/Mind-Palace/commit/1d731d877711cca577c6fa01336dc87d957bc826))
* **bp-036:** re-embed + dream-regeneration experiment harness (Item 15) ([16c4694](https://github.com/ascalva/Mind-Palace/commit/16c469433c7aabffd8d4568da2db30969868ca3b))

# [1.8.0](https://github.com/ascalva/Mind-Palace/compare/v1.7.0...v1.8.0) (2026-07-14)


### Features

* **bp-034:** owner-gated doc_id re-key primitive + verifier rider (Item 14) ([a440dba](https://github.com/ascalva/Mind-Palace/commit/a440dba444a3e9e5eca6c3b3e8461c0c5ffb1b72))
* **bp-034:** the id-mint migrator + owner script + e2e verify (Items 13/15/16) ([20b810f](https://github.com/ascalva/Mind-Palace/commit/20b810f7e547dc161c3ce0cc2fc4c870e7eb1633))
* **ingest:** rename-stable doc_id — decouple identity from source_path (bp-031) ([f002985](https://github.com/ascalva/Mind-Palace/commit/f0029854a67ff5a0d3502368cba9cb8cde837617))
* **research:** persist the EMBED tail into a curated store (bp-029 Items 27–30) ([ac8824a](https://github.com/ascalva/Mind-Palace/commit/ac8824ab627a81d4a22cc1837d8b719e331aed2d))
* **temporal:** the mode-3 operators + superconnection curvature ‖[d,τ]‖ (bp-033) ([3379e7c](https://github.com/ascalva/Mind-Palace/commit/3379e7c020b115a84711027950267731e8a16e8c))
* **temporal:** X_cite citation complex + the dim ker L₁ == β₁ falsifier (bp-032) ([07686fb](https://github.com/ascalva/Mind-Palace/commit/07686fb5661128e102dbb65dcd09699696503fbf))

# [1.7.0](https://github.com/ascalva/Mind-Palace/compare/v1.6.0...v1.7.0) (2026-07-13)


### Bug Fixes

* **ops:** ci_witness — guard check()/release() against non-full sha ([7c13b28](https://github.com/ascalva/Mind-Palace/commit/7c13b2868f3c67a00e17f55501696735f8f98827))


### Features

* **hooks:** stop-audit (d) — flag cross-checkout state bleed (finding-0051 fix 2) ([ce692f0](https://github.com/ascalva/Mind-Palace/commit/ce692f0bd3bd059e5e1a0db409a2f7b633e6a308))
* **research:** wire the live research driver (bp-028 Items 23–26) ([97d98ca](https://github.com/ascalva/Mind-Palace/commit/97d98ca8d77dce5f899f43986f98d2bd14b8b516))

# [1.6.0](https://github.com/ascalva/Mind-Palace/compare/v1.5.0...v1.6.0) (2026-07-13)


### Bug Fixes

* **code-sensor:** revert INTERPRETER_VERSION over-bump — re-pin, not bump (bp-026) ([7b93a2d](https://github.com/ascalva/Mind-Palace/commit/7b93a2d9ec8d6017325a60c32dca7ab16b6bf689))


### Features

* **reference-edges:** symmetric v2 schema + doc↔doc extractor (bp-026 Items 18-20) ([d0fcf5a](https://github.com/ascalva/Mind-Palace/commit/d0fcf5a782f3475e5171ef12388d6498e03fa2b8))

# [1.5.0](https://github.com/ascalva/Mind-Palace/compare/v1.4.0...v1.5.0) (2026-07-13)


### Bug Fixes

* **bp-019:** implement the §6(f) warning path — unparseable non-null cost warns ([6fc4e26](https://github.com/ascalva/Mind-Palace/commit/6fc4e264c2815eb1779104728038fa909c733be3))
* **core:** register the agent identity key in the observation-history sidecar ([6b4daa6](https://github.com/ascalva/Mind-Palace/commit/6b4daa614d0c1d8ab27d702fa2e37da3a95e6c54))


### Features

* **bp-019:** AgentObservationStore — the OBSERVED-only agent-observation stratum ([f6b94ba](https://github.com/ascalva/Mind-Palace/commit/f6b94ba98f7c32ba82ba546f2178c023595b1379))
* **bp-019:** AgentSensingHandoff — the sensing seam's third sibling ([c0322e1](https://github.com/ascalva/Mind-Palace/commit/c0322e16f37b8941c4b12f270d9ea3a1c728b9d2))
* **bp-019:** phi_self v1.0.0 — the cost-stream projector (ops/self_sensor.py) ([4ec7b9b](https://github.com/ascalva/Mind-Palace/commit/4ec7b9b284a2da96aee2c1ac4ff78e4b3a8f3831))
* **bp-019:** wire the self sensor — hook line, driver script, reset entry ([e48c56e](https://github.com/ascalva/Mind-Palace/commit/e48c56e81203c8193b3082ed261a3ef245c88876))
* **config:** add thread_min_persistence (bp-022 Item 4) ([d513d76](https://github.com/ascalva/Mind-Palace/commit/d513d769d53038989e144379161db44f56e8e09a))
* **core:** add the observation-history sidecar, ledger-class and append-only ([e4bf8a6](https://github.com/ascalva/Mind-Palace/commit/e4bf8a67b0fb63f7988411c9f6eb4deab0f0a555))
* **core:** version-key the code-observation store; archive-then-replace ([33d4dc9](https://github.com/ascalva/Mind-Palace/commit/33d4dc96515a868843fc1a60857612463eb0b57e))
* **dreaming:** the THREAD lens — harmonic H1 flow (bp-022 Item 5) ([d0fedc0](https://github.com/ascalva/Mind-Palace/commit/d0fedc06416aa1fdf7259d081fecabad3b78175e))
* **ops:** declare phi_code's interpreter version + the source-hash ratchet ([f8a2f95](https://github.com/ascalva/Mind-Palace/commit/f8a2f95f31f09bb32ef2d17dc4c2a9403f011029))
* **ops:** wire the interpreter version end-to-end; guard the history sidecar ([f087695](https://github.com/ascalva/Mind-Palace/commit/f0876959ec82ff39df4d58825b2d875531b8fe71))
* **temporal:** degree-1 invariants in structural snapshots (bp-022 Item 6) ([833172c](https://github.com/ascalva/Mind-Palace/commit/833172c2745af1f6bb7b1ddb331f4fea12e0010b))

# [1.4.0](https://github.com/ascalva/Mind-Palace/compare/v1.3.0...v1.4.0) (2026-07-12)


### Bug Fixes

* **hooks:** strip trailing inline comment on a quoted write_scope entry ([3c166d6](https://github.com/ascalva/Mind-Palace/commit/3c166d6a29d704b46ed8852629abd426271701a1)), closes [ready#x](https://github.com/ready/issues/x)
* **hooks:** worktree-aware ROOT so enforcement reads the worktree's own active-plan ([65825e7](https://github.com/ascalva/Mind-Palace/commit/65825e7874efe227e41a73db940d5aec96fe2764))
* **mkdocs:** re-point site_url/repo_url to the GitHub Pages host ([de4e6cd](https://github.com/ascalva/Mind-Palace/commit/de4e6cd3e7450ea7dbdbc18e617d45031cdcdd4d)), closes [#4](https://github.com/ascalva/Mind-Palace/issues/4)
* **pages:** add setup-uv step — uvx absent on hosted runners; first live run red at build ([1528ffd](https://github.com/ascalva/Mind-Palace/commit/1528ffd10bb51343370a12be5643a3c877882c63))
* **release:** node 24 on the release runner — semantic-release 25 needs >=22.14 ([c82b53e](https://github.com/ascalva/Mind-Palace/commit/c82b53e36d0ed11f3a9977cab91b5eab66e408ce))
* **tests:** type-arg CompletedProcess[str] to hold the mypy exact-69 baseline (bp-014 CI red) ([d23e0d6](https://github.com/ascalva/Mind-Palace/commit/d23e0d689fc2f12421a6287600e8eb53dc61785b))


### Features

* **bp-011:** V4 reference inventory probe — code<->corpus reference edges ([69dbb9c](https://github.com/ascalva/Mind-Palace/commit/69dbb9c7896d55927e6486397c6950640b2595f2))
* **core:** code-observation store — OBSERVED-only, identity-keyed, mint-disciplined (bp-012 Item 3) ([0a9b37e](https://github.com/ascalva/Mind-Palace/commit/0a9b37eb3b74052bdbdab268e644ea57988f545b))
* **hodge:** add core/complex/hodge.py — the Hodge 1-Laplacian family ([556a09a](https://github.com/ascalva/Mind-Palace/commit/556a09a449f91bb0c0fea8607972de7479eb586a))
* **hooks:** auto-surface resume-brief at the top of the session brief ([06c1aa1](https://github.com/ascalva/Mind-Palace/commit/06c1aa1402d2f9d18fb0668c97fad5497fa1b1e7))
* **ops:** code-observation store joins reset_targets — corpus-side wipe (bp-012 Item 4) ([f966078](https://github.com/ascalva/Mind-Palace/commit/f9660781518b51cd325b171a0aa2c4fcd917c836))
* **ops:** docstring column on the code-snapshot ledger (bp-011 Item 1, B-a) ([6a897cb](https://github.com/ascalva/Mind-Palace/commit/6a897cb2a9782d592f789fc05fdb9caf2e68cada))
* **ops:** register reference_edges.sqlite as a corpus-layer reset target (bp-013 Q4) ([11ffc01](https://github.com/ascalva/Mind-Palace/commit/11ffc01f8e2c312e4ea13f31cd701716692eca2f))
* **ops:** sync() projects phi_code — the observed stratum gains code observations (bp-012 Item 5) ([a1df6da](https://github.com/ascalva/Mind-Palace/commit/a1df6da8501875dafaa234484a8c2d67282a8d16))
* **ops:** type_gate.py — Tier-2 membership + bare-ignore scans (bp-008 Item 8) ([7ccf401](https://github.com/ascalva/Mind-Palace/commit/7ccf401567f01fd5496c01a43e10d22c621185ec))
* **sensor:** Lane-1 reference extraction at projection time (bp-013 Item 7) ([e20bb09](https://github.com/ascalva/Mind-Palace/commit/e20bb09994eddd5bd64d5b71db100868354105b3))
* **stores:** Lane-1 reference-edge store — cross-stratum, balance-isolated (bp-013 Item 6) ([201d61d](https://github.com/ascalva/Mind-Palace/commit/201d61d1f6b374c31c0b9fe92a1021f137ebf691))

# [1.3.0](https://gitlab.com/ascalva-projects/mind-palace/compare/v1.2.0...v1.3.0) (2026-07-11)


### Bug Fixes

* **core:** Message becomes a TypedDict; annotate factory/server entry points ([08a4d0c](https://gitlab.com/ascalva-projects/mind-palace/commit/08a4d0c0d2b285a4a387ebb3819e5cd3b0cbd751))
* **core:** type the config parameter family as Config | None ([8a945a0](https://gitlab.com/ascalva-projects/mind-palace/commit/8a945a01575e4ec28f54c66f8af10e2461883ad8))


### Features

* **core:** Authored[T]/Derived[T] static shadow + verdict-gated promote() stub (bp-009 Item 10) ([5a6e9c5](https://gitlab.com/ascalva-projects/mind-palace/commit/5a6e9c546cc4877de2f7d9c935d5dd52e7fc4e74))
* **core:** typedshims boundary wrappers for lancedb/sknetwork/psutil ([54ebbcb](https://gitlab.com/ascalva-projects/mind-palace/commit/54ebbcb59fc18033f5d5db48d7da795af503c71d))
* **hooks:** A8 status-aware design-note guard — draft-writable, blessed-immutable ([4fe6ad4](https://gitlab.com/ascalva-projects/mind-palace/commit/4fe6ad46aea727d5cf2470367a629c0c070d9393))

# [1.2.0](https://gitlab.com/ascalva-projects/mind-palace/compare/v1.1.0...v1.2.0) (2026-07-11)


### Bug Fixes

* **deps:** declare ripser (core/complex/topology.py) + git in the CI image ([f80e6b2](https://gitlab.com/ascalva-projects/mind-palace/commit/f80e6b2d601efdeee117092e8a817ebf61a5ba20))
* fix mp-env.sh bugs ([6c2e6a6](https://gitlab.com/ascalva-projects/mind-palace/commit/6c2e6a6cda62a6bbe23ba08dfea0678337a8b3d4))
* fix mp-env.sh label checker function ([20ce4d3](https://gitlab.com/ascalva-projects/mind-palace/commit/20ce4d373c0bfd8094ad7711795c1038a03efbf3))
* reset wipes the four provenance sidecar stores (owner-instructed) ([1db295a](https://gitlab.com/ascalva-projects/mind-palace/commit/1db295a0ed941403a9c438ca6a5f56a093ed6ed8))
* rm temp lift global deny ([f5d435d](https://gitlab.com/ascalva-projects/mind-palace/commit/f5d435db66776192ccfb5dba02710ab1a374fef9))
* scope supersede [C]-grounding prohibition to derived C ([87ed48e](https://gitlab.com/ascalva-projects/mind-palace/commit/87ed48ece711be7771d1ed7021fe5380741dc6a9))
* temp lift global deny ([d6e518f](https://gitlab.com/ascalva-projects/mind-palace/commit/d6e518fd9641e9306fb4882143aab3f452e3b808))
* **tests:** hermetic config for the sealed-core live test ([90857e4](https://gitlab.com/ascalva-projects/mind-palace/commit/90857e4a9dfea4495a3e394f3e2cd6a8a59883e4))


### Features

* Added claude development automation, steering, skills, and hook file ([0b21de6](https://gitlab.com/ascalva-projects/mind-palace/commit/0b21de67b879312f8b57e1c38b62e1b74ef02c3a))
* Added the authored-historical supersession store ([a096f3c](https://gitlab.com/ascalva-projects/mind-palace/commit/a096f3cb12f1c42156b520f90bd58aa690411826))
* code-sensor agent — model-less pipeline agent over the repo instrument ([e75974c](https://gitlab.com/ascalva-projects/mind-palace/commit/e75974c675eafcbbfcd4be8cd6bf48b2ca02a0a1))
* **ops:** ci-witness attestations + release-on-deploy + vault CI axis ([e3e0f16](https://gitlab.com/ascalva-projects/mind-palace/commit/e3e0f16119db91494cb8444eab0fadb3e2241eb2))
* **ops:** ci-witness token self-rotation — verify-before-store, attested ([f33eb99](https://gitlab.com/ascalva-projects/mind-palace/commit/f33eb993aac63f53f18a2dd7e1bf206988300f73))
* **ops:** commit house rule + typed ledger lookup + main-only ingest ([ec6ddd3](https://gitlab.com/ascalva-projects/mind-palace/commit/ec6ddd39a356de99ee5b10f4acc400d791ce8111))
* **ops:** mind-palace supersede — owner CLI for the phone-capture flow ([97d5687](https://gitlab.com/ascalva-projects/mind-palace/commit/97d56877ce9ad8335facb46e63cda588da9976ab))
* **ops:** palace deploy — the promotion gate for the always-on system ([48ebcdf](https://gitlab.com/ascalva-projects/mind-palace/commit/48ebcdf351c50d5c3efc734bfd49e4f64cb5fdc0))
* per-commit structural code snapshots (ops/code_snapshot.py) ([01e34e9](https://gitlab.com/ascalva-projects/mind-palace/commit/01e34e9e368e7800548ab98e21e3007932a2c230))
* Revision to edges ([a9e8423](https://gitlab.com/ascalva-projects/mind-palace/commit/a9e8423e54df2ba0b910d325f785c4df4a8ce830))

# [1.1.0](https://gitlab.com/ascalva-projects/mind-palace/compare/v1.0.0...v1.1.0) (2026-07-04)


### Bug Fixes

* Add design notes ([4da6796](https://gitlab.com/ascalva-projects/mind-palace/commit/4da6796ef5bffe3afc6cda46aed03e20ae19231c))


### Features

* Add Founding Corpus Path ([5934f92](https://gitlab.com/ascalva-projects/mind-palace/commit/5934f9272fd6f8a1994703c93afe77a7dc4392f5))
* Added supersession edges, but stop to re-consider type overload ([43eb3db](https://gitlab.com/ascalva-projects/mind-palace/commit/43eb3dbfa37ef0d6fd0458943737976a7173c538))
* Checkpointing work before proceeding to next sub-phase ([5f9867d](https://gitlab.com/ascalva-projects/mind-palace/commit/5f9867d04b513ff00a74ee52bf30dcc51669fc56))

# 1.0.0 (2026-07-04)


### Bug Fixes

* add lockfile ([9aadcf4](https://gitlab.com/ascalva-projects/mind-palace/commit/9aadcf4eacbe0d8fcc7894fbf72d1015c93bdad6))
* update fragments ref ([b3f91a3](https://gitlab.com/ascalva-projects/mind-palace/commit/b3f91a37b337c7d933b1340a807fa1d4b63391d2))


### Features

* Add Ambassador Design Notes ([6ffeeee](https://gitlab.com/ascalva-projects/mind-palace/commit/6ffeeee3f9e3cc4c7401c7ef647689769de3d0e2))
* Add LICENSE File ([848323b](https://gitlab.com/ascalva-projects/mind-palace/commit/848323b09519ae3db2118c406e4d04dd04215e27))
* Add Semantic Release ([1a9ce1e](https://gitlab.com/ascalva-projects/mind-palace/commit/1a9ce1edb3f8b862a2d8d699b5a7171033ce067d))
* Add vault integration and refactor tests ([5e433a3](https://gitlab.com/ascalva-projects/mind-palace/commit/5e433a3380a059612b3e84426356a5ea013453f9))
* Added chunk-digest re-verification ([3ef8436](https://gitlab.com/ascalva-projects/mind-palace/commit/3ef8436352fd34215fd4df61e1cad289ae6e57f7))
* Added Security through strong typed system proposal ([0237c49](https://gitlab.com/ascalva-projects/mind-palace/commit/0237c491ceff319ae098d9f99eaed4fbee5c2663))
* Added Sourcesets and refactor/organize docs ([5a2a392](https://gitlab.com/ascalva-projects/mind-palace/commit/5a2a392d6354957101772ad0f47e0f1d122e1865))
* Added support propagation and temporal self-watching ([db36900](https://gitlab.com/ascalva-projects/mind-palace/commit/db369008ebe173ab3a7c6a76d2e4fb7be9e2d240))
* Added the hands catalog and the acting classes ([e0bf1ad](https://gitlab.com/ascalva-projects/mind-palace/commit/e0bf1ad7da148bdc476ea7b4c11440724159e0fd))
* Audit and Index Design/Research Notes ([852e6e1](https://gitlab.com/ascalva-projects/mind-palace/commit/852e6e17d14898c3d8ee0b6940c0a77a32bf2cc6))
* Built the structural interpreters ([6246df6](https://gitlab.com/ascalva-projects/mind-palace/commit/6246df6f2ede61a9d4a5a74756f27a0a9f13379c))
* Complete Attestation Core ([87dd13e](https://gitlab.com/ascalva-projects/mind-palace/commit/87dd13e57c62fe022761b43c2c5071ef6f5f2b7f))
* Completed Vault End-to-End testing complete ([c920a7c](https://gitlab.com/ascalva-projects/mind-palace/commit/c920a7cdc675509304c82d2554e88a52fc56370d))
* Completed Vault Production Setup With AWS IAM Roles to access cloud ([060a1f6](https://gitlab.com/ascalva-projects/mind-palace/commit/060a1f6604334bacfe72d611cdb2ebe6f064e7ba))
* Completed Vault Wire-Up and Tests (mocked and live) ([0619b58](https://gitlab.com/ascalva-projects/mind-palace/commit/0619b58da51f086a0201ce996306e0bf179a73de))
* Constitution assembly seam closed ([02949dd](https://gitlab.com/ascalva-projects/mind-palace/commit/02949ddad5cb668e573df1e0c28f6d47aa6ecc34))
* Documention cleanup ([8cc68e8](https://gitlab.com/ascalva-projects/mind-palace/commit/8cc68e834059f986199606117237260d5cadd87f))
* Drift Gauge Complete ([6aa0f0c](https://gitlab.com/ascalva-projects/mind-palace/commit/6aa0f0cde94b7b98142dbd12b0b2fb5d9744e7c3))
* Finalize WASM runner, created master process starter, finalized ambassador wiring ([b8f0d44](https://gitlab.com/ascalva-projects/mind-palace/commit/b8f0d446b23eb5169d22aaf875123d1007e3d5ab))
* Finalize Wire-Up, Adds Monitoring, Thin Parent Orchestrator Process, and Update Docs ([fd9de05](https://gitlab.com/ascalva-projects/mind-palace/commit/fd9de054325cafe32fe1ca151e7566639798af55))
* Hands: the type, the gate, read-only sensing (β = 0, safe, parallelizable) ([82d92e7](https://gitlab.com/ascalva-projects/mind-palace/commit/82d92e7a47d5336aed5b2456574144fcccb1a430))
* Logic Hardening Phase Complete ([b9c1906](https://gitlab.com/ascalva-projects/mind-palace/commit/b9c19060525447198e30417ec2e07a3811d64fea))
* Mathematical Reframe of System Started ([68e2df2](https://gitlab.com/ascalva-projects/mind-palace/commit/68e2df2453e896bd49a326e92f4814fc7a194d3b))
* Phase 0 complete ([cf07ade](https://gitlab.com/ascalva-projects/mind-palace/commit/cf07adef1d5b18b1d310f8955db205cadad88e69))
* Phase 1 complete ([7502109](https://gitlab.com/ascalva-projects/mind-palace/commit/7502109eaa7d067609d3f274e8b81120c89b7e99))
* Phase 10 Complete ([6dabf30](https://gitlab.com/ascalva-projects/mind-palace/commit/6dabf309663bee0d75fbe0f0355649a8ae686865))
* Phase 2 complete ([6fe8dad](https://gitlab.com/ascalva-projects/mind-palace/commit/6fe8dad11ada0ae1c1060f90e5ad859870f762bc))
* Phase 3 complete ([daa5966](https://gitlab.com/ascalva-projects/mind-palace/commit/daa5966d365a8f6fca40440d60e6c29adb91d8c4))
* Phase 5 complete ([074edf5](https://gitlab.com/ascalva-projects/mind-palace/commit/074edf5a0a2ae7035179026049b4879b307609f8))
* Phase 6 complete ([cb8bc6d](https://gitlab.com/ascalva-projects/mind-palace/commit/cb8bc6d8ee9b1bc9bb47ab30aff81c449fba80c3))
* Phase 7 complete ([e91cdb7](https://gitlab.com/ascalva-projects/mind-palace/commit/e91cdb7918c9a4aa54193b468936535d1b5e31c8))
* Phase 8 Checkpoint (in progress) ([240d39f](https://gitlab.com/ascalva-projects/mind-palace/commit/240d39fe71e21f26d13ea3e32a5fce247c5f7af2))
* Phase 8 Complete ([8650bc4](https://gitlab.com/ascalva-projects/mind-palace/commit/8650bc46da09b2136754fe17d2685429472be8e8))
* Phase 8.5 Complete (detour into further dreaming r&d, harden ingestion pipeline) ([da74170](https://gitlab.com/ascalva-projects/mind-palace/commit/da741700482d3de367aeaa81806a82da78b30a94))
* Phase 9 Complete ([1a9bb8d](https://gitlab.com/ascalva-projects/mind-palace/commit/1a9bb8d8bb233c1e98895cc673dd5131daacae70))
* R&D Dreaming Phase Complete ([1aaf2d5](https://gitlab.com/ascalva-projects/mind-palace/commit/1aaf2d59a2e911b61ac9e3ab9cebf4920bc79585))
* Tested and Setup File Sync and Fixed Watchdog bug ([17c087d](https://gitlab.com/ascalva-projects/mind-palace/commit/17c087dde58371a1e3bb44b5ed1f5d67aed1ac35))
* The reasoning-complex core is built ([b1b93be](https://gitlab.com/ascalva-projects/mind-palace/commit/b1b93bee1a4838497c719183668bf14565dd757d))
* Update README ([6067a34](https://gitlab.com/ascalva-projects/mind-palace/commit/6067a34beb473319c8483fcab8f194ee1eeaa631))
