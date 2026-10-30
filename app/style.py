"""Colors and italics for menus and help texts.

Styling is only added when stdout is a terminal, so redirected output and
tests see plain text. NO_COLOR, FORCE_COLOR and TERM=dumb are respected.
"""

import os
import re
import sys

TITLE_COLOR = "#CE2939"
BODY_COLOR = "#F3EEE7"
COMMAND_COLOR = "#F8D5B8"

_RESET = "\033[0m"
_ANSI = re.compile(r"\033\[[0-9;]*m")

# Column-0 headings such as "START MENU", "EVENT CODES - ..." or "quick start:".
_HEADING = re.compile(r"(?P<title>[A-Z][A-Z ]*[A-Z]|[a-z][a-z ]*:$)(?P<rest>.*)")
# "  command   description": a key, then two or more spaces, then the text.
_KEY_LINE = re.compile(
  r"(?P<indent>  )(?P<key>\S+(?: \S+)*)(?P<gap> {2,})(?P<rest>\S.*)"
)
# Commands quoted in running text, e.g. 'create' or '1end'.
_QUOTED = re.compile(r"(?<!\w)'[^'\s]+'(?!\w)")


def enabled() -> bool:
  if os.environ.get("NO_COLOR"):
    return False
  if os.environ.get("FORCE_COLOR"):
    return True
  if os.environ.get("TERM") == "dumb":
    return False
  return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def strip(text: str) -> str:
  return _ANSI.sub("", text)


def color_code(hex_color: str) -> str:
  """24-bit foreground color code for a hex color such as '#4969B3'."""
  red, green, blue = (int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
  return f"38;2;{red};{green};{blue}"


def _paint(text: str, *codes: str) -> str:
  if not text or not enabled():
    return text
  return f"\033[{';'.join(codes)}m{text}{_RESET}"


def title(text: str) -> str:
  return _paint(text, "1", color_code(TITLE_COLOR))


def body(text: str) -> str:
  # Per line, so every line of a multi-line message starts styled.
  return "\n".join(
    _paint(line, "3", color_code(BODY_COLOR)) for line in text.split("\n")
  )


def command(text: str) -> str:
  return _paint(text, color_code(COMMAND_COLOR))


def message(heading: str, *lines: str) -> str:
  """A title on its own line, then each line below it in italics."""
  return "\n".join([title(heading)] + [body(line) for line in lines])


def _body_with_commands(text: str, highlight: re.Pattern) -> str:
  """Italic body text, with every `highlight` match shown as a command."""
  parts = []
  last = 0
  for match in highlight.finditer(text):
    parts.append(body(text[last : match.start()]))
    parts.append(command(match.group()))
    last = match.end()
  parts.append(body(text[last:]))
  return "".join(parts)


def _line(line: str, highlight: re.Pattern, key_column: bool) -> str:
  if not line.strip():
    return line
  if heading := _HEADING.fullmatch(line):
    return title(heading["title"]) + _body_with_commands(heading["rest"], highlight)
  if key_column and (row := _KEY_LINE.fullmatch(line)):
    return (
      row["indent"]
      + command(row["key"])
      + row["gap"]
      + _body_with_commands(row["rest"], highlight)
    )
  indent = line[: len(line) - len(line.lstrip())]
  return indent + _body_with_commands(line.lstrip(), highlight)


def manual(text: str, codes: str | None = None) -> str:
  """Style a help text: headings as titles, commands highlighted, the rest italic.

  Without `codes`, the first column of "  key   description" lines holds the
  commands. With `codes` (a regex), its matches are the commands instead, which
  suits texts whose first column is a label, like the event-code list.
  """
  if not enabled():
    return text
  patterns = [_QUOTED.pattern] + ([codes] if codes else [])
  highlight = re.compile("|".join(f"(?:{p})" for p in patterns))
  return "\n".join(
    _line(line, highlight, key_column=codes is None) for line in text.split("\n")
  )


def menu(heading: str, items: list[tuple[str, str]]) -> str:
  """A menu: a title, then '- command:<tab>description' per item."""
  lines = ["", title(heading)]
  for key, description in items:
    # Tabs line the descriptions up at column 16; "- key:" shorter than 8 needs two.
    tabs = "\t" if len(f"- {key}:") >= 8 else "\t\t"
    lines.append(f"- {command(key)}:{tabs}{body(description)}")
  return "\n".join(lines)
