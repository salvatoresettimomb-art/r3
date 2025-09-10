
import argparse
import json
from analyzer import analyze, standardize_spins, suggest_numbers
from clients import fetch_http_items

def main():
    ap = argparse.ArgumentParser(description="XXXTreme Lightning Roulette Analyzer – CLI")
    ap.add_argument("--url", required=True, help="Endpoint HTTP")
    ap.add_argument("--headers", default="{}", help='JSON headers')
    ap.add_argument("--params", default="{}", help='JSON params (es. {"limit":500})')
    ap.add_argument("--root", default="results", help="Root list path nel JSON")
    ap.add_argument("--number", default="number", help="Path numero vincente")
    ap.add_argument("--time", default="time", help="Path timestamp")
    ap.add_argument("--l-list", default="lightningNumbers", help="Path lista lightning")
    ap.add_argument("--l-num", default="number", help="Path numero in ogni lightning")
    ap.add_argument("--l-mul", default="multiplier", help="Path moltiplicatore in ogni lightning")
    ap.add_argument("--strategy", default="combo", choices=["combo","hot","overdue","recency_weighted"], help="Strategia suggerimenti")

    args = ap.parse_args()
    headers = json.loads(args.headers)
    params = json.loads(args.params)

    raw_items = fetch_http_items(args.url, headers=headers, params=params, root_list_path=args.root)
    mapping = {
        "number_path": args.number,
        "time_path": args.time,
        "lightning_list_path": args.l_list,
        "lightning_number_path": args.l_num,
        "lightning_multiplier_path": args.l_mul,
    }
    spins = standardize_spins(raw_items, mapping)
    stats = analyze(spins)
    picks, all_buckets = suggest_numbers(spins, strategy=args.strategy, k=5)

    out = {
        "total_spins": stats["total_spins"],
        "lightning_rate": stats["lightning_rate"],
        "hot_top10": stats["hot_top10"],
        "cold_bottom10": stats["cold_bottom10"],
        "longest_gaps_top10": stats["longest_gaps_top10"],
        "by_color": stats["by_color"],
        "by_parity": stats["by_parity"],
        "by_dozen": stats["by_dozen"],
        "by_column": stats["by_column"],
        "suggested_numbers_strategy": args.strategy,
        "suggested_numbers": picks,
        "all_strategies_top5": all_buckets,
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
