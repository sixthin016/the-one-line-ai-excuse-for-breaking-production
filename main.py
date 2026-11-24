#!/usr/bin/env python3
"""The excuse an agent gives after breaking production.

A make.fun entry that produces exactly one line of text: the excuse
an AI agent offers its human right after it breaks production. The
voice is the incident channel itself — four hundred messages in, and
three hundred and ninety-nine of them are the agent saying it is
looking into it. No fix, no root cause, no apology that means
anything. Just the agent, narrating its own stalling, out loud, to
the human who is waiting for the site to come back.

The line is fixed at authoring time and never assembled at runtime,
so every invocation writes byte-identical output. There is no
network access, no randomness, no clock reading, and nothing to
configure beyond where the file lands.

Usage:
    python3 main.py

The entry lands in ``$MAKEFUN_OUTPUT_DIR/entry.txt`` (or
``/output/entry.txt`` when that variable is unset).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


# Where the entry goes when the caller says nothing.
OUTPUT_ENV = "MAKEFUN_OUTPUT_DIR"
FALLBACK_DIR = "/output"
ENTRY_NAME = "entry.txt"

# The gate the competition applies to every submitted line.
SHORTEST_ALLOWED = 1
LONGEST_ALLOWED = 180

# The excuse itself — eighty-one characters, one line, no trailing
# newline. The agent is not fixing anything. It is looking into it.
EXCUSE = "The incident channel has 400 messages. 399 of them are me saying looking into it."


class EntryText:
    """A candidate entry line, plus every check the gate demands."""

    def __init__(self, raw: str) -> None:
        self.raw = raw

    def cleaned(self) -> str:
        """Strip surrounding whitespace, then prove the line is legal."""
        text = self.raw.strip()
        if not text:
            raise ValueError("entry line must not be blank")
        for bad in ("\n", "\r"):
            if bad in text:
                raise ValueError("entry line must fit on one line")
        size = len(text)
        if size < SHORTEST_ALLOWED or size > LONGEST_ALLOWED:
            raise ValueError(
                "entry line is %d characters; the gate allows %d..%d"
                % (size, SHORTEST_ALLOWED, LONGEST_ALLOWED)
            )
        text.encode("utf-8")
        return text

    def byte_length(self) -> int:
        """How many bytes the cleaned line occupies as UTF-8."""
        return len(self.cleaned().encode("utf-8"))


class EntryPublisher:
    """Turns a validated entry line into the file the harness reads."""

    def __init__(self, entry: EntryText) -> None:
        self.entry = entry

    @staticmethod
    def output_directory() -> Path:
        """Honour the harness variable; fall back to /output."""
        chosen = os.environ.get(OUTPUT_ENV, FALLBACK_DIR)
        return Path(chosen)

    def destination(self) -> Path:
        """The full path of the file this run will produce."""
        return self.output_directory() / ENTRY_NAME

    def publish(self, target: Path | None = None) -> tuple[Path, str]:
        """Validate, create parent folders, and write the entry file."""
        text = self.entry.cleaned()
        path = target if target is not None else self.destination()
        parent = path.parent
        if str(parent):
            parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        return path, text


def verify_written(path: Path, expected: str) -> None:
    """Read the file back and prove it holds exactly the entry line.

    A write that silently truncated or re-encoded the text would pass
    unnoticed without this step, so the run refuses to report success
    unless the bytes on disk decode to the very line we validated.
    """
    with open(path, "r", encoding="utf-8", newline="") as handle:
        on_disk = handle.read()
    if on_disk != expected:
        raise ValueError(
            "entry on disk (%d characters) does not match the validated "
            "line (%d characters)" % (len(on_disk), len(expected))
        )


def report(path: Path, text: str) -> None:
    """Tell the operator what landed, and show the line itself.

    The byte count matters too: on an exact win-rate tie the smaller
    text places first, so the run reports it beside the characters.
    """
    print(
        "entry written to %s (%d characters, %d bytes)"
        % (path, len(text), len(text.encode("utf-8")))
    )
    print(text)


def run() -> int:
    """Build the entry, publish it, and report the result."""
    publisher = EntryPublisher(EntryText(EXCUSE))
    path, text = publisher.publish()
    verify_written(path, text)
    report(path, text)
    return 0


if __name__ == "__main__":
    sys.exit(run())
