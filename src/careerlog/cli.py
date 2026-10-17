import argparse
from datetime import date

from .generate import generate_bullets
from .index import build_index, search
from .schema import LogEntry
from .store import add_entry, load_entries


def split_tags(raw):
    return [t.strip() for t in raw.split(",") if t.strip()]


def main():
    parser = argparse.ArgumentParser(prog="careerlog")
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="Add a log entry")
    add.add_argument("text", help="What you did")
    add.add_argument("--project", default=None, help="Project name")
    add.add_argument("--tags", default="", help="e.g. ml,python")
    add.add_argument("--date", default=None, help="YYYY-MM-DD")
    add.add_argument("--link", default=None, help="Repo or doc URL")

    sub.add_parser("list", help="Show all entries")

    imp = sub.add_parser("import", help="Import entries from a file")
    imp.add_argument("file", help="Lines like: date | project | tags | text")

    sub.add_parser("index", help="Rebuild the search index")

    srch = sub.add_parser("search", help="Find entries by meaning")
    srch.add_argument("query", help="What you are looking for")
    srch.add_argument("-k", type=int, default=5, help="Number of results")

    bul = sub.add_parser("bullets", help="Generate resume bullets")
    bul.add_argument("request", help="e.g. machine learning projects")
    bul.add_argument("-k", type=int, default=5, help="Entries to retrieve")

    args = parser.parse_args()

    if args.command == "add":
        entry = LogEntry(
            date=args.date or date.today().isoformat(),
            project=args.project,
            text=args.text,
            tags=split_tags(args.tags),
            link=args.link,
        )
        add_entry(entry)
        print("Added [" + entry.id + "] " + str(entry.date))

    elif args.command == "list":
        for e in load_entries():
            proj = " <" + e.project + ">" if e.project else ""
            tags = ""
            if e.tags:
                tags = " (" + ", ".join(e.tags) + ")"
            print("[" + e.id + "] " + str(e.date) + proj + ": " + e.text + tags)

    elif args.command == "import":
        count = 0
        with open(args.file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                d, project, tags, text = [p.strip() for p in line.split("|", 3)]
                add_entry(LogEntry(
                    date=d,
                    project=project or None,
                    text=text,
                    tags=split_tags(tags),
                ))
                count += 1
        print("Imported " + str(count) + " entries")

    elif args.command == "index":
        n = build_index(load_entries())
        print("Indexed " + str(n) + " entries")

    elif args.command == "search":
        for r in search(args.query, k=args.k):
            dist = "{:.2f}".format(r["distance"])
            short = r["text"][:90]
            print("[" + r["id"] + "] " + r["date"] + " (" + dist + "): " + short)

    elif args.command == "bullets":
        bullets, hits = generate_bullets(args.request, k=args.k)
        by_id = {h["id"]: h for h in hits}
        if not bullets:
            print("No supported bullets for this request.")
        for b in bullets:
            flag = "" if b["supported"] else "  [UNSUPPORTED]"
            print("\n- " + b["text"] + flag)
            for sid in b["source_ids"]:
                print("    source [" + sid + "]: " + by_id[sid]["text"][:120])


if __name__ == "__main__":
    main()
