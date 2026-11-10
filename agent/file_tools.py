import os
from pathlib import Path

X_DRIVE_ROOT = Path("X:/").resolve()

MAX_READ_BYTES = 1_000_000  # 1 MB
MAX_SEARCH_RESULTS = 100


def _resolve_safe_path(path: str) -> Path:
    """Resolve a user path and ensure it stays inside X:/."""

    candidate = Path(path)

    if not candidate.is_absolute():
        candidate = X_DRIVE_ROOT / candidate

    resolved = candidate.resolve(strict=True) # produces an absolute, normalized path.

    if not resolved.is_relative_to(X_DRIVE_ROOT): # This checks whether the resolved path is inside the permitted root.
        raise PermissionError("Access denied: path is outside X:/")

    return resolved


def _is_link_or_junction(path: Path) -> bool: # Without link protection, recursive search could wander into the Windows directory.
    """Identify links that could redirect traversal."""

    if path.is_symlink():
        return True

    is_junction = getattr(path, "is_junction", None)
    return bool(is_junction and is_junction())


def list_directory(path: str = ".") -> str:
    """List files and folders in a directory on X:/."""

    directory = _resolve_safe_path(path)

    if not directory.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")

    entries = []
    # Identify each entry
    for item in sorted(directory.iterdir(), key=lambda p: p.name.lower()): #iterdir() retrieves the immediate contents of a directory.
        if _is_link_or_junction(item):
            entries.append(f"[LINK] {item.name}")
        elif item.is_dir():
            entries.append(f"[DIR]  {item.name}")
        elif item.is_file():
            size = item.stat().st_size
            entries.append(f"[FILE] {item.name} ({size:,} bytes)")

        if len(entries) >= 100:
            entries.append("... output truncated at 100 entries")
            break

    if not entries:
        return f"Directory is empty: {directory}"

    return f"Contents of {directory}:\n" + "\n".join(entries)


def search_files(
    query: str,
    path: str = ".",
    max_results: int = 50
) -> str:
    """Recursively search filenames on X:/."""

    if not query.strip():
        raise ValueError("Search query cannot be empty.")

    if not 1 <= max_results <= MAX_SEARCH_RESULTS:
        raise ValueError(
            f"max_results must be between 1 and {MAX_SEARCH_RESULTS}."
        )

    root = _resolve_safe_path(path)
    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {root}")

    matches = []
    pending = [root]

    while pending and len(matches) < max_results:
        current = pending.pop()

        try:
            entries = current.iterdir()

            for item in entries:
                try:
                    if _is_link_or_junction(item):
                        continue

                    resolved = item.resolve(strict=True)
                    if not resolved.is_relative_to(X_DRIVE_ROOT):
                        continue

                    if item.is_dir():
                        pending.append(item)

                    elif item.is_file() and query.casefold() in item.name.casefold():
                        matches.append(str(item))
                        if len(matches) >= max_results:
                            break

                except (OSError, PermissionError):
                    continue

        except (OSError, PermissionError):
            continue

    if not matches:
        return f"No files matching '{query}' were found."

    return (
        f"Found {len(matches)} matching file(s):\n"
        + "\n".join(matches)
    )


def read_file(path: str) -> str:
    """Read a small UTF-8 text file from X:/."""

    file_path = _resolve_safe_path(path)

    if not file_path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    if file_path.stat().st_size > MAX_READ_BYTES:
        raise ValueError(
            f"File exceeds the {MAX_READ_BYTES:,}-byte read limit."
        )

    content = file_path.read_bytes()

    # Basic binary-file detection.
    if b"\x00" in content:
        raise ValueError("Cannot read binary files.")

    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError("File is not valid UTF-8 text.")