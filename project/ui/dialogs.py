from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLabel, 
                               QLineEdit, QCheckBox, QWidget)
from PySide6.QtCore import Qt

class ParamsDialog(QDialog):
    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Object Parameters")
        self.resize(350, 400)
        self.setStyleSheet("background-color: #0a0a0a;") # Fundo super escuro igual à foto

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Título superior
        title = QLabel("Object Parameters")
        title.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # Linha separadora
        line = QWidget(); line.setFixedHeight(1); line.setStyleSheet("background-color: #333;")
        layout.addWidget(line)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignLeft)
        form_layout.setSpacing(15)

        # Chave Seletora 1
        self.chk_override = QCheckBox("Override Camera/File")
        self.chk_override.setProperty("class", "ToggleSwitch")
        form_layout.addRow(self.chk_override)

        # Campos de Texto (Simulando os valores da sua imagem)
        self.fields = {}
        labels = [
            ("Emissivity (0 to 1):", "0.92"),
            ("Reflected Temperature (°C):", "20.00"),
            ("Distance (m):", "1.00000"),
            ("Atmosphere Temperature (°C):", "20.00"),
            ("Relative Humidity (%):", "30.0"),
        ]
        
        for text, val in labels:
            inp = QLineEdit(val)
            inp.setFixedWidth(100)
            self.fields[text] = inp
            form_layout.addRow(QLabel(text), inp)

        # Chave Seletora 2
        self.chk_transm = QCheckBox("Transmission (0 to 1):")
        self.chk_transm.setProperty("class", "ToggleSwitch")
        
        inp_transm = QLineEdit("1.000")
        inp_transm.setFixedWidth(100)
        form_layout.addRow(self.chk_transm, inp_transm)

        layout.addLayout(form_layout)
        layout.addStretch()
        
class InfoDialog(QDialog):
    def __init__(self, source_info, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Info")
        self.resize(300, 150)
        layout = QVBoxLayout(self)
        if source_info:
            layout.addWidget(QLabel(f"Camera: {source_info.camera_model}"))
            layout.addWidget(QLabel(f"Resolution: {source_info.image_width} x {source_info.image_height}"))
        else:
            layout.addWidget(QLabel("No file loaded."))