#!/usr/bin/env python3

import sys
from functools import partial

try:
    # Prefer PySide6
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSpacerItem,
        QSizePolicy, QTreeWidget, QTreeWidgetItem, QPushButton, QLabel, QDialog,
        QHeaderView, QToolButton
    )
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QFont, QBrush, QColor
    QT_BACKEND = "PySide6"
except Exception:
    try:
        # Fallback PyQt5
        from PyQt5.QtWidgets import (
            QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSpacerItem,
            QSizePolicy, QTreeWidget, QTreeWidgetItem, QPushButton, QLabel, QDialog,
            QHeaderView, QToolButton
        )
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QFont, QBrush, QColor
        QT_BACKEND = "PyQt5"
    except Exception:
        raise RuntimeError("PySide6 or PyQt5 is required. Install with `pip install PySide6` or `pip install PyQt5`.")

class BlankDialog(QDialog):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(560, 360)
        lbl = QLabel(f"{title} — (blank window)", self)
        lbl.setAlignment(Qt.AlignCenter)
        layout = QVBoxLayout(self)
        layout.addWidget(lbl)

class DecksMockup(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Anki2")
        self.resize(708, 592) # (width, height)

        central = QWidget()
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(16, 16, 16, 16)
        central_layout.setSpacing(12)
        self.setCentralWidget(central)

        # Top: centered navigation container
        nav_container = QWidget()
        nav_container.setObjectName("nav_container")
        nav_layout = QHBoxLayout(nav_container)
        nav_layout.setContentsMargins(22, 8, 22, 8)
        nav_layout.setSpacing(28)

        # Add horizontal spacer to center nav_container later
        central_layout.addItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))
        central_layout.addWidget(nav_container, alignment=Qt.AlignHCenter)
        central_layout.addItem(QSpacerItem(20, 6, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Buttons: Decks, Add, Browse, Stats
        btn_names = ["Decks", "Add", "Browse", "Stats"]
        self.nav_buttons = {}
        for name in btn_names:
            btn = QPushButton(name)
            btn.setFlat(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFocusPolicy(Qt.NoFocus)
            f = btn.font()
            f.setPointSize(14)
            f.setBold(True)
            btn.setFont(f)
            # Only non-Decks open a blank window
            if name != "Decks":
                btn.clicked.connect(partial(self.open_blank, name))
            self.nav_buttons[name] = btn
            nav_layout.addWidget(btn)

        # Style nav container & buttons: grey background, white bold text, no hover highlight
        nav_container.setStyleSheet("""
            QWidget#nav_container { background: #3a3a3a; border-radius: 10px; }
            QPushButton { color: white; background: transparent; border: none; padding: 6px 18px; }
            QPushButton:hover { background: transparent; } 
            QPushButton:pressed { background: transparent; }
        """)

        # Middle: centered deck widget (with vertical spacer above/below)
        central_layout.addItem(QSpacerItem(20, 8, QSizePolicy.Minimum, QSizePolicy.Fixed))

        mid_box = QHBoxLayout()
        central_layout.addLayout(mid_box)
        mid_box.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # Deck QTreeWidget (Deck | New | Learn | Due)
        self.deck_widget = QTreeWidget()
        self.deck_widget.setColumnCount(4)
        self.deck_widget.setHeaderLabels(["Deck", "New", "Learn", "Due"])

        header = self.deck_widget.header()
        hfont = header.font()
        hfont.setBold(True)
        hfont.setPointSize(14)
        hfont.setUnderline(True)
        header.setFont(hfont)
        header.setStyleSheet("QHeaderView::section { background: transparent; color: white; }")
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)

        # Make item font larger
        font = QFont()
        font.setPointSize(14)
        self.deck_widget.setFont(font)
        self.deck_widget.setIndentation(16)
        # Dark rounded look for panel
        self.deck_widget.setStyleSheet("""
            QTreeWidget { background: #2f2f2f; border-radius: 12px; padding: 14px; }
            QTreeWidget::item { padding: 10px 8px; }
            QTreeWidget::item:selected { background: #1f1f1f; border-radius: 8px; }
        """)

        mid_box.addWidget(self.deck_widget)
        mid_box.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        central_layout.addItem(QSpacerItem(20, 24, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Example demo data similar to your screenshot
        demo = [
            (["Core 6000"], (0,0,0)),
            (["Dictionaries of Grammar Sentences", "1 - Basic"], (10,1,2)),
            (["Dictionaries of Grammar Sentences", "2 - Intermediate"], (30,1,2)),
            (["Dictionaries of Grammar Sentences", "3 - Advanced"], (30,0,0)),
            (["Sentence Vocab"], (30,2,1)),
            (["Misc"], (5,4,2)),
        ]

        # Create items and a hidden settings button widget per item
        self.settings_widgets = {}
        for path, counts in demo:
            parent = None
            for i, name in enumerate(path):
                if parent is None:
                    top = self._find_top_item(name)
                    if top is None:
                        item = QTreeWidgetItem(self.deck_widget, [name, "", "", ""])
                        item.setExpanded(True)
                    else:
                        item = top
                else:
                    ch = self._find_child_item(parent, name)
                    if ch is None:
                        item = QTreeWidgetItem(parent, [name, "", "", ""])
                        item.setExpanded(True)
                    else:
                        item = ch
                parent = item
            # set counts on final item
            new_c, learn_c, due_c = counts
            self._set_count_for_item(parent, new_c, 1)
            self._set_count_for_item(parent, learn_c, 2)
            self._set_count_for_item(parent, due_c, 3)
            # create settings button widget for the item (hidden by default)
            settings_btn = QToolButton()
            settings_btn.setText("⚙")
            settings_btn.setCursor(Qt.PointingHandCursor)
            settings_btn.setStyleSheet("QToolButton { background: transparent; color: #cccccc; border: none; font-size: 16px; }")
            settings_btn.clicked.connect(partial(self.open_blank, "Deck options: " + " / ".join(path)))
            container = QWidget()
            cl = QHBoxLayout(container)
            cl.setContentsMargins(0, 0, 8, 0)
            cl.addStretch()
            cl.addWidget(settings_btn)
            container.setVisible(False)
            # put container into the 3rd column (so it sits to the right of 'Due')
            self.deck_widget.setItemWidget(parent, 3, container)
            self.settings_widgets[parent] = container

        # Enable mouse tracking for itemEntered to work (show/hide settings)
        self.deck_widget.setMouseTracking(True)
        self.deck_widget.viewport().setMouseTracking(True)
        self.deck_widget.itemEntered.connect(self._on_item_hover)
        # ensure settings hidden when leaving
        self.deck_widget.viewport().leaveEvent = self._on_viewport_leave

    def _find_top_item(self, name):
        for i in range(self.deck_widget.topLevelItemCount()):
            it = self.deck_widget.topLevelItem(i)
            if it.text(0) == name:
                return it
        return None

    def _find_child_item(self, parent, name):
        for i in range(parent.childCount()):
            it = parent.child(i)
            if it.text(0) == name:
                return it
        return None

    def _set_count_for_item(self, item, val, col):
        txt = str(val) if val is not None and val != 0 else "0"
        item.setText(col, txt)
        print("col: ", col)
        # color logic
        if val == 0:
            color = "#9e9e9e"
        else:
            if col == 1:
                color = "#4ea0ff"  # blue
            elif col == 2:
                color = "#ff6b6b"  # red
            elif col == 3:
                color = "#4cd97b"  # green
            else:
                color = "#e6e6e6"
        # set foreground color
        item.setForeground(col, QBrush(QColor(color)))

    def _on_item_hover(self, item, column):
        # hide all settings first
        for w in self.settings_widgets.values():
            w.setVisible(False)
        if item in self.settings_widgets:
            self.settings_widgets[item].setVisible(True)

    def _on_viewport_leave(self, event):
        for w in self.settings_widgets.values():
            w.setVisible(False)
        return super(QTreeWidget, self.deck_widget).leaveEvent(event)

    def open_blank(self, title):
        dlg = BlankDialog(title, parent=self)
        dlg.setWindowModality(False)
        dlg.show()

def main():
    app = QApplication(sys.argv)
    # global font a little bigger
    f = app.font()
    f.setPointSize(12)
    app.setFont(f)
    win = DecksMockup()
    win.show()
    app.exec_()

if __name__ == "__main__":
    main()
