"""Initial: tabel milik agen (ai_usulan, ai_audit, ai_event, bot_users, registration_codes).

Membangun seluruh skema dari definisi kanonik db/schema.py agar tetap satu sumber
kebenaran (T4.1/T4.3). Tabel sumber eSAKIP dikelola aplikasi SAKIP, bukan migrasi ini.

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-02
"""
from __future__ import annotations

from alembic import op

from db.schema import metadata

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    metadata.drop_all(bind=op.get_bind())
