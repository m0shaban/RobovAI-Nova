"""
Promote an existing user to admin role in local SQLite database.

Usage examples:
  python scripts/set_admin_user.py --email admin@example.com
  python scripts/set_admin_user.py --id 1
  python scripts/set_admin_user.py --email admin@example.com --verify --dry-run
"""

from __future__ import annotations

import argparse
import logging
import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence


logger = logging.getLogger("robovai.scripts.set_admin_user")


class AdminSetupError(Exception):
    """Base exception for admin setup script errors."""


@dataclass(frozen=True)
class TargetUser:
    """Represents a user selected for role update."""

    user_id: int
    email: str
    role: str
    is_verified: Optional[int]


@dataclass(frozen=True)
class ScriptConfig:
    """CLI configuration for admin role update."""

    database_path: str
    user_id: Optional[int]
    email: Optional[str]
    verify: bool
    dry_run: bool


class AdminRoleManager:
    """Encapsulates safe admin role promotion logic for SQLite-backed users table."""

    def __init__(self, database_path: str) -> None:
        self.database_path = database_path

    def promote(self, *, user_id: Optional[int], email: Optional[str], verify: bool, dry_run: bool) -> TargetUser:
        """Promote selected user to admin, optionally marking verified.

        Args:
            user_id: Target user ID.
            email: Target user email.
            verify: Whether to set is_verified=1 (if column exists).
            dry_run: If True, do not write changes.

        Returns:
            Updated user snapshot.

        Raises:
            AdminSetupError: If preconditions fail.
        """
        self._validate_db_exists()

        with sqlite3.connect(self.database_path) as connection:
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()

            self._ensure_users_table(cursor)
            has_is_verified = self._has_column(cursor, "users", "is_verified")
            selected_user = self._select_target_user(cursor, user_id=user_id, email=email, has_is_verified=has_is_verified)

            logger.info(
                "Selected user id=%s email=%s role=%s verified=%s",
                selected_user.user_id,
                selected_user.email,
                selected_user.role,
                selected_user.is_verified,
            )

            if dry_run:
                logger.info("Dry-run mode: no database changes applied")
                return selected_user

            update_fields = ["role = ?"]
            update_values: list[object] = ["admin"]

            if verify and has_is_verified:
                update_fields.append("is_verified = ?")
                update_values.append(1)

            update_values.append(selected_user.user_id)
            update_query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(update_query, update_values)
            connection.commit()

            if cursor.rowcount != 1:
                raise AdminSetupError("Failed to update target user role")

            refreshed_user = self._select_target_user(
                cursor,
                user_id=selected_user.user_id,
                email=None,
                has_is_verified=has_is_verified,
            )
            logger.info(
                "Promotion successful -> id=%s email=%s role=%s verified=%s",
                refreshed_user.user_id,
                refreshed_user.email,
                refreshed_user.role,
                refreshed_user.is_verified,
            )
            return refreshed_user

    def _validate_db_exists(self) -> None:
        if not Path(self.database_path).exists():
            raise AdminSetupError(f"Database file not found: {self.database_path}")

    @staticmethod
    def _ensure_users_table(cursor: sqlite3.Cursor) -> None:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            raise AdminSetupError("'users' table not found in database")

    @staticmethod
    def _has_column(cursor: sqlite3.Cursor, table_name: str, column_name: str) -> bool:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]
        return column_name in columns

    def _select_target_user(
        self,
        cursor: sqlite3.Cursor,
        *,
        user_id: Optional[int],
        email: Optional[str],
        has_is_verified: bool,
    ) -> TargetUser:
        select_columns = "id, email, role"
        if has_is_verified:
            select_columns += ", is_verified"

        if user_id is not None:
            cursor.execute(f"SELECT {select_columns} FROM users WHERE id = ? LIMIT 1", (user_id,))
        elif email is not None:
            cursor.execute(f"SELECT {select_columns} FROM users WHERE lower(email) = lower(?) LIMIT 1", (email,))
        else:
            raise AdminSetupError("Either user_id or email must be provided")

        row = cursor.fetchone()
        if not row:
            target_desc = f"id={user_id}" if user_id is not None else f"email={email}"
            raise AdminSetupError(f"User not found ({target_desc})")

        is_verified_value: Optional[int] = None
        if has_is_verified:
            is_verified_value = int(row["is_verified"])

        return TargetUser(
            user_id=int(row["id"]),
            email=str(row["email"]),
            role=str(row["role"]),
            is_verified=is_verified_value,
        )


def build_arg_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser."""
    parser = argparse.ArgumentParser(description="Promote a user to admin role.")
    parser.add_argument(
        "--db",
        default=os.getenv("DATABASE_PATH", "users.db"),
        help="Path to SQLite database file (default: DATABASE_PATH env or users.db)",
    )
    parser.add_argument("--id", type=int, dest="user_id", help="User ID to promote")
    parser.add_argument("--email", type=str, help="User email to promote")
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Also set is_verified=1 if the column exists",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate target user and print action without applying updates",
    )
    return parser


def parse_config(argv: Optional[Sequence[str]] = None) -> ScriptConfig:
    """Parse and validate CLI config."""
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if bool(args.user_id is None) == bool(args.email is None):
        parser.error("Provide exactly one of --id or --email")

    return ScriptConfig(
        database_path=args.db,
        user_id=args.user_id,
        email=args.email,
        verify=bool(args.verify),
        dry_run=bool(args.dry_run),
    )


def main() -> int:
    """Script entry point."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    try:
        config = parse_config()
        manager = AdminRoleManager(config.database_path)
        updated_user = manager.promote(
            user_id=config.user_id,
            email=config.email,
            verify=config.verify,
            dry_run=config.dry_run,
        )

        mode_text = "DRY-RUN" if config.dry_run else "APPLIED"
        print(
            f"[{mode_text}] user_id={updated_user.user_id} email={updated_user.email} "
            f"role={updated_user.role} verified={updated_user.is_verified}"
        )
        return 0
    except AdminSetupError as error:
        logger.error("Admin setup failed: %s", error)
        return 1
    except Exception as error:
        logger.exception("Unexpected error: %s", error)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
