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
