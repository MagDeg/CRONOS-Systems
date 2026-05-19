"""Module-level error status popup with per-module OK/Issue cards.

Widgets:
    ModuleStatusPopup: Dialog listing all modules, each rendered as a card
        showing OK (green) or Issue (red) based on the error queue.
    _ModuleCard: Single module card with dot indicator and optional description.
"""

# Import QDialog as popup base, layout classes for stacking, QPushButton for close,
# QLabel for text, QFrame as the card container and separator
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame
# Import Qt namespace for alignment constants used on labels
from PySide6.QtCore import Qt

# Import the module/error definitions so this popup knows every module name and how to
# map error codes to their originating module
from definitions.error_defs import ALL_MODULES, ERROR_MODULES, ERROR_MAP

# Green-tinted card stylesheet for modules with no active errors — signals healthy status
_CARD_OK = """
QFrame#ModuleCard {
    background-color: rgba(0, 255, 100, 0.06);
    border: 1px solid rgba(0, 255, 100, 0.25);
    border-radius: 8px;
}
"""

# Red-tinted card stylesheet for modules with active errors — draws the operator's attention
_CARD_ERR = """
QFrame#ModuleCard {
    background-color: rgba(255, 80, 80, 0.08);
    border: 1px solid rgba(255, 80, 80, 0.4);
    border-radius: 8px;
}
"""


class _ModuleCard(QFrame):
    """Card widget showing module name, OK/Issue dot, and optional error description."""

    def __init__(self, name: str, parent=None):
        # Init QFrame as the card container — each card is a styled rectangular block
        super().__init__(parent)
        # Object name so the QSS rules above (#ModuleCard) apply their background and border
        self.setObjectName("ModuleCard")
        # Store the canonical module name so we can reference it when updating status
        self._name = name

        # Inner vertical layout stacks module row (name + dot) and optional error description
        layout = QVBoxLayout(self)
        # Generous horizontal padding, tight vertical padding for a clean card look
        layout.setContentsMargins(12, 8, 12, 8)
        # Tight spacing so the description sits close to the name row
        layout.setSpacing(2)

        # Horizontal row holds module name on the left and OK/Issue dot on the right
        row = QHBoxLayout()
        row.setSpacing(8)

        # Label that displays the module name (e.g. "VCU", "BMS", "IMU")
        lbl = QLabel(name)
        # Apply the global PanelTitle style for consistent header-like appearance
        lbl.setObjectName("PanelTitle")
        # Slightly larger font so module names are readable at a glance
        lbl.setStyleSheet("font-size: 14px;")
        # Stretch factor 1 pushes the dot indicator to the right edge of the card
        row.addWidget(lbl, 1)

        # Dot label will display either a green dot + "OK" or red dot + "Issue"
        self._dot = QLabel()
        # Oversized font so the dot character is prominent and noticeable
        self._dot.setStyleSheet("font-size: 18px;")
        row.addWidget(self._dot)

        # Add the name+dot row into the card's vertical layout
        layout.addLayout(row)

        # Description label shows the error details when a module has an active issue
        self._desc = QLabel()
        # Apply the global DetailText style for secondary info (smaller, muted)
        self._desc.setObjectName("DetailText")
        # Red-tinted text makes error descriptions visually distinct and urgent
        self._desc.setStyleSheet("color: rgba(255, 80, 80, 0.8); font-size: 11px;")
        # Hidden by default — only shown when the module has a non-OK status
        self._desc.setVisible(False)
        layout.addWidget(self._desc)

        # Start every card in OK state; the dialog will bulk-update from the error queue later
        self.set_ok(True, "")

    def set_ok(self, ok: bool, desc: str = ""):
        """Update card to OK (green) or Issue (red) with optional description."""
        if ok:
            # Apply green-tinted card background to signal a healthy module
            self.setStyleSheet(_CARD_OK)
            # Unicode black circle (●) + "OK" — instant green-light visual
            self._dot.setText("\u25CF  OK")
            # Green color so the dot is immediately recognizable as healthy
            self._dot.setStyleSheet("color: #00ff88; font-size: 18px;")
        else:
            # Apply red-tinted card background to signal a module with active errors
            self.setStyleSheet(_CARD_ERR)
            # Unicode black circle (●) + "Issue" — warning visual
            self._dot.setText("\u25CF  Issue")
            # Red color so the dot is immediately recognizable as a problem
            self._dot.setStyleSheet("color: #ff5050; font-size: 18px;")
        # Set the description text (empty string when OK, error string when Issue)
        self._desc.setText(desc)
        # Show description only when there is an issue — OK cards stay clean and minimal
        self._desc.setVisible(not ok)


class ModuleStatusPopup(QDialog):
    """Dialog listing all vehicle modules with per-card OK/Issue status from the error queue."""

    def __init__(self, parent=None):
        # Init QDialog so this functions as a standard popup window
        super().__init__(parent)
        # Set the window title so the user knows this is the module error overview
        self.setWindowTitle("Module Status")
        # Fixed size ensures a consistent layout and prevents resizing issues with the card list
        self.setFixedSize(400, 520)
        # Object name for QSS targeting via #ModuleStatusPopup
        self.setObjectName("ModuleStatusPopup")

        # Root vertical layout stacks title, separator, scrollable cards, separator, close button
        layout = QVBoxLayout(self)
        # Balanced margins so content doesn't touch the window border
        layout.setContentsMargins(16, 16, 16, 16)
        # Comfortable spacing between the major sections
        layout.setSpacing(8)

        # Header label so the user instantly knows what this popup contains
        header = QLabel("Module Status")
        # Apply the global PanelTitle QSS for consistent header styling
        header.setObjectName("PanelTitle")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # Separator between the title and the list of module cards
        sep = QFrame()
        sep.setObjectName("ValueSeparator")
        layout.addWidget(sep)

        # Sub-layout that holds all the _ModuleCard widgets in vertical order
        cards_layout = QVBoxLayout()
        cards_layout.setSpacing(6)

        # Dictionary mapping module name → _ModuleCard so update_errors can find cards quickly
        self._cards = {}
        # Create a card for every known module from the ALL_MODULES definition
        for name in ALL_MODULES:
            card = _ModuleCard(name)
            self._cards[name] = card
            cards_layout.addWidget(card)

        # Stretch factor 1: the cards layout expands/contracts while header/footer stay fixed
        layout.addLayout(cards_layout, 1)

        sep2 = QFrame()
        sep2.setObjectName("ValueSeparator")
        layout.addWidget(sep2)

        # Button row with centered Close button, identical pattern to other popups
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setObjectName("SettingsButton")
        close_btn.setFixedWidth(100)
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # Inline dark background so the popup matches the HUD theme even without the QSS file
        self.setStyleSheet("""
            #ModuleStatusPopup {
                background-color: #050814;
            }
        """)

    def update_errors(self, queue):
        """Update all module cards from the error queue (iterable of (ts, code, name, desc))."""
        # Collect the set of modules that have at least one active error in the queue
        active = set()
        # Collect the error description for each module (first one found wins)
        desc_map = {}
        # Iterate through the error queue tuples: (timestamp, error_code, module_name, description)
        for _ts, code, _name, desc in queue:
            mod = ERROR_MODULES.get(code)
            if mod:
                active.add(mod)
                # Only keep the first description for each module to avoid overwriting
                if mod not in desc_map:
                    desc_map[mod] = desc
        # Walk through every card and set its OK/Issue state based on whether errors were found
        for name, card in self._cards.items():
            card.set_ok(name not in active, desc_map.get(name, ""))
