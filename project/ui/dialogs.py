from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLabel, 
                               QLineEdit, QCheckBox, QWidget, QPushButton, 
                               QHBoxLayout, QMessageBox) 
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


class CalibrationDialog(QDialog):
    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.setWindowTitle("User Calibration")
        self.setFixedSize(380, 220)
        self.model = model

        # Vamos usar um estilo limpo seguindo o seu tema escuro
        self.setStyleSheet("background-color: #0a0a0a; color: #cccccc;")

        layout = QVBoxLayout(self)
        
        # Instrução da equação matemática
        info_label = QLabel("Equation: y = c0 + c1*x + c2*x² ...\n\nEnter coefficients separated by commas.\nExample: 0.5, 1.2, -0.01")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #aaaaaa; margin-bottom: 10px;")
        layout.addWidget(info_label)

        # Form layout para alinhar os inputs
        form_layout = QFormLayout()

        # Input Temperature
        self.txt_temp = QLineEdit()
        self.txt_temp.setText(", ".join(map(str, self.model.user_cal.temp_coeffs)))
        self.txt_temp.setStyleSheet("background-color: #1a1a1a; color: white; border: 1px solid #333; padding: 4px;")
        form_layout.addRow(QLabel("Temperature Coeffs:"), self.txt_temp)

        # Input Radiance
        self.txt_rad = QLineEdit()
        self.txt_rad.setText(", ".join(map(str, self.model.user_cal.rad_coeffs)))
        self.txt_rad.setStyleSheet("background-color: #1a1a1a; color: white; border: 1px solid #333; padding: 4px;")
        form_layout.addRow(QLabel("Radiance Coeffs:"), self.txt_rad)

        layout.addLayout(form_layout)

        # Botões
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Save && Apply")
        btn_save.setStyleSheet("background-color: #0e639c; color: white; padding: 5px 15px; border-radius: 3px;")
        btn_save.clicked.connect(self.save_calibration)
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setStyleSheet("background-color: #333333; color: white; padding: 5px 15px; border-radius: 3px;")
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def save_calibration(self):
        try:
            # Parse dos coeficientes (remove espaços e converte para float)
            t_txt = self.txt_temp.text().strip()
            r_txt = self.txt_rad.text().strip()
            
            t_coeffs = [float(x.strip()) for x in t_txt.split(',')] if t_txt else []
            r_coeffs = [float(x.strip()) for x in r_txt.split(',')] if r_txt else []

            # Atualiza o modelo
            self.model.user_cal.set_temp_coeffs(t_coeffs)
            self.model.user_cal.set_rad_coeffs(r_coeffs)
            
            self.accept() # Fecha a janela com sucesso
            
        except ValueError:
            QMessageBox.warning(self, "Error", "Invalid format. Please use numbers separated by commas.")