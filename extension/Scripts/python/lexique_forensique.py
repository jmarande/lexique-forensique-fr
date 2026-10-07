# -*- coding: utf-8 -*-
import json
import os
import unicodedata

import uno
import unohelper

from com.sun.star.awt import XActionListener, XItemListener

_OPEN_LEXICON_WINDOWS = []


def _ctx():
    return XSCRIPTCONTEXT.getComponentContext()


def _desktop():
    return XSCRIPTCONTEXT.getDesktop()


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


def _report_example(entry):
    return entry.get("exemple_rapport", entry.get("rapport", ""))


def _sources(entry):
    values = entry.get("sources", [])
    if isinstance(values, str):
        return values
    return ", ".join(values) or "—"


def _normalize(value):
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value.casefold().strip()


def _format_entry(e):
    syn = ", ".join(e.get("synonymes", [])) or "—"
    bad = ", ".join(_bad_terms(e)) or "—"
    return (
        f"{e['terme']}\n"
        f"Anglais : {e.get('anglais', '—')}\n"
        f"Catégorie : {e.get('categorie', '—')}\n"
        f"Synonymes : {syn}\n"
        f"Termes déconseillés : {bad}\n"
        f"Sources : {_sources(e)}\n\n"
        f"DÉFINITION\n{e.get('definition', '')}\n\n"
        f"FORMULATION POUR RAPPORT\n{_report_example(e)}"
    )


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


class DialogListener(unohelper.Base, XActionListener, XItemListener):
    def __init__(
        self,
        dialog,
        search_box,
        results_box,
        detail_box,
        status_label,
        insert_button,
        data,
    ):
        self.dialog = dialog
        self.search_box = search_box
        self.results_box = results_box
        self.detail_box = detail_box
        self.status_label = status_label
        self.insert_button = insert_button
        self.data = data
        self.current = None
        self.matches = []
        self.refresh()

    def _set_buttons(self, enabled):
        self.insert_button.getModel().Enabled = enabled

    def _show_current(self, entry):
        self.current = entry
        self.detail_box.Text = _format_entry(entry)
        self._set_buttons(True)

    def refresh(self):
        self.matches = _find_entries(self.search_box.Text, self.data)

        if self.results_box.ItemCount:
            self.results_box.removeItems(0, self.results_box.ItemCount)

        for entry in self.matches:
            self.results_box.addItem(entry["terme"], self.results_box.ItemCount)

        count = len(self.matches)
        self.status_label.getModel().Label = (
            f"{count} résultat" if count == 1 else f"{count} résultats"
        )

        if self.matches:
            self.results_box.selectItemPos(0, True)
            self._show_current(self.matches[0])
        else:
            self.current = None
            self.detail_box.Text = "Aucun terme trouvé."
            self._set_buttons(False)

    def actionPerformed(self, event):
        cmd = event.ActionCommand

        if cmd == "search":
            self.refresh()

        elif cmd == "insert" and self.current:
            doc = _desktop().getCurrentComponent()
            if doc and doc.supportsService("com.sun.star.text.TextDocument"):
                view = doc.getCurrentController().getViewCursor()
                view.getText().insertString(
                    view,
                    _report_example(self.current) or self.current["terme"],
                    False,
                )
                self.status_label.getModel().Label = "Formulation insérée dans le document"

        elif cmd == "close":
            try:
                self.dialog.setVisible(False)
                self.dialog.dispose()
            finally:
                _OPEN_LEXICON_WINDOWS[:] = [
                    item for item in _OPEN_LEXICON_WINDOWS
                    if item.get("dialog") is not self.dialog
                ]

    def itemStateChanged(self, event):
        pos = self.results_box.SelectedItemPos
        if 0 <= pos < len(self.matches):
            self._show_current(self.matches[pos])

    def disposing(self, event):
        pass


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
    model.Height = 218
    model.Title = "Lexique forensique FR — v0.2.1"

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
        "lblStatus",
        "com.sun.star.awt.UnoControlFixedTextModel",
        8, 23, 294, 10,
        Label="",
    )
    add(
        "lstResults",
        "com.sun.star.awt.UnoControlListBoxModel",
        8, 36, 105, 142,
    )
    add(
        "txtDetail",
        "com.sun.star.awt.UnoControlEditModel",
        118, 36, 184, 142,
        MultiLine=True,
        ReadOnly=True,
        VScroll=True,
    )
    add(
        "btnInsert",
        "com.sun.star.awt.UnoControlButtonModel",
        180, 186, 74, 16,
        Label="Insérer formule",
    )
    add(
        "btnClose",
        "com.sun.star.awt.UnoControlButtonModel",
        258, 186, 44, 16,
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

    listener = DialogListener(
        dialog,
        search_box,
        results_box,
        detail_box,
        status_label,
        insert_button,
        _load_data(),
    )

    for control, command in [
        (dialog.getControl("btnSearch"), "search"),
        (insert_button, "insert"),
        (dialog.getControl("btnClose"), "close"),
    ]:
        control.setActionCommand(command)
        control.addActionListener(listener)

    results_box.addItemListener(listener)

    # Fenêtre non modale : Writer reste entièrement utilisable pendant
    # que le lexique est ouvert.
    _OPEN_LEXICON_WINDOWS.append({
        "dialog": dialog,
        "listener": listener,
    })
    dialog.setVisible(True)


g_exportedScripts = (open_lexicon,)
