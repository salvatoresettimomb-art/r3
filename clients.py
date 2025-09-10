
import requests
from typing import Dict, Any, Optional, List

def _get_by_path(d, path, default=None):
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

def fetch_http_items(
    url:str,
    headers: Optional[Dict[str,str]] = None,
    params: Optional[Dict[str,Any]] = None,
    root_list_path: str = ""
) -> List[dict]:
    r = requests.get(url, headers=headers or {}, params=params or {}, timeout=25)
    r.raise_for_status()
    data = r.json()
    if root_list_path:
        items = _get_by_path(data, root_list_path, default=[])
    else:
        items = data
    if not isinstance(items, list):
        items = [items] if items else []
    return items
