#!/usr/bin/env python3
"""
Anki-like 'Decks' window mockup using Qt (PySide6 / PyQt5 fallback).

Features:
- Top row of actions: Decks | Add | Browse | Stats
- Left: nested deck tree (parent/child)
- Right: deck table with columns: Deck | New | Learn | Due
- Clicking a deck in the tree selects/highlights the corresponding row in the table
- Add / Browse / Stats open blank windows
- No network / sync functionality

Run:
    python anki_deck_mockup.py
"""

import sys
from functools import partial

# Try PySide6, fall back to PyQt5
try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
        QTreeView, QTreeWidget, QTreeWidgetItem, QToolBar, QAction, QLabel, QStatusBar,
        QDialog, QHeaderView
    )
    from PySide6.QtGui import QStandardItemModel, QStandardItem, QIcon, QFont
    from PySide6.QtCore import Qt, QSize
    QT_BACKEND = "PySide6"
except Exception:
    try:
        from PyQt5.QtWidgets import (
            QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
            QTreeView, QTreeWidget, QTreeWidgetItem, QToolBar, QAction, QLabel, QStatusBar,
            QDialog, QHeaderView
        )
        from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon, QFont
        from PyQt5.QtCore import Qt, QSize
        QT_BACKEND = "PyQt5"
    except Exception:
        raise RuntimeError("PySide6 or PyQt5 is required to run this script. Install with `pip install PySide6` or `pip install PyQt5`.")


class BlankDialog(QDialog):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(560, 360)
        # Blank content for now
        lbl = QLabel(f"{title} — (blank window)", self)
        lbl.setAlignment(Qt.AlignCenter)
        layout = QVBoxLayout(self)
        layout.addWidget(lbl)


class DecksWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Anki — Decks (mockup)")
        self.resize(980, 640)

        # Top toolbar (row of items)
        self.toolbar = QToolBar()
        self.toolbar.setIconSize(QSize(16, 16))
        self.toolbar.setMovable(False)
        self.addToolBar(Qt.TopToolBarArea, self.toolbar)

        # Actions: Decks (active), Add, Browse, Stats
        self.act_decks = QAction("Decks", self)
        self.act_decks.setCheckable(True)
        self.act_decks.setChecked(True)  # default active
        self.act_add = QAction("Add", self)
        self.act_browse = QAction("Browse", self)
        self.act_stats = QAction("Stats", self)

        # Add to toolbar (group-like visual)
        self.toolbar.addAction(self.act_decks)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.act_add)
        self.toolbar.addAction(self.act_browse)
        self.toolbar.addAction(self.act_stats)

        # Central widget with splitter
        central = QWidget()
        central_layout = QHBoxLayout()
        central_layout.setContentsMargins(6, 6, 6, 6)
        central.setLayout(central_layout)
        self.setCentralWidget(central)

        splitter = QSplitter()
        splitter.setOrientation(Qt.Horizontal)
        central_layout.addWidget(splitter)

        # Left: deck tree
        self.deck_tree = QTreeView()
        self.deck_tree.setHeaderHidden(True)
        self.deck_tree.setMinimumWidth(260)
        splitter.addWidget(self.deck_tree)

        # Right: deck counts in a tree/table (mirrors hierarchy, but has columns)
        self.deck_table = QTreeWidget()
        self.deck_table.setColumnCount(4)
        self.deck_table.setHeaderLabels(["Deck", "New", "Learn", "Due"])
        self.deck_table.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.deck_table.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.deck_table.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.deck_table.header().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        splitter.addWidget(self.deck_table)

        # Status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Mockup: left = deck tree, right = counts (New/Learn/Due)")

        # Populate demo decks and counts
        self._populate_demo_decks()

        # Connect selection changes: tree -> table
        self.deck_tree.selectionModel().selectionChanged.connect(self._on_tree_selection_changed)

        # Connect top actions to open blank windows
        self.act_add.triggered.connect(partial(self._open_blank_window, "Add"))
        self.act_browse.triggered.connect(partial(self._open_blank_window, "Browse"))
        self.act_stats.triggered.connect(partial(self._open_blank_window, "Stats"))
        self.act_decks.triggered.connect(self._on_decks_toggled)

        # Small style adjustments to look closer to Anki
        self._apply_light_styling()

    def _apply_light_styling(self):
        # Use a UI font similar to Anki's default (system dependent)
        font = QFont()
        font.setPointSize(10)
        self.setFont(font)

        # Minimal toolbar style to mimic flat look
        self.toolbar.setStyleSheet("""
            QToolBar { spacing: 8px; padding: 4px }
            QToolButton { padding: 6px 10px; border: 0px; background: transparent; }
            QToolButton:checked { background: #e6f0ff; border-radius: 4px; }
        """)

        # Table row spacing and alternate colors like Anki uses
        self.deck_table.setAlternatingRowColors(True)
        self.deck_table.setStyleSheet("""
            QTreeWidget { selection-background-color: #d0e7ff; }
            QTreeWidget::item { padding: 6px; }
        """)

    def _populate_demo_decks(self):
        """
        Create a demo hierarchy of decks and fill counts.
        This mirrors the nested-deck behaviour in Anki.
        """
        # Example tree structure: list of tuples (path, counts)
        demo = [
            (["Default"], (3, 1, 5)),
            (["Languages", "Japanese"], (7, 2, 13)),
            (["Languages", "Spanish"], (2, 0, 8)),
            (["Math", "Calculus", "Derivatives"], (1, 0, 0)),
            (["Math", "Calculus", "Integrals"], (0, 0, 4)),
            (["Misc"], (5, 4, 2)),
        ]

        # Build left QStandardItemModel for deck_tree
        model = QStandardItemModel()
        root_item = model.invisibleRootItem()

        # We'll also populate right-side QTreeWidget with the same structure
        self.deck_table.clear()

        left_nodes = {}   # map tuple path -> QStandardItem
        right_nodes = {}  # map tuple path -> QTreeWidgetItem

        for path, counts in demo:
            # 'path' is e.g. ["Languages", "Japanese"] or single-element ["Default"]
            p_tuple = tuple(path)
            # Ensure parent chain exists for left model
            parent_item = root_item
            parent_key = ()
            for idx, name in enumerate(path):
                parent_key = parent_key + (name,)
                if parent_key not in left_nodes:
                    item = QStandardItem(name)
                    item.setEditable(False)
                    # Light bolding for top-level decks
                    if idx == 0:
                        f = item.font()
                        f.setBold(True)
                        item.setFont(f)
                    parent_item.appendRow(item)
                    left_nodes[parent_key] = item
                parent_item = left_nodes[parent_key]

        # Assign the model to the tree
        self.deck_tree.setModel(model)
        self.deck_tree.expandAll()

        # Now populate right tree widget mirroring structure, with counts
        # To preserve nested structure we build nodes similarly
        right_root = self.deck_table.invisibleRootItem()
        # we need a helper to get/create nodes in the right tree
        def get_or_create_right_node(path_parts):
            key = tuple(path_parts)
            if key in right_nodes:
                return right_nodes[key]
            if len(path_parts) == 1:
                node = QTreeWidgetItem(self.deck_table, [path_parts[0]])
                node.setExpanded(True)
                right_nodes[key] = node
                return node
            else:
                parent = get_or_create_right_node(path_parts[:-1])
                node = QTreeWidgetItem(parent, [path_parts[-1]])
                node.setExpanded(True)
                right_nodes[key] = node
                return node

        # Fill counts
        for path, counts in demo:
            node = get_or_create_right_node(path)
            new_c, learn_c, due_c = counts
            node.setText(1, str(new_c))
            node.setText(2, str(learn_c))
            node.setText(3, str(due_c))

        # Expand all in the right widget and adjust column widths
        self.deck_table.expandAll()
        self.deck_table.header().resizeSection(0, 380)

        # Select initial first deck (Default)
        # Find index of first top-level node in left tree
        idx = model.index(0, 0)
        if idx.isValid():
            self.deck_tree.setCurrentIndex(idx)

    def _on_tree_selection_changed(self, selected, deselected):
        # respond to tree selection by highlighting matching item in right tree
        sel_indexes = self.deck_tree.selectionModel().selectedIndexes()
        if not sel_indexes:
            return
        index = sel_indexes[0]
        # build the path from the index to the root
        model = self.deck_tree.model()
        path_parts = []
        cur = index
        while cur.isValid():
            path_parts.insert(0, model.data(cur))
            cur = cur.parent()
        # Find corresponding right-side node
        # Use recursive search in deck_table
        def find_node_containing(parent_item, target_name):
            for i in range(parent_item.childCount()):
                child = parent_item.child(i)
                if child.text(0) == target_name:
                    return child
            return None

        # Walk down right-side tree to match the same path
        parent = self.deck_table.invisibleRootItem()
        match = None
        for part in path_parts:
            match = find_node_containing(parent, part)
            if match is None:
                break
            parent = match
        if match:
            # Clear previous selection and select this row
            self.deck_table.setCurrentItem(match)
            self.status.showMessage(f"Selected deck: {' / '.join(path_parts)}")
        else:
            self.deck_table.setCurrentItem(None)
            self.status.showMessage("Selected deck not found on right pane")

    def _open_blank_window(self, title: str):
        dlg = BlankDialog(title, parent=self)
        dlg.setWindowModality(False)
        dlg.show()

    def _on_decks_toggled(self, checked):
        # Keep Decks button checked (it represents the active main view)
        self.act_decks.setChecked(True)
        # Could trigger an explicit refresh; for now, just update status
        self.status.showMessage("Decks (main view)")

def main():
    app = QApplication(sys.argv)
    win = DecksWindow()
    win.show()
    app.exec_()


if __name__ == "__main__":
    main()
