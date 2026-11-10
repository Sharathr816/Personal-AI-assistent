
import os
from pathlib import Path

import win32com.client


# Standard Windows locations containing application shortcuts.
SHORTCUT_SEARCH_DIRS = [
    Path.home() / "Desktop",
    Path.home() / "AppData/Roaming/Microsoft/Windows/Start Menu/Programs",
    Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData"))
        / "Microsoft/Windows/Start Menu/Programs",
    Path(os.environ.get("PUBLIC", r"C:\Users\Public")) / "Desktop",
    Path.home() / "OneDrive/Desktop",
]

# Add any other folders containing your shortcuts here.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

EXTRA_SHORTCUT_DIRS = [
    PROJECT_ROOT.parent / "Tech Downloads"
]


def _get_shortcut_dirs():
    """Return existing shortcut directories without duplicates."""
    directories = SHORTCUT_SEARCH_DIRS + EXTRA_SHORTCUT_DIRS

    return list({
        path.resolve()
        for path in directories
        if path.exists()
    })


def search_applications(query: str, max_results: int = 30) -> str:
    """
    Search Windows shortcuts and return their .lnk and .exe paths.
    """

    if not query.strip():
        raise ValueError("Application search query cannot be empty.")

    if not 1 <= max_results <= 100:
        raise ValueError("max_results must be between 1 and 100.")

    query = query.strip().casefold()
    shell = win32com.client.Dispatch("WScript.Shell")

    results = []
    seen = set()

    for directory in _get_shortcut_dirs():
        for shortcut in directory.rglob("*.lnk"):

            name = shortcut.stem

            if not name.casefold().startswith(query):
                continue

            shortcut_path = str(shortcut.resolve())

            if shortcut_path in seen:
                continue

            seen.add(shortcut_path)

            try:
                link = shell.CreateShortcut(shortcut_path)
                target = link.TargetPath
            except Exception:
                target = ""

            # Include the executable path only if it exists.
            exe_path = None

            if target:
                target_path = Path(target)

                if target_path.suffix.lower() == ".exe" and target_path.is_file():
                    exe_path = str(target_path.resolve())

            results.append({
                "name": name,
                "shortcut_path": shortcut_path,
                "exe_path": exe_path,
            })

            if len(results) >= max_results:
                break

        if len(results) >= max_results:
            break

    if not results:
        return f"No application shortcuts found starting with '{query}'."

    output = [f"Matching applications for '{query}':"]

    for index, app in enumerate(results, start=1):
        output.append(
            f"\n{index}. {app['name']}"
            f"\n   LNK: {app['shortcut_path']}"
            f"\n   EXE: {app['exe_path'] or 'Not available'}"
        )

    return "\n".join(output)



def open_application(shortcut_path: str, exe_path: str = None) -> str:
    """
    Try launching through LNK first.
    If that fails, fall back to the EXE.
    """

    if os.name != "nt":
        raise RuntimeError("Application launching is supported on Windows only.")

    shortcut = Path(shortcut_path).resolve()

    if not shortcut.is_file() or shortcut.suffix.lower() != ".lnk":
        raise ValueError("Invalid or missing Windows shortcut.")

    # Validate shortcut location.
    allowed = False

    for directory in _get_shortcut_dirs():
        try:
            shortcut.relative_to(directory)
            allowed = True
            break
        except ValueError:
            continue

    if not allowed:
        raise PermissionError("Shortcut is outside configured directories.")

    # Validate EXE against the actual shortcut target.
    validated_exe = None

    if exe_path:
        shell = win32com.client.Dispatch("WScript.Shell")
        link = shell.CreateShortcut(str(shortcut))

        actual_target = Path(link.TargetPath).resolve()
        supplied_target = Path(exe_path).resolve()

        if (
            actual_target.suffix.lower() == ".exe"
            and actual_target.is_file()
            and actual_target == supplied_target
        ):
            validated_exe = supplied_target

    # Attempt 1: Launch through LNK.
    try:
        os.startfile(str(shortcut))
        return f"Successfully opened {shortcut.stem} using its shortcut."

    except OSError as lnk_error:
        # Attempt 2: Fall back to EXE.
        if validated_exe and validated_exe.is_file():
            try:
                os.startfile(str(validated_exe))
                return f"Opened {shortcut.stem} using its EXE fallback."

            except OSError as exe_error:
                raise RuntimeError(
                    f"Both launch attempts failed. "
                    f"LNK: {lnk_error}; EXE: {exe_error}"
                )

        raise RuntimeError(
            f"LNK launch failed and no valid EXE fallback is available: {lnk_error}"
        )


