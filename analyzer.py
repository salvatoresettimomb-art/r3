
import math
from collections import Counter, defaultdict
from typing import List, Dict, Any

REDS = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
BLACKS = {2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35}

def _get_by_path(d, path, default=None):
    """Get nested value using a dot-path like 'a.b.0.c'."""
    if not path:
        return d
    cur = d
    for part in path.split("."):
        if part == "":
            continue
        if isinstance(cur, (list, tuple)) and part.isdigit():
            idx = int(part)
            if 0 <= idx < len(cur):
                cur = cur[idx]
            else:
                return default
        elif isinstance(cur, dict):
            if part in cur:
                cur = cur[part]
            else:
                return default
        else:
            return default
    return cur

def color_of(n:int) -> str:
    if n == 0: return "green"
    return "red" if n in REDS else "black"

def dozen_of(n:int) -> str:
    if n == 0: return "zero"
    if 1 <= n <= 12: return "1st"
    if 13 <= n <= 24: return "2nd"
    return "3rd"

def column_of(n:int) -> str:
    if n == 0: return "zero"
    return ["1st","2nd","3rd"][(n-1)%3]

def standardize_spins(raw_items: List[Dict[str, Any]], mapping: Dict[str, str]):
    """
    Normalize raw JSON records into a list of:
    { "number": int, "time": str|None, "lightning": [ {"number": int, "multiplier": int|float}, ... ] }
    mapping keys (dot-paths):
      - number_path (required)
      - time_path (optional)
      - lightning_list_path (optional)
      - lightning_number_path (optional)
      - lightning_multiplier_path (optional)
    """
    out = []
    for item in raw_items:
        n = _get_by_path(item, mapping.get("number_path"))
        if n is None:
            continue
        try:
            n_int = int(n)
        except Exception:
            continue

        t = _get_by_path(item, mapping.get("time_path")) if mapping.get("time_path") else None

        lightning = []
        llp = mapping.get("lightning_list_path")
        if llp:
            lst = _get_by_path(item, llp, default=[])
            if isinstance(lst, (list, tuple)):
                for li in lst:
                    lnum = None
                    lmul = None
                    if mapping.get("lightning_number_path"):
                        lnum = _get_by_path(li, mapping.get("lightning_number_path"))
                    if mapping.get("lightning_multiplier_path"):
                        lmul = _get_by_path(li, mapping.get("lightning_multiplier_path"))
                    try:
                        lnum = int(lnum) if lnum is not None else None
                    except Exception:
                        lnum = None
                    if lnum is not None:
                        lightning.append({"number": lnum, "multiplier": lmul})
        out.append({"number": n_int, "time": t, "lightning": lightning})
    return out

def analyze(spins: List[Dict[str, Any]]):
    nums = [s["number"] for s in spins if isinstance(s.get("number"), int)]
    total = len(nums)

    counts = Counter(nums)
    last_seen = {}
    for idx, n in enumerate(nums):
        last_seen[n] = idx
    gaps = {n: (total-1-last_seen[n]) if n in last_seen else math.inf for n in range(37)}

    lightning_hits = 0
    lightning_mark = []
    for s in spins:
        ln = {x["number"] for x in s.get("lightning", []) if isinstance(x.get("number"), int)}
        if s.get("number") in ln:
            lightning_hits += 1
            lightning_mark.append((s["number"], s.get("lightning")))
    lightning_rate = (lightning_hits / total) if total else 0.0

    by_color = Counter(color_of(n) for n in nums)
    by_parity = Counter(("even" if n%2==0 else "odd") for n in nums if n != 0)
    by_dozen = Counter(dozen_of(n) for n in nums)
    by_column = Counter(column_of(n) for n in nums)

    hot = counts.most_common(10)
    cold = counts.most_common()[:-11:-1]
    top_gaps = sorted(((n, g) for n,g in gaps.items() if g != math.inf), key=lambda x:x[1], reverse=True)[:10]

    return {
        "total_spins": total,
        "freq": counts,
        "hot_top10": hot,
        "cold_bottom10": cold,
        "longest_gaps_top10": top_gaps,
        "by_color": by_color,
        "by_parity": by_parity,
        "by_dozen": by_dozen,
        "by_column": by_column,
        "lightning_rate": lightning_rate,
        "lightning_mark_examples": lightning_mark[:10],
    }

def suggest_numbers(spins: List[Dict[str, Any]], strategy: str = "combo", k:int = 5, decay: float = 0.97):
    """
    Return k suggested numbers using the selected strategy:
      - 'hot': top by frequency
      - 'overdue': top by gap (longest since last seen)
      - 'recency_weighted': exponential-decay weighted frequency (more weight to recent spins)
      - 'combo': average rank of 'hot' and 'overdue'
    """
    stats = analyze(spins)
    total = stats["total_spins"]
    if total == 0:
        return []

    # Build arrays
    counts = [stats["freq"].get(n, 0) for n in range(37)]
    # gaps
    # if inf, set to a large value to make it "very overdue"
    gaps = []
    for n in range(37):
        g = None
        for pair in stats["longest_gaps_top10"]:
            pass
        # recompute exact gap array
    # recompute exact gaps from spins
    seq = [s["number"] for s in spins]
    last_seen = {n: None for n in range(37)}
    for idx, n in enumerate(seq):
        last_seen[n] = idx
    gaps_arr = []
    for n in range(37):
        if last_seen[n] is None:
            gaps_arr.append(float('inf'))
        else:
            gaps_arr.append(total - 1 - last_seen[n])

    def topk_from_scores(scores, k):
        # Returns indices of top k scores (descending); ties broken by lower number for determinism
        idxs = list(range(37))
        idxs.sort(key=lambda n: (-scores[n], n))
        return [n for n in idxs[:k]]

    # 1) HOT
    hot_scores = counts[:]

    # 2) OVERDUE
    # For INF gap, treat as very large
    max_finite = max([g for g in gaps_arr if g != float('inf')], default=0)
    overdue_scores = [ (g if g != float('inf') else max_finite + 1000) for g in gaps_arr ]

    # 3) RECENCY WEIGHTED
    rw_scores = [0.0]*37
    w = 1.0
    for n in reversed(seq):  # newest to oldest
        rw_scores[n] += w
        w *= decay

    # 4) COMBO: normalize and average HOT + OVERDUE
    def normalize(x):
        mn = min(x); mx = max(x)
        if mx == mn:
            return [0.0]*len(x)
        return [(xi - mn)/(mx - mn) for xi in x]
    nh = normalize(hot_scores)
    no = normalize(overdue_scores)
    combo_scores = [(nh[i] + no[i]) / 2.0 for i in range(37)]

    if strategy == "hot":
        scores = hot_scores
    elif strategy == "overdue":
        scores = overdue_scores
    elif strategy == "recency_weighted":
        scores = rw_scores
    else:
        scores = combo_scores

    picks = topk_from_scores(scores, k)

    return picks, {
        "hot": topk_from_scores(hot_scores, k),
        "overdue": topk_from_scores(overdue_scores, k),
        "recency_weighted": topk_from_scores(rw_scores, k),
        "combo": topk_from_scores(combo_scores, k),
    }
