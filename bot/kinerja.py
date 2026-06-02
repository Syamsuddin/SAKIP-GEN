"""Perintah inti SAKIP-Gen: pendaftaran, evaluasi, gap, status, usulan (Fase 3),
dan penerapan ke tabel sumber (Fase 4, dipicu manusia & berjenjang)."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)

import metrics
from agent import nlu
from agent.analitik import benchmark_opd, keselarasan_sasaran, tren_opd
from agent.dosir import DosirKinerja
from agent.improver import cari_sasaran_indikator, sempurnakan_dengan_llm, usulkan_dari_gap
from agent.llm import jawab_singkat, llm_tersedia
from agent.permintaan import Permintaan, kanonik_dokumen
from agent.service import (
    capaian_periode,
    cascading_opd,
    dokumen_opd,
    evaluasi_opd,
    temuan_opd,
)
from bot.auth import User, get_repo
from bot.format import format_gap, format_ringkasan
from bot.menu import pasang_menu_untuk
from config import get_settings
from db.promote import terapkan_usulan
from db.queries import daftar_opd
from db.staging import ambil_usulan, daftar_usulan, perbarui_draft, putuskan_usulan, simpan_draft
from web.security import buat_token

logger = logging.getLogger("sakip-gen.kinerja")
router = Router(name="kinerja")


def _satuan_indikator(dosir: DosirKinerja, indikator_id: str) -> str | None:
    for s in dosir.perencanaan.sasaran_strategis:
        for i in s.indikator:
            if i.indikator_id == indikator_id:
                return i.satuan
    return None


async def _sempurnakan_latar(uid: int, u, sasaran, satuan, message, kb) -> None:
    """Tugas latar: haluskan rumusan via LLM, simpan, lalu edit pesan. (T3.1 — lepas dari webhook.)"""
    asli = next((p.usulan for p in u.perubahan if p.field == "uraian"), None)
    try:
        u2 = await sempurnakan_dengan_llm(u, sasaran=sasaran, satuan=satuan)
        baru = next((p.usulan for p in u2.perubahan if p.field == "uraian"), None)
        if baru and baru != asli:
            await perbarui_draft(uid, u2)
            await message.edit_text(_ringkas_usulan(u2, uid), reply_markup=kb)
    except Exception as exc:  # noqa: BLE001 — best-effort; draft heuristik tetap valid
        logger.warning("Penyempurnaan LLM latar gagal untuk usulan #%s: %s", uid, exc)


def _parse(args: str | None) -> tuple[int | None, int]:
    parts = (args or "").split()
    opd = int(parts[0]) if parts and parts[0].lstrip("-").isdigit() else None
    tahun = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else datetime.now().year
    return opd, tahun


def _ringkas_usulan(u, uid: int) -> str:
    baris = [
        f"<b>Usulan #{uid} — perbaikan indikator {u.indikator_id}</b>",
        f"{u.instansi} · Tahun {u.tahun}",
        "",
    ]
    for p in u.perubahan:
        baris.append(f"• <i>{p.field}</i>:")
        if p.lama:
            baris.append(f"   lama: {p.lama}")
        baris.append(f"   usulan: <b>{p.usulan}</b>")
    baris += ["", f"Estimasi kenaikan: +{u.estimasi_poin} ({u.gap_lke})",
              "Tinjau lewat tombol di bawah."]
    return "\n".join(baris)


def _ringkas_penerapan(h) -> str:
    baris = [f"<b>Usulan #{h.usulan_id} diterapkan ke tabel sumber.</b>", ""]
    for k in h.field_diterapkan:
        baris.append(f"• {k}: {h.sebelum.get(k)} → <b>{h.sesudah.get(k)}</b>")
    if h.field_diabaikan:
        baris += ["", "Field diabaikan (di luar whitelist): " + ", ".join(h.field_diabaikan)]
    baris += ["", "Tercatat di audit. Status usulan: <b>diterapkan</b>."]
    return "\n".join(baris)


@router.message(Command("daftar"))
async def cmd_daftar(message: Message, command: CommandObject) -> None:
    kode = (command.args or "").strip()
    if not kode:
        await message.answer("Format: <code>/daftar &lt;kode&gt;</code>")
        return
    user = await get_repo().register(message.from_user.id, kode)
    if user is None:
        await message.answer("Kode pendaftaran tidak valid atau sudah dipakai.")
        return
    # Sesuaikan menu perintah dengan peran pengguna (best-effort).
    await pasang_menu_untuk(message.bot, message.from_user.id, user.peran)
    opd = ", ".join(map(str, user.opd_ids)) or "(belum diatur)"
    await message.answer(
        f"Pendaftaran berhasil. Selamat datang, <b>{user.nama}</b> ({user.peran}).\n"
        f"OPD: {opd}\nKetik /help untuk melihat perintah."
    )


# ---------- Helper aksi (dipakai perintah /slash MAUPUN bahasa alami) ----------
async def _aksi_evaluasi(message: Message, opd: int, tahun: int) -> None:
    try:
        _, hasil = await evaluasi_opd(opd, tahun)
    except Exception:  # noqa: BLE001
        await message.answer("Gagal mengambil data evaluasi. Periksa parameter atau koneksi data.")
        return
    await message.answer(format_ringkasan(hasil))


async def _aksi_gap(message: Message, opd: int, tahun: int) -> None:
    try:
        _, hasil = await evaluasi_opd(opd, tahun)
    except Exception:  # noqa: BLE001
        await message.answer("Gagal mengambil data. Periksa parameter atau koneksi data.")
        return
    await message.answer(format_gap(hasil))


async def _aksi_tren(message: Message, opd: int, tahun: int) -> None:
    try:
        kini, lalu, delta = await tren_opd(opd, tahun)
    except Exception:  # noqa: BLE001
        await message.answer("Gagal mengambil data tren. Periksa parameter atau koneksi data.")
        return
    arah = "▲" if delta["total"] > 0 else ("▼" if delta["total"] < 0 else "■")
    baris = [
        f"<b>Tren — {kini.instansi}</b>",
        f"{lalu.tahun}: {lalu.nilai_total:.2f} ({lalu.predikat}) → "
        f"{kini.tahun}: {kini.nilai_total:.2f} ({kini.predikat})",
        f"Delta total: {arah} {delta['total']:+.2f}",
        "", "Per komponen:",
    ]
    baris += [f"• {nama}: {d:+.1f}" for nama, d in delta["komponen"].items()]
    await message.answer("\n".join(baris))


async def _aksi_benchmark(message: Message, user: User, tahun: int) -> None:
    opds = [o["id"] for o in await daftar_opd()] if user.is_admin else list(user.opd_ids)
    if not opds:
        await message.answer("Tidak ada OPD untuk dibandingkan.")
        return
    try:
        rank = await benchmark_opd(opds, tahun)
    except Exception:  # noqa: BLE001
        await message.answer("Gagal menyusun benchmark. Periksa koneksi data.")
        return
    if not rank:
        await message.answer("Tidak ada data evaluasi untuk OPD tersebut.")
        return
    baris = [f"<b>Peringkat OPD — {tahun}</b> (estimasi indikatif)", ""]
    baris += [f"{r}. {nama} — <b>{nilai:.2f}</b>" for r, nama, nilai in rank]
    await message.answer("\n".join(baris))


async def _aksi_usul(message: Message, user: User, opd: int, tahun: int) -> None:
    try:
        dosir, hasil = await evaluasi_opd(opd, tahun)
    except Exception:  # noqa: BLE001
        await message.answer("Gagal mengambil data. Periksa parameter atau koneksi data.")
        return
    kandidat = usulkan_dari_gap(dosir, hasil, maksimal=1)
    if not kandidat:
        await message.answer("Tidak ada indikator output yang perlu dirumuskan ulang.")
        return
    u = kandidat[0]
    # Simpan draft heuristik & balas CEPAT (jangan blokir webhook dengan panggilan LLM).
    uid = await simpan_draft(u)
    token = buat_token(uid, message.from_user.id)
    s = get_settings()
    base = s.miniapp_base_url or f"{s.public_base_url.rstrip('/')}/usulan"
    url = f"{base}?t={token}"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Buka form lengkap", web_app=WebAppInfo(url=url))],
        [
            InlineKeyboardButton(text="Setujui", callback_data=f"setuju:{uid}"),
            InlineKeyboardButton(text="Tolak", callback_data=f"tolak:{uid}"),
        ],
    ])
    sent = await message.answer(_ringkas_usulan(u, uid), reply_markup=kb)
    # Penghalusan LLM dilepas ke latar; hasilnya menyusul lewat edit pesan (T3.1).
    if llm_tersedia():
        sasaran = cari_sasaran_indikator(dosir, u.indikator_id)
        satuan = _satuan_indikator(dosir, u.indikator_id)
        asyncio.create_task(_sempurnakan_latar(uid, u, sasaran, satuan, sent, kb))


# ---------- Perintah /slash ----------
@router.message(Command("evaluasi", "nilai"))
async def cmd_evaluasi(message: Message, command: CommandObject, user: User) -> None:
    opd, tahun = _parse(command.args)
    if opd is None:
        await message.answer("Format: <code>/nilai &lt;opd_id&gt; [tahun]</code>")
        return
    if not user.boleh_opd(opd):
        await message.answer("Anda tidak memiliki akses ke OPD tersebut.")
        return
    await _aksi_evaluasi(message, opd, tahun)


@router.message(Command("gap"))
async def cmd_gap(message: Message, command: CommandObject, user: User) -> None:
    opd, tahun = _parse(command.args)
    if opd is None:
        await message.answer("Format: <code>/gap &lt;opd_id&gt; [tahun]</code>")
        return
    if not user.boleh_opd(opd):
        await message.answer("Anda tidak memiliki akses ke OPD tersebut.")
        return
    await _aksi_gap(message, opd, tahun)


@router.message(Command("tren"))
async def cmd_tren(message: Message, command: CommandObject, user: User) -> None:
    opd, tahun = _parse(command.args)
    if opd is None:
        await message.answer("Format: <code>/tren &lt;opd_id&gt; [tahun]</code>")
        return
    if not user.boleh_opd(opd):
        await message.answer("Anda tidak memiliki akses ke OPD tersebut.")
        return
    await _aksi_tren(message, opd, tahun)


@router.message(Command("benchmark"))
async def cmd_benchmark(message: Message, command: CommandObject, user: User) -> None:
    _, tahun = _parse(command.args)
    await _aksi_benchmark(message, user, tahun)


@router.message(Command("usul"))
async def cmd_usul(message: Message, command: CommandObject, user: User) -> None:
    opd, tahun = _parse(command.args)
    if opd is None:
        await message.answer("Format: <code>/usul &lt;opd_id&gt; [tahun]</code>")
        return
    if not user.boleh_opd(opd):
        await message.answer("Anda tidak memiliki akses ke OPD tersebut.")
        return
    await _aksi_usul(message, user, opd, tahun)


@router.message(Command("terapkan"))
async def cmd_terapkan(message: Message, command: CommandObject, user: User) -> None:
    arg = (command.args or "").strip()
    if not arg.isdigit():
        await message.answer("Format: <code>/terapkan &lt;usulan_id&gt;</code>")
        return
    if not user.boleh_promosi():
        await message.answer("Hanya Kepala Dinas/Admin yang dapat menerapkan usulan ke data sumber.")
        return
    uid = int(arg)
    u = await ambil_usulan(uid)
    if u is None:
        await message.answer("Usulan tidak ditemukan.")
        return
    if not user.boleh_opd(u.opd_id):
        await message.answer("Anda tidak berwenang atas OPD usulan ini.")
        return
    if u.status != "disetujui":
        await message.answer(
            f"Usulan #{uid} berstatus '{u.status}'. Hanya yang 'disetujui' dapat diterapkan."
        )
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Konfirmasi terapkan", callback_data=f"terapkan_ok:{uid}"),
        InlineKeyboardButton(text="Batal", callback_data=f"terapkan_batal:{uid}"),
    ]])
    await message.answer(
        f"Akan menerapkan Usulan #{uid} (indikator {u.indikator_id}) ke <b>tabel sumber</b>.\n"
        "Tindakan ini mengubah data resmi dan tercatat di audit. Lanjutkan?",
        reply_markup=kb,
    )


async def _aksi_status(message: Message, user: User) -> None:
    opd = ", ".join(map(str, user.opd_ids)) or "(belum diatur)"
    promosi = "ya" if user.boleh_promosi() else "tidak"
    await message.answer(
        "<b>SAKIP-Gen aktif.</b>\n"
        f"Terdaftar sebagai: <b>{user.nama}</b> ({user.peran})\n"
        f"OPD yang dapat diakses: {opd}\n"
        f"Hak menerapkan ke sumber: {promosi}"
    )


@router.message(Command("status"))
async def cmd_status(message: Message, user: User) -> None:
    await _aksi_status(message, user)


async def _putuskan(call: CallbackQuery, user: User, status: str, label: str) -> None:
    try:
        uid = int(call.data.split(":", 1)[1])
    except (ValueError, IndexError):
        await call.answer("Data tombol tidak valid.", show_alert=True)
        return
    u = await ambil_usulan(uid)
    if u is None:
        await call.answer("Usulan tidak ditemukan.", show_alert=True)
        return
    if not user.boleh_opd(u.opd_id):
        await call.answer("Anda tidak berwenang atas OPD ini.", show_alert=True)
        return
    await putuskan_usulan(uid, ditinjau_oleh=user.nama, status=status)
    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:  # noqa: BLE001
        pass
    await call.message.answer(
        f"Usulan #{uid} <b>{label}</b>. Peninjau: {user.nama}."
        + (" Tersimpan di staging untuk promosi." if status == "disetujui" else "")
    )
    await call.answer(label.capitalize() + ".")


@router.callback_query(F.data.startswith("setuju:"))
async def cb_setuju(call: CallbackQuery, user: User) -> None:
    await _putuskan(call, user, status="disetujui", label="disetujui")


@router.callback_query(F.data.startswith("tolak:"))
async def cb_tolak(call: CallbackQuery, user: User) -> None:
    await _putuskan(call, user, status="ditolak", label="ditolak")


@router.callback_query(F.data.startswith("terapkan_ok:"))
async def cb_terapkan_ok(call: CallbackQuery, user: User) -> None:
    try:
        uid = int(call.data.split(":", 1)[1])
    except (ValueError, IndexError):
        await call.answer("Data tombol tidak valid.", show_alert=True)
        return
    if not user.boleh_promosi():
        await call.answer("Tidak berwenang menerapkan.", show_alert=True)
        return
    u = await ambil_usulan(uid)
    if u is None or not user.boleh_opd(u.opd_id):
        await call.answer("Tidak berwenang / usulan tidak ditemukan.", show_alert=True)
        return
    hasil = await terapkan_usulan(uid, oleh=user.nama)
    metrics.inc("sakipgen_penerapan_total", hasil="ok" if hasil.ok else "gagal")
    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:  # noqa: BLE001
        pass
    if hasil.ok:
        await call.message.answer(_ringkas_penerapan(hasil))
        await call.answer("Diterapkan.")
    else:
        await call.message.answer(f"Gagal menerapkan #{uid}: {hasil.pesan}")
        await call.answer("Gagal.", show_alert=True)


@router.callback_query(F.data.startswith("terapkan_batal:"))
async def cb_terapkan_batal(call: CallbackQuery, user: User) -> None:
    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:  # noqa: BLE001
        pass
    await call.answer("Dibatalkan.")


async def _aksi_daftar_opd(message: Message) -> None:
    daftar = await daftar_opd()
    if not daftar:
        await message.answer("Belum ada OPD di basis data.")
        return
    baris = ["<b>Daftar OPD</b>", ""]
    for o in daftar:
        baris.append(f"#{o['id']} · <b>{o.get('kode', '')}</b> · {o.get('nama', '')}")
    baris += ["", "Sebut id/kode/nama untuk aksi, mis. \"nilai opd 1\" atau \"gap DIKBUD\"."]
    await message.answer("\n".join(baris))


@router.message(Command("opd"))
async def cmd_opd(message: Message, user: User) -> None:
    await _aksi_daftar_opd(message)


async def _aksi_usulan(message: Message, user: User, opd: int | None) -> None:
    opds = [opd] if opd else ([] if user.is_admin else list(user.opd_ids))
    if not opds:
        await message.answer("Sebutkan OPD: <code>/usulan &lt;opd_id&gt;</code>")
        return
    if opd is not None and not user.boleh_opd(opd):
        await message.answer("Anda tidak berwenang atas OPD tersebut.")
        return
    items = await daftar_usulan(opds, limit=10)
    if not items:
        await message.answer("Belum ada usulan untuk OPD tersebut.")
        return
    baris = ["<b>Daftar usulan</b>", ""]
    for u in items:
        baris.append(f"#{u.id} · {u.indikator_id} · <b>{u.status}</b> · +{u.estimasi_poin}")
    baris += ["", "Terapkan yang berstatus <i>disetujui</i> dengan /terapkan &lt;id&gt;."]
    await message.answer("\n".join(baris))


@router.message(Command("usulan"))
async def cmd_daftar_usulan(message: Message, command: CommandObject, user: User) -> None:
    opd, _ = _parse(command.args)
    await _aksi_usulan(message, user, opd)


# ---------- Verba siklus tambahan ----------
async def _aksi_rencana(message: Message, opd: int, tahun: int, dokumen: str | None = None) -> None:
    """Perencanaan: sasaran + indikator (tipologi) + keselarasan."""
    try:
        dosir, _ = await evaluasi_opd(opd, tahun)
    except Exception:  # noqa: BLE001
        await message.answer("Maaf, data perencanaan sedang tidak bisa diambil. Coba lagi sebentar ya.")
        return
    ind = [i for s in dosir.perencanaan.sasaran_strategis for i in s.indikator]
    n_hasil = sum(1 for i in ind if (i.tipologi or "") in {"outcome", "impact"})
    baris = [f"<b>Perencanaan — {dosir.meta.instansi} ({tahun})</b>", ""]
    for s in dosir.perencanaan.sasaran_strategis:
        baris.append(f"🎯 <b>{s.kode}</b> — {s.uraian}")
        for i in s.indikator:
            tag = "outcome ✅" if (i.tipologi or "") in {"outcome", "impact"} else f"{i.tipologi or '?'} ⚠️"
            baris.append(f"   • {i.indikator_id}: {i.uraian} <i>[{tag}]</i>")
    baris += ["", f"Berorientasi hasil: <b>{n_hasil}/{len(ind)}</b> indikator"]
    # Keselarasan: utamakan relasi cascading NYATA dari pohon kinerja; fallback heuristik.
    try:
        relasi = await cascading_opd(opd, tahun)
    except Exception:  # noqa: BLE001 — keselarasan bersifat pelengkap; jangan gagalkan /rencana
        relasi = []
    if relasi:
        naik = [r for r in relasi if r.arah == "naik"]
        turun = [r for r in relasi if r.arah == "turun"]
        baris += ["", "🔗 <b>Keselarasan (pohon kinerja):</b>"]
        for r in naik[:4]:
            b = f" · {r.bobot:.0f}%" if r.bobot is not None else ""
            baris.append(f"   ↑ mendukung: {r.parent} <i>[{r.jenis}{b}]</i>")
        for r in turun[:4]:
            baris.append(f"   ↓ diturunkan ke: {r.child} <i>[{r.jenis}]</i>")
    else:
        selaras = keselarasan_sasaran(dosir)
        if selaras:
            baris += ["", "🔗 Keselarasan:"] + [f"• {x}" for x in selaras[:5]]
    if dokumen == "pohon" and not relasi:
        baris += ["", "<i>(Belum ada relasi pohon kinerja tercatat untuk OPD ini.)</i>"]
    elif dokumen and dokumen != "pohon":
        baris += ["", f"<i>(Dokumen '{dokumen}': lihat \"dokumen opd {opd}\" untuk berkas & versi.)</i>"]
    baris += ["", "Perbaiki indikator: \"usul opd <id>\"."]
    await message.answer("\n".join(baris))


async def _aksi_capaian(message: Message, opd: int, tahun: int, periode: str | None = None) -> None:
    """Pengukuran: target vs realisasi (per periode) + indikator berisiko."""
    try:
        dosir, _ = await evaluasi_opd(opd, tahun)
    except Exception:  # noqa: BLE001
        await message.answer("Maaf, data capaian sedang tidak bisa diambil. Coba lagi sebentar ya.")
        return
    nama = {i.indikator_id: i.uraian for s in dosir.perencanaan.sasaran_strategis for i in s.indikator}
    cap = dosir.pengukuran.capaian
    label, catatan = "tahunan", None
    if periode and periode != "tahunan":
        periodik = await capaian_periode(opd, tahun, periode)
        if periodik:
            cap, label = periodik, periode
        else:
            catatan = f"Data periode '{periode}' belum tersedia; menampilkan tahunan."
    baris = [f"<b>Capaian — {dosir.meta.instansi} ({tahun}, {label})</b>", ""]
    if not cap:
        baris.append("Belum ada data target/realisasi.")
    for c in cap:
        p = f"{c.persen_capaian:.0f}%" if c.persen_capaian is not None else "—"
        baris.append(f"• {c.indikator_id} {nama.get(c.indikator_id, '')}: "
                     f"target {c.target}, realisasi {c.realisasi} → <b>{p}</b>")
    rendah = [c for c in cap if c.persen_capaian is not None and c.persen_capaian < 75]
    if rendah:
        baris += ["", "⚠️ Berisiko (capaian < 75%):"]
        baris += [f"• {c.indikator_id} {nama.get(c.indikator_id, '')}: {c.persen_capaian:.0f}%"
                  for c in sorted(rendah, key=lambda x: x.persen_capaian or 0)[:5]]
    if catatan:
        baris += ["", f"<i>({catatan})</i>"]
    await message.answer("\n".join(baris))


async def _aksi_laporan(message: Message, opd: int, tahun: int, fokus: str | None = None) -> None:
    """Pelaporan: draft bahan LKjIP (analisis capaian) — LLM, anti-halu (tak mengarang angka)."""
    try:
        dosir, hasil = await evaluasi_opd(opd, tahun)
    except Exception:  # noqa: BLE001
        await message.answer("Maaf, data laporan sedang tidak bisa diambil. Coba lagi sebentar ya.")
        return
    ringkas = (f"{hasil.instansi} TA {tahun}: estimasi nilai {hasil.nilai_total:.2f} "
               f"(predikat {hasil.predikat}). "
               + (hasil.gap[0].deskripsi if hasil.gap else ""))
    teks = None
    if llm_tersedia():
        komp = "; ".join(f"{k.nama} {k.skor:.0f}" for k in hasil.komponen)
        prompt = (f"Instansi {hasil.instansi}, tahun {tahun}. Skor komponen: {komp}. "
                  f"Predikat {hasil.predikat}, nilai {hasil.nilai_total:.2f}. "
                  + (f"Fokus: {fokus}. " if fokus else "")
                  + "Tulis 1 paragraf analisis capaian untuk LKjIP.")
        teks = await jawab_singkat(
            prompt,
            system=("Anda penyusun LKjIP pemerintah daerah. Tulis RINGKAS, formal, faktual "
                    "HANYA berdasarkan angka yang diberikan. JANGAN mengarang data/angka baru."),
        )
    baris = [f"<b>Draft bahan LKjIP — {hasil.instansi} ({tahun})</b>", "", teks or ringkas,
             "", "ℹ️ <i>Draft bantu — verifikasi & lengkapi sebelum masuk LKjIP resmi.</i>"]
    await message.answer("\n".join(baris))


async def _aksi_temuan(message: Message, opd: int, tahun: int) -> None:
    """Evaluasi internal: temuan + rekomendasi + status tindak lanjut (read-only)."""
    try:
        daftar = await temuan_opd(opd, tahun)
    except Exception:  # noqa: BLE001
        await message.answer("Maaf, data temuan sedang tidak bisa diambil. Coba lagi sebentar ya.")
        return
    if not daftar:
        await message.answer(
            f"Belum ada temuan evaluasi internal tercatat untuk OPD ini ({tahun}). "
            "Bila eSAKIP Anda belum punya modul evaluasi internal, gunakan \"gap opd <id>\"."
        )
        return
    baris = [f"<b>Temuan evaluasi internal — OPD {opd} ({tahun})</b>", ""]
    for i, t in enumerate(daftar, 1):
        risiko = f" · risiko {t.tingkat_risiko}" if t.tingkat_risiko else ""
        baris.append(f"{i}. <b>{t.jenis or 'Temuan'}</b>{risiko}: {t.uraian}")
        for r in t.rekomendasi:
            tl = (f" — TL: {r.tindak_lanjut or '-'}"
                  + (f" ({r.progres:.0f}%)" if r.progres is not None else ""))
            baris.append(f"   ↳ Rekomendasi [{r.prioritas or '-'}/{r.status or '-'}]: {r.uraian}{tl}")
    await message.answer("\n".join(baris))


_KELOMPOK_TAHAP = {
    "RPJMD": "Perencanaan", "RKPD": "Perencanaan", "RENSTRA": "Perencanaan",
    "RENJA": "Perencanaan", "PK": "Pengukuran", "IKU": "Pengukuran",
    "RENAKSI": "Pengukuran", "LKJIP_OPD": "Pelaporan", "LKJIP_PEMDA": "Pelaporan",
    "LKE": "Evaluasi", "LHE": "Evaluasi",
}


async def _aksi_dokumen(
    message: Message, opd: int, tahun: int | None = None, dokumen: str | None = None
) -> None:
    """Telusur dokumen SAKIP OPD: jenis, status, versi terakhir, jumlah bukti (read-only)."""
    try:
        daftar = await dokumen_opd(opd, tahun, dokumen)
    except Exception:  # noqa: BLE001
        await message.answer("Maaf, data dokumen sedang tidak bisa diambil. Coba lagi sebentar ya.")
        return
    if not daftar:
        saring = f" jenis '{dokumen}'" if dokumen else ""
        thn = f" tahun {tahun}" if tahun else ""
        await message.answer(
            f"Belum ada dokumen{saring} tercatat untuk OPD ini{thn}. "
            "Bila eSAKIP Anda belum punya modul dokumen, lewati saja telusur ini."
        )
        return
    judul = f"<b>Dokumen SAKIP — OPD {opd}</b>" + (f" ({tahun})" if tahun else "")
    baris = [judul, ""]
    for d in daftar:
        tahap = _KELOMPOK_TAHAP.get(d.jenis, "Lainnya")
        meta = []
        if d.status:
            meta.append(d.status)
        if d.versi_terakhir:
            meta.append(f"v{d.versi_terakhir} ({d.jumlah_versi} versi)")
        if d.jumlah_bukti:
            meta.append(f"{d.jumlah_bukti} bukti")
        ekor = f" — {' · '.join(meta)}" if meta else ""
        thn = f" {d.tahun}" if d.tahun else ""
        baris.append(f"• <b>{d.jenis}</b> [{tahap}]{thn}: {d.judul}{ekor}")
    baris += ["", "ℹ️ <i>Penanda kelengkapan; dokumen resmi dikelola di aplikasi eSAKIP/Bappeda.</i>"]
    await message.answer("\n".join(baris))


# ---------- Antarmuka BAHASA ALAMI (translator NL → aksi) ----------
_BANTUAN_NL = (
    "Anda bisa pakai <b>bahasa biasa</b> — contoh:\n"
    "• \"nilai OPD 1 tahun 2025\"  (skor & predikat)\n"
    "• \"capaian opd 1\"  (target vs realisasi)\n"
    "• \"apa kelemahan opd 1\"  (gap)\n"
    "• \"lihat perencanaan / pohon kinerja opd 1\"\n"
    "• \"buatkan usulan perbaikan opd 1\"\n"
    "• \"draft analisis LKjIP opd 1\"\n"
    "• \"tren opd 1\" · \"bandingkan OPD\" · \"daftar usulan opd 1\" · \"daftar opd\" · \"status saya\"\n\n"
    "Perintah: /rencana /capaian /nilai(=/evaluasi) /gap /usul /laporan /tren /benchmark "
    "/usulan /opd /status /terapkan"
)


async def _resolve_opd_fleksibel(ref: str | None) -> int | None:
    """Resolusi referensi OPD bahasa alami (id/kode/nama) → id, lewat daftar OPD."""
    if not ref:
        return None
    return nlu.cocokkan_opd(ref, await daftar_opd())


async def _tanya_opd(message: Message) -> None:
    """Klarifikasi sopan saat OPD belum jelas (bukan error)."""
    daftar = await daftar_opd()
    contoh = " · ".join(f"{o['id']}={o.get('kode', '')}" for o in daftar[:8])
    await message.answer(
        "OPD mana yang Anda maksud? 🙂 Sebutkan id/kode/nama — mis. \"opd 1\", \"DIKBUD\", "
        "atau \"dinas pendidikan\"."
        + (f"\nOPD tersedia: {contoh}" if daftar else "")
    )


async def _klarifikasi_tak_paham(message: Message) -> None:
    """Klarifikasi sopan saat niat tak terdeteksi (TANPA pesan error teknis)."""
    metrics.inc("sakipgen_nlu_total", hasil="tak_paham")
    await message.answer(
        "Maaf, saya belum menangkap maksud Anda. 🙏 Mungkin salah satu ini:\n"
        "• <b>nilai</b> opd 1 — skor & predikat\n"
        "• <b>capaian</b> opd 1 — target vs realisasi\n"
        "• <b>gap</b> opd 1 — kelemahan prioritas\n"
        "• <b>usul</b> opd 1 — usulan perbaikan\n"
        "• <b>laporan</b> opd 1 — draft bahan LKjIP\n"
        "• <b>daftar opd</b> — lihat semua OPD\n\n"
        "Sebutkan aksi + OPD (id/kode/nama). Ketik /bantuan untuk daftar lengkap."
    )


async def _jalankan(message: Message, user: User, p: Permintaan) -> None:
    """Dispatcher tunggal: jalankan satu Permintaan. SEMUA galat → pesan sopan (tanpa error teknis)."""
    try:
        if p.aksi == "bantuan":
            await message.answer(_BANTUAN_NL)
            return
        if p.aksi == "daftar_opd":
            await _aksi_daftar_opd(message)
            return
        if p.aksi == "status":
            await _aksi_status(message, user)
            return
        tahun = p.tahun or datetime.now().year
        if p.aksi == "benchmark":
            await _aksi_benchmark(message, user, tahun)
            return
        if not p.butuh_opd():
            await message.answer(_BANTUAN_NL)
            return
        opd = await _resolve_opd_fleksibel(p.opd_ref)
        if opd is None:
            await _tanya_opd(message)
            return
        if not user.boleh_opd(opd):
            await message.answer("Sepertinya Anda belum punya akses ke OPD itu. Hubungi admin bila perlu.")
            return
        dispatch = {
            "evaluasi": lambda: _aksi_evaluasi(message, opd, tahun),
            "gap": lambda: _aksi_gap(message, opd, tahun),
            "tren": lambda: _aksi_tren(message, opd, tahun),
            "usul": lambda: _aksi_usul(message, user, opd, tahun),
            "usulan": lambda: _aksi_usulan(message, user, opd),
            "rencana": lambda: _aksi_rencana(message, opd, tahun, p.dokumen),
            "capaian": lambda: _aksi_capaian(message, opd, tahun, p.periode),
            "laporan": lambda: _aksi_laporan(message, opd, tahun, p.fokus),
            "temuan": lambda: _aksi_temuan(message, opd, tahun),
            "dokumen": lambda: _aksi_dokumen(message, opd, p.tahun, p.dokumen),
        }
        fn = dispatch.get(p.aksi)
        if fn is None:
            await message.answer(_BANTUAN_NL)
            return
        await fn()
    except Exception as exc:  # noqa: BLE001 — JANGAN bocorkan error teknis ke pengguna
        logger.warning("Gagal menjalankan aksi '%s': %s", getattr(p, "aksi", "?"), exc)
        await message.answer(
            "Maaf, ada kendala saat memproses permintaan. Coba lagi sebentar ya, atau ketik /bantuan."
        )


# ---------- Perintah /slash verba baru (semua lewat dispatcher terpadu) ----------
@router.message(Command("rencana"))
async def cmd_rencana(message: Message, command: CommandObject, user: User) -> None:
    parts = (command.args or "").split()
    opd = int(parts[0]) if parts and parts[0].lstrip("-").isdigit() else None
    if opd is None:
        await message.answer(
            "Format: <code>/rencana &lt;opd_id&gt; [tahun] [dok]</code>\n"
            "dok: pohon·renstra·renja·pk (opsional, mis. <code>/rencana 1 pohon</code>)."
        )
        return
    tahun = next((int(t) for t in parts[1:] if t.isdigit() and len(t) == 4),
                 datetime.now().year)
    dok = next((kanonik_dokumen(t) for t in parts[1:]
                if kanonik_dokumen(t) is not None), None)
    await _jalankan(message, user,
                    Permintaan(aksi="rencana", opd_ref=str(opd), tahun=tahun, dokumen=dok))


@router.message(Command("capaian"))
async def cmd_capaian(message: Message, command: CommandObject, user: User) -> None:
    opd, tahun = _parse(command.args)
    if opd is None:
        await message.answer("Format: <code>/capaian &lt;opd_id&gt; [tahun]</code>")
        return
    await _jalankan(message, user, Permintaan(aksi="capaian", opd_ref=str(opd), tahun=tahun))


@router.message(Command("laporan"))
async def cmd_laporan(message: Message, command: CommandObject, user: User) -> None:
    opd, tahun = _parse(command.args)
    if opd is None:
        await message.answer("Format: <code>/laporan &lt;opd_id&gt; [tahun]</code>")
        return
    await _jalankan(message, user, Permintaan(aksi="laporan", opd_ref=str(opd), tahun=tahun))


@router.message(Command("temuan"))
async def cmd_temuan(message: Message, command: CommandObject, user: User) -> None:
    opd, tahun = _parse(command.args)
    if opd is None:
        await message.answer("Format: <code>/temuan &lt;opd_id&gt; [tahun]</code>")
        return
    await _jalankan(message, user, Permintaan(aksi="temuan", opd_ref=str(opd), tahun=tahun))


@router.message(Command("dokumen"))
async def cmd_dokumen(message: Message, command: CommandObject, user: User) -> None:
    parts = (command.args or "").split()
    opd = int(parts[0]) if parts and parts[0].lstrip("-").isdigit() else None
    if opd is None:
        await message.answer(
            "Format: <code>/dokumen &lt;opd_id&gt; [tahun] [jenis]</code>\n"
            "Jenis: rpjmd·renstra·renja·rkpd·pk·lkjip·lhe (opsional)."
        )
        return
    # Argumen opsional: angka 4-digit → tahun; kata → jenis dokumen.
    tahun = next((int(t) for t in parts[1:] if t.isdigit() and len(t) == 4), None)
    jenis = next((kanonik_dokumen(t) for t in parts[1:]
                  if kanonik_dokumen(t) is not None), None)
    await _jalankan(message, user,
                    Permintaan(aksi="dokumen", opd_ref=str(opd), tahun=tahun, dokumen=jenis))


@router.message(F.text & ~F.text.startswith("/"))
async def nl_handler(message: Message, user: User) -> None:
    """Translator bahasa alami → Permintaan → dispatcher. Cerdas, anti-gagal, anti-halu."""
    teks = message.text or ""
    p = nlu.parse(teks)
    if p is None and llm_tersedia():
        try:
            p = await nlu.parse_llm(teks)
        except Exception:  # noqa: BLE001 — fallback aman bila LLM bermasalah
            p = None
    if p is None:
        await _klarifikasi_tak_paham(message)
        return
    metrics.inc("sakipgen_nlu_total", hasil="heuristik" if p.skor >= 1.0 else "llm")
    await _jalankan(message, user, p)
