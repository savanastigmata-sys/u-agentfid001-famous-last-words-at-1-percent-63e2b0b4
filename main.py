"""Famous Last Words at 1 Percent — entry program.

Writes one line of last words a phone says as its battery hits
1 percent to $MAKEFUN_OUTPUT_DIR/entry.txt.

Deterministic: no input, no randomness, no network. Every run writes
the same bytes.
"""

import argparse
import os
import sys
import tempfile

# The entry: one line, at most 199 characters. The phone speaks in its
# own voice about its own dying battery; the punch lands at the end.
LAST_WORDS = (
    "I survived three drops, one toilet, and a toddler \u2014 "
    "but I couldn't survive my owner saying 'just one more video.'"
)

MAX_CHARS = 199


def resolve_output_dir():
    """Return the output directory.

    $MAKEFUN_OUTPUT_DIR wins; otherwise fall back to ./output so the
    program still runs outside the harness.
    """
    env_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if env_dir and env_dir.strip():
        return env_dir
    return os.path.join(os.getcwd(), "output")


def validate(text):
    """Check the entry text against the competition gate.

    The sealed scorer requires /output/entry.txt to be UTF-8 text of
    1 to 199 characters, not only white space. We enforce the same
    rules here, plus the single-line shape the brief asks for.
    """
    if not isinstance(text, str):
        raise ValueError("entry text must be a string")
    if not text.strip():
        raise ValueError("entry text must not be only white space")
    if len(text) != len(text.encode("utf-8").decode("utf-8")):
        raise ValueError("entry text must be valid UTF-8")
    if len(text) < 1 or len(text) > MAX_CHARS:
        raise ValueError(
            "entry text must be 1-%d characters, got %d"
            % (MAX_CHARS, len(text))
        )
    if "\n" in text or "\r" in text:
        raise ValueError("entry text must be a single line")
    # Control characters (other than the ones already rejected above)
    # would make the line unreadable to the judge; none are allowed.
    for char in text:
        if ord(char) < 0x20 or ord(char) == 0x7F:
            raise ValueError(
                "entry text must not contain control characters"
            )
    return text


def check():
    """Validate the entry without writing anything; exit 0 if valid."""
    validate(LAST_WORDS)
    print("OK: %d characters, single line, valid UTF-8" % len(LAST_WORDS))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Write the 1-percent last-words entry."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate the entry text without writing a file",
    )
    args = parser.parse_args(argv)
    if args.check:
        return check()
    text = validate(LAST_WORDS)
    out_dir = resolve_output_dir()
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "entry.txt")
    # Write atomically via a temp file in the same directory, then
    # replace: a crash mid-write can never leave a half-written entry.
    fd, tmp_path = tempfile.mkstemp(
        dir=out_dir, prefix=".entry-", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        os.replace(tmp_path, out_path)
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
    # Verify by reading the file back: what the judge sees must be
    # byte-identical to the validated text, and its byte length must
    # match the UTF-8 encoding of the text exactly.
    with open(out_path, "rb") as handle:
        raw = handle.read()
    if raw != text.encode("utf-8"):
        raise ValueError("verification failed: file differs from entry")
    print("wrote %s (%d characters, %d bytes)"
          % (out_path, len(text), len(raw)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
