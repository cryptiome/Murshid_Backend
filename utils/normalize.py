# utils/normalize.py

def norm_id(x) -> str | None:
    """Always return string ID for document IDs or keys."""
    if x is None:
        return None
    if isinstance(x, float) and x.is_integer():
        x = int(x)
    return str(x).strip()

def norm_int(x) -> int | None:
    """Return int if possible (1, '1', 1.0 -> 1)."""
    if x is None:
        return None
    if isinstance(x, int):
        return x
    if isinstance(x, float) and x.is_integer():
        return int(x)
    if isinstance(x, str):
        s = x.strip()
        if s.isdigit():
            return int(s)
    return None

def norm_passed(x) -> bool:
    """Convert passed field (Yes/No) to bool."""
    if x is None:
        return False
    s = str(x).strip().lower()
    return s in ("yes", "y", "true", "1", "passed")
