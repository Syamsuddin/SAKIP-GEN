"""Sambungan LLM (Fase 7, dimatangkan Fase 3) — merumuskan ulang indikator output → outcome.

Penyedia: Anthropic (bila `ANTHROPIC_API_KEY`) atau Ollama (bila `OLLAMA_HOST`).
Bila tak ada penyedia atau panggilan gagal, fungsi mengembalikan None → pemanggil
memakai fallback heuristik. Kematangan Fase 3:

- **Caching respons** (memoisasi per (uraian, satuan, tipologi)) — kunci penghematan
  biaya; rumusan identik tak memanggil API berulang.
- **Retry/timeout**: ditangani SDK Anthropic (max_retries + timeout pada klien;
  backoff eksponensial untuk 429/5xx). Tidak di-reimplementasi manual.
- **Circuit breaker**: setelah beberapa gagal beruntun, panggilan dilewati sementara
  (cooldown) agar tak menghantam API yang sedang bermasalah.
- **Pelacakan token/biaya**: usage dari respons dicatat ke log.

Catatan: prompt caching Anthropic TIDAK dipakai — prefix sistem jauh di bawah ambang
cacheable Haiku (≈4096 token), jadi tak akan ter-cache. Memoisasi sisi-aplikasi di
sini yang memberi penghematan nyata.
"""
from __future__ import annotations

import logging
import time

import metrics
from config import get_settings

logger = logging.getLogger("sakip-gen.llm")

_SISTEM = (
    "Anda perumus indikator kinerja SAKIP pemerintah daerah yang mengacu PermenPAN-RB. "
    "Tugas: mengubah indikator OUTPUT/proses menjadi OUTCOME yang mengukur hasil/manfaat "
    "bagi masyarakat, selaras sasaran strategis. Jawab RINGKAS satu kalimat Bahasa "
    "Indonesia formal, tanpa tanda kutip, tanpa penjelasan tambahan."
)

# Few-shot: contoh output→outcome khas SAKIP (T3.3).
_CONTOH = (
    "Contoh:\n"
    "- Output: \"Jumlah sekolah yang direhabilitasi\" (satuan: unit)\n"
    "  Outcome: Persentase sekolah dengan kondisi ruang kelas layak\n"
    "- Output: \"Jumlah pelatihan UMKM yang diselenggarakan\" (satuan: kegiatan)\n"
    "  Outcome: Persentase UMKM binaan yang naik kelas omzet\n"
)

# --- State per-proses: cache respons + circuit breaker ---
_CACHE: dict[tuple[str, str, str], str] = {}
_CACHE_MAKS = 512
_circuit = {"gagal_beruntun": 0, "buka_sampai": 0.0}
_CB_AMBANG = 3        # gagal beruntun sebelum sirkuit dibuka
_CB_COOLDOWN = 60.0   # detik sirkuit terbuka


def reset_llm_state() -> None:
    """Kosongkan cache & circuit breaker (dipakai pengujian)."""
    _CACHE.clear()
    _circuit["gagal_beruntun"] = 0
    _circuit["buka_sampai"] = 0.0


def _kunci(uraian: str, satuan: str | None, tipologi: str | None) -> tuple[str, str, str]:
    return (uraian.strip().lower(), (satuan or "").lower(), (tipologi or "").lower())


def _prompt(uraian: str, satuan: str | None, tipologi: str | None, sasaran: str | None) -> str:
    konteks = f"Sasaran strategis induk: \"{sasaran}\".\n" if sasaran else ""
    return (
        f"{_CONTOH}\n"
        f"{konteks}"
        f"Indikator bertipologi '{tipologi or 'tak diketahui'}' dan masih berorientasi output:\n"
        f"\"{uraian}\" (satuan: {satuan or '-'}).\n"
        "Tulis ULANG menjadi satu indikator OUTCOME yang mengukur hasil/manfaat dan "
        "selaras sasaran di atas. Keluarkan HANYA rumusan indikatornya."
    )


def llm_tersedia(settings=None) -> bool:
    s = settings or get_settings()
    return bool(s.anthropic_api_key or s.ollama_host)


def _catat_biaya(usage) -> None:
    try:
        logger.info(
            "LLM usage: input=%s output=%s cache_read=%s",
            getattr(usage, "input_tokens", "?"),
            getattr(usage, "output_tokens", "?"),
            getattr(usage, "cache_read_input_tokens", 0),
        )
    except Exception:  # noqa: BLE001
        pass


async def _via_anthropic(prompt: str, settings, system: str | None = None) -> str | None:
    try:
        from anthropic import AsyncAnthropic
    except Exception:  # noqa: BLE001 — paket belum terpasang
        return None
    model = settings.llm_model or "claude-haiku-4-5"
    try:
        # SDK menangani retry (max_retries) + timeout dengan backoff eksponensial.
        client = AsyncAnthropic(api_key=settings.anthropic_api_key, max_retries=2, timeout=30.0)
        resp = await client.messages.create(
            model=model, max_tokens=160, system=system or _SISTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        _catat_biaya(getattr(resp, "usage", None))
        teks = " ".join(
            b.text for b in resp.content if getattr(b, "type", None) == "text"
        ).strip()
        return teks or None
    except Exception as e:  # noqa: BLE001
        logger.warning("LLM Anthropic gagal: %s", e)
        return None


async def _via_ollama(prompt: str, settings, system: str | None = None) -> str | None:
    import httpx

    base = settings.ollama_host.rstrip("/")
    model = settings.llm_model or "llama3"
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(
                f"{base}/api/generate",
                json={"model": model, "prompt": (system or _SISTEM) + "\n\n" + prompt,
                      "stream": False},
            )
            r.raise_for_status()
            return (r.json().get("response") or "").strip() or None
    except Exception as e:  # noqa: BLE001
        logger.warning("LLM Ollama gagal: %s", e)
        return None


def _sirkuit_terbuka(now: float) -> bool:
    return now < _circuit["buka_sampai"]


def _catat_hasil(berhasil: bool, now: float) -> None:
    if berhasil:
        _circuit["gagal_beruntun"] = 0
        _circuit["buka_sampai"] = 0.0
    else:
        _circuit["gagal_beruntun"] += 1
        if _circuit["gagal_beruntun"] >= _CB_AMBANG:
            _circuit["buka_sampai"] = now + _CB_COOLDOWN
            logger.warning("LLM circuit breaker terbuka %.0fs setelah %d gagal beruntun.",
                           _CB_COOLDOWN, _circuit["gagal_beruntun"])


async def rumuskan_outcome(
    uraian: str, satuan: str | None = None, tipologi: str | None = None, *,
    sasaran: str | None = None, settings=None,
) -> str | None:
    """Kembalikan rumusan outcome dari LLM, atau None bila tak tersedia/gagal/sirkuit terbuka."""
    s = settings or get_settings()
    if not llm_tersedia(s):
        return None

    kunci = _kunci(uraian, satuan, tipologi)
    if kunci in _CACHE:
        return _CACHE[kunci]

    now = time.monotonic()
    if _sirkuit_terbuka(now):
        logger.info("LLM dilewati: circuit breaker masih terbuka.")
        metrics.inc("sakipgen_llm_total", hasil="skip")
        return None

    prompt = _prompt(uraian, satuan, tipologi, sasaran)
    if s.anthropic_api_key:
        hasil = await _via_anthropic(prompt, s)
    elif s.ollama_host:
        hasil = await _via_ollama(prompt, s)
    else:
        return None

    _catat_hasil(hasil is not None, now)
    metrics.inc("sakipgen_llm_total", hasil="ok" if hasil else "gagal")
    if hasil:
        if len(_CACHE) >= _CACHE_MAKS:
            _CACHE.clear()
        _CACHE[kunci] = hasil
    return hasil


async def jawab_singkat(prompt: str, *, system: str, settings=None) -> str | None:
    """Panggilan LLM umum (route + circuit breaker, TANPA caching) untuk klasifikasi/NLU.

    Dipakai deteksi mislabel (T3.4) & penerjemah bahasa alami (agent/nlu.parse_llm).
    None bila tak tersedia/gagal/sirkuit terbuka.
    """
    s = settings or get_settings()
    if not llm_tersedia(s):
        return None
    now = time.monotonic()
    if _sirkuit_terbuka(now):
        return None
    if s.anthropic_api_key:
        hasil = await _via_anthropic(prompt, s, system=system)
    elif s.ollama_host:
        hasil = await _via_ollama(prompt, s, system=system)
    else:
        return None
    _catat_hasil(hasil is not None, now)
    metrics.inc("sakipgen_llm_total", hasil="ok" if hasil else "gagal")
    return hasil


_SISTEM_KLASIFIKASI = (
    "Anda penilai indikator kinerja SAKIP. Tentukan apakah RUMUSAN indikator benar-benar "
    "sesuai TIPOLOGI yang diklaim (outcome/impact = mengukur hasil/manfaat; output = keluaran "
    "kegiatan). Jawab HANYA satu kata: SESUAI atau TIDAK."
)


async def deteksi_mislabel_llm(uraian: str, tipologi: str | None, *, settings=None) -> bool | None:
    """T3.4 — verifikasi semantik tipologi via LLM.

    Kembalikan True bila rumusan TAK sesuai tipologi (mis. dilabeli outcome tapi berbau
    output), False bila sesuai, None bila tak tersedia/gagal/ambigu (→ pakai heuristik T2.4).
    """
    prompt = (
        f"Tipologi diklaim: {tipologi or 'tak diketahui'}\n"
        f"Rumusan indikator: \"{uraian}\"\n"
        "Apakah rumusan SESUAI tipologi tersebut?"
    )
    hasil = await jawab_singkat(prompt, system=_SISTEM_KLASIFIKASI, settings=settings)
    if not hasil:
        return None
    t = hasil.strip().lower()
    if t.startswith("tidak"):
        return True       # mislabel terdeteksi
    if t.startswith("sesuai"):
        return False
    return None
