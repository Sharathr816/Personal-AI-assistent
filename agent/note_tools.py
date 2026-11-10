import re
from pathlib import Path
import os
import subprocess

from pydantic import BaseModel, ConfigDict, Field


# Project root / notes
NOTES_DIR = Path(__file__).resolve().parent.parent / "notes"


class WriteNoteArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)

class OpenNoteArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    path: str = Field(min_length=1)


def write_note(title: str, content: str) -> str:
    NOTES_DIR.mkdir(parents=True, exist_ok=True)

    # Convert title into a safe filename
    filename = re.sub(
        r'[<>:"/\\|?*\x00-\x1f]',
        "_",
        title
    ).strip(" .")

    if not filename:
        raise ValueError("Invalid note title.")

    # Avoid overwriting existing notes
    path = NOTES_DIR / f"{filename}.txt"
    counter = 1
    while path.exists():
        path = NOTES_DIR / f"{filename}_{counter}.txt"
        counter += 1

    # Save content
    path.write_text(content, encoding="utf-8")
    return f"Note successfully saved: {path}"


def open_note(path: str) -> str:
    if os.name != "nt":
        raise RuntimeError("Opening notes requires Windows.")

    # Resolve the supplied path
    note_path = Path(path)

    if not note_path.is_absolute():
        note_path = NOTES_DIR / note_path

    note_path = note_path.resolve()
    notes_root = NOTES_DIR.resolve()

    # Prevent access outside the notes directory
    if not note_path.is_relative_to(notes_root):
        raise ValueError("Access denied: path outside notes directory.")

    # Verify that the target exists and is a file
    if not note_path.exists() or not note_path.is_file():
        raise FileNotFoundError(f"Note not found: {note_path}")

    # Open using Windows Notepad
    subprocess.Popen(["notepad.exe", str(note_path)])
    return f"Opened note: {note_path.name}"