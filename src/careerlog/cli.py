import argparse
from datetime import date

from .index import build_index, search
from .schema import LogEntry
from .store import add_entry, load_entries


def main():
    parser = argparse.ArgumentParser(prog="careerlog")
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="Add a log entry")
    add.add_argument("text", help="What you did, in plain words")
    add.add_argument("--tags", default="", help="Comma-separated, e.g. ml,python")
    add.add_argument("--date", default=None, help="YYYY-MM-DD (default: today)")
    add.add_argument("--link", default=None, help="Repo / PR / doc URL")

    sub.add_parser("list", help="Show all entries")

    imp = sub.add_parser("import", help="Import entries from a text file")
    imp.add_argument("file", help="Path to file, one entry per line: date | tags | text")

    sub.add_parser("index", help="Rebuild the search index from the log")

    srch = sub.add_parser("search", help="Find entries by meaning")
    srch.add_argument("query", help="What you are looking for")
    srch.add_argument("-k", type=int, default=5, help="How many results")

    args = parser.parse_args()

    if args.command == "add":
        entry = LogEntry(
            date=args.date or date.today().isoformat(),
            text=args.text,
            tags=[t.strip() for t in args.tags.split(",") if t.strip()],
            link=args.link,
        )
        add_entry(entry)
        print(f"Added [{entry.id}] {entry.date}: {entry.text}")

    elif args.command == "list":
        for e in load_entries():
            tags = f" ({', '.join(e.tags)})" if e.tags else ""
            print(f"[{e.id}] {e.date}: {e.text}{tags}")

    elif args.command == "import":
        count = 0
        with open(args.file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                d, tags, text = [part.strip() for part in line.split("|", 2)]
                add_entry(LogEntry(
                    date=d,
                    text=text,
                    tags=[t.strip() for t in tags.split(",") if t.strip()],
                ))
                count += 1
        print(f"Imported {count} entries")

    elif args.command == "index":
        n = build_index(load_entries())
        print(f"Indexed {n} entries")

    elif args.command == "search":
        for r in search(args.query, k=args.k):
            print(f"[{r['id']}] {r['date']} (distance {r['distance']:.2f}): {r['text'][:90]}")


if __name__ == "__main__":
    main()