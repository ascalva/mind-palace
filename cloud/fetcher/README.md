# cloud/fetcher — the research fetcher (Zone C Lambda)

Broad public-literature aggregation, triggered by a de-identified criteria request landing in
S3 `requests/`. Writes a public-literature corpus to S3 `results/`. Runs in the public cloud,
sees **only de-identified criteria**, never private data (BUILD-SPEC §16).

- `sources.py` — key-free public API clients (OpenAlex, Europe PMC, arXiv), normalized to a
  common record. Stdlib `urllib`/`xml` only; the HTTP `fetch` is injected for testing.
- `aggregate.py` — gather → de-dup by DOI/title → bias toward systematic reviews / meta-
  analyses / guidelines → flag preprints as not-yet-vetted → drop unresolvable identifiers.
- `handler.py` — Lambda entrypoint. `process_request` / `handle_event` are pure/injectable;
  `lambda_handler` wires real boto3 + network.

**Dependency-free** (`requirements.txt` is empty): stdlib + the boto3 already in the Lambda
runtime, so the deployment zip is reproducible and minimal. Terraform (`cloud/terraform/
airlock`) zips this directory and deploys it.

**IAM:** `GetObject requests/*` + `PutObject results/*` + CloudWatch Logs. Nothing else. The
Lambda is intentionally **not** in a VPC so it has public internet egress to the literature
APIs — that egress reaches only public endpoints; it has no path to anything private.

Tested in `tests/test_fetcher.py` (fake fetch + fake S3 client; no network).
