import os
import cv2
import numpy as np
from PySide6.QtWidgets import (QGroupBox, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QFileDialog, QLabel, QSlider, QMessageBox, QButtonGroup, QMenu, QLineEdit)
from PySide6.QtCore import Qt, QTimer, QSize, QPoint, QRectF
from PySide6.QtGui import QImage, QPixmap, QIcon, QPainter, QPen, QColor, QPolygon, QLinearGradient, QPainterPath

from core.thermal_model import ThermalModel
from ui.video_widget import ThermalVideoWidget
from ui.dialogs import InfoDialog, ParamsDialog
from utils.config import PALETTES

def get_icon(name, color="#aaaaaa", size=24):
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    pen = QPen(QColor(color)); pen.setWidth(2)
    painter.setPen(pen)
    
    if name == "export":
        # Seta curvada para a direita
        path = QPainterPath()
        path.moveTo(8, 16); path.quadTo(8, 8, 16, 8)
        painter.drawPath(path)
        painter.setBrush(QColor(color)); painter.setPen(Qt.NoPen)
        painter.drawPolygon(QPolygon([QPoint(14, 4), QPoint(20, 8), QPoint(14, 12)]))
    elif name == "prev":
        painter.setBrush(QColor(color)); painter.setPen(Qt.NoPen)
        painter.drawPolygon(QPolygon([QPoint(18, 4), QPoint(18, 20), QPoint(6, 12)]))
    elif name == "next":
        painter.setBrush(QColor(color)); painter.setPen(Qt.NoPen)
        painter.drawPolygon(QPolygon([QPoint(6, 4), QPoint(6, 20), QPoint(18, 12)]))
    elif name == "play":
        painter.setBrush(QColor("#00aaff")); painter.setPen(Qt.NoPen) # Azul
        painter.drawPolygon(QPolygon([QPoint(8, 4), QPoint(8, 20), QPoint(18, 12)]))
    elif name == "pause":
        painter.setBrush(QColor("#00aaff")); painter.setPen(Qt.NoPen) # Quadrado azul
        painter.drawRect(6, 6, 12, 12)
    elif name == "rainbow":
        # Mini arco-íris para o botão de paleta
        grad = QLinearGradient(0, 0, 0, 24)
        grad.setColorAt(0.0, QColor(255, 255, 0)) # Amarelo
        grad.setColorAt(0.3, QColor(255, 0, 0))   # Vermelho
        grad.setColorAt(0.7, QColor(128, 0, 128)) # Roxo
        grad.setColorAt(1.0, QColor(0, 0, 0))     # Preto
        painter.setBrush(grad); painter.setPen(QPen(QColor("#ffffff"), 1))
        painter.drawRect(4, 2, 16, 20)
    elif name == "zoom_fit":
        # Ícone de expandir cruzado azul
        pen = QPen(QColor("#00aaff")); pen.setWidth(2); painter.setPen(pen)
        painter.drawLine(4, 4, 10, 10); painter.drawLine(20, 4, 14, 10)
        painter.drawLine(4, 20, 10, 14); painter.drawLine(20, 20, 14, 14)
        # Setinhas (simplificadas)
        painter.drawLine(4,4, 8,4); painter.drawLine(4,4, 4,8)
        painter.drawLine(20,20, 16,20); painter.drawLine(20,20, 20,16)
    elif name == "unit_no":
        # Texto e símbolo de bloqueado
        painter.drawEllipse(12, 6, 10, 10)
        painter.drawLine(14, 14, 20, 8)
    # ... (Mantenha os ícones antigos folder, cursor, rect, ellipse, clear aqui) ...
    elif name == "folder":
        painter.setBrush(QColor(color)); painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(2, 6, 20, 14, 2, 2); painter.drawRoundedRect(2, 3, 10, 6, 2, 2)
    elif name == "params":
        # Ícone de três controles deslizantes (Sliders) para Parâmetros
        # (Baseado em image_12.png)
        pen = QPen(QColor(color))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush) # Os círculos são vazados

        # Alturas das três linhas horizontais (Y)
        y_top = 6
        y_mid = 12
        y_bot = 18

        # Raio dos círculos (alças)
        r = 3

        # 1. Linha Superior (Alça na Esquerda)
        painter.drawLine(4, y_top, 20, y_top) # Linha horizontal
        painter.drawEllipse(4, y_top - r, r * 2, r * 2) # Círculo (alça)

        # 2. Linha Central (Alça na Direita)
        painter.drawLine(4, y_mid, 20, y_mid) # Linha horizontal
        painter.drawEllipse(14, y_mid - r, r * 2, r * 2) # Círculo (alça)

        # 3. Linha Inferior (Alça na Esquerda)
        painter.drawLine(4, y_bot, 20, y_bot) # Linha horizontal
        painter.drawEllipse(4, y_bot - r, r * 2, r * 2) # Círculo (alça)
    elif name == "cursor":
        painter.setBrush(QColor(color)); painter.setPen(Qt.NoPen)
        poly = QPolygon([QPoint(6, 2), QPoint(6, 18), QPoint(10, 14), QPoint(13, 21), QPoint(16, 20), QPoint(13, 13), QPoint(19, 13)])
        painter.drawPolygon(poly)
    elif name == "ellipse":
        painter.drawEllipse(3, 6, 18, 12)
    elif name == "rect":
        painter.drawRect(4, 5, 16, 14)

    painter.end()
    return QIcon(pixmap)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Thermal Science Files Viewer")
        self.setWindowIcon(QIcon("icons/icone.ico"))
        self.resize(1100, 700)
        self.model = ThermalModel()
        self.current_frame = 0
        self.current_palette = PALETTES["Ironbow"]
        self.timer = QTimer()
        self.timer.timeout.connect(self.next_frame)
        self.setup_ui()
        self.video_widget.pixel_hovered.connect(self.update_cursor_data)
        self.video_widget.stats_updated.connect(self.update_roi_stats)

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # --- PAINEL SUPERIOR ---
        top_layout = QHBoxLayout()
        
        btn_open = QPushButton(); btn_open.setIcon(get_icon("folder")); btn_open.setProperty("class", "FlatIcon")
        btn_open.setIconSize(QSize(30, 30))
        btn_open.clicked.connect(self.open_file); top_layout.addWidget(btn_open)

        sep = QLabel("│"); sep.setStyleSheet("color: #444; font-size: 18px; margin: 0 5px;")
        top_layout.addWidget(sep)

        self.tool_group = QButtonGroup(self)
        tools = [("cursor", "None"), ("rect", "Rect"), ("ellipse", "Circle")]
        for icon_name, mode in tools:
            btn = QPushButton(); btn.setIcon(get_icon(icon_name)); btn.setProperty("class", "FlatIcon")
            btn.setIconSize(QSize(30, 30))
            btn.setCheckable(True); btn.clicked.connect(lambda checked, m=mode: self.video_widget.set_roi_mode(m))
            self.tool_group.addButton(btn); top_layout.addWidget(btn)
            if mode == "None": btn.setChecked(True)

        top_layout.addStretch()

       # Botão Paleta (Arco-íris) no topo direito
        self.btn_palette = QPushButton()
        self.btn_palette.setIcon(get_icon("rainbow"))
        self.btn_palette.setProperty("class", "FlatIcon")
        self.btn_palette.setIconSize(QSize(40, 40))
        palette_menu = QMenu(self)
        for p in PALETTES.keys():
            palette_menu.addAction(p, lambda pal=p: self.change_palette(pal))
        self.btn_palette.setMenu(palette_menu)
        top_layout.addWidget(self.btn_palette)

        # Canto Direito: Unidade
        self.btn_unit = QPushButton("Counts"); self.btn_unit.setIcon(get_icon("unit_no"))
        self.btn_unit.setProperty("class", "FlatIcon")
        self.btn_unit.setIconSize(QSize(40, 40))
        self.btn_unit.setLayoutDirection(Qt.RightToLeft) # Ícone na direita do texto
        self.unit_menu = QMenu(self)
        self.btn_unit.setMenu(self.unit_menu)
        top_layout.addWidget(self.btn_unit)

        # Botões Params e Info simplificados
        btn_params = QPushButton()
        btn_params.setIcon(get_icon("params"))
        btn_params.setProperty("class", "FlatIcon")
        btn_params.setIconSize(QSize(26, 26)) # Ajuste o tamanho se quiser maior
        btn_params.setToolTip("Object Parameters")
        btn_params.clicked.connect(lambda: ParamsDialog(self.model, self).exec())
        top_layout.addWidget(btn_params)
        top_layout.addWidget(btn_params)

        main_layout.addLayout(top_layout)

        # --- CENTRO  ---
        center_layout = QHBoxLayout()

        #  1. PAINEL LATERAL ESQUERDO (Dados e Estatísticas)
        side_panel_container = QWidget()
        side_panel_container.setFixedWidth(180) # Largura fixa para a barra lateral
        side_layout = QVBoxLayout(side_panel_container)
        side_layout.setContentsMargins(5, 0, 5, 0)
        side_layout.setSpacing(15)

        # Grupo: Dados do Cursor (X, Y e Valor)
        cursor_group = QGroupBox("Cursor Data")
        cursor_vbox = QVBoxLayout()
        self.lbl_cursor_pos = QLabel("X: - , Y: -")
        self.lbl_cursor_val = QLabel("Value: -")
        cursor_vbox.addWidget(self.lbl_cursor_pos)
        cursor_vbox.addWidget(self.lbl_cursor_val)
        cursor_group.setLayout(cursor_vbox)
        side_layout.addWidget(cursor_group)

        # Grupo: ROI Stats (Média e Desvio Padrão)
        roi_group = QGroupBox("ROI Statistics")
        roi_vbox = QVBoxLayout()
        self.lbl_roi_mean = QLabel("Mean: -")
        self.lbl_roi_std = QLabel("Std Dev: -")
        roi_vbox.addWidget(self.lbl_roi_mean)
        roi_vbox.addWidget(self.lbl_roi_std)
        roi_group.setLayout(roi_vbox)
        side_layout.addWidget(roi_group)

        side_layout.addStretch() # Empurra os grupos para o topo
        center_layout.addWidget(side_panel_container)

            # 2. WIDGET DE VÍDEO NO CENTRO

        self.video_widget = ThermalVideoWidget()
        center_layout.addWidget(self.video_widget, stretch=1)

        # COLORBAR ESTILIZADA (Min/Max inputs e Zoom to Fit)
        right_panel = QVBoxLayout()
        right_panel.setSpacing(5)
        
        # Botão Zoom To Fit
        btn_zoom = QPushButton(); btn_zoom.setIcon(get_icon("zoom_fit", size=32))
        btn_zoom.setProperty("class", "FlatIcon")
        btn_zoom.setIconSize(QSize(40, 40))
        btn_zoom.clicked.connect(lambda: self.video_widget.fitInView(self.video_widget.scene.sceneRect(), Qt.KeepAspectRatio))
        right_panel.addWidget(btn_zoom, alignment=Qt.AlignCenter)

        self.txt_max = QLineEdit("0.0")
        self.txt_max.setFixedWidth(60); self.txt_max.setAlignment(Qt.AlignCenter)
        right_panel.addWidget(self.txt_max, alignment=Qt.AlignCenter)

        self.colorbar_label = QLabel()
        self.colorbar_label.setFixedWidth(40)
        right_panel.addWidget(self.colorbar_label, stretch=1, alignment=Qt.AlignCenter)

        self.txt_min = QLineEdit("0.0")
        self.txt_min.setFixedWidth(60); self.txt_min.setAlignment(Qt.AlignCenter)
        right_panel.addWidget(self.txt_min, alignment=Qt.AlignCenter)

        center_layout.addLayout(right_panel)
        main_layout.addLayout(center_layout, stretch=1)

        # --- SLIDER (Barra Fina) ---
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setEnabled(False)
        self.slider.sliderMoved.connect(self.seek_frame)
        main_layout.addWidget(self.slider)

        # --- RODAPÉ (Export, Player, Unit) ---
        bottom_layout = QHBoxLayout()
        
        # Canto Esquerdo: Export
        btn_export = QPushButton()
        btn_export.setIcon(get_icon("export"))
        btn_export.setProperty("class", "FlatIcon")
        btn_export.setIconSize(QSize(40, 40))
        btn_export.clicked.connect(self.export_csv)
        bottom_layout.addWidget(btn_export)
        bottom_layout.addStretch()

        # Centro: Controles de Player Azuis
        btn_prev = QPushButton(); btn_prev.setIcon(get_icon("prev")); btn_prev.setProperty("class", "FlatIcon")
        btn_prev.setIconSize(QSize(40, 40))
        btn_prev.clicked.connect(lambda: self.step_frame(-1))
        bottom_layout.addWidget(btn_prev)

        self.btn_play = QPushButton(); self.btn_play.setIcon(get_icon("play")); self.btn_play.setProperty("class", "FlatIcon")
        self.btn_play.clicked.connect(self.toggle_pause)
        bottom_layout.addWidget(self.btn_play)

        btn_next = QPushButton(); btn_next.setIcon(get_icon("next")); btn_next.setProperty("class", "FlatIcon")
        btn_next.setIconSize(QSize(40, 40))
        btn_next.clicked.connect(lambda: self.step_frame(1))
        bottom_layout.addWidget(btn_next)
        
        bottom_layout.addStretch()

        main_layout.addLayout(bottom_layout)

    # --- LÓGICA (Mantenha suas funções open_file, update_frame, etc) ---
    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open", "", "Files (*.ats *.jpg)")
        if path and self.model.load_file(path):
            self.unit_menu.clear()
            for u in self.model.get_supported_units():
                self.unit_menu.addAction(u, lambda unit=u: self.change_unit(unit))
            self.slider.setEnabled(True)
            self.slider.setMaximum(self.model.num_frames - 1)
            self.current_frame = 0
            self.update_frame()
            self.draw_colorbar()
            self.btn_play.setIcon(get_icon("pause"))
            self.timer.start(33)

    def update_frame(self):
        data = self.model.get_frame_data(self.current_frame)
        if data is not None:
            self.video_widget.update_image(data, self.current_palette)
            self.slider.setValue(self.current_frame)
            # Atualiza min e max da colorbar automaticamente (opcional)
            self.txt_max.setText(f"{np.max(data):.1f}")
            self.txt_min.setText(f"{np.min(data):.1f}")

    def next_frame(self):
        if self.model.num_frames > 0:
            self.current_frame = (self.current_frame + 1) % self.model.num_frames
            self.update_frame()

    def toggle_pause(self):
        if self.timer.isActive():
            self.timer.stop(); self.btn_play.setIcon(get_icon("play"))
        else:
            self.timer.start(33); self.btn_play.setIcon(get_icon("pause"))

    def seek_frame(self, pos):
        self.current_frame = pos
        if not self.timer.isActive(): self.update_frame()

    def step_frame(self, dir):
        if self.model.num_frames > 0:
            self.current_frame = max(0, min(self.current_frame + dir, self.model.num_frames - 1))
            self.slider.setValue(self.current_frame)
            if not self.timer.isActive(): self.update_frame()

    def change_unit(self, unit):
        self.model.set_unit(unit)
        self.btn_unit.setText(unit.split()[0]) # Escreve só "Counts" ou "Temperature"
        if not self.timer.isActive(): self.update_frame()

    def change_palette(self, pal):
        self.current_palette = PALETTES.get(pal)
        self.draw_colorbar()
        if not self.timer.isActive(): self.update_frame()

    def draw_colorbar(self):
        # A barra do meio isolada (o histograma lateral exigiria PyqtGraph, 
        # mas mantivemos o gradiente com as caixas separadas perfeitamente)
        grad = np.linspace(255, 0, 500).astype(np.uint8)
        grad = np.tile(grad, (20, 1)).T
        colored = cv2.applyColorMap(grad, self.current_palette)
        rgb = cv2.cvtColor(colored, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        self.colorbar_label.setPixmap(QPixmap.fromImage(qimg).scaled(25, 400, Qt.IgnoreAspectRatio))

    def export_csv(self):
            # Verifica se tem alguma imagem carregada
            if self.model.raw_data is None: 
                QMessageBox.warning(self, "Aviso", "Nenhum termograma carregado para exportar.")
                return
                
            # Sugere um nome de arquivo baseado no frame atual
            suggested = f"{self.model.file_name}_raw_data_frame{self.current_frame}.csv"
            path, _ = QFileDialog.getSaveFileName(self, "Salvar CSV", suggested, "CSV (*.csv)")
            
            # Se o usuário escolheu um local e clicou em Salvar
            if path:
                self.model.export_csv(path)
                QMessageBox.information(self, "Sucesso", "CSV Exportado com sucesso!")

    def update_cursor_data(self, x, y):
        # Atualiza as coordenadas na tela
        self.lbl_cursor_pos.setText(f"X: {x}, Y: {y}")
        
        # Busca o valor térmico real no modelo
        val = self.model.get_value_at(x, y)
        if val is not None:
            # Pega a unidade atual (Counts, C, etc) do modelo para exibir
            unit = getattr(self.model, 'current_unit_label', "")
            self.lbl_cursor_val.setText(f"Value: {val:.2f} {unit}")
        else:
            self.lbl_cursor_val.setText("Value: -")

    def update_roi_stats(self, mean_val, std_val):
        # Esta função recebe os dois floats emitidos pelo sinal stats_updated
        if mean_val == 0.0 and std_val == 0.0:
            self.lbl_roi_mean.setText("Mean: -")
            self.lbl_roi_std.setText("Std Dev: -")
        else:
            self.lbl_roi_mean.setText(f"Mean: {mean_val:.2f}")
            self.lbl_roi_std.setText(f"Std Dev: {std_val:.2f}")