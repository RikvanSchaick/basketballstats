import asyncio
import sys

from prompt_toolkit import PromptSession
from prompt_toolkit.document import Document
from prompt_toolkit.key_binding import KeyBindings

from app import style
from app.clock.gameclock import ClockLogError, GameClockTracker
from app.history import read_history

# Event strings start with the period digit plus MMSS.
PREFIX_LEN = 5
LIVE_CLOCK_INTERVAL = 0.2
CLOCK_TITLE = "GAME CLOCK"


def clock_message(*lines: str) -> None:
  print("\n" + style.message(CLOCK_TITLE, *lines))


def _print_wait(msg: str) -> None:
  print(style.body(f"  {msg}"))


def _clock_prefix(tracker, quarter):
  """Event-string prefix (quarter + MMSS) from the video, or None."""
  if tracker is None:
    return None
  sample = tracker.sample()
  if sample is None or not sample.usable:
    return None
  return f"{quarter}{sample.event_time}"


def setup_tracker(options, quarter=None, match_id=None):
  """Build the game-clock tracker, or return None to stay fully manual."""
  if options.no_video_clock:
    return None

  tracker = GameClockTracker(
    csv_path=options.csv,
    anchor_clock=options.anchor_clock,
    anchor=options.anchor,
    match_id=match_id,
  )
  try:
    path = tracker.load_csv()
    clock_message(f"Using {path.name}")
    tracker.start()
    tracker.set_quarter(quarter)
    info = tracker.anchor_to_video(on_wait=_print_wait)
  except ClockLogError as exc:
    clock_message(
      str(exc), "Continuing without automatic clock times; type them yourself."
    )
    tracker.stop()
    return None
  except KeyboardInterrupt:
    clock_message("Anchoring cancelled; type the times yourself.")
    tracker.stop()
    return None

  print_anchor(info)
  return tracker


def print_anchor(info):
  """Confirmation of where the video was lined up with the CSV."""
  where = f"quarter {info['quarter']} " if info["quarter"] is not None else ""
  clock_message(
    f"{info['document']} anchored at {info['video_seconds']:.3f}s "
    f"= {where}{info['anchor_clock']} ({info['real_time_text']}), "
    f"offset {info['offset']:+.3f}s"
  )


def ask_sync(quarter):
  """Ask whether the video still lines up with the CSV for this quarter."""
  try:
    reply = input(f"Sync video for quarter {quarter}? (y/n): ")
  except EOFError:
    return False
  # Only an explicit "y" re-syncs; anything else keeps the current offset.
  return reply.strip().lower() == "y"


def anchor_quarter(tracker, quarter):
  """Re-anchor the video on `quarter`. False means fall back to manual times."""
  tracker.invalidate_anchor()
  try:
    info = tracker.anchor_to_video(quarter=quarter, on_wait=_print_wait)
  except (ClockLogError, KeyboardInterrupt, EOFError) as exc:
    clock_message(str(exc) or "Anchoring cancelled.", "Type the times yourself.")
    return False
  print_anchor(info)
  return True


def sync_quarter(tracker, quarter, options):
  """Per-quarter sync step. Returns the tracker, or None to go manual."""
  tracker.set_quarter(quarter)

  # Without an offset there is nothing to keep, so never offer to skip.
  if not tracker.ready:
    clock_message("The video is not lined up with the CSV yet.")
  elif tracker.document_changed():
    clock_message("A different video is open in QuickTime Player.")
  elif options.anchor is not None or not sys.stdin.isatty():
    return tracker
  elif not ask_sync(quarter):
    clock_message(f"Keeping the current sync for quarter {quarter}.")
    return tracker

  if anchor_quarter(tracker, quarter):
    return tracker
  tracker.stop()
  return None


def event_input(quarter, tracker=None) -> str:
  lines = read_history()
  counta = 0
  countb = 0

  # The first five characters (period digit + MMSS) are kept in step with the
  # video while the prompt is open; everything the user types after them is
  # left alone.
  autofill = _clock_prefix(tracker, quarter)
  default_text = autofill or f"{quarter}"

  # "prefix" is the text this code last wrote, so a mismatch means the user
  # edited it themselves. "bare" marks the quarter-only fallback, which may
  # only be upgraded while the line is still untouched.
  live = {
    "active": tracker is not None,
    "prefix": default_text,
    "bare": autofill is None,
  }

  def base_default():
    """The text for the 'new event' state, with the freshest clock."""
    return _clock_prefix(tracker, quarter) or autofill or f"{quarter}"

  bindings = KeyBindings()

  def update_defaulta():
    nonlocal default_text
    if counta > 0:
      default_text = lines[-counta].strip()
    else:
      default_text = base_default()

  def update_defaultb():
    nonlocal default_text
    if countb == 1:
      default_text = lines[-1].strip()[:5]
    elif countb == 2:
      default_text = lines[-1].strip()
    else:
      default_text = base_default()

  def apply_recall(event, at_base):
    """Write a recalled/base entry and resync the live-clock state."""
    event.app.current_buffer.text = default_text
    event.app.current_buffer.cursor_position = len(default_text)
    # Only the plain new-event state keeps following the video.
    live["active"] = at_base and tracker is not None
    if live["active"]:
      live["prefix"] = default_text
      live["bare"] = len(default_text) < PREFIX_LEN

  @bindings.add("up")
  def _(event):
    nonlocal counta
    nonlocal countb
    if counta < len(lines):
      countb = 2
      counta += 1
      update_defaulta()
      apply_recall(event, at_base=False)

  @bindings.add("down")
  def _(event):
    nonlocal counta
    nonlocal countb
    if counta > 1:
      countb = 2
    elif counta == 1:
      countb = 0
    if counta > 0:
      counta -= 1
      update_defaulta()
      apply_recall(event, at_base=counta == 0 and countb == 0)

  @bindings.add("tab")
  def _(event):
    nonlocal counta
    nonlocal countb
    countb += 1
    countb = countb % 3
    update_defaultb()
    apply_recall(event, at_base=countb == 0)
    if countb == 2:
      counta = 1
    else:
      counta = 0

  session = PromptSession(key_bindings=bindings)
  buffer = session.default_buffer

  def refresh_prefix():
    """Re-point the prefix at the current clock; False stops the updates."""
    fresh = _clock_prefix(tracker, quarter)
    if not fresh:
      return True
    prefix = live["prefix"]
    text = buffer.text

    if live["bare"]:
      # Nothing typed yet, so the quarter-only line can become a full
      # prefix. Once the user starts typing, leave it to them.
      if text != prefix:
        return False
      updated, cursor = fresh, len(fresh)
    else:
      if not text.startswith(prefix):
        return False  # the user edited the clock themselves
      if fresh == prefix:
        return True
      shift = len(fresh) - len(prefix)
      updated = fresh + text[len(prefix) :]
      cursor = (
        buffer.cursor_position + shift
        if buffer.cursor_position >= len(prefix)
        else min(buffer.cursor_position, len(fresh))
      )

    live["prefix"] = fresh
    live["bare"] = False
    if updated != text:
      buffer.set_document(Document(updated, cursor), bypass_readonly=True)
    return True

  async def follow_clock():
    while True:
      await asyncio.sleep(LIVE_CLOCK_INTERVAL)
      if not live["active"]:
        continue
      if not refresh_prefix():
        live["active"] = False

  def start_following():
    # Background tasks are cancelled and awaited by the application itself
    # when the prompt finishes, including on Ctrl+C.
    session.app.create_background_task(follow_clock())

  eventstring = session.prompt(
    default=default_text,
    pre_run=start_following if tracker is not None else None,
  )
  return eventstring
