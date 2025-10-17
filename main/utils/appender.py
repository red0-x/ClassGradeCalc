from webhandle import driver, get_assignment_links_on_class, scrape_assignment_page, Path
import json
all_results = []


def append(info):
    all_results.append(info)
    out_json = Path.cwd() / "grades.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(all_results)} records to {out_json}")
