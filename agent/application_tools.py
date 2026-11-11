
import os
from pathlib import Path
import psutil
import win32gui
import win32process
import win32con

import win32com.client


# Standard Windows locations containing application shortcuts.
SHORTCUT_SEARCH_DIRS = [
    Path.home() / "Desktop",
    Path.home() / "AppData/Roaming/Microsoft/Windows/Start Menu/Programs",
    Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData"))
        / "Microsoft/Windows/Start Menu/Programs",
    Path(os.environ.get("PUBLIC", r"C:\Users\Public")) / "Desktop",
    Path.home() / "OneDrive/Desktop",
    Path.home() / "Program files",
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
    print("\nSearching application...🔃")
    if not query.strip():
        print("Query problem🫥")
        raise ValueError("Application search query cannot be empty.")

    if not 1 <= max_results <= 100:
        print("Query problem🫥")
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
                print("\nRelevant apps found✅")
                break

        if len(results) >= max_results:
            break

    if not results:
        print("\nCan't find application.😞")
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
    print("\nOpening Queried application...🔃")
    if os.name != "nt":
        raise RuntimeError("Application launching is supported on Windows only.")

    shortcut = Path(shortcut_path).resolve()

    if not shortcut.is_file() or shortcut.suffix.lower() != ".lnk":
        print("\nInvalid or missing Windows shortcut.🤔")
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
        print("\nShortcut is outside configured directories.🫠")
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
        print(f"\nSuccessfully opened {shortcut.stem} using its shortcut😆")
        return f"Successfully opened {shortcut.stem} using its shortcut."

    except OSError as lnk_error:
        # Attempt 2: Fall back to EXE.
        print("\nCouldn't open using .lnk ⛓️‍💥, fallback to .exe")
        if validated_exe and validated_exe.is_file():
            try:
                os.startfile(str(validated_exe))
                print(f"Opened {shortcut.stem} using its EXE fallback👍")
                return f"Opened {shortcut.stem} using its EXE fallback."

            except OSError as exe_error:
                print("\nBoth attempt failed 😞")
                raise RuntimeError(             
                    f"Both launch attempts failed. "
                    f"LNK: {lnk_error}; EXE: {exe_error}"
                )
        print("\nLNK launch failed and no valid EXE fallback is available 🫠")
        raise RuntimeError(
            f"LNK launch failed and no valid EXE fallback is available: {lnk_error}"
        )


# closing applications

# To prevent listing background processes as well
def has_visible_window(pid: int) -> bool:
    found = False

    def callback(hwnd, _):
        nonlocal found
        try:
            if not win32gui.IsWindowVisible(hwnd):
                return True

            _, window_pid = win32process.GetWindowThreadProcessId(hwnd)
            if window_pid == pid:
                found = True
                return False

        except win32gui.error:
            pass

        return True

    try:
        win32gui.EnumWindows(callback, None)

    except win32gui.error:
        return False

    return found


def search_running_applications() -> str:
    """
    Discover applications through their top-level Windows.
    Groups multiple windows belonging to the same executable.
    """

    applications = {} # group windows belonging to the same executable
    print("\nSearching running applications...🔃")
    # EnumWindows() calls this function for every top-level window Windows knows about - Shown under APPS in taskmgr
    def callback(hwnd, _): # Think of hwnd as Windows' ID for an individual window
        try:
            #checks whether the window is visible, retirieve title and ignore empty titles
            if not win32gui.IsWindowVisible(hwnd):
                return True
            title = win32gui.GetWindowText(hwnd).strip()
            if not title:
                return True

            _, pid = win32process.GetWindowThreadProcessId(hwnd) # retrive thread id and process id
            if not pid:
                return True

            # Retrieve info
            process = psutil.Process(pid)
            name = process.name()
            exe = process.exe()

            if not name or not exe:
                return True

            # Group windows by executable
            exe_path = str(Path(exe).resolve())
            key = exe_path.casefold()
            if key not in applications:
                applications[key] = {
                    "name": name,
                    "exe": exe_path,
                    "pid": pid,
                    "windows": [],
                }

            applications[key]["windows"].append(title)

        except (psutil.NoSuchProcess, psutil.AccessDenied): # Processes and windows can disappear while enumeration is happening, we skip it
            pass

        return True

    win32gui.EnumWindows(callback, None) #EnumWindows() uses the callback's return value(True false) to determine whether enumeration should continue.

    if not applications:
        print("\nNo running applications found🫥")
        return "No open applications found."

    output = ["Open applications:"]
    for index, app in enumerate(applications.values(), start=1):
        output.append(
            f"\n{index}. {app['name']}"
            f"\n   PID: {app['pid']}"
            f"\n   EXE: {app['exe']}"
            f"\n   Windows: {', '.join(app['windows'])}"
        )
    print("\nFound running applications😆✅")
    return "\n".join(output)




def close_application(pid: int, exe_path: str) -> str:
    """
    Request graceful closure of an application using its PID.
    Verifies the executable path to avoid terminating a reused PID.
    Does not force-kill the process.
    """

    if os.name != "nt":
        raise RuntimeError("Application closing is supported on Windows only.")

    if pid <= 0:
        raise ValueError("Invalid process ID.")

    process = psutil.Process(pid)
    print("\n Closing requested application...🔃")
    try:
        actual_exe = process.exe()
        if not actual_exe:
            raise ValueError("Cannot determine the process executable.")
        if Path(actual_exe).resolve() != Path(exe_path).resolve(): # This check prevents Mio from accidentally closing an unrelated process.
            raise PermissionError(
                "Executable path does not match the selected process."
            )

        # Collect all visible top-level windows belonging to this PID.
        windows = []
        def collect_windows(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                _, window_pid = win32process.GetWindowThreadProcessId(hwnd)

                if window_pid == pid:
                    windows.append(hwnd)

            return True

        win32gui.EnumWindows(collect_windows, None)

        if not windows:
            print(f"\n{process.name()} (PID {pid}) has no visible windows. "
                            "Cannot request a graceful window close.🥺")
            return (
                f"{process.name()} (PID {pid}) has no visible windows. "
                "Cannot request a graceful window close."
            )

        # Ask each window to close normally.
        for hwnd in windows:
            win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)

        try:
            process.wait(timeout=5)
            print(f"\nSuccessfully closed {process.name()} (PID {pid})😄✅")
            return f"Successfully closed {process.name()} (PID {pid})."

        except psutil.TimeoutExpired:
            print(f"\nClose request sent to {process.name()} (PID {pid}), "
                            "but the process is still running. No force-kill was attempted.😄")
            return (
                f"Close request sent to {process.name()} (PID {pid}), "
                "but the process is still running. No force-kill was attempted."
            )

    except psutil.NoSuchProcess:
        print(f"\nProcess {pid} is no longer running.👍")
        return f"Process {pid} is no longer running."

