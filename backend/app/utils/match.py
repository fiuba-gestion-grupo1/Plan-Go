from typing import Iterable, Optional


def _normalize_keywords(values: Iterable[str]) -> set[str]:
    """
    Pasa todo a lowercase, saca espacios y ignora valores vacíos.
    """
    out: set[str] = set()
    for v in values:
        if isinstance(v, str):
            s = v.strip().lower()
            if s:
                out.add(s)
    return out


def compute_match_percentage(
    me_keywords: Iterable[str],
    other_keywords: Iterable[str],
) -> Optional[int]:
    """
    Calcula el % de coincidencia DESDE MI PUNTO DE VISTA (usuario logueado).

    Fórmula:
        match = (# prefs en común) / (# MIS prefs) * 100

    - Si YO no tengo preferencias => 0
    - Si el otro no tiene preferencias => 0
    - Si no hay overlap => 0
    """

    me_set = _normalize_keywords(me_keywords)
    other_set = _normalize_keywords(other_keywords)

    if not me_set or not other_set:
        return 0

    overlap = me_set & other_set
    if not overlap:
        return 0

    pct = int(round(len(overlap) / len(me_set) * 100))

    if pct < 0:
        pct = 0
    if pct > 100:
        pct = 100

    return pct
