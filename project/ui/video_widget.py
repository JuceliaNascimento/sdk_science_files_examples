import cv2
import numpy as np
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsRectItem, QGraphicsEllipseItem
from PySide6.QtGui import QImage, QPixmap, QPen, QColor, QWheelEvent, QMouseEvent
from PySide6.QtCore import Qt, Signal, QRectF

class ThermalVideoWidget(QGraphicsView):
    pixel_hovered = Signal(int, int)
    stats_updated = Signal(float, float) # Emite (Média, Desvio Padrão)

    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # Configurações para zoom suave e drag (pan)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setStyleSheet("background-color: #000000; border: none;")

        self.pixmap_item = QGraphicsPixmapItem()
        self.scene.addItem(self.pixmap_item)

        self.raw_data = None
        self.current_roi = None
        self.roi_type = "None" # Pode ser "None", "Rect" ou "Circle"
        self.start_pos = None

    def update_image(self, raw_data, colormap):
        self.raw_data = raw_data
        if self.raw_data is None: return

        # Normaliza e aplica cor
        norm = cv2.normalize(self.raw_data, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
        color = cv2.applyColorMap(norm, colormap)
        rgb = cv2.cvtColor(color, cv2.COLOR_BGR2RGB)

        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        self.pixmap_item.setPixmap(QPixmap.fromImage(qimg))
        
        # Atualiza os cálculos caso exista um ROI desenhado
        self.calculate_roi_stats()

    def set_roi_mode(self, mode):
        self.roi_type = mode
        if mode == "None":
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            self.clear_roi()
        else:
            self.setDragMode(QGraphicsView.NoDrag) # Desativa o Pan para poder desenhar

    def clear_roi(self):
        if self.current_roi:
            self.scene.removeItem(self.current_roi)
            self.current_roi = None
            self.stats_updated.emit(0.0, 0.0)

    # --- EVENTOS DE MOUSE (ZOOM E DESENHO) ---

    def wheelEvent(self, event: QWheelEvent):
        # Controle de Zoom com a roda do mouse
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor
        if event.angleDelta().y() > 0:
            self.scale(zoom_in_factor, zoom_in_factor)
        else:
            self.scale(zoom_out_factor, zoom_out_factor)

    def mousePressEvent(self, event: QMouseEvent):
        if self.roi_type != "None" and event.button() == Qt.LeftButton:
            self.clear_roi()
            self.start_pos = self.mapToScene(event.position().toPoint())
            
            pen = QPen(QColor(0, 255, 0)) # Borda verde
            pen.setWidth(2)
            
            if self.roi_type == "Rect":
                self.current_roi = self.scene.addRect(QRectF(self.start_pos, self.start_pos), pen)
            elif self.roi_type == "Circle":
                self.current_roi = self.scene.addEllipse(QRectF(self.start_pos, self.start_pos), pen)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        # Emite a posição do pixel para o MainWindow
        scene_pos = self.mapToScene(event.position().toPoint())
        x, y = int(scene_pos.x()), int(scene_pos.y())
        if self.raw_data is not None and 0 <= x < self.raw_data.shape[1] and 0 <= y < self.raw_data.shape[0]:
            self.pixel_hovered.emit(x, y)

        # Atualiza o desenho do ROI
        if self.current_roi and self.start_pos and event.buttons() == Qt.LeftButton:
            current_pos = scene_pos
            rect = QRectF(self.start_pos, current_pos).normalized()
            if self.roi_type == "Rect":
                self.current_roi.setRect(rect)
            elif self.roi_type == "Circle":
                self.current_roi.setRect(rect)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self.current_roi and event.button() == Qt.LeftButton:
            self.calculate_roi_stats()
        super().mouseReleaseEvent(event)

    # --- LÓGICA MATEMÁTICA ---

    def calculate_roi_stats(self):
        if not self.current_roi or self.raw_data is None: return

        rect = self.current_roi.rect()
        x1, y1 = int(max(0, rect.left())), int(max(0, rect.top()))
        x2, y2 = int(min(self.raw_data.shape[1], rect.right())), int(min(self.raw_data.shape[0], rect.bottom()))

        if x1 >= x2 or y1 >= y2: return # Seleção vazia

        roi_data = self.raw_data[y1:y2, x1:x2]

        if self.roi_type == "Circle":
            # Cria uma máscara circular para o array NumPy
            h, w = roi_data.shape
            cx, cy = w / 2, h / 2
            a, b = w / 2, h / 2 # Raios da elipse
            Y, X = np.ogrid[:h, :w]
            mask = ((X - cx)**2 / (a**2 + 1e-6) + (Y - cy)**2 / (b**2 + 1e-6)) <= 1
            valid_pixels = roi_data[mask]
        else:
            # Retângulo (usa todos os pixels do slice)
            valid_pixels = roi_data

        if valid_pixels.size > 0:
            mean_val = np.mean(valid_pixels)
            std_val = np.std(valid_pixels)
            self.stats_updated.emit(mean_val, std_val)