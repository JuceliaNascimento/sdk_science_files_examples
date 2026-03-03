# utils/theme.py

MODERN_DARK_THEME = """
QMainWindow, QDialog, QMenu { background-color: #1e1e1e; }
QLabel { color: #cccccc; font-family: 'Segoe UI', Arial; font-size: 12px; }

/* Botões Nativos (Flat) */
QPushButton.FlatIcon {
    background-color: transparent; 
    border: none; 
    border-radius: 4px; 
    padding: 4px;
    color: #cccccc; /* <--- ADICIONE ESTA LINHA PARA FORÇAR O TEXTO CLARO */
}
QPushButton.FlatIcon:hover { background-color: #333333; }
QPushButton.FlatIcon:checked { background-color: #444444; border: 1px solid #555; }

/* Menus de contexto (ao clicar no arco-íris ou unidade) */
QMenu { border: 1px solid #3c3c3c; }
QMenu::item { padding: 4px 24px 4px 8px; color: #fff; }
QMenu::item:selected { background-color: #0e639c; }

/* Slider Estilo Fino (Referência image_6fd3ff) */
QSlider::groove:horizontal {
    border: none; height: 4px; background: #3c3c3c; border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #cccccc; border: none; width: 14px; height: 14px; 
    margin: -5px 0; border-radius: 7px;
}
QSlider::handle:horizontal:hover { background: #ffffff; }

/* Inputs Escuros (Referência image_6fd003 e Colorbar) */
QLineEdit, QDoubleSpinBox {
    background-color: #1a1a1a; color: #aaaaaa;
    border: 1px solid #333333; border-radius: 4px; padding: 4px 8px;
}
QLineEdit:focus, QDoubleSpinBox:focus { border: 1px solid #0e639c; color: #ffffff; }

/* Toggle Switch Hack (Chaves seletoras arredondadas) */
QCheckBox.ToggleSwitch {
    spacing: 8px; color: #aaaaaa;
}
QCheckBox.ToggleSwitch::indicator {
    width: 32px; height: 16px; border-radius: 8px; border: none;
}
QCheckBox.ToggleSwitch::indicator:unchecked { background-color: #aaaaaa; }
QCheckBox.ToggleSwitch::indicator:checked { background-color: #0e639c; }
"""