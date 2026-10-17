import json
import re
import sys
import time

sys.path.insert(0, "src")
sys.stdout.reconfigure(encoding="utf-8")

from careerlog.generate import generate_bullets

# Words a bullet should only use if its cited entries use them too.
WATCH_TERMS = [
    "deployed", "deploy", "deployment", "production", "pipeline", "scaled",
    "scalable", "launched", "improved", "optimized", "automated", "end-to-end",
    "real-time", "led", "managed", "mentored", "kubernetes", "docker", "aws",
    "azure", "gcp", "spark", "hadoop", "tensorflow", "pytorch", "keras",
    "scikit-learn", "sklearn", "flask", "fastapi", "django", "tableau",
    "power bi", "sql", "mlops", "ci/cd", "api", "react", "java",
]
NUM = re.compile(r"\d+(?:,\d{3})*(?:\.\d+)?")


def norm(text):
    for ch in ("\u2010", "\u2011", "\u2013", "\u2014"):
        text = text.replace(ch, "-")
    return text.lower()


def numbers(text):
    return {n.replace(",", "") for n in NUM.findall(text)}


def has(text, term):
    pattern = r"(?<![\w-])" + re.escape(term) + r"(?![\w-])"
    return re.search(pattern, text) is not None


def generate_with_retry(request):
    last = ""
    for attempt in range(3):
        try:
            return generate_bullets(request, k=8), ""
        except Exception as exc:
            last = str(exc)[:120]
            time.sleep(5 * (attempt + 1))
    return None, last


def main():
    with open("eval/cases.jsonl", encoding="utf-8") as f:
        cases = [json.loads(line) for line in f if line.strip()]

    results = []
    problems = []
    for case in cases:
        out, err = generate_with_retry(case["request"])
        if out is None:
            print(case["id"], "ERROR", err)
            results.append({"case": case, "error": err})
            continue

        bullets, used = out
        by_id = {e["id"]: e for e in used}
        cited_projects = set()
        rows = []
        for b in bullets:
            cited = [by_id[i] for i in b["source_ids"] if i in by_id]
            for e in cited:
                if e["project"]:
                    cited_projects.add(e["project"])
            source = norm(" ".join(e["text"] for e in cited))
            text = norm(b["text"])
            bad_nums = sorted(numbers(text) - numbers(source))
            bad_terms = [t for t in WATCH_TERMS if has(text, t) and not has(source, t)]
            ok = bool(cited) and not bad_nums and not bad_terms
            rows.append({"text": b["text"], "ok": ok, "no_citation": not cited,
                         "bad_numbers": bad_nums, "bad_terms": bad_terms})
            if not ok:
                problems.append((case["id"], b["text"], not cited, bad_nums, bad_terms))

        expected = set(case["expected_projects"])
        recall = len(expected & cited_projects) / len(expected) if expected else None
        n_ok = sum(r["ok"] for r in rows)
        results.append({"case": case, "n_bullets": len(rows), "n_ok": n_ok,
                        "recall": recall, "projects": sorted(cited_projects),
                        "bullets": rows})

        if case["type"] == "uncovered":
            status = "PASS" if not rows else "FAIL (wrote bullets)"
            print(case["id"], "uncovered", "bullets=" + str(len(rows)), status)
        else:
            print(case["id"], "covered  ", "bullets=" + str(len(rows)),
                  "ok=" + str(n_ok), "recall=" + "{:.2f}".format(recall))
        time.sleep(1)

    done = [r for r in results if "error" not in r]
    unc = [r for r in done if r["case"]["type"] == "uncovered"]
    cov = [r for r in done if r["case"]["type"] == "covered"]
    abstained = sum(r["n_bullets"] == 0 for r in unc)
    total = sum(r["n_bullets"] for r in cov)
    good = sum(r["n_ok"] for r in cov)
    recalls = [r["recall"] for r in cov]
    hits = sum(1 for r in cov if r["recall"] and r["recall"] > 0)

    print("\n=== SUMMARY ===")
    print("Errors:", len(results) - len(done))
    if unc:
        print("Abstention on uncovered requests:", abstained, "/", len(unc))
    if cov:
        print("Fully supported bullets:", good, "/", total)
        print("Average project recall: {:.2f}".format(sum(recalls) / len(recalls)))
        print("Requests with at least one expected project:", hits, "/", len(cov))

    if problems:
        print("\n=== BULLETS WITH PROBLEMS ===")
        for cid, text, no_cit, nums, terms in problems:
            print("\n[" + cid + "] " + text)
            if no_cit:
                print("   no valid citation")
            if nums:
                print("   numbers not in source:", nums)
            if terms:
                print("   terms not in source:", terms)

    with open("eval/results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
