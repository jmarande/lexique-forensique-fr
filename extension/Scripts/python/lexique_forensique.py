# -*- coding: utf-8 -*-
import json
import os
import re
import unicodedata
import urllib.request
import hashlib
import tempfile

import uno
import unohelper

from com.sun.star.awt import XActionListener, XItemListener, XMouseListener, XTopWindowListener

_OPEN_LEXICON_WINDOWS = []
_OPEN_VERIFY_WINDOWS = []
_OPEN_SCENARIO_WINDOWS = []
_OPEN_SCENARIO_EDITOR_WINDOWS = []
_OPEN_TERM_WINDOWS = []
_OPEN_TERM_EDITOR_WINDOWS = []
_OPEN_ABOUT_WINDOWS = []

CURRENT_VERSION = "0.7.20"
GITHUB_URL = "https://github.com/jmarande/lexique-forensique-fr"
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


def _scan_document_text(text, data):
    normalized_text = _normalize(text)
    alerts = []

    for entry in data:
        for bad in _bad_terms(entry):
            normalized_bad = _normalize(bad)
            if not normalized_bad:
                continue

            pattern = r"(?<!\w)" + re.escape(normalized_bad) + r"(?!\w)"
            count = len(re.findall(pattern, normalized_text))
            if count:
                alerts.append({
                    "entry": entry,
                    "found": bad,
                    "count": count,
                })

    return sorted(
        alerts,
        key=lambda item: (
            _normalize(item["entry"].get("terme", "")),
            _normalize(item["found"]),
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
    def __init__(self, dialog, alerts_box, detail_box, status_label, replace_button, data):
        self.dialog = dialog
        self.alerts_box = alerts_box
        self.detail_box = detail_box
        self.status_label = status_label
        self.replace_button = replace_button
        self.data = data
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
        self.alerts = _scan_document_text(doc.Text.String, self.data)
        self._clear_alerts()

        for alert in self.alerts:
            self.alerts_box.addItem(
                f"{alert['found']} → {alert['entry']['terme']} ({alert['count']})",
                self.alerts_box.ItemCount,
            )

        total = sum(alert["count"] for alert in self.alerts)
        if self.alerts:
            self.status_label.getModel().Label = (
                f"{total} occurrence" if total == 1
                else f"{total} occurrences terminologiques"
            )
            self.alerts_box.selectItemPos(0, True)
            self._show_alert(self.alerts[0])
        else:
            self.detail_box.Text = (
                "Aucune alerte terminologique détectée dans le document actif."
            )
            self.status_label.getModel().Label = "Aucune alerte terminologique"

    def replace_current(self):
        if not self.current_alert or not self.current_found_range:
            return
        replacement = self.current_alert["entry"]["terme"]
        self.current_found_range.String = replacement
        self.current_found_range = None
        self.scan()

    def actionPerformed(self, event):
        if event.ActionCommand == "rescan":
            self.scan()
        elif event.ActionCommand == "replace":
            self.replace_current()
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
            self.add_button.getModel().Label = "Ajouter"
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
        self.add_button.getModel().Label = "Mettre à jour"

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

        index = self._selected_formulation_index()
        if index >= 0 and self.add_button.getModel().Label == "Mettre à jour":
            label = self.formulations[index].get("type") or "Formulation"
            self.formulations[index] = {
                "type": label,
                "texte": current_text,
            }
            self._populate_formulations(index)
            self.status_label.getModel().Label = "Formulation mise à jour"
            return

        self.formulations.append({
            "type": "Formulation",
            "texte": current_text,
        })
        self._populate_formulations(len(self.formulations) - 1)
        self.formulation_text_box.Text = ""
        self.add_button.getModel().Label = "Ajouter"
        self.status_label.getModel().Label = "Formulation ajoutée"

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
        index = self._selected_formulation_index()
        current_text = (self.formulation_text_box.Text or "").strip()
        if index >= 0:
            self._commit_current_formulation()
        elif current_text:
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
        8, 8, 104, 10, Label="Alertes détectées")
    add("lstVerifyAlerts", "com.sun.star.awt.UnoControlListBoxModel",
        8, 20, 104, 164)
    add("txtVerifyDetail", "com.sun.star.awt.UnoControlEditModel",
        118, 20, 174, 164, MultiLine=True, ReadOnly=True, VScroll=True)
    add("lblVerifyStatus", "com.sun.star.awt.UnoControlFixedTextModel",
        8, 190, 284, 10, Label="")
    add("btnVerifyReplace", "com.sun.star.awt.UnoControlButtonModel",
        8, 208, 104, 16, Label="Remplacer occurrence", Enabled=False)
    add("btnVerifyRescan", "com.sun.star.awt.UnoControlButtonModel",
        118, 208, 78, 16, Label="Revérifier")
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
    )
    for control_name, command in [
        ("btnVerifyReplace", "replace"),
        ("btnVerifyRescan", "rescan"),
        ("btnVerifyClose", "close"),
    ]:
        control = dialog.getControl(control_name)
        control.setActionCommand(command)
        control.addActionListener(listener)

    dialog.getControl("lstVerifyAlerts").addItemListener(listener)
    dialog.addTopWindowListener(listener)
    _OPEN_VERIFY_WINDOWS.append({"dialog": dialog, "listener": listener})
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
    model.PositionY = 55
    model.Width = 430
    model.Height = 372
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
        8, 80, 414, 60, MultiLine=True, VScroll=True,
        Text=entry.get("definition", ""))

    add("lblFormulations", "com.sun.star.awt.UnoControlFixedTextModel",
        8, 148, 150, 10, Label="Formulations pour rapport")
    add("lstTermFormulations", "com.sun.star.awt.UnoControlListBoxModel",
        8, 160, 414, 72)
    add("btnTermFormUp", "com.sun.star.awt.UnoControlButtonModel",
        8, 236, 46, 16, Label="Monter")
    add("btnTermFormDown", "com.sun.star.awt.UnoControlButtonModel",
        58, 236, 56, 16, Label="Descendre")
    add("btnTermFormRemove", "com.sun.star.awt.UnoControlButtonModel",
        118, 236, 56, 16, Label="Supprimer")

    add("lblFormText", "com.sun.star.awt.UnoControlFixedTextModel",
        8, 262, 150, 10, Label="Créer une formulation")
    add("txtFormText", "com.sun.star.awt.UnoControlEditModel",
        8, 274, 414, 50, MultiLine=True, VScroll=True)
    add("btnTermFormAdd", "com.sun.star.awt.UnoControlButtonModel",
        300, 328, 122, 16, Label="Ajouter")

    add("lblTermEditStatus", "com.sun.star.awt.UnoControlFixedTextModel",
        8, 350, 180, 10, Label="")
    add("btnTermEditCancel", "com.sun.star.awt.UnoControlButtonModel",
        300, 346, 54, 18, Label="Annuler")
    add("btnTermEditSave", "com.sun.star.awt.UnoControlButtonModel",
        360, 346, 62, 18, Label="Enregistrer")

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
        dialog.getControl("lblTermEditStatus"),
    )

    for control_name, command in [
        ("btnTermFormAdd", "add"),
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


def show_about(*args):
    ctx = _ctx()
    smgr = ctx.ServiceManager
    toolkit = smgr.createInstanceWithContext("com.sun.star.awt.Toolkit", ctx)
    model = smgr.createInstanceWithContext(
        "com.sun.star.awt.UnoControlDialogModel", ctx
    )
    model.PositionX = 95
    model.PositionY = 65
    model.Width = 220
    model.Height = 102
    model.Title = "À propos de Lexique forensique FR"

    def add(name, service, x, y, w, h, **props):
        item = model.createInstance(service)
        item.Name = name
        item.PositionX, item.PositionY = x, y
        item.Width, item.Height = w, h
        for key, value in props.items():
            setattr(item, key, value)
        model.insertByName(name, item)

    add(
        "txtAbout",
        "com.sun.star.awt.UnoControlFixedTextModel",
        10, 10, 200, 42,
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
        10, 62, 62, 16,
        Label="GitHub",
    )
    add(
        "btnClose",
        "com.sun.star.awt.UnoControlButtonModel",
        158, 62, 52, 16,
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
    show_about,
    check_updates,
)
