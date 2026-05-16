def print_result_payload(res: dict) -> str:
    sources = ", ".join(
        source.get("label", "unknown") for source in res.get("sources", [])
    )
    return (
        f"[Mode: {res.get('mode')}]\nAnswer:\n{res.get('answer')}\nSources: {sources}"
    )


def _print_result(res: dict) -> None:
    print(print_result_payload(res))


def print_help_payload() -> str:
    return "ask | mode | ingest | filter | history | reset | status | help | quit"


def _print_help() -> None:
    print(print_help_payload())
