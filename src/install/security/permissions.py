"""
File Permission Management.

INSTALL-SEC-002: Secure file permissions for installation.
"""

import grp
import logging
import os
import pwd
import stat
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class PermissionLevel(Enum):
    """Permission strictness levels."""

    SECRETS = "secrets"  # 600 - owner read/write only
    CONFIG = "config"  # 600 - owner read/write only
    DATA = "data"  # 700 - owner full access
    LOGS = "logs"  # 644 - owner read/write, others read
    PUBLIC = "public"  # 755 - owner full, others read/execute


# Permission mappings
PERMISSION_MODES = {
    PermissionLevel.SECRETS: 0o600,
    PermissionLevel.CONFIG: 0o600,
    PermissionLevel.DATA: 0o700,
    PermissionLevel.LOGS: 0o644,
    PermissionLevel.PUBLIC: 0o755,
}


@dataclass
class PermissionIssue:
    """Permission issue detected."""

    path: Path
    current_mode: int
    expected_mode: int
    severity: str  # critical, high, medium, low
    message: str
    fix_command: str


def get_permission_mode(path: Path) -> int:
    """
    Get current permission mode of a file/directory.

    Args:
        path: Path to check.

    Returns:
        Permission mode (e.g., 0o644).
    """
    return stat.S_IMODE(path.stat().st_mode)


def format_mode(mode: int) -> str:
    """
    Format permission mode as string.

    Args:
        mode: Permission mode.

    Returns:
        String representation (e.g., "644").
    """
    return oct(mode)[2:]


def set_secure_permissions(
    path: Path,
    level: PermissionLevel,
    recursive: bool = False,
) -> bool:
    """
    Set secure permissions on a path.

    Args:
        path: Path to set permissions on.
        level: Permission level.
        recursive: Apply recursively to directories.

    Returns:
        True if successful.
    """
    mode = PERMISSION_MODES[level]

    try:
        if path.is_dir() and recursive:
            # Set directory permissions
            os.chmod(path, mode)

            # Set file permissions (files need different mode than dirs)
            file_mode = mode & ~stat.S_IXUSR & ~stat.S_IXGRP & ~stat.S_IXOTH
            if level == PermissionLevel.DATA:
                file_mode = PERMISSION_MODES[PermissionLevel.CONFIG]

            for child in path.rglob("*"):
                if child.is_file():
                    os.chmod(child, file_mode)
                elif child.is_dir():
                    os.chmod(child, mode)
        else:
            os.chmod(path, mode)

        logger.info(f"Set permissions {format_mode(mode)} on {path}")
        return True

    except PermissionError as e:
        logger.error(f"Permission denied setting {mode} on {path}: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to set permissions on {path}: {e}")
        return False


def verify_permissions(
    ragged_home: Path,
) -> list[PermissionIssue]:
    """
    Verify file permissions in ragged home.

    Args:
        ragged_home: Path to ragged home directory.

    Returns:
        List of permission issues found.
    """
    issues: list[PermissionIssue] = []

    # Expected permissions
    permission_checks = [
        # Secrets
        (ragged_home / ".env", PermissionLevel.SECRETS, "critical"),
        # Config
        (ragged_home / "config.yaml", PermissionLevel.CONFIG, "high"),
        # Data directories
        (ragged_home, PermissionLevel.DATA, "medium"),
        (ragged_home / "data", PermissionLevel.DATA, "medium"),
        (ragged_home / "documents", PermissionLevel.DATA, "medium"),
        (ragged_home / "cache", PermissionLevel.DATA, "low"),
        # Logs
        (ragged_home / "logs", PermissionLevel.LOGS, "low"),
    ]

    for path, expected_level, severity in permission_checks:
        if not path.exists():
            continue

        current_mode = get_permission_mode(path)
        expected_mode = PERMISSION_MODES[expected_level]

        # Check if current permissions are too permissive
        if _is_too_permissive(current_mode, expected_mode):
            issues.append(PermissionIssue(
                path=path,
                current_mode=current_mode,
                expected_mode=expected_mode,
                severity=severity,
                message=f"{path.name} has permissions {format_mode(current_mode)}, "
                        f"should be {format_mode(expected_mode)}",
                fix_command=f"chmod {format_mode(expected_mode)} {path}",
            ))

    return issues


def _is_too_permissive(current: int, expected: int) -> bool:
    """
    Check if current permissions are more permissive than expected.

    Args:
        current: Current permission mode.
        expected: Expected permission mode.

    Returns:
        True if current is more permissive.
    """
    # Check each permission bit
    # Current should not have permissions that expected doesn't have
    extra_perms = current & ~expected

    # Specifically check group and other permissions
    group_other_mask = stat.S_IRWXG | stat.S_IRWXO
    return bool(extra_perms & group_other_mask)


def fix_permissions(
    issues: list[PermissionIssue],
    dry_run: bool = False,
) -> list[tuple[PermissionIssue, bool]]:
    """
    Fix permission issues.

    Args:
        issues: List of permission issues.
        dry_run: Only report what would be done.

    Returns:
        List of (issue, success) tuples.
    """
    results: list[tuple[PermissionIssue, bool]] = []

    for issue in issues:
        if dry_run:
            logger.info(f"Would fix: {issue.fix_command}")
            results.append((issue, True))
            continue

        try:
            os.chmod(issue.path, issue.expected_mode)
            logger.info(f"Fixed permissions on {issue.path}")
            results.append((issue, True))
        except Exception as e:
            logger.error(f"Failed to fix {issue.path}: {e}")
            results.append((issue, False))

    return results


def get_file_owner(path: Path) -> tuple[str, str]:
    """
    Get file owner user and group.

    Args:
        path: Path to check.

    Returns:
        Tuple of (username, groupname).
    """
    try:
        stat_info = path.stat()
        username = pwd.getpwuid(stat_info.st_uid).pw_name
        groupname = grp.getgrgid(stat_info.st_gid).gr_name
        return username, groupname
    except (KeyError, AttributeError):
        return str(path.stat().st_uid), str(path.stat().st_gid)


def verify_ownership(
    path: Path,
    expected_user: str | None = None,
) -> bool:
    """
    Verify file ownership.

    Args:
        path: Path to check.
        expected_user: Expected owner username.

    Returns:
        True if ownership is correct.
    """
    if expected_user is None:
        expected_user = pwd.getpwuid(os.getuid()).pw_name

    owner, _ = get_file_owner(path)
    return owner == expected_user


def format_permission_report(issues: list[PermissionIssue]) -> str:
    """
    Format permission issues as report.

    Args:
        issues: List of permission issues.

    Returns:
        Formatted report string.
    """
    if not issues:
        return "All file permissions are secure"

    lines = ["Permission Issues Found:", ""]

    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    sorted_issues = sorted(issues, key=lambda i: severity_order.get(i.severity, 4))

    for issue in sorted_issues:
        severity_marker = {
            "critical": "[!]",
            "high": "[H]",
            "medium": "[M]",
            "low": "[L]",
        }.get(issue.severity, "[?]")

        lines.append(f"{severity_marker} {issue.message}")
        lines.append(f"    Fix: {issue.fix_command}")
        lines.append("")

    return "\n".join(lines)


def ensure_secure_directory(
    path: Path,
    level: PermissionLevel = PermissionLevel.DATA,
) -> bool:
    """
    Ensure directory exists with secure permissions.

    Args:
        path: Directory path.
        level: Permission level.

    Returns:
        True if successful.
    """
    mode = PERMISSION_MODES[level]

    try:
        if not path.exists():
            path.mkdir(parents=True, mode=mode)
        else:
            os.chmod(path, mode)
        return True
    except Exception as e:
        logger.error(f"Failed to create secure directory {path}: {e}")
        return False
