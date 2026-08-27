"""Interactive REPL for the GTM agent.

Run from the repo root with:

    uv run python3 repl.py
    uv run python3 repl.py --user-id rep_jchen

Slash commands: /help  /rep [id]  /reps  /new  /quit
"""

import argparse
import uuid

try:
    import readline  # noqa: F401  — enables arrow-key history on Unix
except ImportError:
    pass

from langsmith.run_trees import get_cached_client

from gtm_agent.data_service import get_rep
from gtm_agent.gtm_records import REP_IDS
from gtm_agent.gtm_agent import run_agent

DEFAULT_REP_ID = "rep_jchen"

HELP = """\
Commands:
  /help          Show this help
  /rep [id]      Show or switch the signed-in rep
  /reps          List known reps
  /new           Start a new conversation thread
  /quit          Exit (also Ctrl-D)

Anything else is sent to the agent as a rep request.
"""


def _format_rep(record: dict) -> str:
    return f"{record['rep_id']}  {record['name']}  <{record['email']}>"


def _resolve_rep(value: str) -> dict | None:
    return get_rep(value.strip())


def _list_reps() -> str:
    return "\n".join("  " + _format_rep(r) for r in REP_IDS)


def main() -> None:
    parser = argparse.ArgumentParser(description="Interactive REPL for the GTM agent.")
    parser.add_argument(
        "--user-id",
        default=DEFAULT_REP_ID,
        help=f"Signed-in rep id or name (default: {DEFAULT_REP_ID})",
    )
    args = parser.parse_args()

    record = _resolve_rep(args.user_id)
    if record is None:
        parser.error(f"unknown rep {args.user_id!r}\nKnown reps:\n{_list_reps()}")
    user_id = record["rep_id"]
    thread_id = str(uuid.uuid4())

    print("GTM agent REPL. Type /help for commands, /quit to exit.")
    print(f"Signed in as {_format_rep(record)}")
    print(f"Thread {thread_id}")
    print()

    while True:
        try:
            line = input(f"[{user_id}] > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not line:
            continue

        if line in ("/quit", "/exit", "/q"):
            break

        if line in ("/help", "/h", "/?"):
            print(HELP)
            continue

        if line == "/reps":
            print(_list_reps())
            continue

        if line == "/new":
            thread_id = str(uuid.uuid4())
            print(f"New thread {thread_id}")
            continue

        if line == "/rep" or line.startswith("/rep "):
            rest = line[4:].strip()
            if not rest:
                print(f"Signed in as {_format_rep(get_rep(user_id))}")
                continue
            switched = _resolve_rep(rest)
            if switched is None:
                print(f"Unknown rep {rest!r}. Try /reps.")
                continue
            user_id = switched["rep_id"]
            print(f"Signed in as {_format_rep(switched)}")
            continue

        if line.startswith("/"):
            print(f"Unknown command {line.split()[0]}. Type /help.")
            continue

        try:
            result = run_agent(line, user_id=user_id, thread_id=thread_id)
        except Exception as exc:
            print(f"Error: {exc}")
            continue
        print()
        print(result["reply"])
        print()

    get_cached_client().flush()
    print("Bye.")


if __name__ == "__main__":
    main()
