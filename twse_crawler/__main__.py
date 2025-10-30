import argparse
import sys
import time
import datetime as dt
from typing import Optional

from .db import ensure_indexes, upsert_t86, upsert_bfi82u
from .twse_api import fetch_t86, fetch_bfi82u


def parse_date(s: str) -> dt.date:
    return dt.datetime.strptime(s, "%Y-%m-%d").date()


def date_range(start: dt.date, end: dt.date):
    d = start
    delta = dt.timedelta(days=1)
    while d <= end:
        yield d
        d += delta


def run_one(date: dt.date, want_t86: bool, want_bfi82u: bool) -> None:
    if want_t86:
        t86_docs = fetch_t86(date)
        if t86_docs:
            n = upsert_t86(t86_docs)
            print(f"[T86] {date} upserted: {n} rows")
        else:
            print(f"[T86] {date} no data or holiday")

    if want_bfi82u:
        bdoc = fetch_bfi82u(date)
        if bdoc:
            upsert_bfi82u(bdoc)
            print(f"[BFI82U] {date} upserted")
        else:
            print(f"[BFI82U] {date} no data or holiday")


def main(argv: Optional[list[str]] = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]

    parser = argparse.ArgumentParser(description="TWSE crawler to MongoDB")
    sub = parser.add_subparsers(dest="cmd", required=True)

    def add_common(p: argparse.ArgumentParser):
        g = p.add_mutually_exclusive_group(required=True)
        g.add_argument("--date", help="單日 YYYY-MM-DD")
        g.add_argument("--start", help="區間起 YYYY-MM-DD")
        p.add_argument("--end", help="區間迄 YYYY-MM-DD（與 --start 搭配）")
        p.add_argument("--sleep", type=float, default=0.6, help="每日請求間隔秒數")

    p_t86 = sub.add_parser("t86", help="抓取 T86")
    add_common(p_t86)

    p_b = sub.add_parser("bfi82u", help="抓取 BFI82U")
    add_common(p_b)

    p_both = sub.add_parser("both", help="兩者皆抓")
    add_common(p_both)

    args = parser.parse_args(argv)
    ensure_indexes()

    if args.date:
        d = parse_date(args.date)
        run_one(d, want_t86=args.cmd in ("t86", "both"), want_bfi82u=args.cmd in ("bfi82u", "both"))
        return 0

    if not args.start or not args.end:
        print("--start 與 --end 需同時提供", file=sys.stderr)
        return 2

    start = parse_date(args.start)
    end = parse_date(args.end)
    if end < start:
        print("end 需 >= start", file=sys.stderr)
        return 2

    for d in date_range(start, end):
        run_one(d, want_t86=args.cmd in ("t86", "both"), want_bfi82u=args.cmd in ("bfi82u", "both"))
        time.sleep(args.sleep)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

