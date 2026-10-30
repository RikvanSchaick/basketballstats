from app import paths


def read_history() -> list[str]:
  with open(paths.HISTORY, "r") as f:
    return f.read().splitlines()


def write_history(lines: list[str]) -> None:
  with open(paths.HISTORY, "w") as f:
    f.writelines(line + "\n" for line in lines)


def append_history(*lines: str) -> None:
  with open(paths.HISTORY, "a") as f:
    f.writelines(line + "\n" for line in lines)
