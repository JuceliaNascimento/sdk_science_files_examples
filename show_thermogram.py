import cv2
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw
import fnv
import fnv.reduce
import fnv.file
import numpy as np
import os
import csv

# --- CONFIGURAÇÃO DE CORES (DARK THEME) ---
COLOR_BG_VIDEO = "#000000"    
COLOR_PANEL    = "#2e2e2e"    
COLOR_WINDOW   = "#3e3e3e"    
COLOR_TEXT     = "#ffffff"    
COLOR_BTN      = "#444444"    
COLOR_ACCENT   = "#007bff"    

# --- MAPA DE PALETAS ---
PALETTES = {
    "Jet (Padrão)": cv2.COLORMAP_JET,
    "Ironbow": cv2.COLORMAP_INFERNO,
    "Lava": cv2.COLORMAP_HOT,
    "Arctic": cv2.COLORMAP_OCEAN,
    "Rainbow": cv2.COLORMAP_RAINBOW,
    "Viridis": cv2.COLORMAP_VIRIDIS,
    "Bone (P&B)": cv2.COLORMAP_BONE,
}

def create_circle_image(color, size=16):
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((0, 0, size, size), fill=color)
    return ImageTk.PhotoImage(image)

def create_colorbar_gradient(height, colormap_id, width=30):
    gradient = np.linspace(255, 0, height).astype(np.uint8)
    gradient = np.tile(gradient, (width, 1)).T
    colored = cv2.applyColorMap(gradient, colormap_id)
    colored = cv2.cvtColor(colored, cv2.COLOR_BGR2RGB)
    return Image.fromarray(colored)

class ThermalProPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("CEMTEC Science File")
        self.root.geometry("1100x750")
        self.root.configure(bg=COLOR_PANEL)

        # --- GESTÃO DE DIRETÓRIO E ÍCONES ---
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Ícone da Janela Principal
        try:
            icon_path = os.path.join(script_dir, "icone.jpg")
            icon_img = ImageTk.PhotoImage(Image.open(icon_path))
            self.root.iconphoto(True, icon_img)
        except: pass

        # --- ESTADO DO SISTEMA ---
        self.im = None            
        self.raw_data = None      
        self.current_frame = 0    
        self.paused = True        
        self.file_loaded = False  
        self.slider_drag_active = False
        self.current_palette = cv2.COLORMAP_JET 
        self.win_info = self.win_params = self.win_stats = None

        # --- ESTILIZAÇÃO DO SLIDER ---
        style = ttk.Style(root)
        style.theme_use('clam')
        self.img_normal = create_circle_image(COLOR_ACCENT)
        self.img_pressed = create_circle_image("#0056b3")
        
        try:
            style.element_create('custom.Horizontal.Scale.slider', 'image', self.img_normal, ('pressed', self.img_pressed))
        except: pass

        style.layout('custom.Horizontal.TScale', [
            ('custom.Horizontal.Scale.trough', {'sticky': 'nswe'}),
            ('custom.Horizontal.Scale.slider', {'side': 'left', 'sticky': ''})
        ])
        style.configure('custom.Horizontal.TScale', background=COLOR_PANEL, troughcolor="#505050", sliderthickness=16)

        # --- INTERFACE (TOPO) ---
        self.top_frame = tk.Frame(root, bg=COLOR_PANEL, pady=10, padx=10)
        self.top_frame.pack(side=tk.TOP, fill=tk.X)

        tk.Button(self.top_frame, text="📂 Abrir", command=self.open_file, bg=COLOR_BTN, fg="white", relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        
        self.unit_var = tk.StringVar(value="Counts")
        self.unit_combo = ttk.Combobox(self.top_frame, textvariable=self.unit_var, state="disabled", width=10)
        self.unit_combo['values'] = ("Counts", "Temp (K/C)", "Radiancia")
        self.unit_combo.pack(side=tk.LEFT, padx=10)
        self.unit_combo.bind("<<ComboboxSelected>>", self.change_unit)

        self.palette_var = tk.StringVar(value="Jet (Padrão)")
        self.palette_combo = ttk.Combobox(self.top_frame, textvariable=self.palette_var, state="readonly", width=12)
        self.palette_combo['values'] = list(PALETTES.keys())
        self.palette_combo.pack(side=tk.LEFT, padx=5)
        self.palette_combo.bind("<<ComboboxSelected>>", self.change_palette)

        tk.Button(self.top_frame, text="ℹ️ Info", command=self.open_window_info, bg=COLOR_BTN, fg="white", relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        tk.Button(self.top_frame, text="⚙️ Params", command=self.open_window_params, bg=COLOR_BTN, fg="white", relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        tk.Button(self.top_frame, text="📊 Stats", command=self.open_window_stats, bg=COLOR_BTN, fg="white", relief=tk.FLAT).pack(side=tk.LEFT, padx=2)

        # --- ÁREA CENTRAL ---
        self.main_container = tk.Frame(root, bg=COLOR_BG_VIDEO)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        self.colorbar_canvas = tk.Canvas(self.main_container, width=60, bg=COLOR_BG_VIDEO, highlightthickness=0)
        self.colorbar_canvas.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=10)

        self.canvas = tk.Canvas(self.main_container, bg=COLOR_BG_VIDEO, highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas.bind("<Motion>", self.read_pixel_value)
        self.info_text_id = self.canvas.create_text(10, 10, text="", fill="white", anchor=tk.NW, font="Consolas 10")

        # --- RODAPÉ ---
        self.bottom_frame = tk.Frame(root, bg=COLOR_PANEL, pady=10, padx=20)
        self.bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.lbl_frames = tk.Label(self.bottom_frame, text="Frame: 0 / 0", bg=COLOR_PANEL, fg="#aaaaaa", font="Arial 9")
        self.lbl_frames.pack()

        self.slider = ttk.Scale(self.bottom_frame, from_=0, to=100, orient=tk.HORIZONTAL, command=self.seek, style='custom.Horizontal.TScale')
        self.slider.pack(fill=tk.X, pady=10)
        self.slider.bind("<ButtonPress-1>", lambda e: setattr(self, 'slider_drag_active', True))
        self.slider.bind("<ButtonRelease-1>", lambda e: setattr(self, 'slider_drag_active', False))

        # CONTROLES (Aqui corrigimos o erro de referência)
        self.controls_container = tk.Frame(self.bottom_frame, bg=COLOR_PANEL)
        self.controls_container.pack()

        tk.Button(self.controls_container, text="⏮", command=lambda: self.step(-1), bg=COLOR_BTN, fg="white", relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        
        self.btn_play_txt = tk.StringVar(value="▶")
        self.play_btn = tk.Button(self.controls_container, textvariable=self.btn_play_txt, command=self.toggle_pause, bg=COLOR_ACCENT, fg="white", width=6, relief=tk.FLAT)
        self.play_btn.pack(side=tk.LEFT, padx=10)
        
        tk.Button(self.controls_container, text="⏭", command=lambda: self.step(1), bg=COLOR_BTN, fg="white", relief=tk.FLAT).pack(side=tk.LEFT, padx=5)

        # Ícone Exportar CSV
        try:
            exp_path = os.path.join(script_dir, "export_icon.png")
            exp_img = Image.open(exp_path).resize((20, 20))
            self.tk_export_icon = ImageTk.PhotoImage(exp_img)
            tk.Button(self.controls_container, image=self.tk_export_icon, command=self.export_to_csv, bg=COLOR_BTN, relief=tk.FLAT).pack(side=tk.LEFT, padx=20)
        except: pass

        self.update_loop()

    # --- FUNÇÕES DE EXPORTAÇÃO E LOGICA ---
    def export_to_csv(self):
        """Exporta o frame atual para CSV."""
        if not self.file_loaded or self.raw_data is None: return
        f_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if f_path:
            with open(f_path, 'w', newline='') as f:
                csv.writer(f).writerows(self.raw_data)
            messagebox.showinfo("Sucesso", "CSV Exportado!")

    def open_file(self):
        path = filedialog.askopenfilename(filetypes=[("ATS Files", "*.ats")])
        if path:
            self.im = fnv.file.ImagerFile(path)
            self.im.unit = fnv.Unit.COUNTS
            self.file_loaded = True
            self.paused = False
            self.btn_play_txt.set("❚❚")
            self.unit_combo.config(state="readonly")
            self.slider.config(to=self.im.num_frames-1, state="normal")
            self.play_btn.config(state="normal", bg=COLOR_ACCENT)
            self.refresh_gradient()

    def change_unit(self, e=None):
        if not self.file_loaded: return
        sel = self.unit_var.get()
        self.im.unit = fnv.Unit.COUNTS if sel == "Counts" else fnv.Unit.TEMPERATURE_FACTORY if "Temp" in sel else fnv.Unit.RADIANCE_FACTORY
        if self.paused: self.show_frame()

    def change_palette(self, e=None):
        self.current_palette = PALETTES.get(self.palette_var.get(), cv2.COLORMAP_JET)
        if self.file_loaded:
            self.refresh_gradient()
            if self.paused: self.show_frame()

    def refresh_gradient(self):
        self.gradient_pil = create_colorbar_gradient(500, self.current_palette)

    def toggle_pause(self):
        self.paused = not self.paused
        self.btn_play_txt.set("▶" if self.paused else "❚❚")

    def seek(self, val):
        if self.file_loaded:
            self.current_frame = int(float(val))
            if self.paused or self.slider_drag_active: self.show_frame()

    def step(self, d):
        if self.file_loaded:
            self.current_frame = max(0, min(self.current_frame + d, self.im.num_frames - 1))
            self.slider.set(self.current_frame)
            self.show_frame()

    def show_frame(self):
        if not self.file_loaded: return
        self.im.get_frame(self.current_frame)
        self.raw_data = np.array(self.im.final, copy=False).reshape((self.im.height, self.im.width))
        
        norm = cv2.normalize(self.raw_data, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
        color = cv2.applyColorMap(norm, self.current_palette)
        rgb = cv2.cvtColor(color, cv2.COLOR_BGR2RGB)
        
        self.photo = ImageTk.PhotoImage(Image.fromarray(rgb))
        self.canvas.delete("img")
        self.canvas.create_image(self.canvas.winfo_width()//2, self.canvas.winfo_height()//2, image=self.photo, tags="img")
        self.canvas.tag_raise(self.info_text_id)
        
        self.lbl_frames.config(text=f"Frame: {self.current_frame} / {self.im.num_frames-1}")
        self.draw_colorbar(self.raw_data.min(), self.raw_data.max())
        if self.win_stats: self.update_stats_ui(self.raw_data)

    def draw_colorbar(self, mn, mx):
        h = self.colorbar_canvas.winfo_height()
        if h < 50 or self.gradient_pil is None: return
        grad = ImageTk.PhotoImage(self.gradient_pil.resize((25, h-40)))
        self.colorbar_canvas.delete("all")
        self.colorbar_canvas.create_image(30, h//2, image=grad)
        self.colorbar_canvas.image = grad # Keep reference
        fmt = "{:.0f}" if self.unit_var.get() == "Counts" else "{:.1f}"
        self.colorbar_canvas.create_text(30, 15, text=fmt.format(mx), fill="white")
        self.colorbar_canvas.create_text(30, h-15, text=fmt.format(mn), fill="white")

    def read_pixel_value(self, e):
        if not self.file_loaded or self.raw_data is None: return
        dx = (self.canvas.winfo_width() - self.im.width) // 2
        dy = (self.canvas.winfo_height() - self.im.height) // 2
        ix, iy = e.x - dx, e.y - dy
        if 0 <= ix < self.im.width and 0 <= iy < self.im.height:
            val = self.raw_data[iy, ix]
            txt = f"{int(val)}" if self.unit_var.get() == "Counts" else f"{val:.2f}"
            self.canvas.itemconfigure(self.info_text_id, text=f"X:{ix} Y:{iy} | {txt}")

    # --- JANELAS FLUTUANTES (SKELETON) ---
    def open_window_info(self):
        if not self.win_info:
            self.win_info = tk.Toplevel(self.root, bg=COLOR_WINDOW)
            self.win_info.title("Info")
            self.win_info.geometry("300x200")
            self.win_info.protocol("WM_DELETE_WINDOW", lambda: self.close_win('win_info'))
            if self.file_loaded: tk.Label(self.win_info, text=f"Cam: {self.im.source_info.camera_model}", bg=COLOR_WINDOW, fg="white").pack(pady=10)

    def open_window_params(self):
        if not self.win_params:
            self.win_params = tk.Toplevel(self.root, bg=COLOR_WINDOW)
            self.win_params.title("Params")
            self.win_params.geometry("250x200")
            self.win_params.protocol("WM_DELETE_WINDOW", lambda: self.close_win('win_params'))
            tk.Label(self.win_params, text="Emissividade:", bg=COLOR_WINDOW, fg="white").pack()
            e = tk.Entry(self.win_params); e.pack(); e.insert(0, "0.95")

    def open_window_stats(self):
        if not self.win_stats:
            self.win_stats = tk.Toplevel(self.root, bg=COLOR_WINDOW)
            self.win_stats.title("Stats")
            self.win_stats.geometry("200x150")
            self.win_stats.protocol("WM_DELETE_WINDOW", lambda: self.close_win('win_stats'))
            self.lbl_s = tk.Label(self.win_stats, text="Máx: --", bg=COLOR_WINDOW, fg="white", font="Arial 12")
            self.lbl_s.pack(pady=20)

    def update_stats_ui(self, data):
        if hasattr(self, 'lbl_s'): self.lbl_s.config(text=f"Máx: {data.max():.1f}")

    def close_win(self, name):
        getattr(self, name).destroy()
        setattr(self, name, None)

    def update_loop(self):
        if self.file_loaded and not self.paused and not self.slider_drag_active:
            self.show_frame()
            self.slider.set(self.current_frame)
            self.current_frame = (self.current_frame + 1) % self.im.num_frames
        self.root.after(33, self.update_loop)

if __name__ == "__main__":
    root = tk.Tk()
    app = ThermalProPlayer(root)
    root.mainloop()