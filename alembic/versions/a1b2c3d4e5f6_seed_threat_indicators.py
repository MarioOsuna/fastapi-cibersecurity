"""seed_threat_indicators

Revision ID: a1b2c3d4e5f6
Revises: c4832cae2f8d
Create Date: 2026-06-29 18:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "c4832cae2f8d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

INDICATORS = [
    {
        "id": "08ffe73b-a179-4f5b-a1f8-95021f59a12f",
        "indicator_value": "185.220.101.34",
        "indicator_type": "IP",
        "source": "Tor Exit Node List",
        "risk_score": 95.0,
        "is_active": True,
        "first_seen": "2026-06-10T08:12:00Z",
        "last_seen": "2026-06-22T17:28:00Z",
        "created_at": "2026-06-10T08:12:00Z",
    },
    {
        "id": "927e5f0b-a307-4001-bc9b-967a0cbcad15",
        "indicator_value": "malware-c2.evil.ru",
        "indicator_type": "DOMAIN",
        "source": "VirusTotal",
        "risk_score": 92.0,
        "is_active": True,
        "first_seen": "2026-06-08T03:15:00Z",
        "last_seen": "2026-06-22T12:00:00Z",
        "created_at": "2026-06-08T03:15:00Z",
    },
    {
        "id": "754de35f-52d1-4c5c-9007-7c497892bd8f",
        "indicator_value": "d41d8cd98f00b204e9800998ecf8427e",
        "indicator_type": "HASH",
        "source": "VirusTotal",
        "risk_score": 90.0,
        "is_active": True,
        "first_seen": "2026-06-09T20:00:00Z",
        "last_seen": "2026-06-22T17:28:00Z",
        "created_at": "2026-06-09T20:00:00Z",
    },
    {
        "id": "ee90385b-4531-4ce2-a205-9919cd60ac0c",
        "indicator_value": "91.240.118.172",
        "indicator_type": "IP",
        "source": "AlienVault OTX",
        "risk_score": 88.0,
        "is_active": True,
        "first_seen": "2026-06-12T22:45:00Z",
        "last_seen": "2026-06-22T17:28:00Z",
        "created_at": "2026-06-12T22:45:00Z",
    },
    {
        "id": "c126cf5c-3d3c-4564-bbe1-4ac14df9e4be",
        "indicator_value": "phishing-bank.com",
        "indicator_type": "DOMAIN",
        "source": "PhishTank",
        "risk_score": 85.0,
        "is_active": True,
        "first_seen": "2026-06-11T18:00:00Z",
        "last_seen": "2026-06-21T23:45:00Z",
        "created_at": "2026-06-11T18:00:00Z",
    },
    {
        "id": "7dc9ee63-a75b-4fad-8658-1b6a337370e7",
        "indicator_value": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6",
        "indicator_type": "HASH",
        "source": "Hybrid Analysis",
        "risk_score": 85.0,
        "is_active": True,
        "first_seen": "2026-06-13T10:30:00Z",
        "last_seen": "2026-06-22T17:28:00Z",
        "created_at": "2026-06-13T10:30:00Z",
    },
    {
        "id": "7d838b35-f15c-4714-9e36-233222ac0702",
        "indicator_value": "cdn-update.totallylegit.xyz",
        "indicator_type": "DOMAIN",
        "source": "Threat Intelligence Feed",
        "risk_score": 78.0,
        "is_active": True,
        "first_seen": "2026-06-14T07:30:00Z",
        "last_seen": "2026-06-22T09:15:00Z",
        "created_at": "2026-06-14T07:30:00Z",
    },
    {
        "id": "b2344d5c-51bf-4b92-bae4-f6f7331845bb",
        "indicator_value": "45.155.205.99",
        "indicator_type": "IP",
        "source": "AbuseIPDB",
        "risk_score": 72.0,
        "is_active": True,
        "first_seen": "2026-06-15T14:30:00Z",
        "last_seen": "2026-06-22T17:28:00Z",
        "created_at": "2026-06-15T14:30:00Z",
    },
    {
        "id": "b547ee62-4f2c-4723-8d92-1e12d384fece",
        "indicator_value": "e99a18c428cb38d5f260853678922e03",
        "indicator_type": "HASH",
        "source": "MalwareBazaar",
        "risk_score": 70.0,
        "is_active": True,
        "first_seen": "2026-06-16T22:15:00Z",
        "last_seen": "2026-06-22T17:28:00Z",
        "created_at": "2026-06-16T22:15:00Z",
    },
    {
        "id": "a35248c0-2f7b-4c34-90f4-4d25c0df0571",
        "indicator_value": "103.75.201.18",
        "indicator_type": "IP",
        "source": "Spamhaus DROP",
        "risk_score": 65.0,
        "is_active": True,
        "first_seen": "2026-06-18T11:20:00Z",
        "last_seen": "2026-06-22T17:28:00Z",
        "created_at": "2026-06-18T11:20:00Z",
    },
    {
        "id": "ec350480-4ede-4df9-8094-67f02a0905e7",
        "indicator_value": "203.0.113.42",
        "indicator_type": "IP",
        "source": "Internal Honeypot",
        "risk_score": 40.0,
        "is_active": True,
        "first_seen": "2026-06-20T06:10:00Z",
        "last_seen": "2026-06-22T17:28:00Z",
        "created_at": "2026-06-20T06:10:00Z",
    },
]


def upgrade() -> None:
    table = sa.table(
        "threat_indicators",
        sa.column("id", sa.Uuid),
        sa.column("indicator_value", sa.String),
        sa.column("indicator_type", sa.String),
        sa.column("source", sa.String),
        sa.column("risk_score", sa.Float),
        sa.column("is_active", sa.Boolean),
        sa.column("first_seen", sa.DateTime),
        sa.column("last_seen", sa.DateTime),
        sa.column("created_at", sa.DateTime),
    )
    op.bulk_insert(table, INDICATORS)


def downgrade() -> None:
    op.execute(
        "DELETE FROM threat_indicators WHERE id IN ("
        + ", ".join(f"'{i['id']}'" for i in INDICATORS)
        + ")"
    )
