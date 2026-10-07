# -*- coding: utf-8 -*-
import json
import os
import uno
import unohelper

from com.sun.star.awt import XActionListener

EXT_ID = "fr.lexique.forensique"


def _ctx():
    return XSCRIPTCONTEXT.getComponentContext()


def _desktop():
    return XSCRIPTCONTEXT.getDesktop()


def _extension_root():
    """Return the installed extension directory from this script location."""
    # In an installed .oxt, this file lives in:
    # <extension-root>/Scripts/python/lexique_forensique.py
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
    )


def _load_data():
    path = os.path.join(_extension_root(), "data", "lexique.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _bad_terms(entry):
    return entry.get("termes_deconseilles", entry.get("deconseilles", []))


def _report_example(entry):
    return entry.get("exemple_rapport", entry.get("rapport", ""))


def _format_entry(e):
    syn = ", ".join(e.get("synonymes", [])) or "—"
    bad = ", ".join(_bad_terms(e)) or "—"
    return (
        f"{e['terme']}\n"
        f"Anglais : {e.get('anglais','—')}\n"
        f"Catégorie : {e.get('categorie','—')}\n"
        f"Synonymes : {syn}\n"
        f"Termes déconseillés : {bad}\n\n"
        f"Définition\n{e.get('definition','')}\n\n"
        f"Exemple de formulation\n{_report_example(e)}"
    )


def _find_entries(query, data):
    q = (query or "").strip().lower()
    if not q:
        return data
    out = []
    for e in data:
        hay = " ".join([
            e.get("terme", ""),
            e.get("anglais", ""),
            e.get("categorie", ""),
            " ".join(e.get("synonymes", [])),
            " ".join(_bad_terms(e)),
        ]).lower()
        if q in hay:
            out.append(e)
    return out


class DialogListener(unohelper.Base, XActionListener):
    def __init__(self, dialog, search_box, results_box, detail_box, insert_button, data):
        self.dialog = dialog
        self.search_box = search_box
        self.results_box = results_box
        self.detail_box = detail_box
        self.insert_button = insert_button
        self.data = data
        self.current = None
        self.matches = []
        self.refresh()

    def refresh(self):
        matches = _find_entries(self.search_box.Text, self.data)
        self.matches = matches
        self.results_box.removeItems(0, self.results_box.ItemCount)
        for e in matches:
            self.results_box.addItem(e["terme"], self.results_box.ItemCount)
        if matches:
            self.results_box.selectItemPos(0, True)
            self.current = matches[0]
            self.detail_box.Text = _format_entry(self.current)
            self.insert_button.Enabled = True
        else:
            self.current = None
            self.detail_box.Text = "Aucun terme trouvé."
            self.insert_button.Enabled = False

    def actionPerformed(self, event):
        cmd = event.ActionCommand
        if cmd == "search":
            self.refresh()
        elif cmd == "select":
            pos = self.results_box.SelectedItemPos
            if 0 <= pos < len(self.matches):
                self.current = self.matches[pos]
                self.detail_box.Text = _format_entry(self.current)
                self.insert_button.Enabled = True
        elif cmd == "insert" and self.current:
            doc = _desktop().getCurrentComponent()
            if doc and doc.supportsService("com.sun.star.text.TextDocument"):
                view = doc.getCurrentController().getViewCursor()
                text = view.getText()
                text.insertString(
                    view,
                    _report_example(self.current) or self.current["terme"],
                    False,
                )
        elif cmd == "close":
            self.dialog.endExecute()

    def disposing(self, event):
        pass


def open_lexicon(*args):
    ctx = _ctx()
    smgr = ctx.ServiceManager
    toolkit = smgr.createInstanceWithContext("com.sun.star.awt.Toolkit", ctx)
    model = smgr.createInstanceWithContext("com.sun.star.awt.UnoControlDialogModel", ctx)
    model.PositionX = 80
    model.PositionY = 50
    model.Width = 250
    model.Height = 190
    model.Title = "Lexique forensique FR — v0.1.2"

    def add(name, service, x, y, w, h, **props):
        m = model.createInstance(service)
        m.Name = name
        m.PositionX, m.PositionY, m.Width, m.Height = x, y, w, h
        for k, v in props.items():
            setattr(m, k, v)
        model.insertByName(name, m)

    add("lblSearch", "com.sun.star.awt.UnoControlFixedTextModel", 8, 8, 44, 12, Label="Recherche :")
    add("txtSearch", "com.sun.star.awt.UnoControlEditModel", 52, 6, 130, 14)
    add("btnSearch", "com.sun.star.awt.UnoControlButtonModel", 186, 6, 56, 14, Label="Rechercher")
    add("lstResults", "com.sun.star.awt.UnoControlListBoxModel", 8, 26, 90, 128)
    add("txtDetail", "com.sun.star.awt.UnoControlEditModel", 102, 26, 140, 128, MultiLine=True, ReadOnly=True, VScroll=True)
    add("btnInsert", "com.sun.star.awt.UnoControlButtonModel", 102, 160, 68, 16, Label="Insérer")
    add("btnClose", "com.sun.star.awt.UnoControlButtonModel", 174, 160, 68, 16, Label="Fermer")

    dialog = smgr.createInstanceWithContext("com.sun.star.awt.UnoControlDialog", ctx)
    dialog.setModel(model)
    dialog.createPeer(toolkit, None)

    search_box = dialog.getControl("txtSearch")
    results_box = dialog.getControl("lstResults")
    detail_box = dialog.getControl("txtDetail")
    insert_button = dialog.getControl("btnInsert")

    listener = DialogListener(
        dialog,
        search_box,
        results_box,
        detail_box,
        insert_button,
        _load_data(),
    )

    for control, command in [
        (dialog.getControl("btnSearch"), "search"),
        (results_box, "select"),
        (insert_button, "insert"),
        (dialog.getControl("btnClose"), "close"),
    ]:
        control.setActionCommand(command)
        control.addActionListener(listener)

    dialog.execute()
    dialog.dispose()


g_exportedScripts = (open_lexicon,)
