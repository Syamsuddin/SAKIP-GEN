"""Metrik Prometheus minimal (Fase 4) — tanpa dependensi eksternal.

Counter in-proses + eksposisi format teks Prometheus (dibaca di GET /metrics). Modul
daun: hanya bergantung stdlib, sehingga aman diimpor lintas lapisan (agent/db/web/bot)
tanpa membalik arah ketergantungan. Cocok untuk 1 worker; multi-worker memerlukan
agregasi terpusat (lihat rencana T5.1).
"""
from __future__ import annotations

import threading

_lock = threading.Lock()
_counters: dict[tuple[str, tuple[tuple[str, str], ...]], float] = {}

_HELP = {
    "sakipgen_evaluasi_total": "Jumlah evaluasi LKE dijalankan",
    "sakipgen_usulan_total": "Jumlah draft usulan dibuat",
    "sakipgen_penerapan_total": "Jumlah penerapan usulan ke tabel sumber (per hasil)",
    "sakipgen_llm_total": "Jumlah panggilan perumusan LLM (per hasil)",
    "sakipgen_nlu_total": "Jumlah terjemahan bahasa alami (per hasil)",
    "sakipgen_error_total": "Jumlah error HTTP tak tertangani",
}


def inc(nama: str, value: float = 1.0, **labels: str) -> None:
    """Naikkan counter `nama` (opsional berlabel)."""
    key = (nama, tuple(sorted(labels.items())))
    with _lock:
        _counters[key] = _counters.get(key, 0.0) + value


def reset() -> None:
    """Kosongkan seluruh counter (dipakai pengujian)."""
    with _lock:
        _counters.clear()


def render() -> str:
    """Eksposisi teks Prometheus (text/plain; version=0.0.4)."""
    with _lock:
        items = sorted(_counters.items())
    lines: list[str] = []
    seen: set[str] = set()
    for (nama, labels), val in items:
        if nama not in seen:
            seen.add(nama)
            lines.append(f"# HELP {nama} {_HELP.get(nama, nama)}")
            lines.append(f"# TYPE {nama} counter")
        lab = "{" + ",".join(f'{k}="{v}"' for k, v in labels) + "}" if labels else ""
        lines.append(f"{nama}{lab} {val}")
    return "\n".join(lines) + "\n"
