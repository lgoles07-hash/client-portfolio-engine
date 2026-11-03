"""CLI: python run.py [client.json ...] [--data my_returns.csv] [--out output]"""
import argparse
from pathlib import Path

from engine.allocate import build_allocation
from engine.data import load_returns
from engine.ips import write_report
from engine.profile import ClientProfile


def main():
    ap = argparse.ArgumentParser(description="Client profile -> portfolio -> IPS")
    ap.add_argument("clients", nargs="*", help="client JSON files (default: everything in clients/)")
    ap.add_argument("--data", help="custom returns CSV (percent, columns match data/annual_returns.csv)")
    ap.add_argument("--out", default="output")
    args = ap.parse_args()

    files = [Path(c) for c in args.clients] or sorted(Path("clients").glob("*.json"))
    returns = load_returns(args.data)
    for f in files:
        p = ClientProfile.from_json(f)
        alloc = build_allocation(p, returns)
        report = write_report(p, alloc, returns, args.out)
        mix = ", ".join(f"{k} {v:.0%}" for k, v in alloc.weights.items() if v)
        print(f"{p.name}: equity {alloc.equity_final:.0%} | {mix}\n  -> {report}")


if __name__ == "__main__":
    main()
