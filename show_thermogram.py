import cv2
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw

import fnv
import fnv.reduce
import fnv.file
import numpy as np

# --- CONFIGURAÇÃO DE CORES ---
COLOR_BG_VIDEO = "#000000"    # Preto (Área do vídeo)
COLOR_PANEL    = "#2e2e2e"    # Cinza Escuro (Painéis)
COLOR_TEXT     = "#ffffff"    # Branco (Texto)
COLOR_BTN      = "#444444"    # Cinza Botão
COLOR_ACCENT   = "#007bff"    # Azul (Slider e Destaques)

# --- MAPA DE PALETAS (Nomes amigáveis -> Constantes OpenCV) ---
PALETTES = {
    "Jet (Padrão)": cv2.COLORMAP_JET,
    "Ironbow": cv2.COLORMAP_INFERNO,   # Inferno é o mais próximo do Ironbow
    "Lava": cv2.COLORMAP_HOT,
    "Arctic": cv2.COLORMAP_OCEAN,
    "Rainbow": cv2.COLORMAP_RAINBOW,
    "Viridis": cv2.COLORMAP_VIRIDIS,
    "Plasma": cv2.COLORMAP_PLASMA,
    "Bone (P&B)": cv2.COLORMAP_BONE,
    "Deep Green": cv2.COLORMAP_DEEPGREEN
}

# --- FUNÇÕES AUXILIARES ---

def create_circle_image(color, bg_color, size=18):
    """Cria a bolinha do slider com fundo transparente simulado."""
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((0, 0, size, size), fill=color)
    return ImageTk.PhotoImage(image)

def create_colorbar_gradient(height, colormap_id, width=40):
    """Gera o gradiente da barra de cores baseado na paleta escolhida."""
    # Cria array vertical de 255 a 0
    gradient = np.linspace(255, 0, height).astype(np.uint8)
    gradient = np.tile(gradient, (width, 1)).T
    
    # Aplica a paleta selecionada
    colored = cv2.applyColorMap(gradient, colormap_id)
    colored = cv2.cvtColor(colored, cv2.COLOR_BGR2RGB)
    return Image.fromarray(colored)

class ThermalProPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Thermal Analysis Pro")
        self.root.configure(bg=COLOR_PANEL)
        self.root.geometry("1000x720")

        # --- Variáveis de Estado ---
        self.im = None            
        self.raw_data = None      
        self.current_frame = 0    
        self.paused = True        
        self.file_loaded = False  
        self.slider_drag_active = False
        self.gradient_pil = None
        self.current_palette = cv2.COLORMAP_JET # Paleta padrão
        
        # --- ESTILIZAÇÃO DO SLIDER ---
        style = ttk.Style(root)
        style.theme_use('clam') 
        
        self.img_normal = create_circle_image(COLOR_ACCENT, COLOR_PANEL, size=16)
        self.img_pressed = create_circle_image("#0056b3", COLOR_PANEL, size=16)
        
        try:
            style.element_create('custom.Horizontal.Scale.slider', 'image', self.img_normal,
                                 ('pressed', self.img_pressed), border=0)
        except tk.TclError: pass 

        style.layout('custom.Horizontal.TScale', [
            ('custom.Horizontal.Scale.trough', {'sticky': 'nswe'}),
            ('custom.Horizontal.Scale.slider', {'side': 'left', 'sticky': ''})
        ])
        
        style.configure('custom.Horizontal.TScale', 
                        background=COLOR_PANEL,
                        troughcolor="#505050",
                        sliderthickness=16,
                        borderwidth=0)

        # ==========================================================
        # CONSTRUÇÃO DO LAYOUT
        # ==========================================================

        # 1. TOPO (Header)
        self.top_frame = tk.Frame(root, bg=COLOR_PANEL, height=60, pady=10, padx=10)
        self.top_frame.pack(side=tk.TOP, fill=tk.X)

        # Botão Arquivo
        self.btn_load = tk.Button(self.top_frame, text="📂 Abrir", command=self.open_file,
                                  bg=COLOR_BTN, fg=COLOR_TEXT, relief=tk.FLAT, padx=10)
        self.btn_load.pack(side=tk.LEFT, padx=5)

        # Seletor de MODO (Unidade)
        tk.Label(self.top_frame, text="Modo:", bg=COLOR_PANEL, fg=COLOR_TEXT).pack(side=tk.LEFT, padx=(20, 5))
        self.unit_var = tk.StringVar(value="Counts")
        self.unit_combo = ttk.Combobox(self.top_frame, textvariable=self.unit_var, state="disabled", width=12)
        self.unit_combo['values'] = ("Counts", "Temp (K/C)", "Radiancia")
        self.unit_combo.pack(side=tk.LEFT, padx=5)
        self.unit_combo.bind("<<ComboboxSelected>>", self.change_unit)

        # --- NOVO: Seletor de PALETA ---
        tk.Label(self.top_frame, text="Paleta:", bg=COLOR_PANEL, fg=COLOR_TEXT).pack(side=tk.LEFT, padx=(20, 5))
        self.palette_var = tk.StringVar(value="Jet (Padrão)")
        self.palette_combo = ttk.Combobox(self.top_frame, textvariable=self.palette_var, state="readonly", width=15)
        self.palette_combo['values'] = list(PALETTES.keys())
        self.palette_combo.pack(side=tk.LEFT, padx=5)
        self.palette_combo.bind("<<ComboboxSelected>>", self.change_palette)
        # -------------------------------

        # 2. RODAPÉ (Footer)
        self.bottom_frame = tk.Frame(root, bg=COLOR_PANEL, height=100, pady=10, padx=20)
        self.bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.lbl_frames = tk.Label(self.bottom_frame, text="Frame: 0 / 0", 
                                   bg=COLOR_PANEL, fg="#aaaaaa", font=("Arial", 9))
        self.lbl_frames.pack(side=tk.TOP, pady=(0, 2))

        self.slider = ttk.Scale(self.bottom_frame, from_=0, to=100, orient=tk.HORIZONTAL, 
                                command=self.seek, style='custom.Horizontal.TScale')
        self.slider.pack(side=tk.TOP, fill=tk.X, pady=(0, 15))
        self.slider.state(['disabled'])
        self.slider.bind("<ButtonPress-1>", self.on_slider_press)
        self.slider.bind("<ButtonRelease-1>", self.on_slider_release)

        # Controles Play/Pause
        self.controls_container = tk.Frame(self.bottom_frame, bg=COLOR_PANEL)
        self.controls_container.pack(side=tk.TOP)

        self.btn_prev = tk.Button(self.controls_container, text="⏮", command=lambda: self.step(-1), 
                                  bg=COLOR_BTN, fg=COLOR_TEXT, relief=tk.FLAT, width=4)
        self.btn_prev.pack(side=tk.LEFT, padx=5)

        self.btn_text = tk.StringVar(value="▶")
        self.play_pause_btn = tk.Button(self.controls_container, textvariable=self.btn_text, command=self.toggle_pause, 
                                        bg=COLOR_ACCENT, fg="white", font=("Arial", 12, "bold"), relief=tk.FLAT, width=6)
        self.play_pause_btn.pack(side=tk.LEFT, padx=15)
        self.play_pause_btn.config(state="disabled", bg="#555555")

        self.btn_next = tk.Button(self.controls_container, text="⏭", command=lambda: self.step(1), 
                                  bg=COLOR_BTN, fg=COLOR_TEXT, relief=tk.FLAT, width=4)
        self.btn_next.pack(side=tk.LEFT, padx=5)

        # 3. CENTRO (Vídeo + Colorbar)
        self.center_frame = tk.Frame(root, bg=COLOR_BG_VIDEO)
        self.center_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.colorbar_canvas = tk.Canvas(self.center_frame, width=70, bg=COLOR_BG_VIDEO, highlightthickness=0)
        self.colorbar_canvas.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 10), pady=10)

        self.canvas = tk.Canvas(self.center_frame, bg=COLOR_BG_VIDEO, highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.canvas.bind("<Motion>", self.read_pixel_value)

        self.info_text_id = self.canvas.create_text(10, 10, text="", fill="white", anchor=tk.NW, font=("Consolas", 10))

        self.update_loop()

    # --- LÓGICA ---

    def open_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Thermal Files", "*.ats"), ("All Files", "*.*")])
        if not file_path: return

        try:
            self.im = fnv.file.ImagerFile(file_path)
            self.im.unit = fnv.Unit.COUNTS
            
            self.current_frame = 0
            self.file_loaded = True
            self.paused = False 
            self.btn_text.set("❚❚")
            
            self.slider.configure(to=self.im.num_frames - 1, value=0)
            self.slider.state(['!disabled'])
            self.play_pause_btn.config(state="normal", bg=COLOR_ACCENT)
            self.unit_combo.config(state="readonly")
            self.unit_var.set("Counts")
            
            self.update_frame_label()
            
            # Recria o gradiente inicial com a paleta atual
            self.refresh_gradient()
            
            self.root.title(f"Thermal Pro - {file_path.split('/')[-1]}")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir arquivo: {e}")

    def update_frame_label(self):
        if self.file_loaded:
            total = self.im.num_frames - 1
            self.lbl_frames.config(text=f"Frame: {self.current_frame} / {total}")

    def change_unit(self, event=None):
        if not self.file_loaded: return
        try:
            sel = self.unit_var.get()
            if sel == "Counts": self.im.unit = fnv.Unit.COUNTS
            elif sel.startswith("Temp"): self.im.unit = fnv.Unit.TEMPERATURE
            else: self.im.unit = fnv.Unit.RADIANCE
            if self.paused: self.show_frame()
        except: pass

    # --- NOVA LÓGICA DE PALETA ---
    def change_palette(self, event=None):
        pal_name = self.palette_var.get()
        if pal_name in PALETTES:
            self.current_palette = PALETTES[pal_name]
            
            # Se já tem arquivo, recria o gradiente da barra lateral e atualiza tela
            if self.file_loaded:
                self.refresh_gradient()
                if self.paused:
                    self.show_frame()

    def refresh_gradient(self):
        """Recria o gradiente da barra de cores com a paleta nova"""
        self.gradient_pil = create_colorbar_gradient(height=500, colormap_id=self.current_palette, width=30)
    # -----------------------------

    def toggle_pause(self):
        if not self.file_loaded: return
        self.paused = not self.paused
        self.btn_text.set("▶" if self.paused else "❚❚")

    def step(self, direction):
        if not self.file_loaded: return
        self.paused = True
        self.btn_text.set("▶")
        self.current_frame += direction
        self.current_frame = max(0, min(self.current_frame, self.im.num_frames - 1))
        self.show_frame()
        self.slider.set(self.current_frame)
        self.update_frame_label()

    def seek(self, value):
        if not self.file_loaded: return
        self.current_frame = int(float(value))
        self.update_frame_label()
        if self.paused or self.slider_drag_active:
            self.show_frame()

    def on_slider_press(self, event): self.slider_drag_active = True
    def on_slider_release(self, event): self.slider_drag_active = False

    def read_pixel_value(self, event):
        if not self.file_loaded or self.raw_data is None: return
        
        c_w, c_h = self.canvas.winfo_width(), self.canvas.winfo_height()
        im_w, im_h = self.im.width, self.im.height
        dx = (c_w - im_w) // 2
        dy = (c_h - im_h) // 2
        ix, iy = event.x - dx, event.y - dy

        if 0 <= ix < im_w and 0 <= iy < im_h:
            val = self.raw_data[iy, ix]
            unit = self.unit_var.get()
            txt_val = f"{int(val)}" if unit == "Counts" else f"{val:.2f}"
            self.canvas.itemconfigure(self.info_text_id, text=f"X:{ix} Y:{iy} | {txt_val} {unit}")
        else:
            self.canvas.itemconfigure(self.info_text_id, text="")

    def draw_colorbar(self, min_v, max_v):
        w, h = self.colorbar_canvas.winfo_width(), self.colorbar_canvas.winfo_height()
        if h < 50: return

        grad_resize = self.gradient_pil.resize((30, h - 40))
        self.tk_grad = ImageTk.PhotoImage(grad_resize)
        
        self.colorbar_canvas.delete("all")
        self.colorbar_canvas.create_image(w//2, h//2, image=self.tk_grad)
        
        unit = self.unit_var.get()
        fmt = "{:.0f}" if unit == "Counts" else "{:.1f}"
        
        self.colorbar_canvas.create_text(w//2, 12, text=fmt.format(max_v), fill="white", font=("Arial", 9, "bold"))
        self.colorbar_canvas.create_text(w//2, h-12, text=fmt.format(min_v), fill="white", font=("Arial", 9, "bold"))

    def show_frame(self):
        if not self.file_loaded: return

        self.im.get_frame(self.current_frame)
        self.raw_data = np.array(self.im.final, copy=False).reshape((self.im.height, self.im.width))
        
        min_v, max_v = self.raw_data.min(), self.raw_data.max()
        
        data_norm = cv2.normalize(self.raw_data, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
        
        # AQUI USAMOS A PALETA SELECIONADA
        color_frame = cv2.applyColorMap(data_norm, self.current_palette)
        
        color_frame = cv2.cvtColor(color_frame, cv2.COLOR_BGR2RGB)
        
        self.photo = ImageTk.PhotoImage(image=Image.fromarray(color_frame))
        
        c_w, c_h = self.canvas.winfo_width(), self.canvas.winfo_height()
        self.canvas.delete("img_tag")
        self.canvas.create_image(c_w//2, c_h//2, image=self.photo, tags="img_tag")
        self.canvas.tag_raise(self.info_text_id)

        self.draw_colorbar(min_v, max_v)

    def update_loop(self):
        if self.file_loaded and not self.paused and not self.slider_drag_active:
            self.show_frame()
            self.slider.set(self.current_frame)
            self.update_frame_label()
            
            self.current_frame += 1
            if self.current_frame >= self.im.num_frames:
                self.current_frame = 0 
        
        self.root.after(33, self.update_loop)

if __name__ == "__main__":
    root = tk.Tk()
    player = ThermalProPlayer(root)
    root.mainloop()