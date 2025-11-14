#!/usr/bin/env python3
"""
Database migration script for the LLM Gateway.

Usage:
    python migrate.py upgrade    # Upgrade to latest version
    python migrate.py downgrade  # Downgrade one version
    python migrate.py current    # Show current version
    python migrate.py history    # Show migration history
"""

import sys
from pathlib import Path
from alembic.config import Config
from alembic import command


def get_alembic_config():
    """Get Alembic configuration."""
    gateway_dir = Path(__file__).resolve().parent
    alembic_ini = gateway_dir / "alembic.ini"

    if not alembic_ini.exists():
        print(f"Error: Alembic configuration not found at {alembic_ini}")
        sys.exit(1)

    alembic_cfg = Config(str(alembic_ini))
    alembic_cfg.set_main_option("script_location", str(gateway_dir / "alembic"))

    return alembic_cfg


def main():
    """Run migration commands."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1].lower()
    alembic_cfg = get_alembic_config()

    if cmd == "upgrade":
        target = sys.argv[2] if len(sys.argv) > 2 else "head"
        print(f"Upgrading database to {target}...")
        command.upgrade(alembic_cfg, target)
        print("✓ Database upgraded successfully")

    elif cmd == "downgrade":
        target = sys.argv[2] if len(sys.argv) > 2 else "-1"
        print(f"Downgrading database to {target}...")
        command.downgrade(alembic_cfg, target)
        print("✓ Database downgraded successfully")

    elif cmd == "current":
        print("Current database version:")
        command.current(alembic_cfg)

    elif cmd == "history":
        print("Migration history:")
        command.history(alembic_cfg)

    elif cmd == "revision":
        message = sys.argv[2] if len(sys.argv) > 2 else "New migration"
        print(f"Creating new migration: {message}")
        command.revision(alembic_cfg, message=message, autogenerate=True)
        print("✓ Migration file created")

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
