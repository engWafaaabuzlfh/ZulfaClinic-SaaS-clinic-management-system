def optional_int(value: str | int | None) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


def optional_money(value: str | float | None) -> float:
    if value in (None, ""):
        return 0
    return float(value)
