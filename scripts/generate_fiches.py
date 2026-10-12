#!/usr/bin/env python3
"""Génère les fiches Markdown publiques depuis data/lexique.json."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "lexique.json"
DEST = ROOT / "fiches"
TAXONOMY = ROOT / "data" / "taxonomie-proposition.json"


def clean(value):
    return str(value or "").replace("\r", "").strip()


def generate():
    fiches = json.loads(DATA.read_text(encoding="utf-8"))
    if not isinstance(fiches, list) or not all(isinstance(f, dict) for f in fiches):
        raise ValueError("Format de lexique inattendu")
    ids = [f["id"] for f in fiches]
    if len(ids) != len(set(ids)) or any(not x or "/" in x or "\\" in x or x in (".", "..") for x in ids):
        raise ValueError("Identifiants invalides ou dupliqués")
    taxonomy = json.loads(TAXONOMY.read_text(encoding="utf-8"))
    families = {f["id"]: f for f in taxonomy["familles"]}
    mapping = {x["id"]: x for x in taxonomy["classement"]}
    if set(mapping) != set(ids):
        raise ValueError("Classification incomplète ou fiche inconnue")
    domains = {x["id"]: x for x in taxonomy["domaines"]}
    def category(item):
        segments = item["classification"].split("/")
        if len(segments) != 2 or segments[0] not in families:
            raise ValueError("Famille inconnue")
        family = families[segments[0]]
        children = {sub["id"]: sub for sub in family["sous_categories"]}
        if segments[1] not in children:
            raise ValueError("Sous-catégorie inconnue")
        return family, children[segments[1]]
    for item in mapping.values():
        category(item)
        if any(d not in domains for d in item.get("domaines", [])):
            raise ValueError("Domaine inconnu")
    by_id = {f["id"]: f for f in fiches}
    for f in fiches:
        for ref in f.get("renvois", []):
            if ref.get("id") not in by_id or not clean(ref.get("nuance")):
                raise ValueError("Renvoi invalide dans " + f["id"])
    DEST.mkdir(exist_ok=True)
    expected = {"README.md"} | {x + ".md" for x in ids}
    for f in fiches:
        cls = mapping[f["id"]]
        family, subcategory = category(cls)
        lines = ["# " + clean(f["terme"]), "",
                 "**Classification :** " + clean(family.get("icone")) + " " + clean(family["label"]) + " → " + clean(subcategory["label"]), ""]
        selected_domains = [domains[x]["label"] for x in cls.get("domaines", [])]
        if selected_domains:
            lines += ["**Domaines d’application :** " + ", ".join(selected_domains), ""]

        if f.get("anglais"):
            lines += ["**Équivalent anglais :** " + clean(f["anglais"]), ""]
        lines += ["## Définition", "", clean(f["definition"]), ""]
        if f.get("synonymes"):
            lines += ["## Synonymes", ""] + ["- " + clean(s) for s in f["synonymes"]] + [""]
        if f.get("termes_deconseilles"):
            lines += ["## Termes déconseillés", ""] + ["- " + clean(s) for s in f["termes_deconseilles"]] + [""]
        if f.get("renvois") or f.get("guide_choix"):
            lines += ["<details>", "<summary><strong>Termes proches · aide au choix</strong></summary>", ""]
            for ref in f.get("renvois", []):
                target = by_id[ref["id"]]
                lines += ["- [" + clean(target["terme"]) + "](" + ref["id"] + ".md) — " + clean(ref["nuance"])]
            if f.get("guide_choix"):
                lines += ["", "**Quel terme utiliser ?**", "", "| Situation | Terme conseillé | Pourquoi ? |", "|---|---|---|"]
                for case in f["guide_choix"]:
                    fields = [clean(case.get(key)).replace("|", r"\\|").replace("\\n", " ") for key in ("situation", "terme", "justification")]
                    lines += ["| " + " | ".join(fields) + " |"]
            lines += ["", "</details>", ""]
        forms = f.get("formulations_rapport") or []
        if forms:
            lines += ["## Formulations pour rapport", ""]
            for form in forms:
                lines += ["### " + clean(form.get("type", "Formulation")), "", clean(form.get("texte")), ""]
        elif f.get("exemple_rapport"):
            lines += ["## Exemple de formulation", "", clean(f["exemple_rapport"]), ""]
        lines += ["> Ces fiches sont des documents de travail du projet : les définitions restent soumises à la revue terminologique et documentaire.", "", "[← Retour à l’index](README.md)", ""]
        (DEST / (f["id"] + ".md")).write_text("\n".join(lines), encoding="utf-8")
    entries = sorted(fiches, key=lambda f: clean(f["terme"]).casefold())
    index = ["# Catalogue des fiches — Lexique forensique FR", "",
             "Catalogue généré automatiquement depuis [data/lexique.json](../data/lexique.json).",
             "Ce catalogue n'est pas une validation juridique ou normative des définitions.", "",
             f"**{len(entries)} fiches disponibles**", ""]
    for family in taxonomy["familles"]:
        grouped = [f for f in entries if mapping[f["id"]]["classification"].split("/")[0] == family["id"]]
        if not grouped:
            continue
        index += ["## " + clean(family.get("icone")) + " " + clean(family["label"]), ""]
        for sub in family["sous_categories"]:
            members = [f for f in grouped if mapping[f["id"]]["classification"].split("/")[1] == sub["id"]]
            if members:
                index += ["### " + clean(sub["label"]), ""]
                index += ["- [" + clean(f["terme"]) + "](" + f["id"] + ".md)" for f in members]
                index += [""]
    index += ["## Index alphabétique", ""]
    for f in entries:
        index.append("- [" + clean(f["terme"]) + "](" + f["id"] + ".md)")
    index += ["", "[← Présentation du projet](../README.md)", ""]
    (DEST / "README.md").write_text("\n".join(index), encoding="utf-8")
    for stale in DEST.glob("*.md"):
        if stale.name not in expected:
            stale.unlink()
    return expected


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Signaler les différences sans modifier le dépôt")
    args = parser.parse_args()
    if args.check:
        import tempfile
        import shutil
        with tempfile.TemporaryDirectory() as tmp:
            backup = {p.name: p.read_bytes() for p in DEST.glob("*.md")} if DEST.exists() else {}
            generated = generate()
            current = {p.name: p.read_bytes() for p in DEST.glob("*.md")}
            if current != backup:
                for p in DEST.glob("*.md"):
                    p.unlink()
                for name, data in backup.items():
                    (DEST / name).write_bytes(data)
                raise SystemExit("Les fiches générées ne sont pas à jour")
            print(f"OK : {len(generated)-1} fiches synchronisées")
    else:
        print(f"{len(generate())-1} fiches générées")
