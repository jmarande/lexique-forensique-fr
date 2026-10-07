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

from com.sun.star.awt import XActionListener, XItemListener, XTopWindowListener

_OPEN_LEXICON_WINDOWS = []
_OPEN_ABOUT_WINDOWS = []

CURRENT_VERSION = "0.7.1"
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


def _bad_terms(entry):
    return entry.get("termes_deconseilles", entry.get("deconseilles", []))


def _report_formulations(entry):
    values = entry.get("formulations_rapport")
    if isinstance(values, list):
        result = []
        for item in values:
            if isinstance(item, dict):
                text = item.get("texte", "").strip()
                label = item.get("type", "").strip()
                if text:
                    result.append((label, text))
            elif isinstance(item, str) and item.strip():
                result.append(("", item.strip()))
        if result:
            return result

    legacy = entry.get("exemple_rapport", entry.get("rapport", "")).strip()
    return [("", legacy)] if legacy else []


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

    lines = [
        prefix + e["terme"],
        f"Anglais : {e.get('anglais', '—')}",
        f"Catégorie : {e.get('categorie', '—')}",
    ]

    if e.get("editeur"):
        lines.append(f"Éditeur : {e['editeur']}")
    if e.get("plateformes"):
        values = e["plateformes"]
        lines.append(
            "Plateformes : "
            + (", ".join(values) if isinstance(values, list) else str(values))
        )

    lines.extend([
        f"Synonymes : {syn}",
        f"Termes déconseillés : {bad}",
        f"Sources : {_sources(e)}",
        "",
        "DÉFINITION",
        e.get("definition", ""),
    ])

    if e.get("donnees_potentielles"):
        lines.extend([
            "",
            "DONNÉES POTENTIELLEMENT RENCONTRÉES",
            " • " + "\n • ".join(e["donnees_potentielles"]),
        ])

    if e.get("points_attention"):
        lines.extend([
            "",
            "POINTS D’ATTENTION",
            " • " + "\n • ".join(e["points_attention"]),
        ])

    return "\n".join(lines)


def _find_entries(query, data):
    q = _normalize(query)
    if not q:
        results = list(data)
    else:
        results = []
        for e in data:
            fields = [
                e.get("terme", ""),
                e.get("anglais", ""),
                e.get("categorie", ""),
                e.get("definition", ""),
                " ".join(e.get("synonymes", [])),
                " ".join(_bad_terms(e)),
            ]
            if q in _normalize(" ".join(fields)):
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


class DialogListener(unohelper.Base, XActionListener, XItemListener, XTopWindowListener):
    def __init__(
        self,
        dialog,
        search_box,
        results_box,
        alerts_box,
        detail_box,
        formulations_box,
        status_label,
        insert_button,
        replace_button,
        data,
    ):
        self.dialog = dialog
        self.search_box = search_box
        self.results_box = results_box
        self.alerts_box = alerts_box
        self.detail_box = detail_box
        self.formulations_box = formulations_box
        self.status_label = status_label
        self.insert_button = insert_button
        self.replace_button = replace_button
        self.data = data
        self.current = None
        self.matches = []
        self.scan_alerts = []
        self.current_alert = None
        self.current_found_range = None
        self.current_formulations = []
        self.refresh()

    def _set_insert_enabled(self, enabled):
        self.insert_button.getModel().Enabled = enabled

    def _set_replace_enabled(self, enabled):
        self.replace_button.getModel().Enabled = enabled

    def _clear_results(self):
        if self.results_box.ItemCount:
            self.results_box.removeItems(0, self.results_box.ItemCount)

    def _clear_alerts(self):
        if self.alerts_box.ItemCount:
            self.alerts_box.removeItems(0, self.alerts_box.ItemCount)

    def _refresh_formulations(self, entry):
        if self.formulations_box.ItemCount:
            self.formulations_box.removeItems(0, self.formulations_box.ItemCount)

        formulations = _report_formulations(entry)
        self.current_formulations = formulations

        for label, text in formulations:
            display = f"{label.capitalize()} — {text}" if label else text
            self.formulations_box.addItem(display, self.formulations_box.ItemCount)

        if formulations:
            self.formulations_box.selectItemPos(0, True)
            self._set_insert_enabled(True)
        else:
            self._set_insert_enabled(False)

    def _show_search_entry(self, entry):
        self.current = entry
        self.current_alert = None
        self.current_found_range = None
        self.detail_box.Text = _format_entry(entry)
        self._refresh_formulations(entry)
        self._set_replace_enabled(False)

    def _goto_alert_occurrence(self, alert):
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
                f"Occurrence sélectionnée : {alert['found']} → "
                f"{alert['entry']['terme']}"
            )
        else:
            self._set_replace_enabled(False)
            self.status_label.getModel().Label = (
                "Occurrence introuvable dans le document actif"
            )

    def _show_scan_alert(self, alert):
        self.current = alert["entry"]
        self.current_alert = alert
        self.detail_box.Text = _format_entry(self.current, warning=alert)
        self._refresh_formulations(self.current)
        self._goto_alert_occurrence(alert)

    def _replace_current_occurrence(self):
        if not self.current_alert or not self.current_found_range:
            self.status_label.getModel().Label = "Aucune occurrence sélectionnée"
            return

        replacement = self.current_alert["entry"]["terme"]
        self.current_found_range.String = replacement
        self.current_found_range = None
        self.status_label.getModel().Label = (
            f"Occurrence remplacée par : {replacement}"
        )
        self.scan_document()

    def refresh(self):
        self.matches = _find_entries(self.search_box.Text, self.data)

        self._clear_results()

        for entry in self.matches:
            self.results_box.addItem(entry["terme"], self.results_box.ItemCount)

        count = len(self.matches)
        self.status_label.getModel().Label = (
            f"{count} résultat" if count == 1 else f"{count} résultats"
        )

        if self.matches:
            self.results_box.selectItemPos(0, True)
            self._show_search_entry(self.matches[0])
        else:
            self.current = None
            self.detail_box.Text = "Aucun terme trouvé."
            self._set_insert_enabled(False)

    def scan_document(self):
        doc = _desktop().getCurrentComponent()
        if not doc or not doc.supportsService("com.sun.star.text.TextDocument"):
            self.status_label.getModel().Label = "Aucun document Writer actif"
            return

        self.current_alert = None
        self.current_found_range = None
        self._set_replace_enabled(False)
        self.scan_alerts = _scan_document_text(doc.Text.String, self.data)
        self._clear_alerts()

        for alert in self.scan_alerts:
            label = (
                f"{alert['found']} → {alert['entry']['terme']} "
                f"({alert['count']})"
            )
            self.alerts_box.addItem(label, self.alerts_box.ItemCount)

        total = sum(alert["count"] for alert in self.scan_alerts)

        if self.scan_alerts:
            self.status_label.getModel().Label = (
                f"{total} occurrence"
                if total == 1
                else f"{total} occurrences terminologiques"
            )
            self.alerts_box.selectItemPos(0, True)
            self._show_scan_alert(self.scan_alerts[0])
        else:
            self.current_alert = None
            self.current_found_range = None
            self.status_label.getModel().Label = "Aucune alerte terminologique"
            self._set_replace_enabled(False)

    def actionPerformed(self, event):
        cmd = event.ActionCommand

        if cmd == "search":
            self.refresh()

        elif cmd == "scan":
            self.scan_document()

        elif cmd == "replace":
            self._replace_current_occurrence()

        elif cmd == "insert" and self.current:
            pos = self.formulations_box.SelectedItemPos
            if 0 <= pos < len(self.current_formulations):
                text_to_insert = self.current_formulations[pos][1]
            else:
                text_to_insert = self.current["terme"]

            doc = _desktop().getCurrentComponent()
            if doc and doc.supportsService("com.sun.star.text.TextDocument"):
                view = doc.getCurrentController().getViewCursor()
                view.getText().insertString(
                    view,
                    text_to_insert,
                    False,
                )
                self.status_label.getModel().Label = (
                    "Formulation sélectionnée insérée dans le document"
                )

        elif cmd == "close":
            self._close_dialog()

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

    def itemStateChanged(self, event):
        if event.Source is self.formulations_box:
            pos = self.formulations_box.SelectedItemPos
            self._set_insert_enabled(
                0 <= pos < len(self.current_formulations)
            )
        elif event.Source is self.alerts_box:
            pos = self.alerts_box.SelectedItemPos
            if 0 <= pos < len(self.scan_alerts):
                self._show_scan_alert(self.scan_alerts[pos])
        else:
            pos = self.results_box.SelectedItemPos
            if 0 <= pos < len(self.matches):
                self._show_search_entry(self.matches[pos])

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

        _message_box(
            "Mise à jour disponible",
            (
                f"Version installée : {CURRENT_VERSION}\n"
                f"Dernière version : {latest}\n\n"
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
    model.Height = 286
    model.Title = "Lexique forensique FR — v0.7.1"

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
        "btnScan",
        "com.sun.star.awt.UnoControlButtonModel",
        8, 174, 105, 16,
        Label="Vérifier document",
    )
    add(
        "lblStatus",
        "com.sun.star.awt.UnoControlFixedTextModel",
        104, 27, 198, 10,
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
        "lblAlerts",
        "com.sun.star.awt.UnoControlFixedTextModel",
        8, 192, 105, 10,
        Label="Alertes du document",
    )
    add(
        "lstAlerts",
        "com.sun.star.awt.UnoControlListBoxModel",
        8, 204, 105, 32,
    )
    add(
        "txtDetail",
        "com.sun.star.awt.UnoControlEditModel",
        118, 46, 184, 126,
        MultiLine=True,
        ReadOnly=True,
        VScroll=True,
    )
    add(
        "lblFormulations",
        "com.sun.star.awt.UnoControlFixedTextModel",
        118, 178, 184, 10,
        Label="FORMULATIONS POUR RAPPORT",
    )
    add(
        "lstFormulations",
        "com.sun.star.awt.UnoControlListBoxModel",
        118, 190, 184, 46,
    )
    add(
        "btnReplace",
        "com.sun.star.awt.UnoControlButtonModel",
        8, 240, 105, 16,
        Label="Remplacer occurrence",
        Enabled=False,
    )
    add(
        "btnInsert",
        "com.sun.star.awt.UnoControlButtonModel",
        214, 240, 88, 16,
        Label="Insérer la proposition",
    )
    add(
        "btnClose",
        "com.sun.star.awt.UnoControlButtonModel",
        258, 266, 44, 16,
        Label="Fermer",
    )

    dialog = smgr.createInstanceWithContext(
        "com.sun.star.awt.UnoControlDialog", ctx
    )
    dialog.setModel(model)
    dialog.createPeer(toolkit, None)

    search_box = dialog.getControl("txtSearch")
    results_box = dialog.getControl("lstResults")
    alerts_box = dialog.getControl("lstAlerts")
    detail_box = dialog.getControl("txtDetail")
    formulations_box = dialog.getControl("lstFormulations")
    status_label = dialog.getControl("lblStatus")
    insert_button = dialog.getControl("btnInsert")
    replace_button = dialog.getControl("btnReplace")

    listener = DialogListener(
        dialog,
        search_box,
        results_box,
        alerts_box,
        detail_box,
        formulations_box,
        status_label,
        insert_button,
        replace_button,
        _load_data(),
    )

    for control, command in [
        (dialog.getControl("btnSearch"), "search"),
        (dialog.getControl("btnScan"), "scan"),
        (replace_button, "replace"),
        (insert_button, "insert"),
        (dialog.getControl("btnClose"), "close"),
    ]:
        control.setActionCommand(command)
        control.addActionListener(listener)

    results_box.addItemListener(listener)
    alerts_box.addItemListener(listener)
    formulations_box.addItemListener(listener)
    dialog.addTopWindowListener(listener)

    _OPEN_LEXICON_WINDOWS.append({
        "dialog": dialog,
        "listener": listener,
    })
    dialog.setVisible(True)


g_exportedScripts = (open_lexicon, show_about, check_updates)
