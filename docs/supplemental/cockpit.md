# The owner cockpit — dotfiles snippets & the read-map format

Supplemental to bp-072 (decision-routing v1). The repo ships the **session and the data**
(`scripts/cockpit.sh`, `scripts/docket.py`, `scripts/readmap.py`, the `palace bless` flip);
your **dotfiles own the editor**. This file is the boundary: the editor-side tailoring lives
here as *proposals you adopt by hand* — nothing here is written by an agent or applied
automatically. Copy what you want into `~/.config/nvim/` and `~/.tmux.conf`.

Open the cockpit with `./scripts/cockpit.sh` (idempotent — re-run to re-join, never
rebuilds). It lays out a `desk` window (the docket in vim, left · a `claude` session, right)
and an `ops` window (`palace status` + the daemon log), sets a status-bar awaiting-count, and
turns on `focus-events` for the current server at runtime.

---

## The guide-not-gate rule (read this first — the trust surface, named honestly)

> The agent curating the read map is a filter that could hide things. Mitigations: the FULL
> diff is always one `:DiffviewOpen` away; the read map is a guide, never the only path; audit
> sampling (decision-routing's gauge) occasionally reads beyond the map. Curation aids
> attention; it never substitutes for access.

The docket and the read map **point**; they never **gate**. Every blessing, ratification, and
answer is still the owner's deliberate act. `palace bless` is a keystroke over the hand edit —
same guarantees, refused to agents (it exits non-zero when `CLAUDECODE` is set) — not a new
authority.

---

## nvim snippets (adopt by hand)

```lua
-- Live buffers: the docket / a journal refreshes on pane focus while a build runs.
vim.o.autoread = true
vim.api.nvim_create_autocmd({ "FocusGained", "BufEnter" }, {
  command = "checktime",
})

-- Act by keystroke: bless the plan whose buffer you just read (owner-run; the agent
-- never touches this — the Stop-gate blessing audit is unchanged either way).
-- Prompts for the plan id, defaulting to the token under the cursor (e.g. `bp-072`).
vim.keymap.set("n", "<leader>pb", function()
  local default = vim.fn.expand("<cword>")
  local id = vim.fn.input("bless plan: ", default)
  if id ~= "" then
    vim.cmd("!uv run scripts/palace.py bless " .. vim.fn.shellescape(id))
  end
end, { desc = "palace bless <plan-id>" })

-- Read-map traversal: walk a seal's curated reading as a native quickfix list.
-- :PalaceRead bp-073  ->  :cfile <the map>  ->  ]q / [q to step, the *why* on each line.
vim.api.nvim_create_user_command("PalaceRead", function(opts)
  local tmp = vim.fn.tempname()
  local ok = os.execute("uv run scripts/readmap.py " .. vim.fn.shellescape(opts.args) .. " > " .. tmp)
  if ok == 0 then
    vim.cmd("cfile " .. tmp)       -- populate the quickfix list; ]q / [q to walk
    vim.cmd("copen")
  else
    vim.notify("no structured read-map block for " .. opts.args .. " (legacy prose seal?)", vim.log.levels.WARN)
  end
end, { nargs = 1, desc = "load a seal's read map into quickfix" })

-- Docket refresh: regenerate the derived view and (re-)open it, one keystroke.
-- The cockpit's own docket nvim already ships this map (cockpit.sh passes it via -c
-- at launch — session-owned, like the tmux settings). Adopt here only if you want
-- the same keystroke in every nvim you open at the repo, not just the cockpit's.
vim.keymap.set("n", "<leader>dr", function()
  vim.cmd("silent !uv run scripts/docket.py --write")
  vim.cmd("edit .claude/state/docket.md")
end, { desc = "refresh + open the docket" })

-- Suggested plugins (a toolchain, not a requirement):
--   render-markdown.nvim  -- the docket & journals render as prose, not raw markdown
--   diffview.nvim         -- :DiffviewOpen — the FULL diff, always one command away (guide-not-gate)
```

## tmux snippet (`~/.tmux.conf`, adopt by hand)

`cockpit.sh` sets `focus-events` on the running server at launch (ephemeral, repo-owned). To
make it permanent for every session, add the line to your config — this is the dotfile side of
the same setting:

```tmux
set -g focus-events on
```

### Session-switching tips

The cockpit lives in its own `palace` session, so you keep your own session alongside it and
jump between them like cmd+tab: `prefix + s` opens the choose-tree (pick any session), and
`prefix + L` toggles to the last session (a fast two-session flip). `cockpit.sh` is
`$TMUX`-aware — run from inside tmux it `switch-client`s to `palace` (never nests), run from a
bare shell it `attach`es.

---

## The exhaust lane — build reports on your phone (owner-side, by hand)

The **exhaust lane** (`dn-exhaust-lane`) is the outbound mirror of the vault: where the vault
Syncthing share carries the corpus *in* (owner-written, system-read), the exhaust share carries
system-emitted artifacts *out* (system-written, owner-read) — starting with delegated-build
reports as self-contained HTML you read on your phone. It is a **separate Syncthing share**,
`~/.mind-palace/exhaust/`, a *sibling* to the vault — never a subdirectory (structural isolation:
the ingest scanner has no configured path to it, and a unit test enforces that no source root can
lie inside it). The root is pinned once in config (`config/defaults.toml [exhaust] path`) and read
through `get_config().exhaust.path`, so the writer and the invariant test never drift.

Two one-time, owner-performed setup steps (nothing here is automated — the system writes files
into the lane; you pair it and read it):

1. **Pair the share in SyncTrain.** Add `~/.mind-palace/exhaust` as a new folder in Syncthing and
   share it to your phone over Tailscale — exactly as the vault share is paired, one extra folder.
   Private default (Constitution 11): Syncthing-over-Tailscale, no third party.
2. **Add the iPhone Files shortcut.** In the Files app, favorite the synced
   `…/exhaust/reports/` directory. Reports are named `YYYY-MM-DD-<bp-id>-<slug>.html`, so Files
   sorts them newest-first by name; tap one and it renders in place (self-contained, theme-aware —
   no external assets, dark-mode aware).

The writer that places a report (the orchestrator runs this at merge-ready; it composes the
report, the script only places it):

```sh
uv run scripts/exhaust_report.py <composed.html> --plan bp-NNN --slug <slug>
# -> writes <exhaust>/reports/YYYY-MM-DD-bp-NNN-<slug>.html  (creates reports/;
#    refuses a silent overwrite — pass --force to replace an existing dated report)
```

**Guide, not gate (the bp-072 rule holds here too).** A report is a *review surface*: every
blessing, apply, or merge it mentions is still performed at your keyboard. The lane delivers what
happened for you to read; it never acts. The system writes exhaust and reads the vault; neither
lane reads the other.

---

## The read-map block format (seals author this, session-33 onward)

Every sealed plan's journal carries a **read map**: the load-bearing ~15–20% of the diff worth
reading, so the owner reads the design and the falsifiers, not the mechanical coverage. From
now on it is a fenced `read-map` block — `scripts/readmap.py <plan-id>` emits the **last** such
block in the journal **verbatim** as vim quickfix lines (the authoring format *is* the output
format, so nothing transforms and nothing drifts):

````markdown
```read-map
eval/harness/re_measure.py:41: the co-production projection — the fail-loud witness
tests/unit/test_re_measure.py:118: the falsifier worth reading
core/mirror.py:210: why the bottleneck is NOT the proven edge (one-line why per span)
```
````

- One quickfix line per span: **`path:line: why`**. The `path:line` prefix is what vim jumps
  to; the trailing text after the second `:` is the one-line reason it's on the map.
- Order the spans by reading priority: design first, then load-bearing code, then the
  falsifier-encoding tests. Mechanical coverage is *counted*, not listed ("+11 tests; 3 worth
  reading").
- A listed path that no longer exists still emits (readmap warns to stderr, keeps the line) —
  the map records where the concept lived at seal time.
- Legacy seals wrote this as prose; `readmap.py` does **not** parse prose — it exits 1 with an
  honest message rather than guess. Old seals are not back-filled.

The **checkpoint** skill carries the authoring cross-reference: a seal's read map is written in
this block format (added to that skill by the orchestrator at seal time — outside builder
scope).
