STYLE = """
QWidget { background: #F4F7F9; color: #20303E; font-size: 14px; }
QMainWindow { background: #F4F7F9; }
QFrame#sidebar { background: #132D38; border: none; }
QFrame#sidebar QLabel { background: transparent; color: #EFF8F7; }
QLabel#brand { font-size: 21px; font-weight: 700; padding: 12px 0; }
QFrame#sidebar QPushButton { background: transparent; color: #E1F0EF; border: none; text-align: left; padding: 13px 16px; border-radius: 7px; }
QFrame#sidebar QPushButton:checked { background: #24505B; color: white; font-weight: 600; }
QFrame#sidebar QPushButton:hover { background: #1D424E; }
QLabel#title { font-size: 29px; font-weight: 700; color: #173541; }
QLabel#section { font-size: 20px; font-weight: 600; }
QLabel#subtitle { font-size: 15px; color: #4F6470; }
QLabel#muted { color: #4F6470; }
QLabel#steps { color: #09695D; background: #E2F1ED; padding: 14px 18px; border-radius: 6px; font-weight: 600; }
QLabel#notice { background: #EAF0F3; color: #3F5563; padding: 12px; border-radius: 6px; }
QLabel#drop { background: #EAF5F2; border: 2px dashed #76AFA4; border-radius: 10px; color: #24554C; font-size: 15px; }
QLabel#stats { font-size: 17px; padding: 14px; background: white; border: 1px solid #CFDAE0; border-radius: 7px; }
QPushButton { background: white; border: 1px solid #B6C7CF; border-radius: 6px; padding: 9px 14px; min-height: 19px; }
QPushButton:hover { background: #E5EFF1; border-color: #527C85; }
QPushButton:pressed { background: #D5E7E8; }
QPushButton#primary { background: #09695D; color: white; border-color: #09695D; font-weight: 600; }
QPushButton#primary:hover { background: #075448; }
QPushButton:disabled { color: #687D89; background: #E3EAEE; border-color: #CED9E0; }
QPushButton:focus, QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QCheckBox:focus { border: 2px solid #168A86; }
QLineEdit, QComboBox, QSpinBox { background: white; border: 1px solid #B7C8D0; border-radius: 5px; padding: 7px; min-height: 20px; selection-background-color: #09695D; }
QComboBox QAbstractItemView { background: white; selection-background-color: #CDE7E1; selection-color: #173541; }
QTableView, QTableWidget, QTextEdit { background: white; alternate-background-color: #F3F7F8; border: 1px solid #C7D5DD; border-radius: 5px; gridline-color: #E0E8ED; selection-background-color: #D2EAE5; selection-color: #173541; }
QTextEdit { padding: 8px; }
QHeaderView::section { background: #E6EEF2; border: none; border-right: 1px solid #D2DFE6; border-bottom: 1px solid #C7D5DD; padding: 10px; font-weight: 600; }
QTabWidget::pane { border: 1px solid #CCD9E0; border-radius: 6px; }
QTabBar::tab { background: #E5EDF1; color: #3F5663; padding: 10px 16px; border-bottom: 2px solid transparent; }
QTabBar::tab:selected { background: white; color: #09695D; border-bottom: 2px solid #09695D; font-weight: 600; }
QTabBar::tab:disabled { color: #738692; }
QCheckBox { padding: 6px 2px; spacing: 8px; }
QCheckBox::indicator { width: 17px; height: 17px; }
QProgressBar { border: 1px solid #BED1D5; border-radius: 4px; background: #E8F0F2; height: 10px; text-align: center; }
QProgressBar::chunk { background: #139A87; border-radius: 4px; }
QScrollArea { border: none; }
QToolTip { background: #173541; color: white; border: none; padding: 8px; }
"""
