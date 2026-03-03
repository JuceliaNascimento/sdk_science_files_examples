import cv2

# --- CONFIGURAÇÃO DE CORES (Estilo Dark) ---
BG_COLOR = "#1e1e1e"
PANEL_COLOR = "#2d2d30"
TEXT_COLOR = "#ffffff"

# --- PALETAS DE CORES ---
PALETTES = {
    "Ironbow": cv2.COLORMAP_INFERNO,
    "Jet": cv2.COLORMAP_JET,
    "Lava": cv2.COLORMAP_HOT,
    "Arctic": cv2.COLORMAP_OCEAN,
    "Rainbow": cv2.COLORMAP_RAINBOW,
    "Viridis": cv2.COLORMAP_VIRIDIS,
    "Bone (P&B)": cv2.COLORMAP_BONE,
}