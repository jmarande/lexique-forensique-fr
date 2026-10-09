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
_OPEN_ABOUT_WINDOWS = []

CURRENT_VERSION = "0.7.16"
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


def _load_data():
    path = os.path.join(_extension_root(), "data", "lexique.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_scenarios():
    path = os.path.join(_extension_root(), "data", "scenarios.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


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
    def __init__(self, dialog, scenarios_box, detail_box, status_label, data, scenarios):
        self.dialog = dialog
        self.scenarios_box = scenarios_box
        self.detail_box = detail_box
        self.status_label = status_label
        self.data = data
        self.scenarios = scenarios
        self.current = None
        self._populate()

    def _populate(self):
        for scenario in self.scenarios:
            self.scenarios_box.addItem(
                scenario.get("titre", "Scénario"),
                self.scenarios_box.ItemCount,
            )
        if self.scenarios:
            self.scenarios_box.selectItemPos(0, True)
            self._show(0)

    def _show(self, index):
        if not (0 <= index < len(self.scenarios)):
            return
        scenario = self.scenarios[index]
        self.current = scenario
        steps = _scenario_steps(scenario, self.data)
        parts = [
            scenario.get("titre", "Scénario"),
            f"Catégorie : {scenario.get('categorie', '—')}",
            "",
            scenario.get("description", ""),
            "",
            "PHRASES INSÉRÉES",
        ]
        if steps:
            for number, step in enumerate(steps, start=1):
                parts.append("")
                parts.append(f"{number}. {step['terme']} — {step['formulation']}")
                parts.append(step["texte"])
        else:
            parts.append("")
            parts.append("Aucune formulation valide dans ce scénario.")
        self.detail_box.Text = "\n".join(parts)
        self.status_label.getModel().Label = (
            f"{len(steps)} phrase" if len(steps) == 1 else f"{len(steps)} phrases"
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

    def actionPerformed(self, event):
        if event.ActionCommand == "insert":
            self.insert_current()
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


def open_scenarios(*args):
    ctx = _ctx()
    smgr = ctx.ServiceManager
    toolkit = smgr.createInstanceWithContext("com.sun.star.awt.Toolkit", ctx)
    model = smgr.createInstanceWithContext(
        "com.sun.star.awt.UnoControlDialogModel", ctx
    )
    model.PositionX = 90
    model.PositionY = 55
    model.Width = 330
    model.Height = 270
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
        8, 8, 116, 10, Label="Scénarios")
    add("lstScenarios", "com.sun.star.awt.UnoControlListBoxModel",
        8, 20, 116, 210)
    add("txtScenarioDetail", "com.sun.star.awt.UnoControlEditModel",
        130, 20, 192, 210, MultiLine=True, ReadOnly=True, VScroll=True)
    add("lblScenarioStatus", "com.sun.star.awt.UnoControlFixedTextModel",
        130, 234, 90, 10, Label="")
    add("btnScenarioInsert", "com.sun.star.awt.UnoControlButtonModel",
        224, 232, 98, 16, Label="Insérer le scénario")
    add("btnScenarioClose", "com.sun.star.awt.UnoControlButtonModel",
        270, 252, 52, 14, Label="Fermer")

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
    )
    for control_name, command in [
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
    request = urllib.request.Request(
        download_url,
        headers={"User-Agent": "Lexique-forensique-FR-LibreOffice"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read()

    digest = hashlib.sha256(data).hexdigest().lower()
    if expected_sha256 and digest != expected_sha256.lower():
        raise RuntimeError("L'empreinte SHA-256 de la mise à jour ne correspond pas.")

    with open(target, "wb") as f:
        f.write(data)

    return target


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
    model.Title = "Lexique forensique FR — v0.7.16"

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
    show_about,
    check_updates,
)
