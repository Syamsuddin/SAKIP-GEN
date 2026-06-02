# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

SAKIP-Gen is an AI **evaluator + drafter** for Indonesian local-government performance
accountability (SAKIP, per PermenPAN-RB 88/2021). It runs *alongside* an existing SAKIP web
app + MySQL, and is reached through a **Telegram bot** and a **Telegram Mini App** (webview).
A single FastAPI process serves the healthcheck, the Telegram webhook, and the Mini App, with
an in-process scheduler.

Codebase comments, docstrings, identifiers, and user-facing strings are in **Indonesian** —
match that language when editing or adding code.

## Commands

```bash
# Setup
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

# Tests (must be 101 passed; no MySQL needed — SQLite in-memory + in-process ASGI)
python -m pytest -q
python -m pytest tests/test_fase4.py -q            # one phase file
python -m pytest tests/test_fase4.py::test_terapkan_happy -q   # one test

# Lint / type-check (config in pyproject.toml)
ruff check .
mypy .

# Demo evaluation without MySQL (seeds SQLite, prints score/predikat/gap)
python demo_evaluasi.py

# Run the bot locally via long-polling (no HTTPS/webhook needed)
cp .env.example .env     # fill BOT_TOKEN, WEBHOOK_SECRET, PUBLIC_BASE_URL at minimum
python dev_polling.py

# Production entrypoint (1 worker — scheduler is in-process; behind Nginx+TLS)
gunicorn app:app -c deploy/gunicorn.conf.py
```

Tests map 1:1 to implementation phases: `tests/test_faseN.py` covers the Fase N changes
described in [CHANGELOG.md](CHANGELOG.md). When you change a phase's code, update its test file.

## Governance model (non-negotiable design constraints)

These four pillars shape the whole architecture — preserve them in any change:

1. **MySQL is the single source of truth.** The `ai_*` tables are staging/derived only.
2. **The agent's direct DB access is read-only.** Every write goes through a human-approved
   staging path.
3. **The agent is an evaluator + drafter, not a decider.** It never sets official scores.
4. **Human-in-the-loop + server-side audit.** Telegram is a *trigger*, not the system of record.

Critically, the read / staging / promote separation is enforced by **three distinct MySQL
credentials with least-privilege GRANTs — not by application flags.** This is realized in
[db/engines.py](db/engines.py) as three independent lazy engines:

| Engine getter | Env URL | Privilege | Used for |
|---|---|---|---|
| `get_ro_engine` | `DB_RO_URL` | `SELECT` | building Dosir / analytics ([db/queries.py](db/queries.py)) |
| `get_staging_engine` | `DB_STAGING_URL` | `INSERT/SELECT/UPDATE` on `ai_usulan`, `INSERT/SELECT` on `ai_event` | proposals ([db/staging.py](db/staging.py)) |
| `get_promote_engine` | `DB_PROMOTE_URL` | `SELECT` + column-level `UPDATE` on the indicator columns allowed by the active profile (esakip: `nama,jenis_indikator` on `sakip_indikator`; reference: `uraian,satuan,tipologi` on `indikator`), `INSERT ai_audit` | applying approved proposals ([db/promote.py](db/promote.py)) |

## Architecture & data flow

The core flow, layer by layer:

1. **`db/queries.py` + `db/profiles/`** read SAKIP source tables (RO engine) and assemble a
   **Dosir Kinerja** (`agent/dosir.py`) — the normalized performance dossier for one OPD + year.
   The **schema seam is now the profile adapter**: `bangun_dosir` delegates to the active
   `SchemaProfile` (`DB_SCHEMA_PROFILE`) — `reference`
   ([db/ddl/schema_referensi.sql](db/ddl/schema_referensi.sql), demo/tests) or `esakip`
   ([db/mysql/schema.sql](db/mysql/schema.sql), real). **Onboarding a new eSAKIP = writing one
   profile class** (`db/profiles/base.py` Protocol), not editing core. The profile also exposes
   `ambil_temuan`, `ambil_capaian` (periodic), `ambil_dokumen`, `ambil_cascading`. SQL is portable
   and derived values are computed in Python so the same code runs on SQLite in tests.
2. **`agent/evaluator.py`** scores the Dosir against the LKE model (PermenPAN-RB 88/2021):
   **Pengungkit 60 + Hasil 40** — Perencanaan 18, Pengukuran 18, Pelaporan 9, Evaluasi Internal 15,
   Capaian Kinerja 40 — a total `nilai`, an **AA–D predikat**, prioritized `GapTemuan`, and data
   `peringatan` (integrity). Weights are overridable via `LKE_BOBOT`. The scoring is a
   **transparent heuristic / approximation** that needs calibration to the official LKE rubric.
3. **`agent/improver.py`** turns gaps into `UsulanPerbaikan` proposals (output→outcome
   indicator rewrites). `_rumusan_outcome` is heuristic; `agent/llm.py` optionally refines it
   via Anthropic/Ollama with a heuristic fallback.
4. **`db/staging.py`** persists drafts to `ai_usulan` (draft → disetujui/ditolak).
5. **`db/promote.py`** `terapkan_usulan()` applies an *approved* proposal to the source table.
   This is the most sensitive code; it enforces four guards in one transaction: status must be
   `disetujui`; **optimistic lock** (re-hash current source via `hash_indikator` and compare to
   `hash_data_lama`, reject if changed); **column whitelist** = the active profile's
   `kolom_diizinkan`; and transactional before→after audit into `ai_audit`. Promotion is
   human-triggered only.

Entry points and the Telegram/web layer:

- **[app.py](app.py)** — FastAPI app + lifespan (sets webhook, starts scheduler, runs
  `audit_keamanan` warnings). Routes: `/healthz`, `/readyz` (checks all 3 DB engines),
  `POST /webhook/<WEBHOOK_SECRET>` (constant-time secret compare, feeds updates to the aiogram
  Dispatcher).
- **[bot/instance.py](bot/instance.py)** — builds `bot` + `dp`; middleware order is
  **throttle (outer) → audit → auth (inner) → handler**. `kinerja_router` is included before
  `base_router` so specific commands win over the fallback.
- **[bot/auth.py](bot/auth.py)** — allowlist + RBAC. `User.boleh_opd()` gates OPD access;
  `User.boleh_promosi()` (kepala_dinas/admin) gates `/terapkan`. Public commands
  (`/start`, `/help`, `/ping`, `/daftar`) bypass registration; `ADMIN_TELEGRAM_IDS` grants admin
  without `/daftar`. Default repo is **in-memory** (lost on restart); set `USE_SQL_AUTH=true` to use
  the SQL repo (`bot/auth_sql.py`, `db/ddl/auth.sql`).
- **Unified command grammar** — both `/slash` and **natural language** produce one `Permintaan`
  ([agent/permintaan.py](agent/permintaan.py), closed `AKSI_VALID` enum) executed by a single
  dispatcher `_jalankan` in [bot/kinerja.py](bot/kinerja.py). NL goes through
  [agent/nlu.py](agent/nlu.py): heuristic `parse()` → LLM `parse_llm()` (structured) → grounding
  (`cocokkan_opd`) → execute or polite clarification (never raw errors; `/terapkan` is blocked via NL).
- **[bot/kinerja.py](bot/kinerja.py)** — data verbs: `/daftar`, `/nilai`(=`/evaluasi`), `/gap`,
  `/rencana`, `/capaian`, `/laporan`, `/temuan`, `/dokumen`, `/tren`, `/benchmark`, `/usul`,
  `/usulan`, `/status`, `/opd`, `/terapkan`, plus the `nl_handler`.
- **[bot/menu.py](bot/menu.py)** — `setMyCommands` per scope: global default + per-chat menus by
  role (operator/kepala_dinas/admin), set at startup and after `/daftar`.
- **[web/](web/)** — Mini App form + HTTP hardening. `web/security.py` issues opaque tokens
  (itsdangerous) and validates Telegram `initData`; `web/middleware.py` adds security headers,
  request-id, and a body-size cap; `web/ratelimit.py` is a per-process `SlidingWindowLimiter`.

## Key gotchas

- **Single worker only.** The scheduler runs in-process and rate-limit/throttle state is
  per-process, so production uses `workers=1`. Multi-worker would need a shared store (Redis)
  and would double-fire the scheduler.
- **Engines are lazy and overridable.** `get_*_engine()` build on first use and only require
  `DB_*_URL` then — so Fase 0/1 and all tests run without MySQL. Tests inject SQLite via
  `set_ro_engine` / `set_staging_engine` / `set_promote_engine` (see
  [tests/test_fase4.py](tests/test_fase4.py), which points all three at one SQLite DB to
  simulate a single MySQL).
- **Config is `pydantic-settings` from `.env`**, cached via `get_settings()` (`@lru_cache`).
  Only `bot_token`, `webhook_secret`, `public_base_url` are required; DB/LLM settings are
  optional so partial deployments work. `audit_keamanan()` emits non-fatal startup warnings
  in `env=production`.
- **Auto-apply only supports `tipe == "perbaikan_indikator"`.** Other proposal types are
  drafted but rejected by `terapkan_usulan`.

## Where to look

`docs/` holds the authoritative deep docs: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
(unified dispatcher, NL pipeline, schema profiles, module map),
[docs/DATA_MODEL.md](docs/DATA_MODEL.md) (domain models, scoring algorithm 88/2021, both schema
mappings), [docs/INTERFACES.md](docs/INTERFACES.md) (bot commands, natural language, per-role menu,
endpoints, Mini App), [docs/USER_GUIDE.md](docs/USER_GUIDE.md),
[docs/EXECUTIVE_SUMMARY.md](docs/EXECUTIVE_SUMMARY.md), [docs/SECURITY.md](docs/SECURITY.md),
[docs/CONFIGURATION.md](docs/CONFIGURATION.md) (all `.env` vars), [docs/INSTALL.md](docs/INSTALL.md),
and [deploy/DEPLOY.md](deploy/DEPLOY.md) (go-live runbook). DDL for the `ai_*` tables lives in
[db/ddl/](db/ddl/); the real eSAKIP schema/seed/grants in [db/mysql/](db/mysql/).
