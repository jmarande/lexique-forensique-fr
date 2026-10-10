# -*- coding: utf-8 -*-
import json
import os
import re
import unicodedata
import urllib.request
from urllib.parse import quote, unquote
import hashlib
import tempfile
import shutil
import time

import uno
import unohelper

from com.sun.star.awt import XActionListener, XItemListener, XMouseListener, XTopWindowListener

_OPEN_LEXICON_WINDOWS = []
_OPEN_VERIFY_WINDOWS = []
_OPEN_OCCURRENCE_WINDOWS = []
_OPEN_OCCURRENCE_EDITOR_WINDOWS = []
_OPEN_SCENARIO_WINDOWS = []
_OPEN_SCENARIO_EDITOR_WINDOWS = []
_OPEN_TERM_WINDOWS = []
_OPEN_TERM_EDITOR_WINDOWS = []
_OPEN_DATA_TRANSFER_WINDOWS = []
_OPEN_ABOUT_WINDOWS = []

CURRENT_VERSION = "0.8.1"
GITHUB_URL = "https://github.com/jmarande/lexique-forensique-fr"
GITHUB_PROPOSE_URL = GITHUB_URL + "/issues/new"
GITHUB_LATEST_RELEASE_API = (
    "https://api.github.com/repos/jmarande/lexique-forensique-fr/releases/latest"
)
UPDATE_ASSET_NAME = "lexique-forensique-fr.oxt"


def _ctx():
    return XSCRIPTCONTEXT.getComponentContext()


def _desktop():
    return XSCRIPTCONTEXT.getDesktop()


def _open_url(url):
    ctx = _ctx()
    smgr = ctx.ServiceManager
    shell = smgr.createInstanceWithContext(
        "com.sun.star.system.SystemShellExecute", ctx
    )
    shell.execute(url, "", 0)



def _prepare_term_proposal(entry):
    """Préparer une proposition GitHub publique, sans envoi automatique."""
    if entry.get("_source") != "user":
        raise ValueError("Seules les fiches personnelles peuvent être proposées")
    term = (entry.get("terme") or "").strip()
    definition = (entry.get("definition") or "").strip()
    if not term or not definition:
        raise ValueError("Complétez le terme et sa définition avant de proposer la fiche")

    def limited(value, size=1500):
        return str(value or "").strip()[:size]

    formulations = []
    for item in (entry.get("formulations_rapport") or [])[:12]:
        if not isinstance(item, dict):
            continue
        wording = limited(item.get("texte"), 700)
        if wording:
            formulations.append(
                "- **" + limited(item.get("type") or "Formulation", 80)
                + "** : " + wording
            )
    synonyms = entry.get("synonymes") or []
    if not isinstance(synonyms, list):
        synonyms = []
    sources = entry.get("sources") or []
    if not isinstance(sources, list):
        sources = []
    body = (
        "## Terme français\n" + limited(term, 140)
        + "\n\n## Équivalent anglais\n" + limited(entry.get("anglais"), 140)
        + "\n\n## Catégorie\n" + limited(entry.get("categorie"), 140)
        + "\n\n## Définition proposée\n" + limited(definition)
        + "\n\n## Synonymes\n" + ", ".join(limited(v, 100) for v in synonyms[:20])
        + "\n\n## Formulations pour rapport\n"
        + ("\n".join(formulations) if formulations else "Aucune formulation proposée.")
        + "\n\n## Références documentaires\n"
        + ("\n".join("- " + limited(v, 250) for v in sources[:15]) if sources else "À compléter.")
        + "\n\n## Observations pour la relecture\nÀ compléter."
    )
    return (GITHUB_PROPOSE_URL + "?template=proposition-fiche.md&title="
            + quote("[Fiche proposée] " + limited(term, 90), safe="")
            + "&body=" + quote(body, safe=""))



def _prepare_term_proposals(entries):
    """Créer une unique proposition pour une sélection explicite de fiches."""
    if not entries:
        raise ValueError("Sélectionnez au moins une fiche personnelle")
    parts = []
    for index, entry in enumerate(entries, 1):
        prepared = _prepare_term_proposal(entry)
        encoded_body = prepared.split("&body=", 1)[1]
        parts.append("## Fiche " + str(index) + " : "
                     + str(entry.get("terme") or "").strip()[:100]
                     + "\n\n" + unquote(encoded_body))
    body = (
        "Proposition collective de " + str(len(entries))
        + " fiche(s) personnelles, à examiner individuellement.\n\n"
        + "\n\n---\n\n".join(parts)
    )
    title = ("[Fiches proposées] " + str(len(entries)) + " fiche(s)")
    url = (GITHUB_PROPOSE_URL + "?template=proposition-fiche.md&title="
           + quote(title, safe="") + "&body=" + quote(body, safe=""))
    if len(url) > 7000:
        raise ValueError(
            "Sélection trop volumineuse pour un formulaire GitHub : "
            "choisissez moins de fiches ou raccourcissez leurs textes"
        )
    return url


def _message_box(title, message):
    ctx = _ctx()
    smgr = ctx.ServiceManager
    toolkit = smgr.createInstanceWithContext("com.sun.star.awt.Toolkit", ctx)
    parent = toolkit.getDesktopWindow()
    box = toolkit.createMessageBox(
        parent,
        "infobox",
        1,
        title,
        message,
    )
    box.execute()


def _version_tuple(value):
    value = (value or "").strip().lstrip("vV")
    parts = []
    for item in value.split("."):
        digits = "".join(ch for ch in item if ch.isdigit())
        if digits == "":
            break
        parts.append(int(digits))
    return tuple(parts or [0])


def _extension_root():
    """Return the installed extension directory from this script location."""
    script_path = __file__
    if script_path.startswith("file:"):
        script_path = uno.fileUrlToSystemPath(script_path)
    return os.path.abspath(
        os.path.join(os.path.dirname(script_path), os.pardir, os.pardir)
    )


def _user_data_dir():
    base = os.path.join(os.path.expanduser("~"), ".lexique-forensique-fr")
    os.makedirs(base, exist_ok=True)
    return base


def _user_lexicon_path():
    return os.path.join(_user_data_dir(), "lexique-utilisateur.json")


def _load_builtin_data():
    path = os.path.join(_extension_root(), "data", "lexique.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    for item in data:
        item["_source"] = "builtin"
    return data


def _load_user_data():
    path = _user_lexicon_path()
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return []
    if not isinstance(data, list):
        return []
    for item in data:
        item["_source"] = "user"
    return data


def _save_user_data(data):
    payload = []
    for item in data:
        clean = {k: v for k, v in item.items() if not k.startswith("_")}
        payload.append(clean)
    with open(_user_lexicon_path(), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def _load_data():
    return _load_builtin_data() + _load_user_data()


def _user_occurrences_path():
    return os.path.join(_user_data_dir(), "occurrences-utilisateur.json")


def _normalize_occurrence_item(item, source):
    occurrence = (
        item.get("occurrence")
        or item.get("anglais")
        or ""
    ).strip()
    replacements = item.get("remplacements")
    if not isinstance(replacements, list):
        replacement = (item.get("francais") or "").strip()
        replacements = [replacement] if replacement else []
    replacements = [
        str(value).strip()
        for value in replacements
        if str(value).strip()
    ]
    preferred = (item.get("prefere") or "").strip()
    if not preferred and replacements:
        preferred = replacements[0]
    return {
        "occurrence": occurrence,
        "remplacements": replacements,
        "prefere": preferred,
        "note": (item.get("note") or "").strip(),
        "_source": source,
    }


def _load_builtin_occurrences():
    path = os.path.join(_extension_root(), "data", "traductions.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return []
    if not isinstance(data, list):
        return []
    return [
        _normalize_occurrence_item(item, "builtin")
        for item in data
        if isinstance(item, dict)
    ]


def _load_user_occurrences():
    path = _user_occurrences_path()
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return []
    if not isinstance(data, list):
        return []
    return [
        _normalize_occurrence_item(item, "user")
        for item in data
        if isinstance(item, dict)
    ]


def _save_user_occurrences(data):
    payload = []
    for item in data:
        payload.append({
            "occurrence": (item.get("occurrence") or "").strip(),
            "remplacements": list(item.get("remplacements") or []),
            "prefere": (item.get("prefere") or "").strip(),
            "note": (item.get("note") or "").strip(),
        })
    with open(_user_occurrences_path(), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def _clean_user_items(items):
    return [
        {key: value for key, value in item.items() if not key.startswith("_")}
        for item in items
    ]


def _export_user_payload():
    return {
        "format": "lexique-forensique-fr-user-data",
        "version": 1,
        "lexique": _clean_user_items(_load_user_data()),
        "scenarios": _clean_user_items(_load_user_scenarios()),
        "occurrences": _clean_user_items(_load_user_occurrences()),
    }


def _validate_user_payload(payload):
    if not isinstance(payload, dict):
        raise ValueError("Le fichier importé n’est pas un objet JSON valide.")
    if payload.get("format") != "lexique-forensique-fr-user-data":
        raise ValueError("Ce fichier n’est pas une base utilisateur Lexique forensique FR.")
    if payload.get("version") != 1:
        raise ValueError("Version de fichier utilisateur non prise en charge.")
    for key in ("lexique", "scenarios", "occurrences"):
        if key not in payload or not isinstance(payload[key], list):
            raise ValueError(f"Section obligatoire invalide : {key}.")
        if not all(isinstance(item, dict) for item in payload[key]):
            raise ValueError(f"Contenu invalide dans la section : {key}.")
    return payload


def _merge_user_items(local_items, imported_items, kind):
    merged = list(local_items)
    existing_ids = {
        str(item.get("id"))
        for item in merged
        if item.get("id") not in (None, "")
    }

    def natural_key(item):
        if kind == "lexique":
            return _normalize(item.get("terme", ""))
        if kind == "scenarios":
            return _normalize(item.get("titre", ""))
        return _normalize(
            item.get("occurrence")
            or item.get("anglais")
            or ""
        )

    existing_natural = {
        natural_key(item)
        for item in merged
        if natural_key(item)
    }
    added = 0
    skipped = 0
    for raw in imported_items:
        item = dict(raw)
        item_id = str(item.get("id")) if item.get("id") not in (None, "") else ""
        key = natural_key(item)
        if (item_id and item_id in existing_ids) or (key and key in existing_natural):
            skipped += 1
            continue
        merged.append(item)
        if item_id:
            existing_ids.add(item_id)
        if key:
            existing_natural.add(key)
        added += 1
    return merged, added, skipped


def _backup_current_user_data():
    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup_dir = os.path.join(_user_data_dir(), "sauvegardes", stamp)
    os.makedirs(backup_dir, exist_ok=True)
    for source in (
        _user_lexicon_path(),
        _user_scenarios_path(),
        _user_occurrences_path(),
    ):
        if os.path.exists(source):
            shutil.copy2(source, os.path.join(backup_dir, os.path.basename(source)))
    return backup_dir


def _refresh_user_data_windows():
    for item in list(_OPEN_LEXICON_WINDOWS):
        try:
            item["listener"].reload_data()
        except Exception:
            pass
    for item in list(_OPEN_TERM_WINDOWS):
        try:
            listener = item["listener"]
            listener.user_data = _load_user_data()
            listener._populate()
        except Exception:
            pass
    for item in list(_OPEN_SCENARIO_WINDOWS):
        try:
            listener = item["listener"]
            listener.data = _load_data()
            listener.user_scenarios = _load_user_scenarios()
            listener._populate()
        except Exception:
            pass
    for item in list(_OPEN_VERIFY_WINDOWS):
        try:
            item["listener"].reload_occurrences()
        except Exception:
            pass
    for item in list(_OPEN_OCCURRENCE_WINDOWS):
        try:
            listener = item["listener"]
            listener.builtin_items = _load_builtin_occurrences()
            listener.user_items = _load_user_occurrences()
            listener._populate()
        except Exception:
            pass


def _pick_json_file(save=False):
    ctx = _ctx()
    smgr = ctx.ServiceManager
    picker = smgr.createInstanceWithContext(
        "com.sun.star.ui.dialogs.FilePicker", ctx
    )
    picker.initialize((10 if save else 0,))
    try:
        picker.appendFilter("Fichier JSON (*.json)", "*.json")
        picker.setCurrentFilter("Fichier JSON (*.json)")
    except Exception:
        pass
    if save:
        try:
            picker.setDefaultName("lexique-forensique-utilisateur.json")
        except Exception:
            pass
    if picker.execute() != 1:
        return None
    files = picker.getFiles()
    if not files:
        return None
    url = files[0]
    path = uno.fileUrlToSystemPath(url)
    if save and not path.lower().endswith(".json"):
        path += ".json"
    return path


def _load_translations():
    return _load_builtin_occurrences() + _load_user_occurrences()


def _load_scenarios():
    path = os.path.join(_extension_root(), "data", "scenarios.json")
    with open(path, "r", encoding="utf-8") as f:
        scenarios = json.load(f)
    for item in scenarios:
        item["_source"] = "builtin"
    return scenarios


def _user_scenarios_path():
    return os.path.join(_user_data_dir(), "scenarios-utilisateur.json")


def _load_user_scenarios():
    path = _user_scenarios_path()
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            scenarios = json.load(f)
    except Exception:
        return []
    if not isinstance(scenarios, list):
        return []
    for item in scenarios:
        item["_source"] = "user"
    return scenarios


def _save_user_scenarios(scenarios):
    path = _user_scenarios_path()
    payload = []
    for item in scenarios:
        clean = {k: v for k, v in item.items() if not k.startswith("_")}
        payload.append(clean)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def _scenario_steps(scenario, data):
    entries = {entry.get("id"): entry for entry in data}
    resolved = []
    for step in scenario.get("etapes", []):
        entry = entries.get(step.get("terme"))
        if not entry:
            continue
        wanted = (step.get("formulation") or "").strip()
        selected = None
        for label, text in _report_formulations(entry):
            if label == wanted:
                selected = text
                break
        if selected:
            resolved.append({
                "terme": entry.get("terme", step.get("terme", "")),
                "formulation": wanted,
                "texte": selected,
            })
    return resolved


def _bad_terms(entry):
    return entry.get("termes_deconseilles", entry.get("deconseilles", []))


def _report_formulations(entry):
    values = entry.get("formulations_rapport")
    result = []
    if isinstance(values, list):
        for item in values:
            if isinstance(item, dict):
                text = (item.get("texte") or "").strip()
                label = (item.get("type") or "").strip()
                if text:
                    result.append((label or "Proposition", text))
            elif isinstance(item, str) and item.strip():
                result.append(("Proposition", item.strip()))
    if result:
        return result

    legacy = (entry.get("exemple_rapport") or entry.get("rapport") or "").strip()
    return [("Formulation", legacy)] if legacy else []


def _report_example(entry):
    formulations = _report_formulations(entry)
    return formulations[0][1] if formulations else ""


def _sources(entry):
    values = entry.get("sources", [])
    if isinstance(values, str):
        return values
    return ", ".join(values) or "—"


def _normalize(value):
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value.casefold().strip()


def _format_entry(e, warning=None):
    syn = ", ".join(e.get("synonymes", [])) or "—"
    bad = ", ".join(_bad_terms(e)) or "—"
    prefix = ""
    if warning:
        prefix = (
            f"ALERTE TERMINOLOGIQUE\n"
            f"{warning['found']} → {e['terme']}\n"
            f"Occurrences détectées : {warning['count']}\n\n"
        )

    base = (
        prefix
        + f"{e['terme']}\n"
        + f"Anglais : {e.get('anglais', '—')}\n"
        + f"Catégorie : {e.get('categorie', '—')}\n"
        + f"Synonymes : {syn}\n\n"
        + f"DÉFINITION\n{e.get('definition', '')}\n\n"
        + "FORMULATIONS POUR RAPPORT\n"
    )

    formulations = _report_formulations(e)
    ranges = []
    parts = [base]

    for index, (label, text) in enumerate(formulations, start=1):
        if index > 1:
            parts.append("\n\n")
        parts.append(f"{index}. {label.upper()}\n")
        start = sum(len(part) for part in parts)
        parts.append(text)
        end = start + len(text)
        ranges.append({
            "start": start,
            "end": end,
            "label": label,
            "text": text,
        })

    if not formulations:
        parts.append("—")

    return "".join(parts), ranges
def _find_entries(query, data, category=None):
    q = _normalize(query)
    results = []
    for e in data:
        if category and e.get("categorie", "") != category:
            continue

        if q:
            fields = [
                e.get("terme", ""),
                e.get("anglais", ""),
                e.get("categorie", ""),
                e.get("definition", ""),
                " ".join(e.get("synonymes", [])),
                " ".join(_bad_terms(e)),
            ]
            if q not in _normalize(" ".join(fields)):
                continue

        results.append(e)

    return sorted(results, key=lambda e: _normalize(e.get("terme", "")))


def _scan_document_text(text, data, translations=None):
    normalized_text = _normalize(text)
    alerts = []

    for entry in data:
        for bad in _bad_terms(entry):
            normalized_bad = _normalize(bad)
            if not normalized_bad:
                continue

            pattern = r"(?<!\\w)" + re.escape(normalized_bad) + r"(?!\\w)"
            count = len(re.findall(pattern, normalized_text))
            if count:
                alerts.append({
                    "kind": "terminologie",
                    "entry": entry,
                    "found": bad,
                    "replacement": entry.get("terme", ""),
                    "count": count,
                })

    for item in translations or []:
        source = (item.get("occurrence") or "").strip()
        replacements = [
            value.strip()
            for value in item.get("remplacements", [])
            if value and value.strip()
        ]
        preferred = (item.get("prefere") or "").strip()
        if preferred and preferred not in replacements:
            replacements.insert(0, preferred)
        if not preferred and replacements:
            preferred = replacements[0]
        if not source or not preferred or _normalize(source) == _normalize(preferred):
            continue

        normalized_source = _normalize(source)
        pattern = r"(?<!\\w)" + re.escape(normalized_source) + r"(?!\\w)"
        count = len(re.findall(pattern, normalized_text))
        if count:
            alerts.append({
                "kind": "traduction",
                "entry": None,
                "found": source,
                "replacement": preferred,
                "replacements": replacements,
                "count": count,
                "note": (item.get("note") or "").strip(),
                "source": item.get("_source", "builtin"),
            })

    return sorted(
        alerts,
        key=lambda item: (
            0 if item.get("kind") == "traduction" else 1,
            _normalize(item.get("found", "")),
        ),
    )


class DialogListener(
    unohelper.Base,
    XActionListener,
    XItemListener,
    XMouseListener,
    XTopWindowListener,
):
    def __init__(
        self,
        dialog,
        search_box,
        results_box,
        detail_box,
        status_label,
        insert_button,
        category_box,
        data,
    ):
        self.dialog = dialog
        self.search_box = search_box
        self.results_box = results_box
        self.detail_box = detail_box
        self.status_label = status_label
        self.insert_button = insert_button
        self.category_box = category_box
        self.data = data
        self.categories = sorted(
            {e.get("categorie", "") for e in data if e.get("categorie", "")},
            key=_normalize,
        )
        self.current_category = None
        self.current = None
        self.matches = []
        self.formulation_ranges = []
        self.selected_formulation_index = 0
        self.refresh()

    def _set_insert_enabled(self, enabled):
        self.insert_button.getModel().Enabled = enabled

    def _clear_results(self):
        if self.results_box.ItemCount:
            self.results_box.removeItems(0, self.results_box.ItemCount)

    def reload_data(self):
        previous_category = self.current_category
        self.data = _load_data()
        self.categories = sorted(
            {e.get("categorie", "") for e in self.data if e.get("categorie", "")},
            key=_normalize,
        )

        if self.category_box.ItemCount:
            self.category_box.removeItems(0, self.category_box.ItemCount)
        self.category_box.addItem("Toutes", self.category_box.ItemCount)
        for category in self.categories:
            self.category_box.addItem(category, self.category_box.ItemCount)

        if previous_category and previous_category in self.categories:
            self.current_category = previous_category
            self.category_box.setText(previous_category)
        else:
            self.current_category = None
            self.category_box.setText("Toutes")

        self.refresh()

    def _display_entry(self, entry):
        text, ranges = _format_entry(entry)
        self.detail_box.Text = text
        self.formulation_ranges = ranges
        self.selected_formulation_index = 0
        if ranges:
            self._select_formulation(0)
            self._set_insert_enabled(True)
        else:
            self._set_insert_enabled(False)

    def _select_formulation(self, index):
        if not (0 <= index < len(self.formulation_ranges)):
            return
        self.selected_formulation_index = index
        item = self.formulation_ranges[index]
        selection = uno.createUnoStruct("com.sun.star.awt.Selection")
        selection.Min = item["start"]
        selection.Max = item["end"]
        self.detail_box.setSelection(selection)

    def _show_entry(self, entry):
        self.current = entry
        self._display_entry(entry)

    def refresh(self):
        self.matches = _find_entries(
            self.search_box.Text,
            self.data,
            category=self.current_category,
        )
        self._clear_results()
        for entry in self.matches:
            self.results_box.addItem(entry["terme"], self.results_box.ItemCount)

        count = len(self.matches)
        self.status_label.getModel().Label = (
            f"{count} résultat" if count == 1 else f"{count} résultats"
        )
        if self.matches:
            self.results_box.selectItemPos(0, True)
            self._show_entry(self.matches[0])
        else:
            self.current = None
            self.formulation_ranges = []
            self.detail_box.Text = "Aucun terme trouvé."
            self._set_insert_enabled(False)

    def actionPerformed(self, event):
        cmd = event.ActionCommand
        if cmd == "search":
            self.refresh()
        elif cmd == "verify":
            open_verification()
        elif cmd == "scenarios":
            open_scenarios()
        elif cmd == "manage_terms":
            open_term_manager(self)
        elif cmd == "insert" and self.current:
            if self.formulation_ranges:
                item = self.formulation_ranges[self.selected_formulation_index]
                text_to_insert = item["text"]
            else:
                text_to_insert = self.current["terme"]
            doc = _desktop().getCurrentComponent()
            if doc and doc.supportsService("com.sun.star.text.TextDocument"):
                view = doc.getCurrentController().getViewCursor()
                view.getText().insertString(view, text_to_insert, False)
                self.status_label.getModel().Label = (
                    "Formulation insérée dans le document"
                )
        elif cmd == "close":
            self._close_dialog()

    def mouseReleased(self, event):
        if not self.formulation_ranges:
            return
        selection = self.detail_box.getSelection()
        position = selection.Min
        for index, item in enumerate(self.formulation_ranges):
            if item["start"] <= position <= item["end"]:
                self._select_formulation(index)
                return

    def mousePressed(self, event):
        pass

    def mouseEntered(self, event):
        pass

    def mouseExited(self, event):
        pass

    def itemStateChanged(self, event):
        source_name = ""
        try:
            source_name = event.Source.getModel().Name
        except Exception:
            pass
        if source_name == "cmbCategory":
            value = (event.Source.getText() or "").strip()
            if value == "Toutes":
                self.current_category = None
            elif value in self.categories:
                self.current_category = value
            else:
                return
            self.refresh()
        else:
            pos = self.results_box.SelectedItemPos
            if 0 <= pos < len(self.matches):
                self._show_entry(self.matches[pos])

    def _close_dialog(self):
        try:
            self.dialog.setVisible(False)
            self.dialog.dispose()
        finally:
            _OPEN_LEXICON_WINDOWS[:] = [
                item for item in _OPEN_LEXICON_WINDOWS
                if item.get("dialog") is not self.dialog
            ]

    def windowClosing(self, event):
        self._close_dialog()

    def windowOpened(self, event):
        pass

    def windowClosed(self, event):
        pass

    def windowMinimized(self, event):
        pass

    def windowNormalized(self, event):
        pass

    def windowActivated(self, event):
        pass

    def windowDeactivated(self, event):
        pass

    def disposing(self, event):
        pass


class VerificationListener(
    unohelper.Base,
    XActionListener,
    XItemListener,
    XTopWindowListener,
):
    def __init__(
        self,
        dialog,
        alerts_box,
        detail_box,
        status_label,
        replace_button,
        data,
        translations,
    ):
        self.dialog = dialog
        self.alerts_box = alerts_box
        self.detail_box = detail_box
        self.status_label = status_label
        self.replace_button = replace_button
        self.data = data
        self.translations = translations
        self.alerts = []
        self.current_alert = None
        self.current_found_range = None
        self.scan()

    def _clear_alerts(self):
        if self.alerts_box.ItemCount:
            self.alerts_box.removeItems(0, self.alerts_box.ItemCount)

    def _set_replace_enabled(self, enabled):
        self.replace_button.getModel().Enabled = enabled

    def _goto_occurrence(self, alert):
        doc = _desktop().getCurrentComponent()
        if not doc or not doc.supportsService("com.sun.star.text.TextDocument"):
            self.current_found_range = None
            self._set_replace_enabled(False)
            return

        descriptor = doc.createSearchDescriptor()
        descriptor.SearchString = alert["found"]
        descriptor.SearchCaseSensitive = False
        descriptor.SearchWords = True
        found = doc.findFirst(descriptor)
        self.current_found_range = found

        if found:
            doc.getCurrentController().select(found)
            self._set_replace_enabled(True)
            self.status_label.getModel().Label = (
                f"Occurrence sélectionnée : {alert['found']}"
            )
        else:
            self._set_replace_enabled(False)
            self.status_label.getModel().Label = "Occurrence introuvable"

    def _show_alert(self, alert):
        self.current_alert = alert
        if alert.get("kind") == "traduction":
            note = alert.get("note") or (
                "Terme anglais détecté dans le document. "
                "La traduction proposée vise à franciser l’export."
            )
            alternatives = alert.get("replacements", [])
            proposals = "\n".join(
                f"• {value}" for value in alternatives
            ) or f"• {alert['replacement']}"
            origin = (
                "Occurrence utilisateur"
                if alert.get("source") == "user"
                else "Occurrence fournie avec l’extension"
            )
            self.detail_box.Text = (
                "TRADUCTION / NORMALISATION\n"
                f"{alert['found']}\n\n"
                f"Remplacement préféré : {alert['replacement']}\n\n"
                f"Remplacements possibles :\n{proposals}\n\n"
                f"Occurrences détectées : {alert['count']}\n"
                f"Origine : {origin}\n\n"
                f"{note}"
            )
        else:
            text, _ = _format_entry(alert["entry"], warning=alert)
            self.detail_box.Text = text
        self._goto_occurrence(alert)

    def scan(self):
        doc = _desktop().getCurrentComponent()
        if not doc or not doc.supportsService("com.sun.star.text.TextDocument"):
            self.status_label.getModel().Label = "Aucun document Writer actif"
            return

        self.current_alert = None
        self.current_found_range = None
        self._set_replace_enabled(False)
        self.alerts = _scan_document_text(
            doc.Text.String,
            self.data,
            self.translations,
        )
        self._clear_alerts()

        for alert in self.alerts:
            prefix = (
                "Traduction"
                if alert.get("kind") == "traduction"
                else "Terminologie"
            )
            self.alerts_box.addItem(
                f"[{prefix}] {alert['found']} → "
                f"{alert['replacement']} ({alert['count']})",
                self.alerts_box.ItemCount,
            )

        total = sum(alert["count"] for alert in self.alerts)
        if self.alerts:
            self.status_label.getModel().Label = (
                f"{total} occurrence" if total == 1
                else f"{total} occurrences à vérifier"
            )
            self.alerts_box.selectItemPos(0, True)
            self._show_alert(self.alerts[0])
        else:
            self.detail_box.Text = (
                "Aucun terme à traduire ou à normaliser détecté dans le document actif."
            )
            self.status_label.getModel().Label = "Aucune alerte"

    def reload_occurrences(self):
        self.translations = _load_translations()
        self.scan()

    def replace_current(self):
        if not self.current_alert or not self.current_found_range:
            return
        replacement = self.current_alert["replacement"]
        self.current_found_range.String = replacement
        self.current_found_range = None
        self.scan()

    def actionPerformed(self, event):
        if event.ActionCommand == "rescan":
            self.scan()
        elif event.ActionCommand == "replace":
            self.replace_current()
        elif event.ActionCommand == "manage_occurrences":
            open_occurrence_manager(self)
        elif event.ActionCommand == "close":
            self._close_dialog()

    def itemStateChanged(self, event):
        pos = self.alerts_box.SelectedItemPos
        if 0 <= pos < len(self.alerts):
            self._show_alert(self.alerts[pos])

    def _close_dialog(self):
        try:
            self.dialog.setVisible(False)
            self.dialog.dispose()
        finally:
            _OPEN_VERIFY_WINDOWS[:] = [
                item for item in _OPEN_VERIFY_WINDOWS
                if item.get("dialog") is not self.dialog
            ]

    def windowClosing(self, event):
        self._close_dialog()

    def windowOpened(self, event):
        pass

    def windowClosed(self, event):
        pass

    def windowMinimized(self, event):
        pass

    def windowNormalized(self, event):
        pass

    def windowActivated(self, event):
        pass

    def windowDeactivated(self, event):
        pass

    def disposing(self, event):
        pass


class OccurrenceManagerListener(
    unohelper.Base,
    XActionListener,
    XItemListener,
    XTopWindowListener,
):
    def __init__(
        self,
        dialog,
        items_box,
        detail_box,
        status_label,
        verification_listener,
        builtin_items,
        user_items,
    ):
        self.dialog = dialog
        self.items_box = items_box
        self.detail_box = detail_box
        self.status_label = status_label
        self.verification_listener = verification_listener
        self.builtin_items = builtin_items
        self.user_items = user_items
        self.items = []
        self._closing = False
        self._populate()

    def _populate(self, select_index=0):
        if self.items_box.ItemCount:
            self.items_box.removeItems(0, self.items_box.ItemCount)
        self.items = sorted(
            self.builtin_items + self.user_items,
            key=lambda item: _normalize(item.get("occurrence", "")),
        )
        for item in self.items:
            prefix = "★ " if item.get("_source") == "user" else ""
            self.items_box.addItem(
                prefix + item.get("occurrence", "Occurrence"),
                self.items_box.ItemCount,
            )
        if self.items:
            select_index = min(max(select_index, 0), len(self.items) - 1)
            self.items_box.selectItemPos(select_index, True)
            self._show(select_index)
        else:
            self.detail_box.Text = "Aucune occurrence enregistrée."

    def _show(self, index):
        if not (0 <= index < len(self.items)):
            return
        item = self.items[index]
        origin = (
            "Occurrence utilisateur"
            if item.get("_source") == "user"
            else "Occurrence fournie avec l’extension"
        )
        replacements = item.get("remplacements", [])
        lines = "\n".join(f"• {value}" for value in replacements) or "—"
        self.detail_box.Text = (
            f"{item.get('occurrence', '').upper()}\n"
            f"Origine : {origin}\n\n"
            f"Remplacements possibles :\n{lines}\n\n"
            f"Remplacement préféré : {item.get('prefere') or '—'}"
        )
        note = item.get("note")
        if note:
            self.detail_box.Text += f"\n\nNOTE\n{note}"
        self.status_label.getModel().Label = origin

    def _current(self):
        pos = self.items_box.SelectedItemPos
        if 0 <= pos < len(self.items):
            return pos, self.items[pos]
        return -1, None

    def new_item(self):
        item = {
            "occurrence": "",
            "remplacements": [],
            "prefere": "",
            "note": "",
            "_source": "user",
        }
        open_occurrence_editor(self, item, True)

    def edit_current(self):
        _index, item = self._current()
        if not item:
            return
        if item.get("_source") != "user":
            self.status_label.getModel().Label = (
                "Les occurrences fournies sont protégées"
            )
            return
        open_occurrence_editor(self, item, False)

    def delete_current(self):
        index, item = self._current()
        if not item:
            return
        if item.get("_source") != "user":
            self.status_label.getModel().Label = (
                "Les occurrences fournies ne peuvent pas être supprimées"
            )
            return
        try:
            self.user_items.remove(item)
        except ValueError:
            return
        _save_user_occurrences(self.user_items)
        self._populate(max(index - 1, 0))
        self._notify_verification()
        self.status_label.getModel().Label = "Occurrence utilisateur supprimée"

    def save_from_editor(self, item, is_new):
        if is_new:
            self.user_items.append(item)
        _save_user_occurrences(self.user_items)
        self._populate()
        self._notify_verification()
        for index, current in enumerate(self.items):
            if current is item:
                self.items_box.selectItemPos(index, True)
                self._show(index)
                break

    def _notify_verification(self):
        if self.verification_listener is not None:
            try:
                self.verification_listener.reload_occurrences()
            except Exception:
                pass

    def actionPerformed(self, event):
        if event.ActionCommand == "new":
            self.new_item()
        elif event.ActionCommand == "edit":
            self.edit_current()
        elif event.ActionCommand == "delete":
            self.delete_current()
        elif event.ActionCommand == "close":
            self._close_dialog()

    def itemStateChanged(self, event):
        pos = self.items_box.SelectedItemPos
        if 0 <= pos < len(self.items):
            self._show(pos)

    def _close_dialog(self):
        if self._closing:
            return
        self._closing = True
        try:
            try:
                self.dialog.removeTopWindowListener(self)
            except Exception:
                pass
            self.dialog.setVisible(False)
            self.dialog.dispose()
        finally:
            _OPEN_OCCURRENCE_WINDOWS[:] = [
                item for item in _OPEN_OCCURRENCE_WINDOWS
                if item.get("dialog") is not self.dialog
            ]

    def windowClosing(self, event):
        self._close_dialog()
    def windowOpened(self, event): pass
    def windowClosed(self, event): pass
    def windowMinimized(self, event): pass
    def windowNormalized(self, event): pass
    def windowActivated(self, event): pass
    def windowDeactivated(self, event): pass
    def disposing(self, event): pass


class OccurrenceEditorListener(
    unohelper.Base,
    XActionListener,
    XTopWindowListener,
):
    def __init__(
        self,
        dialog,
        parent_listener,
        item,
        is_new,
        occurrence_box,
        replacements_box,
        preferred_box,
        note_box,
        status_label,
    ):
        self.dialog = dialog
        self.parent_listener = parent_listener
        self.item = item
        self.is_new = is_new
        self.occurrence_box = occurrence_box
        self.replacements_box = replacements_box
        self.preferred_box = preferred_box
        self.note_box = note_box
        self.status_label = status_label
        self._closing = False

    def save(self):
        occurrence = (self.occurrence_box.Text or "").strip()
        replacements = [
            line.strip()
            for line in (self.replacements_box.Text or "").splitlines()
            if line.strip()
        ]
        preferred = (self.preferred_box.Text or "").strip()
        if not occurrence:
            self.status_label.getModel().Label = (
                "L’occurrence à détecter est obligatoire"
            )
            return
        if not replacements:
            self.status_label.getModel().Label = (
                "Ajoutez au moins un remplacement"
            )
            return
        if not preferred:
            preferred = replacements[0]
        if preferred not in replacements:
            replacements.insert(0, preferred)

        self.item["occurrence"] = occurrence
        self.item["remplacements"] = replacements
        self.item["prefere"] = preferred
        self.item["note"] = (self.note_box.Text or "").strip()
        self.item["_source"] = "user"
        self.parent_listener.save_from_editor(self.item, self.is_new)
        self._close_dialog()

    def actionPerformed(self, event):
        if event.ActionCommand == "save":
            self.save()
        elif event.ActionCommand == "cancel":
            self._close_dialog()

    def _close_dialog(self):
        if self._closing:
            return
        self._closing = True
        try:
            try:
                self.dialog.removeTopWindowListener(self)
            except Exception:
                pass
            self.dialog.setVisible(False)
            self.dialog.dispose()
        finally:
            _OPEN_OCCURRENCE_EDITOR_WINDOWS[:] = [
                item for item in _OPEN_OCCURRENCE_EDITOR_WINDOWS
                if item.get("dialog") is not self.dialog
            ]

    def windowClosing(self, event):
        self._close_dialog()
    def windowOpened(self, event): pass
    def windowClosed(self, event): pass
    def windowMinimized(self, event): pass
    def windowNormalized(self, event): pass
    def windowActivated(self, event): pass
    def windowDeactivated(self, event): pass
    def disposing(self, event): pass


class ScenarioListener(
    unohelper.Base,
    XActionListener,
    XItemListener,
    XTopWindowListener,
):
    def __init__(
        self,
        dialog,
        scenarios_box,
        detail_box,
        status_label,
        data,
        builtin_scenarios,
        user_scenarios,
    ):
        self.dialog = dialog
        self.scenarios_box = scenarios_box
        self.detail_box = detail_box
        self.status_label = status_label
        self.data = data
        self.builtin_scenarios = builtin_scenarios
        self.user_scenarios = user_scenarios
        self.scenarios = self.builtin_scenarios + self.user_scenarios
        self.current = None
        self._populate()

    def _populate(self, select_index=0):
        if self.scenarios_box.ItemCount:
            self.scenarios_box.removeItems(0, self.scenarios_box.ItemCount)
        self.scenarios = self.builtin_scenarios + self.user_scenarios
        for scenario in self.scenarios:
            prefix = "★ " if scenario.get("_source") == "user" else ""
            self.scenarios_box.addItem(
                prefix + scenario.get("titre", "Scénario"),
                self.scenarios_box.ItemCount,
            )
        if self.scenarios:
            select_index = min(max(select_index, 0), len(self.scenarios) - 1)
            self.scenarios_box.selectItemPos(select_index, True)
            self._show(select_index)
        else:
            self.current = None
            self.detail_box.Text = "Aucun scénario disponible."

    def _show(self, index):
        if not (0 <= index < len(self.scenarios)):
            return
        scenario = self.scenarios[index]
        self.current = scenario
        steps = _scenario_steps(scenario, self.data)
        origin = (
            "Scénario utilisateur"
            if scenario.get("_source") == "user"
            else "Scénario fourni avec l’extension"
        )
        parts = [
            scenario.get("titre", "Scénario").upper(),
            f"Catégorie : {scenario.get('categorie', '—')}",
            f"Origine : {origin}",
            "",
            scenario.get("description", ""),
            "",
            (
                f"COMPOSITION — {len(steps)} PHRASE"
                if len(steps) == 1
                else f"COMPOSITION — {len(steps)} PHRASES"
            ),
        ]
        if steps:
            for number, step in enumerate(steps, start=1):
                parts.append("")
                parts.append(
                    f"{number}. {step['terme']} / {step['formulation']}"
                )
                parts.append(step["texte"])
        else:
            parts.append("")
            parts.append("Aucune formulation valide dans ce scénario.")
        self.detail_box.Text = "\n".join(parts)
        self.status_label.getModel().Label = (
            "Prêt à insérer"
            if steps
            else "Scénario incomplet"
        )

    def insert_current(self):
        if not self.current:
            return
        steps = _scenario_steps(self.current, self.data)
        if not steps:
            return
        doc = _desktop().getCurrentComponent()
        if not doc or not doc.supportsService("com.sun.star.text.TextDocument"):
            self.status_label.getModel().Label = "Aucun document Writer actif"
            return
        text_to_insert = "\n\n".join(step["texte"] for step in steps)
        view = doc.getCurrentController().getViewCursor()
        view.getText().insertString(view, text_to_insert, False)
        self.status_label.getModel().Label = "Scénario inséré dans le document"

    def _current_index(self):
        pos = self.scenarios_box.SelectedItemPos
        return pos if 0 <= pos < len(self.scenarios) else -1

    def duplicate_current(self):
        index = self._current_index()
        if index < 0:
            return
        source = self.scenarios[index]
        duplicate = {
            "id": "user-" + str(len(self.user_scenarios) + 1),
            "titre": source.get("titre", "Scénario") + " — copie",
            "categorie": source.get("categorie", "Personnalisé"),
            "description": source.get("description", ""),
            "etapes": list(source.get("etapes", [])),
            "_source": "user",
        }
        self.user_scenarios.append(duplicate)
        _save_user_scenarios(self.user_scenarios)
        self._populate(len(self.builtin_scenarios) + len(self.user_scenarios) - 1)
        self.status_label.getModel().Label = "Scénario dupliqué"

    def new_from_current(self):
        item = {
            "id": "user-" + str(len(self.user_scenarios) + 1),
            "titre": "Nouveau scénario",
            "categorie": "Personnalisé",
            "description": "",
            "etapes": [],
            "_source": "user",
        }
        self.user_scenarios.append(item)
        _save_user_scenarios(self.user_scenarios)
        index = len(self.builtin_scenarios) + len(self.user_scenarios) - 1
        self._populate(index)
        open_scenario_editor(self, item)

    def edit_current(self):
        index = self._current_index()
        if index < 0:
            return
        scenario = self.scenarios[index]
        if scenario.get("_source") != "user":
            duplicate = {
                "id": "user-" + str(len(self.user_scenarios) + 1),
                "titre": scenario.get("titre", "Scénario") + " — personnalisé",
                "categorie": scenario.get("categorie", "Personnalisé"),
                "description": scenario.get("description", ""),
                "etapes": [dict(step) for step in scenario.get("etapes", [])],
                "_source": "user",
            }
            self.user_scenarios.append(duplicate)
            _save_user_scenarios(self.user_scenarios)
            scenario = duplicate
            index = len(self.builtin_scenarios) + len(self.user_scenarios) - 1
            self._populate(index)
        open_scenario_editor(self, scenario)

    def delete_current(self):
        index = self._current_index()
        if index < len(self.builtin_scenarios):
            self.status_label.getModel().Label = (
                "Les scénarios fournis ne peuvent pas être supprimés"
            )
            return
        user_index = index - len(self.builtin_scenarios)
        if not (0 <= user_index < len(self.user_scenarios)):
            return
        self.user_scenarios.pop(user_index)
        _save_user_scenarios(self.user_scenarios)
        self._populate(max(index - 1, 0))
        self.status_label.getModel().Label = "Scénario utilisateur supprimé"

    def actionPerformed(self, event):
        if event.ActionCommand == "insert":
            self.insert_current()
        elif event.ActionCommand == "new":
            self.new_from_current()
        elif event.ActionCommand == "duplicate":
            self.duplicate_current()
        elif event.ActionCommand == "edit":
            self.edit_current()
        elif event.ActionCommand == "delete":
            self.delete_current()
        elif event.ActionCommand == "close":
            self._close_dialog()

    def itemStateChanged(self, event):
        pos = self.scenarios_box.SelectedItemPos
        if 0 <= pos < len(self.scenarios):
            self._show(pos)

    def _close_dialog(self):
        try:
            self.dialog.setVisible(False)
            self.dialog.dispose()
        finally:
            _OPEN_SCENARIO_WINDOWS[:] = [
                item for item in _OPEN_SCENARIO_WINDOWS
                if item.get("dialog") is not self.dialog
            ]

    def windowClosing(self, event):
        self._close_dialog()

    def windowOpened(self, event):
        pass

    def windowClosed(self, event):
        pass

    def windowMinimized(self, event):
        pass

    def windowNormalized(self, event):
        pass

    def windowActivated(self, event):
        pass

    def windowDeactivated(self, event):
        pass

    def disposing(self, event):
        pass


class ScenarioEditorListener(
    unohelper.Base,
    XActionListener,
    XItemListener,
    XTopWindowListener,
):
    def __init__(
        self,
        dialog,
        parent_listener,
        scenario,
        title_box,
        category_box,
        description_box,
        steps_box,
        term_box,
        formulation_box,
        status_label,
    ):
        self.dialog = dialog
        self.parent_listener = parent_listener
        self.scenario = scenario
        self.title_box = title_box
        self.category_box = category_box
        self.description_box = description_box
        self.steps_box = steps_box
        self.term_box = term_box
        self.formulation_box = formulation_box
        self.status_label = status_label
        self.data = parent_listener.data
        self._closing = False
        self.entries = sorted(
            [e for e in self.data if _report_formulations(e)],
            key=lambda e: _normalize(e.get("terme", "")),
        )
        self.steps = [dict(step) for step in scenario.get("etapes", [])]
        self._populate_terms()
        self._populate_steps()

    def _clear(self, control):
        if control.ItemCount:
            control.removeItems(0, control.ItemCount)

    def _populate_terms(self):
        self._clear(self.term_box)
        for entry in self.entries:
            self.term_box.addItem(entry.get("terme", ""), self.term_box.ItemCount)
        if self.entries:
            self.term_box.selectItemPos(0, True)
            self._populate_formulations(0)

    def _populate_formulations(self, entry_index):
        self._clear(self.formulation_box)
        if not (0 <= entry_index < len(self.entries)):
            return
        for label, _text in _report_formulations(self.entries[entry_index]):
            self.formulation_box.addItem(label, self.formulation_box.ItemCount)
        if self.formulation_box.ItemCount:
            self.formulation_box.selectItemPos(0, True)

    def _step_label(self, step):
        entry = next(
            (e for e in self.data if e.get("id") == step.get("terme")),
            None,
        )
        term = entry.get("terme", step.get("terme", "Terme")) if entry else step.get("terme", "Terme")
        return f"{term} — {step.get('formulation', '')}"

    def _populate_steps(self, select_index=None):
        self._clear(self.steps_box)
        for step in self.steps:
            self.steps_box.addItem(
                self._step_label(step),
                self.steps_box.ItemCount,
            )
        if self.steps:
            if select_index is None:
                select_index = 0
            select_index = min(max(select_index, 0), len(self.steps) - 1)
            self.steps_box.selectItemPos(select_index, True)
        self.status_label.getModel().Label = (
            f"{len(self.steps)} phrase" if len(self.steps) == 1
            else f"{len(self.steps)} phrases"
        )

    def _selected_term_index(self):
        pos = self.term_box.SelectedItemPos
        return pos if 0 <= pos < len(self.entries) else -1

    def _selected_step_index(self):
        pos = self.steps_box.SelectedItemPos
        return pos if 0 <= pos < len(self.steps) else -1

    def add_step(self):
        entry_index = self._selected_term_index()
        if entry_index < 0:
            return
        form_pos = self.formulation_box.SelectedItemPos
        formulations = _report_formulations(self.entries[entry_index])
        if not (0 <= form_pos < len(formulations)):
            return
        label, _text = formulations[form_pos]
        self.steps.append({
            "terme": self.entries[entry_index].get("id"),
            "formulation": label,
        })
        self._populate_steps(len(self.steps) - 1)

    def remove_step(self):
        index = self._selected_step_index()
        if index < 0:
            return
        self.steps.pop(index)
        self._populate_steps(max(index - 1, 0))

    def move_step(self, delta):
        index = self._selected_step_index()
        target = index + delta
        if index < 0 or not (0 <= target < len(self.steps)):
            return
        self.steps[index], self.steps[target] = self.steps[target], self.steps[index]
        self._populate_steps(target)

    def save(self):
        title = (self.title_box.Text or "").strip()
        if not title:
            self.status_label.getModel().Label = "Le titre est obligatoire"
            return
        self.scenario["titre"] = title
        self.scenario["categorie"] = (
            (self.category_box.Text or "").strip() or "Personnalisé"
        )
        self.scenario["description"] = (self.description_box.Text or "").strip()
        self.scenario["etapes"] = [dict(step) for step in self.steps]
        self.scenario["_source"] = "user"
        _save_user_scenarios(self.parent_listener.user_scenarios)
        selected = (
            len(self.parent_listener.builtin_scenarios)
            + self.parent_listener.user_scenarios.index(self.scenario)
        )
        self.parent_listener._populate(selected)
        self.parent_listener.status_label.getModel().Label = (
            "Scénario personnalisé enregistré"
        )
        self._close_dialog()

    def actionPerformed(self, event):
        cmd = event.ActionCommand
        if cmd == "add":
            self.add_step()
        elif cmd == "remove":
            self.remove_step()
        elif cmd == "up":
            self.move_step(-1)
        elif cmd == "down":
            self.move_step(1)
        elif cmd == "save":
            self.save()
        elif cmd == "cancel":
            self._close_dialog()

    def itemStateChanged(self, event):
        source_name = ""
        try:
            source_name = event.Source.getModel().Name
        except Exception:
            pass
        if source_name == "cmbEditTerm":
            entry_index = self._selected_term_index()
            if entry_index >= 0:
                self._populate_formulations(entry_index)

    def _close_dialog(self):
        if self._closing:
            return
        self._closing = True
        try:
            try:
                self.dialog.removeTopWindowListener(self)
            except Exception:
                pass
            self.dialog.setVisible(False)
            self.dialog.dispose()
        finally:
            _OPEN_SCENARIO_EDITOR_WINDOWS[:] = [
                item for item in _OPEN_SCENARIO_EDITOR_WINDOWS
                if item.get("dialog") is not self.dialog
            ]

    def windowClosing(self, event):
        self._close_dialog()

    def windowOpened(self, event):
        pass

    def windowClosed(self, event):
        pass

    def windowMinimized(self, event):
        pass

    def windowNormalized(self, event):
        pass

    def windowActivated(self, event):
        pass

    def windowDeactivated(self, event):
        pass

    def disposing(self, event):
        pass


class TermManagerListener(
    unohelper.Base,
    XActionListener,
    XItemListener,
    XTopWindowListener,
):
    def __init__(
        self,
        dialog,
        terms_box,
        detail_box,
        status_label,
        builtin_data,
        user_data,
        lexicon_listener=None,
    ):
        self.dialog = dialog
        self.terms_box = terms_box
        self.detail_box = detail_box
        self.status_label = status_label
        self.builtin_data = builtin_data
        self.user_data = user_data
        self.lexicon_listener = lexicon_listener
        self.data = []
        self.current = None
        self._closing = False
        self._populate()

    def _populate(self, select_index=0):
        if self.terms_box.ItemCount:
            self.terms_box.removeItems(0, self.terms_box.ItemCount)
        self.data = sorted(
            self.builtin_data + self.user_data,
            key=lambda e: _normalize(e.get("terme", "")),
        )
        for entry in self.data:
            prefix = "★ " if entry.get("_source") == "user" else ""
            self.terms_box.addItem(
                prefix + entry.get("terme", "Terme"),
                self.terms_box.ItemCount,
            )
        if self.data:
            select_index = min(max(select_index, 0), len(self.data) - 1)
            self.terms_box.selectItemPos(select_index, True)
            self._show(select_index)
        else:
            self.current = None
            self.detail_box.Text = "Aucun terme disponible."

    def _show(self, index):
        if not (0 <= index < len(self.data)):
            return
        entry = self.data[index]
        self.current = entry
        text, _ranges = _format_entry(entry)
        origin = (
            "Terme utilisateur"
            if entry.get("_source") == "user"
            else "Terme fourni avec l’extension"
        )
        self.detail_box.Text = (
            f"ORIGINE\n{origin}\n\n" + text
        )
        self.status_label.getModel().Label = origin

    def _current_index(self):
        pos = self.terms_box.SelectedItemPos
        return pos if 0 <= pos < len(self.data) else -1

    def _notify_lexicon(self):
        if self.lexicon_listener is not None:
            try:
                self.lexicon_listener.reload_data()
            except Exception:
                pass

    def _new_id(self):
        existing = {e.get("id") for e in self.builtin_data + self.user_data}
        number = 1
        while f"user-term-{number}" in existing:
            number += 1
        return f"user-term-{number}"

    def new_term(self):
        entry = {
            "id": self._new_id(),
            "terme": "Nouveau terme",
            "anglais": "",
            "categorie": "Personnalisé",
            "definition": "",
            "synonymes": [],
            "termes_deconseilles": [],
            "formulations_rapport": [],
            "sources": [],
            "_source": "user",
        }
        self.user_data.append(entry)
        _save_user_data(self.user_data)
        open_term_editor(self, entry)

    def duplicate_current(self):
        index = self._current_index()
        if index < 0:
            return
        source = self.data[index]
        duplicate = {
            "id": self._new_id(),
            "terme": source.get("terme", "Terme") + " — copie",
            "anglais": source.get("anglais", ""),
            "categorie": source.get("categorie", "Personnalisé"),
            "definition": source.get("definition", ""),
            "synonymes": list(source.get("synonymes", [])),
            "termes_deconseilles": list(_bad_terms(source)),
            "formulations_rapport": [
                {"type": label, "texte": text}
                for label, text in _report_formulations(source)
            ],
            "points_attention": list(source.get("points_attention", [])),
            "sources": [],
            "_source": "user",
        }
        self.user_data.append(duplicate)
        _save_user_data(self.user_data)
        self._populate()
        self._notify_lexicon()
        self.status_label.getModel().Label = "Terme dupliqué"

    def edit_current(self):
        index = self._current_index()
        if index < 0:
            return
        entry = self.data[index]
        if entry.get("_source") != "user":
            source = entry
            entry = {
                "id": self._new_id(),
                "terme": source.get("terme", "Terme") + " — personnalisé",
                "anglais": source.get("anglais", ""),
                "categorie": source.get("categorie", "Personnalisé"),
                "definition": source.get("definition", ""),
                "synonymes": list(source.get("synonymes", [])),
                "termes_deconseilles": list(_bad_terms(source)),
                "formulations_rapport": [
                    {"type": label, "texte": text}
                    for label, text in _report_formulations(source)
                ],
                "points_attention": list(source.get("points_attention", [])),
                "sources": [],
                "_source": "user",
            }
            self.user_data.append(entry)
            _save_user_data(self.user_data)
        open_term_editor(self, entry)

    def delete_current(self):
        index = self._current_index()
        if index < 0:
            return
        entry = self.data[index]
        if entry.get("_source") != "user":
            self.status_label.getModel().Label = (
                "Les termes fournis ne peuvent pas être supprimés"
            )
            return
        try:
            self.user_data.remove(entry)
        except ValueError:
            return
        _save_user_data(self.user_data)
        self._populate(max(index - 1, 0))
        self._notify_lexicon()
        self.status_label.getModel().Label = "Terme utilisateur supprimé"

    def refresh_after_edit(self, entry):
        self._populate()
        self._notify_lexicon()
        for index, item in enumerate(self.data):
            if item is entry or item.get("id") == entry.get("id"):
                self.terms_box.selectItemPos(index, True)
                self._show(index)
                break

    def actionPerformed(self, event):
        cmd = event.ActionCommand
        if cmd == "new":
            self.new_term()
        elif cmd == "duplicate":
            self.duplicate_current()
        elif cmd == "edit":
            self.edit_current()
        elif cmd == "delete":
            self.delete_current()
        elif cmd == "close":
            self._close_dialog()

    def itemStateChanged(self, event):
        pos = self.terms_box.SelectedItemPos
        if 0 <= pos < len(self.data):
            self._show(pos)

    def _close_dialog(self):
        if self._closing:
            return
        self._closing = True
        try:
            try:
                self.dialog.removeTopWindowListener(self)
            except Exception:
                pass
            self.dialog.setVisible(False)
            self.dialog.dispose()
        finally:
            _OPEN_TERM_WINDOWS[:] = [
                item for item in _OPEN_TERM_WINDOWS
                if item.get("dialog") is not self.dialog
            ]

    def windowClosing(self, event):
        self._close_dialog()

    def windowOpened(self, event):
        pass
    def windowClosed(self, event):
        pass
    def windowMinimized(self, event):
        pass
    def windowNormalized(self, event):
        pass
    def windowActivated(self, event):
        pass
    def windowDeactivated(self, event):
        pass
    def disposing(self, event):
        pass


class TermEditorListener(
    unohelper.Base,
    XActionListener,
    XItemListener,
    XTopWindowListener,
):
    def __init__(
        self,
        dialog,
        parent_listener,
        entry,
        term_box,
        english_box,
        category_box,
        synonyms_box,
        definition_box,
        formulations_box,
        formulation_text_box,
        add_button,
        update_button,
        status_label,
    ):
        self.dialog = dialog
        self.parent_listener = parent_listener
        self.entry = entry
        self.term_box = term_box
        self.english_box = english_box
        self.category_box = category_box
        self.synonyms_box = synonyms_box
        self.definition_box = definition_box
        self.formulations_box = formulations_box
        self.formulation_text_box = formulation_text_box
        self.add_button = add_button
        self.update_button = update_button
        self.status_label = status_label
        self._closing = False
        self.formulations = [
            {"type": label or "Formulation", "texte": text}
            for label, text in _report_formulations(entry)
        ]
        self._populate_formulations()

    def _clear(self, control):
        if control.ItemCount:
            control.removeItems(0, control.ItemCount)

    def _populate_formulations(self, select_index=None):
        self._clear(self.formulations_box)
        for item in self.formulations:
            text = (item.get("texte") or "").strip()
            label = text if len(text) <= 52 else text[:49].rstrip() + "…"
            self.formulations_box.addItem(
                label or "(formulation vide)",
                self.formulations_box.ItemCount,
            )
        if self.formulations:
            if select_index is None:
                select_index = 0
            select_index = min(max(select_index, 0), len(self.formulations) - 1)
            self.formulations_box.selectItemPos(select_index, True)
            self._load_formulation(select_index)
        else:
            self.formulation_text_box.Text = ""
            self.update_button.getModel().Enabled = False
        self.status_label.getModel().Label = (
            f"{len(self.formulations)} formulation"
            if len(self.formulations) == 1
            else f"{len(self.formulations)} formulations"
        )

    def _selected_formulation_index(self):
        pos = self.formulations_box.SelectedItemPos
        return pos if 0 <= pos < len(self.formulations) else -1

    def _load_formulation(self, index):
        if not (0 <= index < len(self.formulations)):
            return
        item = self.formulations[index]
        self.formulation_text_box.Text = item.get("texte", "")
        self.update_button.getModel().Enabled = True

    def _commit_current_formulation(self):
        index = self._selected_formulation_index()
        if index < 0:
            return
        text = (self.formulation_text_box.Text or "").strip()
        label = self.formulations[index].get("type") or "Formulation"
        self.formulations[index] = {"type": label, "texte": text}

    def add_formulation(self):
        current_text = (self.formulation_text_box.Text or "").strip()
        if not current_text:
            self.status_label.getModel().Label = "Saisissez une formulation"
            return

        self.formulations.append({
            "type": "Formulation",
            "texte": current_text,
        })
        self._populate_formulations(len(self.formulations) - 1)
        self.formulation_text_box.Text = ""
        self.update_button.getModel().Enabled = False
        try:
            self.formulations_box.selectItemPos(-1, False)
        except Exception:
            pass
        self.status_label.getModel().Label = "Formulation ajoutée"

    def update_formulation(self):
        index = self._selected_formulation_index()
        if index < 0:
            self.status_label.getModel().Label = (
                "Sélectionnez une formulation à mettre à jour"
            )
            return

        current_text = (self.formulation_text_box.Text or "").strip()
        if not current_text:
            self.status_label.getModel().Label = "Saisissez une formulation"
            return

        label = self.formulations[index].get("type") or "Formulation"
        self.formulations[index] = {
            "type": label,
            "texte": current_text,
        }
        self._populate_formulations(index)
        self.status_label.getModel().Label = "Formulation mise à jour"

    def remove_formulation(self):
        index = self._selected_formulation_index()
        if index < 0:
            return
        self.formulations.pop(index)
        self._populate_formulations(max(index - 1, 0))
        if not self.formulations:
            self.add_button.getModel().Label = "Ajouter"

    def move_formulation(self, delta):
        index = self._selected_formulation_index()
        target = index + delta
        if index < 0 or not (0 <= target < len(self.formulations)):
            return
        self._commit_current_formulation()
        self.formulations[index], self.formulations[target] = (
            self.formulations[target],
            self.formulations[index],
        )
        self._populate_formulations(target)

    def save(self):
        term = (self.term_box.Text or "").strip()
        if not term:
            self.status_label.getModel().Label = "Le terme est obligatoire"
            return
        current_text = (self.formulation_text_box.Text or "").strip()
        if current_text:
            self.formulations.append({
                "type": "Formulation",
                "texte": current_text,
            })
        self.entry["terme"] = term
        self.entry["anglais"] = (self.english_box.Text or "").strip()
        category = ""
        try:
            category = (self.category_box.getSelectedItem() or "").strip()
        except Exception:
            try:
                category = (self.category_box.getText() or "").strip()
            except Exception:
                category = ""
        self.entry["categorie"] = category or "Personnalisé"
        self.entry["definition"] = (self.definition_box.Text or "").strip()
        self.entry["synonymes"] = [
            value.strip()
            for value in (self.synonyms_box.Text or "").split(",")
            if value.strip()
        ]
        self.entry["formulations_rapport"] = [
            item for item in self.formulations
            if (item.get("texte") or "").strip()
        ]
        self.entry["_source"] = "user"
        _save_user_data(self.parent_listener.user_data)
        self.parent_listener.refresh_after_edit(self.entry)
        self.parent_listener.status_label.getModel().Label = (
            "Terme utilisateur enregistré"
        )
        self._close_dialog()

    def actionPerformed(self, event):
        cmd = event.ActionCommand
        if cmd == "add":
            self.add_formulation()
        elif cmd == "update":
            self.update_formulation()
        elif cmd == "remove":
            self.remove_formulation()
        elif cmd == "up":
            self.move_formulation(-1)
        elif cmd == "down":
            self.move_formulation(1)
        elif cmd == "save":
            self.save()
        elif cmd == "cancel":
            self._close_dialog()

    def itemStateChanged(self, event):
        index = self._selected_formulation_index()
        if index >= 0:
            self._load_formulation(index)

    def _close_dialog(self):
        if self._closing:
            return
        self._closing = True
        try:
            try:
                self.dialog.removeTopWindowListener(self)
            except Exception:
                pass
            self.dialog.setVisible(False)
            self.dialog.dispose()
        finally:
            _OPEN_TERM_EDITOR_WINDOWS[:] = [
                item for item in _OPEN_TERM_EDITOR_WINDOWS
                if item.get("dialog") is not self.dialog
            ]

    def windowClosing(self, event):
        self._close_dialog()

    def windowOpened(self, event):
        pass
    def windowClosed(self, event):
        pass
    def windowMinimized(self, event):
        pass
    def windowNormalized(self, event):
        pass
    def windowActivated(self, event):
        pass
    def windowDeactivated(self, event):
        pass
    def disposing(self, event):
        pass


class DataTransferListener(
    unohelper.Base,
    XActionListener,
    XTopWindowListener,
):
    def __init__(self, dialog, status_label, proposal_list):
        self.dialog = dialog
        self.status_label = status_label
        self.proposal_list = proposal_list
        self.proposal_entries = []
        self._closing = False
        self.refresh_proposals()

    def refresh_proposals(self):
        self.proposal_entries = _load_user_data()
        self.proposal_list.removeItems(0, self.proposal_list.ItemCount)
        for entry in self.proposal_entries:
            self.proposal_list.addItem(entry.get('terme') or 'Sans nom', self.proposal_list.ItemCount)

    def propose_selected(self):
        self.refresh_entries_if_needed()
        selected = list(self.proposal_list.SelectedItemsPos)
        entries = [self.proposal_entries[i] for i in selected if 0 <= i < len(self.proposal_entries)]
        try:
            url = _prepare_term_proposals(entries)
        except ValueError as exc:
            self.status_label.getModel().Label = str(exc)
            _message_box('Proposer des fiches', str(exc))
            return
        _message_box('Proposer des fiches',
                     'Le navigateur va afficher les fiches sélectionnées. '
                     'Aucune proposition n’est envoyée automatiquement. '
                     'Une publication GitHub est publique : vérifiez chaque '
                     'formulation et retirez les informations confidentielles '
                     'avant de confirmer. Un compte GitHub est requis.')
        try:
            _open_url(url)
            self.status_label.getModel().Label = 'Proposition prête dans le navigateur'
        except Exception:
            self.status_label.getModel().Label = 'Impossible d’ouvrir GitHub'

    def refresh_entries_if_needed(self):
        # Ne pas réinitialiser la sélection pendant que l’utilisateur la prépare.
        return

    def export_data(self):
        try:
            path = _pick_json_file(save=True)
            if not path:
                self.status_label.getModel().Label = "Export annulé"
                return
            payload = _export_user_payload()
            with open(path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
                f.write("\n")
            self.status_label.getModel().Label = "Base utilisateur exportée"
            _message_box(
                "Export des données utilisateur",
                "La base utilisateur a été exportée avec succès.",
            )
        except Exception as exc:
            _message_box(
                "Export des données utilisateur",
                f"Impossible d’exporter la base utilisateur.\n\nDétail : {exc}",
            )

    def import_data(self, mode):
        try:
            path = _pick_json_file(save=False)
            if not path:
                self.status_label.getModel().Label = "Import annulé"
                return
            with open(path, "r", encoding="utf-8") as f:
                payload = _validate_user_payload(json.load(f))

            backup_dir = _backup_current_user_data()

            if mode == "replace":
                lexique = payload["lexique"]
                scenarios = payload["scenarios"]
                occurrences = [
                    _normalize_occurrence_item(item, "user")
                    for item in payload["occurrences"]
                ]
                summary = (
                    f"{len(lexique)} terme(s), "
                    f"{len(scenarios)} scénario(s), "
                    f"{len(occurrences)} occurrence(s) importés."
                )
            else:
                lexique, l_added, l_skipped = _merge_user_items(
                    _load_user_data(), payload["lexique"], "lexique"
                )
                scenarios, s_added, s_skipped = _merge_user_items(
                    _load_user_scenarios(), payload["scenarios"], "scenarios"
                )
                imported_occurrences = [
                    _normalize_occurrence_item(item, "user")
                    for item in payload["occurrences"]
                ]
                occurrences, o_added, o_skipped = _merge_user_items(
                    _load_user_occurrences(), imported_occurrences, "occurrences"
                )
                summary = (
                    f"Ajoutés : {l_added} terme(s), {s_added} scénario(s), "
                    f"{o_added} occurrence(s).\n"
                    f"Conservés car déjà présents : "
                    f"{l_skipped + s_skipped + o_skipped}."
                )

            _save_user_data(lexique)
            _save_user_scenarios(scenarios)
            _save_user_occurrences(occurrences)
            _refresh_user_data_windows()
            self.status_label.getModel().Label = (
                "Import fusionné" if mode == "merge" else "Base remplacée"
            )
            action = "fusionnée avec" if mode == "merge" else "remplacée par"
            _message_box(
                "Import des données utilisateur",
                (
                    f"La base utilisateur a été {action} le fichier importé.\n\n"
                    f"{summary}\n\n"
                    "Une sauvegarde de la base précédente a été créée dans :\n"
                    f"{backup_dir}"
                ),
            )
        except Exception as exc:
            _message_box(
                "Import des données utilisateur",
                (
                    "Aucune donnée n’a été importée.\n\n"
                    f"Détail : {exc}"
                ),
            )

    def actionPerformed(self, event):
        if event.ActionCommand == "export":
            self.export_data()
        elif event.ActionCommand == "merge":
            self.import_data("merge")
        elif event.ActionCommand == "replace":
            self.import_data("replace")
        elif event.ActionCommand == "propose":
            self.propose_selected()
        elif event.ActionCommand == "close":
            self._close_dialog()

    def _close_dialog(self):
        if self._closing:
            return
        self._closing = True
        try:
            try:
                self.dialog.removeTopWindowListener(self)
            except Exception:
                pass
            self.dialog.setVisible(False)
            self.dialog.dispose()
        finally:
            _OPEN_DATA_TRANSFER_WINDOWS[:] = [
                item for item in _OPEN_DATA_TRANSFER_WINDOWS
                if item.get("dialog") is not self.dialog
            ]

    def windowClosing(self, event):
        self._close_dialog()
    def windowOpened(self, event): pass
    def windowClosed(self, event): pass
    def windowMinimized(self, event): pass
    def windowNormalized(self, event): pass
    def windowActivated(self, event): pass
    def windowDeactivated(self, event): pass
    def disposing(self, event): pass


class AboutListener(unohelper.Base, XActionListener, XTopWindowListener):
    def __init__(self, dialog):
        self.dialog = dialog

    def actionPerformed(self, event):
        if event.ActionCommand == "github":
            _open_url(GITHUB_URL)
        elif event.ActionCommand == "close":
            self._close_dialog()

    def _close_dialog(self):
        try:
            self.dialog.setVisible(False)
            self.dialog.dispose()
        finally:
            _OPEN_ABOUT_WINDOWS[:] = [
                item for item in _OPEN_ABOUT_WINDOWS
                if item.get("dialog") is not self.dialog
            ]

    def windowClosing(self, event):
        self._close_dialog()

    def windowOpened(self, event):
        pass

    def windowClosed(self, event):
        pass

    def windowMinimized(self, event):
        pass

    def windowNormalized(self, event):
        pass

    def windowActivated(self, event):
        pass

    def windowDeactivated(self, event):
        pass

    def disposing(self, event):
        pass


def open_verification(*args):
    ctx = _ctx()
    smgr = ctx.ServiceManager
    toolkit = smgr.createInstanceWithContext("com.sun.star.awt.Toolkit", ctx)
    model = smgr.createInstanceWithContext(
        "com.sun.star.awt.UnoControlDialogModel", ctx
    )
    model.PositionX = 92
    model.PositionY = 58
    model.Width = 300
    model.Height = 250
    model.Title = "Vérification du document"

    def add(name, service, x, y, w, h, **props):
        item = model.createInstance(service)
        item.Name = name
        item.PositionX, item.PositionY = x, y
        item.Width, item.Height = w, h
        for key, value in props.items():
            setattr(item, key, value)
        model.insertByName(name, item)

    add("lblAlerts", "com.sun.star.awt.UnoControlFixedTextModel",
        8, 8, 104, 10, Label="Éléments détectés")
    add("lstVerifyAlerts", "com.sun.star.awt.UnoControlListBoxModel",
        8, 20, 104, 164)
    add("txtVerifyDetail", "com.sun.star.awt.UnoControlEditModel",
        118, 20, 174, 164, MultiLine=True, ReadOnly=True, VScroll=True)
    add("lblVerifyStatus", "com.sun.star.awt.UnoControlFixedTextModel",
        8, 190, 284, 10, Label="")
    add("btnVerifyReplace", "com.sun.star.awt.UnoControlButtonModel",
        8, 208, 104, 16, Label="Remplacer cette occurrence", Enabled=False)
    add("btnVerifyRescan", "com.sun.star.awt.UnoControlButtonModel",
        118, 208, 78, 16, Label="Revérifier")
    add("btnVerifyManage", "com.sun.star.awt.UnoControlButtonModel",
        202, 208, 90, 16, Label="Gérer les occurrences")
    add("btnVerifyClose", "com.sun.star.awt.UnoControlButtonModel",
        240, 228, 52, 16, Label="Fermer")

    dialog = smgr.createInstanceWithContext(
        "com.sun.star.awt.UnoControlDialog", ctx
    )
    dialog.setModel(model)
    dialog.createPeer(toolkit, None)

    listener = VerificationListener(
        dialog,
        dialog.getControl("lstVerifyAlerts"),
        dialog.getControl("txtVerifyDetail"),
        dialog.getControl("lblVerifyStatus"),
        dialog.getControl("btnVerifyReplace"),
        _load_data(),
        _load_translations(),
    )
    for control_name, command in [
        ("btnVerifyReplace", "replace"),
        ("btnVerifyRescan", "rescan"),
        ("btnVerifyManage", "manage_occurrences"),
        ("btnVerifyClose", "close"),
    ]:
        control = dialog.getControl(control_name)
        control.setActionCommand(command)
        control.addActionListener(listener)

    dialog.getControl("lstVerifyAlerts").addItemListener(listener)
    dialog.addTopWindowListener(listener)
    _OPEN_VERIFY_WINDOWS.append({"dialog": dialog, "listener": listener})
    dialog.setVisible(True)


def open_occurrence_editor(parent_listener, item, is_new=False):
    ctx = _ctx()
    smgr = ctx.ServiceManager
    toolkit = smgr.createInstanceWithContext("com.sun.star.awt.Toolkit", ctx)
    model = smgr.createInstanceWithContext(
        "com.sun.star.awt.UnoControlDialogModel", ctx
    )
    model.PositionX = 108
    model.PositionY = 62
    model.Width = 360
    model.Height = 250
    model.Title = "Occurrence utilisateur"

    def add(name, service, x, y, w, h, **props):
        control = model.createInstance(service)
        control.Name = name
        control.PositionX, control.PositionY = x, y
        control.Width, control.Height = w, h
        for key, value in props.items():
            setattr(control, key, value)
        model.insertByName(name, control)

    add("lblOccurrence", "com.sun.star.awt.UnoControlFixedTextModel",
        8, 8, 100, 10, Label="Occurrence à détecter :")
    add("txtOccurrence", "com.sun.star.awt.UnoControlEditModel",
        8, 20, 344, 16, Text=item.get("occurrence", ""))
    add("lblReplacements", "com.sun.star.awt.UnoControlFixedTextModel",
        8, 46, 180, 10, Label="Remplacements possibles — un par ligne :")
    add("txtReplacements", "com.sun.star.awt.UnoControlEditModel",
        8, 58, 344, 70, MultiLine=True, VScroll=True,
        Text="\n".join(item.get("remplacements", [])))
    add("lblPreferred", "com.sun.star.awt.UnoControlFixedTextModel",
        8, 138, 100, 10, Label="Remplacement préféré :")
    add("txtPreferred", "com.sun.star.awt.UnoControlEditModel",
        8, 150, 344, 16, Text=item.get("prefere", ""))
    add("lblOccurrenceNote", "com.sun.star.awt.UnoControlFixedTextModel",
        8, 176, 80, 10, Label="Note facultative :")
    add("txtOccurrenceNote", "com.sun.star.awt.UnoControlEditModel",
        8, 188, 344, 30, MultiLine=True, VScroll=True,
        Text=item.get("note", ""))
    add("lblOccurrenceEditStatus", "com.sun.star.awt.UnoControlFixedTextModel",
        8, 224, 190, 10, Label="")
    add("btnOccurrenceCancel", "com.sun.star.awt.UnoControlButtonModel",
        232, 226, 54, 18, Label="Annuler")
    add("btnOccurrenceSave", "com.sun.star.awt.UnoControlButtonModel",
        292, 226, 60, 18, Label="Enregistrer")

    dialog = smgr.createInstanceWithContext(
        "com.sun.star.awt.UnoControlDialog", ctx
    )
    dialog.setModel(model)
    dialog.createPeer(toolkit, None)

    listener = OccurrenceEditorListener(
        dialog,
        parent_listener,
        item,
        is_new,
        dialog.getControl("txtOccurrence"),
        dialog.getControl("txtReplacements"),
        dialog.getControl("txtPreferred"),
        dialog.getControl("txtOccurrenceNote"),
        dialog.getControl("lblOccurrenceEditStatus"),
    )
    for control_name, command in [
        ("btnOccurrenceSave", "save"),
        ("btnOccurrenceCancel", "cancel"),
    ]:
        control = dialog.getControl(control_name)
        control.setActionCommand(command)
        control.addActionListener(listener)

    dialog.addTopWindowListener(listener)
    _OPEN_OCCURRENCE_EDITOR_WINDOWS.append({
        "dialog": dialog,
        "listener": listener,
    })
    dialog.setVisible(True)


def open_occurrence_manager(verification_listener=None):
    ctx = _ctx()
    smgr = ctx.ServiceManager
    toolkit = smgr.createInstanceWithContext("com.sun.star.awt.Toolkit", ctx)
    model = smgr.createInstanceWithContext(
        "com.sun.star.awt.UnoControlDialogModel", ctx
    )
    model.PositionX = 96
    model.PositionY = 58
    model.Width = 390
    model.Height = 292
    model.Title = "Gestion des occurrences"

    def add(name, service, x, y, w, h, **props):
        control = model.createInstance(service)
        control.Name = name
        control.PositionX, control.PositionY = x, y
        control.Width, control.Height = w, h
        for key, value in props.items():
            setattr(control, key, value)
        model.insertByName(name, control)

    add("lblOccurrences", "com.sun.star.awt.UnoControlFixedTextModel",
        8, 8, 142, 10, Label="Occurrences à détecter")
    add("lstOccurrences", "com.sun.star.awt.UnoControlListBoxModel",
        8, 20, 142, 232)
    add("txtOccurrenceDetail", "com.sun.star.awt.UnoControlEditModel",
        158, 20, 224, 232, MultiLine=True, ReadOnly=True, VScroll=True)
    add("lblOccurrenceStatus", "com.sun.star.awt.UnoControlFixedTextModel",
        158, 258, 150, 10, Label="")
    add("btnOccurrenceNew", "com.sun.star.awt.UnoControlButtonModel",
        8, 256, 52, 16, Label="Nouveau")
    add("btnOccurrenceEdit", "com.sun.star.awt.UnoControlButtonModel",
        64, 256, 52, 16, Label="Modifier")
    add("btnOccurrenceDelete", "com.sun.star.awt.UnoControlButtonModel",
        120, 256, 58, 16, Label="Supprimer")
    add("btnOccurrenceClose", "com.sun.star.awt.UnoControlButtonModel",
        330, 274, 52, 14, Label="Fermer")

    dialog = smgr.createInstanceWithContext(
        "com.sun.star.awt.UnoControlDialog", ctx
    )
    dialog.setModel(model)
    dialog.createPeer(toolkit, None)

    listener = OccurrenceManagerListener(
        dialog,
        dialog.getControl("lstOccurrences"),
        dialog.getControl("txtOccurrenceDetail"),
        dialog.getControl("lblOccurrenceStatus"),
        verification_listener,
        _load_builtin_occurrences(),
        _load_user_occurrences(),
    )
    for control_name, command in [
        ("btnOccurrenceNew", "new"),
        ("btnOccurrenceEdit", "edit"),
        ("btnOccurrenceDelete", "delete"),
        ("btnOccurrenceClose", "close"),
    ]:
        control = dialog.getControl(control_name)
        control.setActionCommand(command)
        control.addActionListener(listener)

    dialog.getControl("lstOccurrences").addItemListener(listener)
    dialog.addTopWindowListener(listener)
    _OPEN_OCCURRENCE_WINDOWS.append({
        "dialog": dialog,
        "listener": listener,
    })
    dialog.setVisible(True)


def open_scenario_editor(parent_listener, scenario):
    ctx = _ctx()
    smgr = ctx.ServiceManager
    toolkit = smgr.createInstanceWithContext("com.sun.star.awt.Toolkit", ctx)
    model = smgr.createInstanceWithContext(
        "com.sun.star.awt.UnoControlDialogModel", ctx
    )
    model.PositionX = 105
    model.PositionY = 60
    model.Width = 420
    model.Height = 320
    model.Title = "Personnaliser le scénario"

    def add(name, service, x, y, w, h, **props):
        item = model.createInstance(service)
        item.Name = name
        item.PositionX, item.PositionY = x, y
        item.Width, item.Height = w, h
        for key, value in props.items():
            setattr(item, key, value)
        model.insertByName(name, item)

    add("lblEditTitle", "com.sun.star.awt.UnoControlFixedTextModel",
        8, 8, 44, 10, Label="Titre :")
    add("txtEditTitle", "com.sun.star.awt.UnoControlEditModel",
        54, 6, 358, 14, Text=scenario.get("titre", ""))
    add("lblEditCategory", "com.sun.star.awt.UnoControlFixedTextModel",
        8, 28, 44, 10, Label="Catégorie :")
    add("txtEditCategory", "com.sun.star.awt.UnoControlEditModel",
        54, 26, 160, 14, Text=scenario.get("categorie", "Personnalisé"))
    add("lblEditDescription", "com.sun.star.awt.UnoControlFixedTextModel",
        8, 48, 52, 10, Label="Description :")
    add("txtEditDescription", "com.sun.star.awt.UnoControlEditModel",
        8, 60, 404, 42, MultiLine=True, VScroll=True,
        Text=scenario.get("description", ""))

    add("lblEditSteps", "com.sun.star.awt.UnoControlFixedTextModel",
        8, 110, 150, 10, Label="Composition du scénario")
    add("lstEditSteps", "com.sun.star.awt.UnoControlListBoxModel",
        8, 122, 202, 142)
    add("btnStepUp", "com.sun.star.awt.UnoControlButtonModel",
        8, 268, 34, 16, Label="↑")
    add("btnStepDown", "com.sun.star.awt.UnoControlButtonModel",
        46, 268, 34, 16, Label="↓")
    add("btnStepRemove", "com.sun.star.awt.UnoControlButtonModel",
        84, 268, 58, 16, Label="Retirer")

    add("lblAddTerm", "com.sun.star.awt.UnoControlFixedTextModel",
        220, 110, 70, 10, Label="Ajouter une phrase")
    add("lblEditTerm", "com.sun.star.awt.UnoControlFixedTextModel",
        220, 130, 42, 10, Label="Terme :")
    add("cmbEditTerm", "com.sun.star.awt.UnoControlListBoxModel",
        220, 142, 192, 14, Dropdown=True)
    add("lblEditFormulation", "com.sun.star.awt.UnoControlFixedTextModel",
        220, 164, 60, 10, Label="Formulation :")
    add("cmbEditFormulation", "com.sun.star.awt.UnoControlListBoxModel",
        220, 176, 192, 14, Dropdown=True)
    add("btnStepAdd", "com.sun.star.awt.UnoControlButtonModel",
        318, 198, 94, 16, Label="Ajouter la phrase")

    add("lblEditStatus", "com.sun.star.awt.UnoControlFixedTextModel",
        220, 226, 192, 10, Label="")
    add("btnEditSave", "com.sun.star.awt.UnoControlButtonModel",
        304, 286, 108, 18, Label="Enregistrer")
    add("btnEditCancel", "com.sun.star.awt.UnoControlButtonModel",
        242, 286, 56, 18, Label="Annuler")

    dialog = smgr.createInstanceWithContext(
        "com.sun.star.awt.UnoControlDialog", ctx
    )
    dialog.setModel(model)
    dialog.createPeer(toolkit, None)

    listener = ScenarioEditorListener(
        dialog,
        parent_listener,
        scenario,
        dialog.getControl("txtEditTitle"),
        dialog.getControl("txtEditCategory"),
        dialog.getControl("txtEditDescription"),
        dialog.getControl("lstEditSteps"),
        dialog.getControl("cmbEditTerm"),
        dialog.getControl("cmbEditFormulation"),
        dialog.getControl("lblEditStatus"),
    )

    for control_name, command in [
        ("btnStepAdd", "add"),
        ("btnStepRemove", "remove"),
        ("btnStepUp", "up"),
        ("btnStepDown", "down"),
        ("btnEditSave", "save"),
        ("btnEditCancel", "cancel"),
    ]:
        control = dialog.getControl(control_name)
        control.setActionCommand(command)
        control.addActionListener(listener)

    term_control = dialog.getControl("cmbEditTerm")
    term_control.addItemListener(listener)
    dialog.addTopWindowListener(listener)
    _OPEN_SCENARIO_EDITOR_WINDOWS.append({
        "dialog": dialog,
        "listener": listener,
    })
    dialog.setVisible(True)


def open_scenarios(*args):
    ctx = _ctx()
    smgr = ctx.ServiceManager
    toolkit = smgr.createInstanceWithContext("com.sun.star.awt.Toolkit", ctx)
    model = smgr.createInstanceWithContext(
        "com.sun.star.awt.UnoControlDialogModel", ctx
    )
    model.PositionX = 90
    model.PositionY = 55
    model.Width = 390
    model.Height = 292
    model.Title = "Scénarios de rédaction"

    def add(name, service, x, y, w, h, **props):
        item = model.createInstance(service)
        item.Name = name
        item.PositionX, item.PositionY = x, y
        item.Width, item.Height = w, h
        for key, value in props.items():
            setattr(item, key, value)
        model.insertByName(name, item)

    add("lblScenarios", "com.sun.star.awt.UnoControlFixedTextModel",
        8, 8, 142, 10, Label="Choisir un scénario")
    add("lstScenarios", "com.sun.star.awt.UnoControlListBoxModel",
        8, 20, 142, 232)
    add("txtScenarioDetail", "com.sun.star.awt.UnoControlEditModel",
        158, 20, 224, 232, MultiLine=True, ReadOnly=True, VScroll=True)
    add("lblScenarioStatus", "com.sun.star.awt.UnoControlFixedTextModel",
        158, 258, 96, 10, Label="")
    add("btnScenarioNew", "com.sun.star.awt.UnoControlButtonModel",
        8, 256, 42, 16, Label="Nouveau")
    add("btnScenarioDuplicate", "com.sun.star.awt.UnoControlButtonModel",
        54, 256, 48, 16, Label="Dupliquer")
    add("btnScenarioEdit", "com.sun.star.awt.UnoControlButtonModel",
        106, 256, 44, 16, Label="Modifier")
    add("btnScenarioDelete", "com.sun.star.awt.UnoControlButtonModel",
        8, 276, 48, 14, Label="Supprimer")
    add("btnScenarioInsert", "com.sun.star.awt.UnoControlButtonModel",
        274, 256, 108, 16, Label="Insérer le scénario")
    add("btnScenarioClose", "com.sun.star.awt.UnoControlButtonModel",
        330, 274, 52, 14, Label="Fermer")

    dialog = smgr.createInstanceWithContext(
        "com.sun.star.awt.UnoControlDialog", ctx
    )
    dialog.setModel(model)
    dialog.createPeer(toolkit, None)

    listener = ScenarioListener(
        dialog,
        dialog.getControl("lstScenarios"),
        dialog.getControl("txtScenarioDetail"),
        dialog.getControl("lblScenarioStatus"),
        _load_data(),
        _load_scenarios(),
        _load_user_scenarios(),
    )
    for control_name, command in [
        ("btnScenarioNew", "new"),
        ("btnScenarioDuplicate", "duplicate"),
        ("btnScenarioEdit", "edit"),
        ("btnScenarioDelete", "delete"),
        ("btnScenarioInsert", "insert"),
        ("btnScenarioClose", "close"),
    ]:
        control = dialog.getControl(control_name)
        control.setActionCommand(command)
        control.addActionListener(listener)

    dialog.getControl("lstScenarios").addItemListener(listener)
    dialog.addTopWindowListener(listener)
    _OPEN_SCENARIO_WINDOWS.append({"dialog": dialog, "listener": listener})
    dialog.setVisible(True)


def open_term_editor(parent_listener, entry):
    ctx = _ctx()
    smgr = ctx.ServiceManager
    toolkit = smgr.createInstanceWithContext("com.sun.star.awt.Toolkit", ctx)
    model = smgr.createInstanceWithContext(
        "com.sun.star.awt.UnoControlDialogModel", ctx
    )
    model.PositionX = 105
    model.PositionY = 10
    model.Width = 430
    model.Height = 292
    model.Title = "Éditer un terme utilisateur"

    def add(name, service, x, y, w, h, **props):
        item = model.createInstance(service)
        item.Name = name
        item.PositionX, item.PositionY = x, y
        item.Width, item.Height = w, h
        for key, value in props.items():
            setattr(item, key, value)
        model.insertByName(name, item)

    add("lblTerm", "com.sun.star.awt.UnoControlFixedTextModel",
        8, 8, 44, 10, Label="Terme :")
    add("txtTerm", "com.sun.star.awt.UnoControlEditModel",
        54, 6, 368, 14, Text=entry.get("terme", ""))
    categories = sorted(
        {
            e.get("categorie", "")
            for e in parent_listener.builtin_data + parent_listener.user_data
            if e.get("categorie", "")
        },
        key=_normalize,
    )
    if "Personnalisé" not in categories:
        categories.append("Personnalisé")

    add("lblEnglish", "com.sun.star.awt.UnoControlFixedTextModel",
        8, 28, 44, 10, Label="Anglais :")
    add("txtEnglish", "com.sun.star.awt.UnoControlEditModel",
        54, 26, 156, 14, Text=entry.get("anglais", ""))
    add("lblTermCategory", "com.sun.star.awt.UnoControlFixedTextModel",
        220, 28, 50, 10, Label="Catégorie :")
    add("lstTermCategory", "com.sun.star.awt.UnoControlListBoxModel",
        272, 26, 150, 14,
        Dropdown=True,
        StringItemList=tuple(categories))
    add("lblSynonyms", "com.sun.star.awt.UnoControlFixedTextModel",
        8, 48, 54, 10, Label="Synonymes :")
    add("txtSynonyms", "com.sun.star.awt.UnoControlEditModel",
        64, 46, 358, 14, Text=", ".join(entry.get("synonymes", [])))
    add("lblDefinition", "com.sun.star.awt.UnoControlFixedTextModel",
        8, 68, 54, 10, Label="Définition :")
    add("txtTermDefinition", "com.sun.star.awt.UnoControlEditModel",
        8, 80, 414, 40, MultiLine=True, VScroll=True,
        Text=entry.get("definition", ""))

    add("lblFormulations", "com.sun.star.awt.UnoControlFixedTextModel",
        8, 124, 150, 10, Label="Formulations pour rapport")
    add("lstTermFormulations", "com.sun.star.awt.UnoControlListBoxModel",
        8, 136, 414, 44)
    add("btnTermFormUp", "com.sun.star.awt.UnoControlButtonModel",
        8, 184, 46, 16, Label="Monter")
    add("btnTermFormDown", "com.sun.star.awt.UnoControlButtonModel",
        58, 184, 56, 16, Label="Descendre")
    add("btnTermFormRemove", "com.sun.star.awt.UnoControlButtonModel",
        118, 184, 56, 16, Label="Supprimer")

    add("lblFormText", "com.sun.star.awt.UnoControlFixedTextModel",
        8, 206, 150, 10, Label="Créer une formulation")
    add("txtFormText", "com.sun.star.awt.UnoControlEditModel",
        8, 218, 414, 34, MultiLine=True, VScroll=True)
    add("btnTermFormUpdate", "com.sun.star.awt.UnoControlButtonModel",
        238, 256, 84, 16, Label="Mettre à jour", Enabled=False)
    add("btnTermFormAdd", "com.sun.star.awt.UnoControlButtonModel",
        328, 256, 94, 16, Label="Ajouter")

    add("lblTermEditStatus", "com.sun.star.awt.UnoControlFixedTextModel",
        8, 277, 180, 10, Label="")
    add("btnTermEditCancel", "com.sun.star.awt.UnoControlButtonModel",
        300, 274, 54, 16, Label="Annuler")
    add("btnTermEditSave", "com.sun.star.awt.UnoControlButtonModel",
        360, 274, 62, 16, Label="Enregistrer")

    dialog = smgr.createInstanceWithContext(
        "com.sun.star.awt.UnoControlDialog", ctx
    )
    dialog.setModel(model)
    dialog.createPeer(toolkit, None)

    category_control = dialog.getControl("lstTermCategory")
    current_category = entry.get("categorie", "Personnalisé")
    try:
        category_control.selectItem(current_category, True)
    except Exception:
        if category_control.ItemCount:
            category_control.selectItemPos(0, True)

    listener = TermEditorListener(
        dialog,
        parent_listener,
        entry,
        dialog.getControl("txtTerm"),
        dialog.getControl("txtEnglish"),
        dialog.getControl("lstTermCategory"),
        dialog.getControl("txtSynonyms"),
        dialog.getControl("txtTermDefinition"),
        dialog.getControl("lstTermFormulations"),
        dialog.getControl("txtFormText"),
        dialog.getControl("btnTermFormAdd"),
        dialog.getControl("btnTermFormUpdate"),
        dialog.getControl("lblTermEditStatus"),
    )

    for control_name, command in [
        ("btnTermFormAdd", "add"),
        ("btnTermFormUpdate", "update"),
        ("btnTermFormRemove", "remove"),
        ("btnTermFormUp", "up"),
        ("btnTermFormDown", "down"),
        ("btnTermEditSave", "save"),
        ("btnTermEditCancel", "cancel"),
    ]:
        control = dialog.getControl(control_name)
        control.setActionCommand(command)
        control.addActionListener(listener)

    dialog.getControl("lstTermFormulations").addItemListener(listener)
    dialog.addTopWindowListener(listener)
    _OPEN_TERM_EDITOR_WINDOWS.append({
        "dialog": dialog,
        "listener": listener,
    })
    dialog.setVisible(True)


def open_term_manager(lexicon_listener=None, *args):
    ctx = _ctx()
    smgr = ctx.ServiceManager
    toolkit = smgr.createInstanceWithContext("com.sun.star.awt.Toolkit", ctx)
    model = smgr.createInstanceWithContext(
        "com.sun.star.awt.UnoControlDialogModel", ctx
    )
    model.PositionX = 90
    model.PositionY = 52
    model.Width = 390
    model.Height = 292
    model.Title = "Gestion des termes"

    def add(name, service, x, y, w, h, **props):
        item = model.createInstance(service)
        item.Name = name
        item.PositionX, item.PositionY = x, y
        item.Width, item.Height = w, h
        for key, value in props.items():
            setattr(item, key, value)
        model.insertByName(name, item)

    add("lblManagedTerms", "com.sun.star.awt.UnoControlFixedTextModel",
        8, 8, 142, 10, Label="Termes du lexique")
    add("lstManagedTerms", "com.sun.star.awt.UnoControlListBoxModel",
        8, 20, 142, 232)
    add("txtManagedTermDetail", "com.sun.star.awt.UnoControlEditModel",
        158, 20, 224, 232, MultiLine=True, ReadOnly=True, VScroll=True)
    add("lblManagedTermStatus", "com.sun.star.awt.UnoControlFixedTextModel",
        158, 258, 104, 10, Label="")
    add("btnManagedTermNew", "com.sun.star.awt.UnoControlButtonModel",
        8, 256, 42, 16, Label="Nouveau")
    add("btnManagedTermDuplicate", "com.sun.star.awt.UnoControlButtonModel",
        54, 256, 48, 16, Label="Dupliquer")
    add("btnManagedTermEdit", "com.sun.star.awt.UnoControlButtonModel",
        106, 256, 44, 16, Label="Modifier")
    add("btnManagedTermDelete", "com.sun.star.awt.UnoControlButtonModel",
        8, 276, 48, 14, Label="Supprimer")
    add("btnManagedTermClose", "com.sun.star.awt.UnoControlButtonModel",
        330, 274, 52, 14, Label="Fermer")

    dialog = smgr.createInstanceWithContext(
        "com.sun.star.awt.UnoControlDialog", ctx
    )
    dialog.setModel(model)
    dialog.createPeer(toolkit, None)

    listener = TermManagerListener(
        dialog,
        dialog.getControl("lstManagedTerms"),
        dialog.getControl("txtManagedTermDetail"),
        dialog.getControl("lblManagedTermStatus"),
        _load_builtin_data(),
        _load_user_data(),
        lexicon_listener,
    )
    for control_name, command in [
        ("btnManagedTermNew", "new"),
        ("btnManagedTermDuplicate", "duplicate"),
        ("btnManagedTermEdit", "edit"),
        ("btnManagedTermDelete", "delete"),
        ("btnManagedTermClose", "close"),
    ]:
        control = dialog.getControl(control_name)
        control.setActionCommand(command)
        control.addActionListener(listener)

    dialog.getControl("lstManagedTerms").addItemListener(listener)
    dialog.addTopWindowListener(listener)
    _OPEN_TERM_WINDOWS.append({"dialog": dialog, "listener": listener})
    dialog.setVisible(True)


def open_user_data_transfer(*args):
    ctx = _ctx()
    smgr = ctx.ServiceManager
    toolkit = smgr.createInstanceWithContext("com.sun.star.awt.Toolkit", ctx)
    model = smgr.createInstanceWithContext(
        "com.sun.star.awt.UnoControlDialogModel", ctx
    )
    model.PositionX = 105
    model.PositionY = 12
    model.Width = 340
    model.Height = 300
    model.Title = "Exporter / Importer les données utilisateur"

    def add(name, service, x, y, w, h, **props):
        item = model.createInstance(service)
        item.Name = name
        item.PositionX, item.PositionY = x, y
        item.Width, item.Height = w, h
        for key, value in props.items():
            setattr(item, key, value)
        model.insertByName(name, item)

    add(
        "txtTransferInfo",
        "com.sun.star.awt.UnoControlFixedTextModel",
        10, 10, 320, 38,
        Label=(
            "Sauvegardez ou transférez vos termes, scénarios et occurrences "
            "personnalisés dans un seul fichier JSON."
        ),
        MultiLine=True,
    )
    add("lblExport", "com.sun.star.awt.UnoControlFixedTextModel",
        10, 56, 70, 10, Label="EXPORTER")
    add("btnUserExport", "com.sun.star.awt.UnoControlButtonModel",
        10, 70, 150, 20, Label="Exporter ma base utilisateur")

    add("lblImport", "com.sun.star.awt.UnoControlFixedTextModel",
        10, 102, 70, 10, Label="IMPORTER")
    add(
        "txtImportInfo",
        "com.sun.star.awt.UnoControlFixedTextModel",
        10, 114, 320, 22,
        Label=(
            "Fusionner conserve vos données actuelles. "
            "Remplacer écrase uniquement vos données utilisateur."
        ),
        MultiLine=True,
    )
    add("btnUserImportMerge", "com.sun.star.awt.UnoControlButtonModel",
        10, 140, 150, 20, Label="Importer et fusionner")
    add("btnUserImportReplace", "com.sun.star.awt.UnoControlButtonModel",
        168, 140, 162, 20, Label="Importer et remplacer")
    add("lblProposals", "com.sun.star.awt.UnoControlFixedTextModel",
        10, 168, 310, 10, Label="PROPOSER DES FICHES PERSONNELLES")
    add("lstProposalTerms", "com.sun.star.awt.UnoControlListBoxModel",
        10, 180, 320, 64, MultiSelection=True)
    add("btnProposeSelected", "com.sun.star.awt.UnoControlButtonModel",
        168, 248, 162, 19, Label="Proposer les fiches sélectionnées")
    add("lblTransferStatus", "com.sun.star.awt.UnoControlFixedTextModel",
        10, 276, 258, 12, Label="")
    add("btnTransferClose", "com.sun.star.awt.UnoControlButtonModel",
        278, 274, 52, 16, Label="Fermer")

    dialog = smgr.createInstanceWithContext(
        "com.sun.star.awt.UnoControlDialog", ctx
    )
    dialog.setModel(model)
    dialog.createPeer(toolkit, None)

    listener = DataTransferListener(
        dialog,
        dialog.getControl("lblTransferStatus"),
        dialog.getControl("lstProposalTerms"),
    )
    for control_name, command in [
        ("btnUserExport", "export"),
        ("btnUserImportMerge", "merge"),
        ("btnUserImportReplace", "replace"),
        ("btnProposeSelected", "propose"),
        ("btnTransferClose", "close"),
    ]:
        control = dialog.getControl(control_name)
        control.setActionCommand(command)
        control.addActionListener(listener)

    dialog.addTopWindowListener(listener)
    _OPEN_DATA_TRANSFER_WINDOWS.append({
        "dialog": dialog,
        "listener": listener,
    })
    dialog.setVisible(True)


_HELP_TOPICS = [
    ("Présentation",
     "Lexique forensique FR\\n\\n"
     "Extension LibreOffice Writer consacrée à la terminologie de criminalistique numérique.\\n"
     "Toutes les rubriques de cette aide sont accessibles sans connexion Internet.\\n\\n"
     "Les définitions et formulations sont des aides à la rédaction : elles doivent être adaptées aux constatations."),
    ("Rechercher un terme",
     "Menu Lexique forensique > Rechercher un terme…\\n\\n"
     "Recherchez un terme ou filtrez par catégorie. Consultez sa définition, les synonymes et, "
     "le cas échéant, les formulations pour rapport. Vérifiez leur adéquation avec les faits observés."),
    ("Fiches personnelles",
     "Dans la gestion des termes, créez ou modifiez vos propres fiches.\\n\\n"
     "Une fiche peut comporter un terme, sa traduction, une catégorie, une définition, "
     "des synonymes et plusieurs formulations pour rapport.\\n\\n"
     "Les fiches personnelles sont conservées dans votre profil utilisateur."),
    ("Formulations et scénarios",
     "Les formulations pour rapport correspondent à des situations distinctes. "
     "Sélectionnez une formulation pertinente avant de l'insérer dans Writer.\\n\\n"
     "Les scénarios assemblent plusieurs formulations et peuvent être personnalisés."),
    ("Vérifier le document",
     "La vérification du document permet de repérer les libellés anglais "
     "et les termes déconseillés, puis de proposer leur remplacement.\\n\\n"
     "Lisez toujours le contexte avant de remplacer une occurrence."),
    ("Exporter / Importer",
     "Menu Lexique forensique > Exporter / Importer…\\n\\n"
     "Exporter enregistre vos termes, scénarios et occurrences personnels dans un fichier JSON.\\n"
     "Importer et fusionner préserve les données locales et ajoute les éléments absents.\\n"
     "Importer et remplacer substitue les données personnelles après une sauvegarde."),
    ("Proposer des fiches",
     "Menu Lexique forensique > Exporter / Importer…\\n\\n"
     "Sélectionnez une ou plusieurs fiches personnelles dans la liste (Ctrl ou Maj selon le système), "
     "puis cliquez sur « Proposer les fiches sélectionnées ».\\n\\n"
     "Cette fonction ouvre GitHub dans le navigateur et nécessite Internet et un compte GitHub. "
     "Vous choisissez vous-même de publier ou non. Les propositions publiées sont publiques : "
     "retirez toute donnée confidentielle ou propre à une procédure.\\n\\n"
     "L'aide reste disponible hors ligne, mais l'envoi de propositions nécessite une connexion."),
    ("Mises à jour",
     "Menu Lexique forensique > Mettre à jour…\\n\\n"
     "La recherche et l'installation d'une nouvelle version nécessitent Internet. "
     "Vos fiches et règles personnelles restent dans votre profil et ne sont pas effacées "
     "par la mise à jour normale de l'extension."),
]

_OPEN_HELP_WINDOWS = []


class HelpDialogListener(unohelper.Base, XActionListener, XItemListener, XTopWindowListener):
    def __init__(self, dialog, topics, detail):
        self.dialog = dialog
        self.topics = topics
        self.detail = detail
        self._closing = False
        self.itemStateChanged(None)

    def itemStateChanged(self, event):
        index = self.topics.SelectedItemPos
        if 0 <= index < len(_HELP_TOPICS):
            self.detail.Text = _HELP_TOPICS[index][0] + "\\n\\n" + _HELP_TOPICS[index][1]

    def actionPerformed(self, event):
        if event.ActionCommand == "close":
            self._close_dialog()

    def _close_dialog(self):
        if self._closing:
            return
        self._closing = True
        try:
            try:
                self.dialog.removeTopWindowListener(self)
            except Exception:
                pass
            self.dialog.setVisible(False)
            self.dialog.dispose()
        finally:
            _OPEN_HELP_WINDOWS[:] = [
                entry for entry in _OPEN_HELP_WINDOWS if entry["dialog"] is not self.dialog
            ]

    def windowClosing(self, event):
        self._close_dialog()

    def windowOpened(self, event):
        pass

    def windowClosed(self, event):
        pass

    def windowMinimized(self, event):
        pass

    def windowNormalized(self, event):
        pass

    def windowActivated(self, event):
        pass

    def windowDeactivated(self, event):
        pass


def show_help(*args):
    """Afficher une aide embarquée, sans requête réseau."""
    for entry in _OPEN_HELP_WINDOWS:
        try:
            entry["dialog"].toFront()
            return
        except Exception:
            pass
    ctx = _ctx()
    smgr = ctx.ServiceManager
    toolkit = smgr.createInstanceWithContext("com.sun.star.awt.Toolkit", ctx)
    model = smgr.createInstanceWithContext("com.sun.star.awt.UnoControlDialogModel", ctx)
    model.PositionX = 50
    model.PositionY = 12
    model.Width = 390
    model.Height = 248
    model.Title = "Aide — Lexique forensique FR"

    def add(name, service, x, y, w, h, **props):
        item = model.createInstance(service)
        item.Name = name
        item.PositionX, item.PositionY = x, y
        item.Width, item.Height = w, h
        for key, value in props.items():
            setattr(item, key, value)
        model.insertByName(name, item)

    add("lblHelpTopics", "com.sun.star.awt.UnoControlFixedTextModel",
        8, 8, 120, 12, Label="Rubriques")
    add("lstHelpTopics", "com.sun.star.awt.UnoControlListBoxModel",
        8, 24, 118, 188, StringItemList=tuple(name for name, _ in _HELP_TOPICS))
    add("txtHelpDetail", "com.sun.star.awt.UnoControlEditModel",
        134, 24, 248, 188, ReadOnly=True, MultiLine=True, VScroll=True)
    add("btnHelpClose", "com.sun.star.awt.UnoControlButtonModel",
        320, 222, 62, 18, Label="Fermer")

    dialog = smgr.createInstanceWithContext("com.sun.star.awt.UnoControlDialog", ctx)
    dialog.setModel(model)
    dialog.createPeer(toolkit, None)
    topics = dialog.getControl("lstHelpTopics")
    detail = dialog.getControl("txtHelpDetail")
    topics.selectItemPos(0, True)
    listener = HelpDialogListener(dialog, topics, detail)
    topics.addItemListener(listener)
    close = dialog.getControl("btnHelpClose")
    close.setActionCommand("close")
    close.addActionListener(listener)
    dialog.addTopWindowListener(listener)
    _OPEN_HELP_WINDOWS.append({"dialog": dialog, "listener": listener})
    dialog.setVisible(True)


def show_about(*args):
    ctx = _ctx()
    smgr = ctx.ServiceManager
    toolkit = smgr.createInstanceWithContext("com.sun.star.awt.Toolkit", ctx)
    model = smgr.createInstanceWithContext(
        "com.sun.star.awt.UnoControlDialogModel", ctx
    )
    model.PositionX = 95
    model.PositionY = 65
    model.Width = 250
    model.Height = 118
    model.Title = "À propos de Lexique forensique FR"

    def add(name, service, x, y, w, h, **props):
        item = model.createInstance(service)
        item.Name = name
        item.PositionX, item.PositionY = x, y
        item.Width, item.Height = w, h
        for key, value in props.items():
            setattr(item, key, value)
        model.insertByName(name, item)

    logo_path = os.path.join(_extension_root(), "images", "logo.png")
    logo_url = uno.systemPathToFileUrl(logo_path)
    add(
        "imgAboutLogo",
        "com.sun.star.awt.UnoControlImageControlModel",
        10, 10, 42, 42,
        ImageURL=logo_url,
        ScaleImage=True,
        Border=0,
    )
    add(
        "txtAbout",
        "com.sun.star.awt.UnoControlFixedTextModel",
        60, 10, 180, 54,
        Label=(
            "Lexique forensique FR\n"
            f"Version {CURRENT_VERSION}\n"
            "Auteur : Jérémy MARANDE\n"
            "Lexique français de criminalistique numérique"
        ),
        MultiLine=True,
    )
    add(
        "btnGitHub",
        "com.sun.star.awt.UnoControlButtonModel",
        10, 84, 62, 16,
        Label="GitHub",
    )
    add(
        "btnClose",
        "com.sun.star.awt.UnoControlButtonModel",
        188, 84, 52, 16,
        Label="Fermer",
    )

    dialog = smgr.createInstanceWithContext(
        "com.sun.star.awt.UnoControlDialog", ctx
    )
    dialog.setModel(model)
    dialog.createPeer(toolkit, None)

    listener = AboutListener(dialog)
    dialog.addTopWindowListener(listener)
    for control_name, command in [
        ("btnGitHub", "github"),
        ("btnClose", "close"),
    ]:
        control = dialog.getControl(control_name)
        control.setActionCommand(command)
        control.addActionListener(listener)

    _OPEN_ABOUT_WINDOWS.append({
        "dialog": dialog,
        "listener": listener,
    })
    dialog.setVisible(True)



def _release_notes_text(release):
    body = (release.get("body") or "").strip()
    if not body:
        return "Aucune note de version fournie."
    body = body.replace("\r\n", "\n").replace("\r", "\n")
    lines = []
    for raw in body.split("\n"):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("##"):
            line = line.lstrip("#").strip()
        if line.startswith("- "):
            line = "• " + line[2:].strip()
        lines.append(line)
    text = "\n".join(lines)
    if len(text) > 1200:
        text = text[:1197].rstrip() + "..."
    return text or "Aucune note de version fournie."


def _download_update(download_url, expected_sha256):
    update_dir = tempfile.mkdtemp(prefix="lexique-forensique-fr-")
    target = os.path.join(update_dir, UPDATE_ASSET_NAME)

    urls = [download_url]
    if expected_sha256:
        separator = "&" if "?" in download_url else "?"
        urls.append(
            download_url
            + separator
            + "lexique_sha256="
            + expected_sha256[:12]
        )

    last_digest = ""
    for url in urls:
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Lexique-forensique-FR-LibreOffice",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
            },
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            data = response.read()

        last_digest = hashlib.sha256(data).hexdigest().lower()
        if not expected_sha256 or last_digest == expected_sha256.lower():
            with open(target, "wb") as f:
                f.write(data)
            return target

    raise RuntimeError(
        "L'empreinte SHA-256 de la mise à jour ne correspond pas "
        "(téléchargement possiblement mis en cache par GitHub)."
    )


def check_updates(*args):
    try:
        request = urllib.request.Request(
            GITHUB_LATEST_RELEASE_API,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "Lexique-forensique-FR-LibreOffice",
            },
        )
        with urllib.request.urlopen(request, timeout=8) as response:
            release = json.loads(response.read().decode("utf-8"))

        latest = release.get("tag_name", "")
        if not latest:
            raise RuntimeError("La dernière release GitHub ne fournit pas de version.")

        if _version_tuple(latest) <= _version_tuple(CURRENT_VERSION):
            _message_box(
                "Lexique forensique FR",
                f"La version {CURRENT_VERSION} est à jour.",
            )
            return

        asset = None
        for item in release.get("assets", []):
            if item.get("name") == UPDATE_ASSET_NAME:
                asset = item
                break

        if not asset:
            raise RuntimeError(
                f"Le fichier {UPDATE_ASSET_NAME} est absent de la release {latest}."
            )

        download_url = asset.get("browser_download_url", "")
        if not download_url:
            raise RuntimeError("URL de téléchargement de la mise à jour introuvable.")

        expected_sha256 = ""
        digest = asset.get("digest") or ""
        if digest.lower().startswith("sha256:"):
            expected_sha256 = digest.split(":", 1)[1].strip()

        release_notes = _release_notes_text(release)
        _message_box(
            "Mise à jour disponible",
            (
                f"Version installée : {CURRENT_VERSION}\n"
                f"Dernière version : {latest}\n\n"
                "NOUVEAUTÉS\n"
                f"{release_notes}\n\n"
                "La nouvelle extension va être téléchargée."
            ),
        )

        package_path = _download_update(download_url, expected_sha256)
        _open_url(uno.systemPathToFileUrl(package_path))

    except Exception as exc:
        _message_box(
            "Mise à jour",
            (
                "Impossible d'effectuer la mise à jour automatique.\n\n"
                f"Détail : {exc}\n\n"
                "Aucune page web ne sera ouverte automatiquement."
            ),
        )


def open_lexicon(*args):
    ctx = _ctx()
    smgr = ctx.ServiceManager
    toolkit = smgr.createInstanceWithContext("com.sun.star.awt.Toolkit", ctx)
    model = smgr.createInstanceWithContext(
        "com.sun.star.awt.UnoControlDialogModel", ctx
    )

    model.PositionX = 70
    model.PositionY = 45
    model.Width = 310
    model.Height = 334
    model.Title = f"Lexique forensique FR — v{CURRENT_VERSION}"

    data = _load_data()
    categories = sorted(
        {e.get("categorie", "") for e in data if e.get("categorie", "")},
        key=_normalize,
    )

    def add(name, service, x, y, w, h, **props):
        item = model.createInstance(service)
        item.Name = name
        item.PositionX = x
        item.PositionY = y
        item.Width = w
        item.Height = h
        for key, value in props.items():
            setattr(item, key, value)
        model.insertByName(name, item)

    add(
        "lblSearch",
        "com.sun.star.awt.UnoControlFixedTextModel",
        8, 8, 44, 12,
        Label="Recherche :",
    )
    add(
        "txtSearch",
        "com.sun.star.awt.UnoControlEditModel",
        52, 6, 178, 14,
    )
    add(
        "btnSearch",
        "com.sun.star.awt.UnoControlButtonModel",
        234, 6, 68, 14,
        Label="Rechercher",
    )
    add(
        "btnVerify",
        "com.sun.star.awt.UnoControlButtonModel",
        8, 174, 105, 16,
        Label="Vérifier le document",
    )
    add(
        "btnScenarios",
        "com.sun.star.awt.UnoControlButtonModel",
        8, 194, 105, 16,
        Label="Scénarios",
    )
    add(
        "btnManageTerms",
        "com.sun.star.awt.UnoControlButtonModel",
        8, 214, 105, 16,
        Label="Gérer les termes",
    )
    add(
        "lblCategory",
        "com.sun.star.awt.UnoControlFixedTextModel",
        8, 27, 42, 10,
        Label="Catégorie :",
    )
    add(
        "cmbCategory",
        "com.sun.star.awt.UnoControlComboBoxModel",
        50, 25, 104, 14,
        Dropdown=True,
        StringItemList=tuple(["Toutes"] + categories),
        Text="Toutes",
    )
    add(
        "lblStatus",
        "com.sun.star.awt.UnoControlFixedTextModel",
        160, 27, 142, 10,
        Label="",
    )
    add(
        "lblLexique",
        "com.sun.star.awt.UnoControlFixedTextModel",
        8, 44, 105, 10,
        Label="Lexique",
    )
    add(
        "lstResults",
        "com.sun.star.awt.UnoControlListBoxModel",
        8, 56, 105, 112,
    )
    add(
        "txtDetail",
        "com.sun.star.awt.UnoControlEditModel",
        118, 46, 184, 236,
        MultiLine=True,
        ReadOnly=True,
        VScroll=True,
        HideInactiveSelection=False,
    )
    add(
        "btnInsert",
        "com.sun.star.awt.UnoControlButtonModel",
        214, 288, 88, 16,
        Label="Insérer formule",
    )
    add(
        "btnClose",
        "com.sun.star.awt.UnoControlButtonModel",
        258, 314, 44, 16,
        Label="Fermer",
    )

    dialog = smgr.createInstanceWithContext(
        "com.sun.star.awt.UnoControlDialog", ctx
    )
    dialog.setModel(model)
    dialog.createPeer(toolkit, None)

    search_box = dialog.getControl("txtSearch")
    results_box = dialog.getControl("lstResults")
    detail_box = dialog.getControl("txtDetail")
    status_label = dialog.getControl("lblStatus")
    insert_button = dialog.getControl("btnInsert")
    category_box = dialog.getControl("cmbCategory")
    listener = DialogListener(
        dialog,
        search_box,
        results_box,
        detail_box,
        status_label,
        insert_button,
        category_box,
        data,
    )

    for control, command in [
        (dialog.getControl("btnSearch"), "search"),
        (dialog.getControl("btnVerify"), "verify"),
        (dialog.getControl("btnScenarios"), "scenarios"),
        (dialog.getControl("btnManageTerms"), "manage_terms"),
        (insert_button, "insert"),
        (dialog.getControl("btnClose"), "close"),
    ]:
        control.setActionCommand(command)
        control.addActionListener(listener)

    results_box.addItemListener(listener)
    category_box.addItemListener(listener)
    detail_box.addMouseListener(listener)
    dialog.addTopWindowListener(listener)

    _OPEN_LEXICON_WINDOWS.append({
        "dialog": dialog,
        "listener": listener,
    })
    dialog.setVisible(True)


g_exportedScripts = (
    open_lexicon,
    open_verification,
    open_scenarios,
    open_term_manager,
    open_user_data_transfer,
    show_about,
    check_updates,
)
