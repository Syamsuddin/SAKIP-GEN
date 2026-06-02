"""Uji Fase 6 (deploy): konfigurasi gunicorn, isi artefak, dan skrip ops importable."""
from __future__ import annotations

import importlib.util
from pathlib import Path

DEPLOY = Path(__file__).resolve().parents[1] / "deploy"


def _load(path: Path):
    name = path.stem.replace(".", "_") + "_mod"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_gunicorn_conf():
    conf = _load(DEPLOY / "gunicorn.conf.py")
    assert conf.workers == 1                       # penjadwal in-process -> satu worker
    assert "UvicornWorker" in conf.worker_class
    assert conf.bind                               # ada bind default


def test_systemd_unit():
    txt = (DEPLOY / "sakip-gen.service").read_text()
    assert "gunicorn" in txt and "app:app" in txt
    assert "NoNewPrivileges=true" in txt
    assert "EnvironmentFile=" in txt
    assert "WantedBy=multi-user.target" in txt


def test_nginx_conf():
    txt = (DEPLOY / "nginx-sakip-gen.conf").read_text()
    assert "proxy_pass http://127.0.0.1:8000" in txt
    assert "X-Forwarded-For" in txt
    assert "listen 443" in txt


def test_scripts_importable():
    # Memastikan skrip ops bebas galat sintaks/impor (tanpa menjalankan main()).
    _load(DEPLOY / "manage_webhook.py")
    _load(DEPLOY / "preflight.py")


def test_deploy_docs():
    txt = (DEPLOY / "DEPLOY.md").read_text().lower()
    for kata in ("systemd", "nginx", "certbot", "webhook", "checklist", "preflight"):
        assert kata in txt
