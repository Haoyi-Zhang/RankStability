#!/usr/bin/env python3
"""Audit the distributed bibliography, live-resolution ledger, and citations.

The executable audit checks the frozen evidence packet: exact key coverage, 61
unique entries, identifier syntax/uniqueness, title/year/venue agreement, the
2026-09-21 live-resolution record, exact frozen manuscript-citation snapshot coverage, bounded
citation clusters, and the required 12+5+5 complete-paper calibration matrix.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BIB = ROOT / "literature" / "references.bib"
LEDGER = ROOT / "literature" / "reference-provenance.csv"
CALIBRATION = ROOT / "literature-calibration.csv"
LIVE_AUDIT = ROOT / "literature" / "reference-live-audit.csv"
CITATION_SNAPSHOT = ROOT / "literature" / "manuscript-citations.json"
EXPECTED_REFERENCES = 61
EXPECTED_CALIBRATION = {"same-venue": 12, "influential": 5, "adjacent": 5}


def parse_bibtex(text: str) -> dict[str, dict[str, str]]:
    entries: dict[str, dict[str, str]] = {}
    i = 0
    while True:
        at = text.find("@", i)
        if at < 0:
            break
        m = re.match(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", text[at:], re.S)
        if not m:
            raise AssertionError(f"unparsed BibTeX entry near byte {at}")
        kind, key = m.group(1).lower(), m.group(2)
        body_start = at + m.end()
        depth = 1
        quote = False
        escaped = False
        j = body_start
        while j < len(text) and depth:
            ch = text[j]
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                quote = not quote
            elif not quote and ch == "{":
                depth += 1
            elif not quote and ch == "}":
                depth -= 1
            j += 1
        if depth:
            raise AssertionError(f"unterminated BibTeX entry {key}")
        body = text[body_start : j - 1]
        if key in entries:
            raise AssertionError(f"duplicate BibTeX key {key}")
        fields: dict[str, str] = {"entry_type": kind}
        k = 0
        while k < len(body):
            while k < len(body) and (body[k].isspace() or body[k] == ","):
                k += 1
            if k >= len(body):
                break
            fm = re.match(r"([A-Za-z][A-Za-z0-9_-]*)\s*=\s*", body[k:])
            if not fm:
                raise AssertionError(f"unparsed field in {key}: {body[k:k+60]!r}")
            name = fm.group(1).lower()
            k += fm.end()
            if k >= len(body):
                raise AssertionError(f"missing value for {key}.{name}")
            if body[k] == "{":
                start = k + 1
                d = 1
                k += 1
                esc = False
                while k < len(body) and d:
                    ch = body[k]
                    if esc:
                        esc = False
                    elif ch == "\\":
                        esc = True
                    elif ch == "{":
                        d += 1
                    elif ch == "}":
                        d -= 1
                    k += 1
                if d:
                    raise AssertionError(f"unterminated value for {key}.{name}")
                value = body[start : k - 1]
            elif body[k] == '"':
                start = k + 1
                k += 1
                esc = False
                while k < len(body):
                    ch = body[k]
                    if esc:
                        esc = False
                    elif ch == "\\":
                        esc = True
                    elif ch == '"':
                        break
                    k += 1
                if k >= len(body):
                    raise AssertionError(f"unterminated quoted value for {key}.{name}")
                value = body[start:k]
                k += 1
            else:
                vm = re.match(r"([^,\s]+)", body[k:])
                if not vm:
                    raise AssertionError(f"unparsed scalar for {key}.{name}")
                value = vm.group(1)
                k += vm.end()
            fields[name] = re.sub(r"\s+", " ", value).strip()
        entries[key] = fields
        i = j
    return entries


def norm(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def identifier(fields: dict[str, str]) -> str:
    if fields.get("doi"):
        return "doi:" + fields["doi"].lower()
    if fields.get("isbn"):
        return "isbn:" + re.sub(r"[^0-9Xx]", "", fields["isbn"]).upper()
    return ""


def valid_isbn(value: str) -> bool:
    digits = re.sub(r"[^0-9Xx]", "", value).upper()
    if len(digits) == 10:
        if not digits[:9].isdigit() or not (digits[9].isdigit() or digits[9] == "X"):
            return False
        total = sum((10 - i) * int(ch) for i, ch in enumerate(digits[:9]))
        total += 10 if digits[9] == "X" else int(digits[9])
        return total % 11 == 0
    if len(digits) == 13 and digits.isdigit():
        return sum((1 if i % 2 == 0 else 3) * int(ch) for i, ch in enumerate(digits)) % 10 == 0
    return False


def run() -> dict[str, object]:
    bib_text = BIB.read_text(encoding="utf-8")
    assert not re.search(r"(?i)\b(?:TODO|TBD|PLACEHOLDER)\b|example\.com", bib_text)
    entries = parse_bibtex(bib_text)
    assert len(entries) == EXPECTED_REFERENCES, len(entries)

    ids: dict[str, str] = {}
    titles: dict[str, str] = {}
    doi_count = 0
    isbn_count = 0
    for key, fields in entries.items():
        assert fields.get("title") and fields.get("author") and fields.get("year"), key
        assert re.fullmatch(r"(?:19|20)\d{2}", fields["year"]), (key, fields["year"])
        assert 1900 <= int(fields["year"]) <= 2026, (key, fields["year"])
        ident = identifier(fields)
        assert ident, f"missing DOI/ISBN for {key}"
        if ident.startswith("doi:"):
            doi = ident[4:]
            assert re.fullmatch(r"10\.\d{4,9}/\S+", doi, re.I), (key, doi)
            doi_count += 1
        else:
            isbn = ident[5:]
            assert valid_isbn(isbn), (key, isbn)
            isbn_count += 1
        if ident in ids:
            raise AssertionError(f"duplicate identifier {ident}: {ids[ident]}, {key}")
        ids[ident] = key
        title_key = re.sub(r"[^a-z0-9]+", "", fields["title"].lower())
        if title_key in titles:
            raise AssertionError(f"duplicate normalized title: {titles[title_key]}, {key}")
        titles[title_key] = key

    rows = list(csv.DictReader(LEDGER.open(encoding="utf-8", newline="")))
    assert len(rows) == EXPECTED_REFERENCES
    assert {r["bib_key"] for r in rows} == set(entries)
    assert all(r["verification_url"].startswith("https://") for r in rows)
    assert all(r["verification_basis"] and r["manuscript_role"] for r in rows)
    assert all(r["checked_on"] == "2026-09-21" for r in rows)
    for row in rows:
        key = row["bib_key"]
        fields = entries[key]
        venue = fields.get("journal") or fields.get("booktitle") or fields.get("publisher") or ""
        assert norm(row["title"]) == norm(fields["title"]), key
        assert row["year"] == fields["year"], key
        assert norm(row["venue"]) == norm(venue), key
        ident = identifier(fields)
        assert row["identifier"].lower() == ident.lower(), key
        if ident.startswith("doi:"):
            assert row["verification_url"].lower().rstrip("/") == ("https://doi.org/" + ident[4:]).lower(), key
        else:
            assert re.sub(r"[^0-9Xx]", "", ident[5:]).upper() in re.sub(r"[^0-9Xx]", "", row["verification_url"]).upper(), key


    live_rows = list(csv.DictReader(LIVE_AUDIT.open(encoding="utf-8", newline="")))
    assert len(live_rows) == EXPECTED_REFERENCES
    assert {r["bib_key"] for r in live_rows} == set(entries)
    assert all(r["verification_date"] == "2026-09-21" for r in live_rows)
    assert all(r["resolution"] == "resolved" for r in live_rows)
    assert all(r["metadata_match"] in {"matched", "corrected_then_matched"} for r in live_rows)
    corrected = {r["bib_key"] for r in live_rows if r["metadata_match"] == "corrected_then_matched"}
    assert corrected == {"zhang10random", "zhang13together"}

    citation_snapshot = json.loads(CITATION_SNAPSHOT.read_text(encoding="utf-8"))
    assert set(citation_snapshot) == {"source_files", "cited_keys", "citation_clusters", "maximum_citation_cluster"}
    cited = citation_snapshot["cited_keys"]
    clusters = citation_snapshot["citation_clusters"]
    assert isinstance(cited, list) and all(isinstance(key, str) for key in cited)
    assert isinstance(clusters, list) and all(
        isinstance(cluster, list) and all(isinstance(key, str) for key in cluster)
        for cluster in clusters
    )
    flattened = [key for cluster in clusters for key in cluster]
    assert set(cited) == set(flattened) == set(entries), (set(entries) - set(cited), set(cited) - set(entries))
    assert cited == sorted(set(cited))
    maximum_cluster = max(map(len, clusters), default=0)
    assert citation_snapshot["maximum_citation_cluster"] == maximum_cluster <= 8

    calibration = list(csv.DictReader(CALIBRATION.open(encoding="utf-8", newline="")))
    counts = {name: 0 for name in EXPECTED_CALIBRATION}
    for row in calibration:
        assert row["bib_key"] in entries, row["bib_key"]
        assert row["full_text_route"].startswith("https://")
        assert row["category"] in counts
        counts[row["category"]] += 1
    assert counts == EXPECTED_CALIBRATION, counts
    assert len({r["bib_key"] for r in calibration}) == len(calibration) == 22

    return {
        "references": len(entries),
        "unique_identifiers": len(ids),
        "unique_normalized_titles": len(titles),
        "doi_identifiers": doi_count,
        "isbn_identifiers": isbn_count,
        "provenance_rows": len(rows),
        "live_resolution_rows": len(live_rows),
        "corrected_metadata_entries": sorted(corrected),
        "manuscript_cited_keys": len(set(cited)),
        "maximum_citation_cluster": maximum_cluster,
        "calibration_counts": counts,
        "placeholder_scan": "passed",
        "audit_scope": "frozen bibliography, live-resolution ledger, citation coverage, and calibration consistency",
        "network_resolution_scope": "live metadata comparison was performed on 2026-09-21 and frozen in reference-live-audit.csv",
    }


if __name__ == "__main__":
    result = run()
    (ROOT / "results/reference-audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
