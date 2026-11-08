"""The open corpus's edge readers (dn-corpus-instance §5.2, §7): the only processes of the corpus
instance that touch the network.

One reader a source, each run by the operator (`scripts/corpus.py fetch <name>`), never by a
request: it fetches its source politely (one connection, the source's own rate limit, a generic
User-Agent that names the tool and no person), reduces each item to the landing form (the prose,
its markup removed, its title prepended) and appends it to the source's stream under the
instance's root, with the item's metadata (dates, relations, identifiers) beside it in
`meta/items.jsonl`. The stream is the handoff to the lander (`core/ingest/stream.py`): nothing
here imports the core, and nothing in the core imports this package. Every reader resumes where
it stopped and stops at its byte budget.
"""
