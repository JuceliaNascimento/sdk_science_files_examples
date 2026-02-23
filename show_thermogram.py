import cv2
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw
import sys
import fnv
import fnv.reduce
import fnv.file
import numpy as np
import os
import csv
import pandas as pd # Adicionado para suportar a tua lógica de DataFrame

# --- CONFIGURAÇÃO DE CORES ---
COLOR_BG_VIDEO = "#000000"    
COLOR_PANEL    = "#2e2e2e"    
COLOR_WINDOW   = "#3e3e3e"    
COLOR_TEXT     = "#ffffff"    
COLOR_BTN      = "#444444"    
COLOR_ACCENT   = "#007bff"    

PALETTES = {
    "Jet (Padrão)": cv2.COLORMAP_JET,
    "Ironbow": cv2.COLORMAP_INFERNO,
    "Lava": cv2.COLORMAP_HOT,
    "Arctic": cv2.COLORMAP_OCEAN,
    "Rainbow": cv2.COLORMAP_RAINBOW,
    "Viridis": cv2.COLORMAP_VIRIDIS,
    "Bone (P&B)": cv2.COLORMAP_BONE,
}

def resource_path(relative_path):
    """ Retorna o caminho absoluto para recursos, funcionando em dev e como exe """
    try:
        # O PyInstaller cria uma pasta temporária e armazena o caminho em _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class ThermalProPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Thermal Analysis Pro")
        self.root.geometry("1100x750")
        self.root.configure(bg=COLOR_PANEL)

        script_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = resource_path("icone.jpg")
        # Ícone da Janela Principal
        try:
            icon_path = os.path.join(script_dir, "icone.jpg")
            icon_img = ImageTk.PhotoImage(Image.open(icon_path))
            self.root.iconphoto(True, icon_img)
        except: pass

        self.im = None            
        self.raw_data = None      
        self.current_frame = 0    
        self.paused = True        
        self.file_loaded = False  
        self.slider_drag_active = False
        self.current_palette = cv2.COLORMAP_JET 
        self.win_info = self.win_params = self.win_stats = None

        # --- LAYOUT TOPO ---
        self.top_frame = tk.Frame(root, bg=COLOR_PANEL, pady=10, padx=10)
        self.top_frame.pack(side=tk.TOP, fill=tk.X)

        tk.Button(self.top_frame, text="📂 Abrir", command=self.open_file, bg=COLOR_BTN, fg="white", relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        
        self.unit_var = tk.StringVar(value="Counts")
        self.unit_combo = ttk.Combobox(self.top_frame, textvariable=self.unit_var, state="disabled", width=12)
        self.unit_combo['values'] = ("Counts", "Temp (K/C)", "Radiancia")
        self.unit_combo.pack(side=tk.LEFT, padx=10)
        self.unit_combo.bind("<<ComboboxSelected>>", self.change_unit)

        self.palette_var = tk.StringVar(value="Jet (Padrão)")
        self.palette_combo = ttk.Combobox(self.top_frame, textvariable=self.palette_var, state="readonly", width=15)
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

        self.slider = ttk.Scale(self.bottom_frame, from_=0, to=100, orient=tk.HORIZONTAL, command=self.seek)
        self.slider.pack(fill=tk.X, pady=10)

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
            exp_img = ImageTk.PhotoImage(Image.open(exp_path).resize((22, 22)))
            self.tk_export_icon = exp_img
            tk.Button(self.controls_container, image=self.tk_export_icon, command=self.export_to_csv, bg=COLOR_BTN, relief=tk.FLAT).pack(side=tk.LEFT, padx=20)
        except: pass

        self.update_loop()

    # ==========================================================
    # A TUA LÓGICA DE EXTRAÇÃO (ADAPTADA)
    # ==========================================================
    def obter_parametros(self):
        """Extrai os metadados e retorna um DataFrame limpo (Lógica proposta pelo usuário)."""
        if not self.file_loaded:
            return pd.DataFrame()

        obj_params = self.im.object_parameters # self.im é o teu imagem_atual
        propriedades = dir(obj_params)
        
        # Filtra propriedades privadas
        propriedades = [x for x in propriedades if not x.startswith("__")]
        
        # Filtra para manter apenas propriedades de dados (evitar métodos)
        # Nota: no fnv, os parâmetros úteis costumam ser floats ou ints
        valores = []
        propriedades_validas = []
        for x in propriedades:
            val = getattr(obj_params, x)
            if isinstance(val, (int, float, str)) and not callable(val):
                valores.append(val)
                propriedades_validas.append(x)

        # Cria o DataFrame
        df = pd.DataFrame({
            "Propriedade": propriedades_validas,
            "Valor": valores
        })

        # Limpeza de texto conforme proposto
        df['Propriedade'] = df['Propriedade'].str.replace('_', ' ', regex=False).str.capitalize()
        df['Valor'] = df['Valor'].apply(lambda x: f"{x:.4f}" if isinstance(x, float) else x)
        
        return df

    # ==========================================================
    # GESTÃO DAS JANELAS FLUTUANTES
    # ==========================================================
    def open_window_params(self):
        if self.win_params: self.win_params.lift(); return
        
        self.win_params = tk.Toplevel(self.root, bg=COLOR_WINDOW)
        self.win_params.title("Parâmetros do Objeto (Lógica Dinâmica)")
        self.win_params.geometry("450x400")
        self.win_params.protocol("WM_DELETE_WINDOW", lambda: self.close_win('win_params'))

        # Criar a tabela para exibir o DataFrame
        cols = ("Propriedade", "Valor")
        self.tree_params = ttk.Treeview(self.win_params, columns=cols, show="headings")
        self.tree_params.heading("Propriedade", text="Propriedade")
        self.tree_params.heading("Valor", text="Valor")
        self.tree_params.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Button(self.win_params, text="🔄 Atualizar via dir()", command=self.refresh_params_table, 
                  bg=COLOR_ACCENT, fg="white", relief=tk.FLAT).pack(pady=5)
        
        self.refresh_params_table()

    def refresh_params_table(self):
        """Usa a tua lógica de DataFrame para popular a Treeview."""
        if not self.file_loaded or not self.win_params: return
        
        # Limpa tabela atual
        for i in self.tree_params.get_children(): self.tree_params.delete(i)
        
        # Obtém o DataFrame usando a tua lógica
        df = self.obter_parametros()
        
        # Insere as linhas do DataFrame na Treeview
        for _, row in df.iterrows():
            self.tree_params.insert("", tk.END, values=(row['Propriedade'], row['Valor']))

    # ==========================================================
    # RESTANTE DAS FUNÇÕES (FRAMEWORK)
    # ==========================================================
    def open_file(self):
        path = filedialog.askopenfilename(filetypes=[("ATS Files", "*.ats")])
        if path:
            self.im = fnv.file.ImagerFile(path)
            self.im.unit = fnv.Unit.COUNTS
            self.file_loaded = True
            self.paused = False
            self.unit_combo.config(state="readonly")
            self.slider.config(to=self.im.num_frames-1)
            self.play_btn.config(state="normal")
            self.refresh_gradient()

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
        
        self.lbl_frames.config(text=f"Frame: {self.current_frame} / {self.im.num_frames-1}")
        self.draw_colorbar(self.raw_data.min(), self.raw_data.max())

    def export_to_csv(self):
        if not self.file_loaded or self.raw_data is None: return
        f_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if f_path:
            pd.DataFrame(self.raw_data).to_csv(f_path, index=False, header=False)
            messagebox.showinfo("Sucesso", "CSV Exportado via Pandas!")

    def draw_colorbar(self, mn, mx):
        h = self.colorbar_canvas.winfo_height()
        if h < 50 or not hasattr(self, 'gradient_pil'): return
        grad = ImageTk.PhotoImage(self.gradient_pil.resize((25, h-40)))
        self.colorbar_canvas.delete("all")
        self.colorbar_canvas.create_image(30, h//2, image=grad)
        self.colorbar_canvas.image = grad
        fmt = "{:.1f}"
        self.colorbar_canvas.create_text(30, 15, text=fmt.format(mx), fill="white")
        self.colorbar_canvas.create_text(30, h-15, text=fmt.format(mn), fill="white")

    def change_unit(self, e=None):
        if not self.file_loaded: return
        sel = self.unit_var.get()
        if sel == "Counts": self.im.unit = fnv.Unit.COUNTS
        elif "Temp" in sel: self.im.unit = fnv.Unit.TEMPERATURE_FACTORY
        else: self.im.unit = fnv.Unit.RADIANCE_FACTORY
        if self.paused: self.show_frame()

    def change_palette(self, e=None):
        self.current_palette = PALETTES.get(self.palette_var.get(), cv2.COLORMAP_JET)
        if self.file_loaded:
            self.refresh_gradient()
            if self.paused: self.show_frame()

    def refresh_gradient(self):
        gradient = np.linspace(255, 0, 500).astype(np.uint8)
        gradient = np.tile(gradient, (30, 1)).T
        colored = cv2.applyColorMap(gradient, self.current_palette)
        self.gradient_pil = Image.fromarray(cv2.cvtColor(colored, cv2.COLOR_BGR2RGB))

    def read_pixel_value(self, e):
        if not self.file_loaded or self.raw_data is None: return
        dx = (self.canvas.winfo_width() - self.im.width) // 2
        dy = (self.canvas.winfo_height() - self.im.height) // 2
        ix, iy = e.x - dx, e.y - dy
        if 0 <= ix < self.im.width and 0 <= iy < self.im.height:
            val = self.raw_data[iy, ix]
            self.canvas.itemconfigure(self.info_text_id, text=f"X:{ix} Y:{iy} | Valor: {val:.2f}")

    def open_window_info(self):
        if self.win_info: self.win_info.lift(); return
        self.win_info = tk.Toplevel(self.root, bg=COLOR_WINDOW); self.win_info.title("Info")
        self.win_info.geometry("300x150")
        self.win_info.protocol("WM_DELETE_WINDOW", lambda: self.close_win('win_info'))
        if self.file_loaded: tk.Label(self.win_info, text=f"Câmera: {self.im.source_info.camera_model}", bg=COLOR_WINDOW, fg="white").pack(pady=20)

    def open_window_stats(self):
        if self.win_stats: self.win_stats.lift(); return
        self.win_stats = tk.Toplevel(self.root, bg=COLOR_WINDOW); self.win_stats.title("Stats")
        self.win_stats.geometry("200x100")
        self.win_stats.protocol("WM_DELETE_WINDOW", lambda: self.close_win('win_stats'))
        self.lbl_mx = tk.Label(self.win_stats, text="Máx: --", bg=COLOR_WINDOW, fg="white"); self.lbl_mx.pack(pady=20)

    def close_win(self, name):
        getattr(self, name).destroy()
        setattr(self, name, None)

    def toggle_pause(self):
        if self.file_loaded:
            self.paused = not self.paused
            self.btn_play_txt.set("▶" if self.paused else "❚❚")

    def seek(self, val):
        if self.file_loaded:
            self.current_frame = int(float(val))
            if self.paused: self.show_frame()

    def step(self, d):
        if self.file_loaded:
            self.current_frame = max(0, min(self.current_frame + d, self.im.num_frames - 1))
            self.slider.set(self.current_frame)
            self.show_frame()

    def update_loop(self):
        if self.file_loaded and not self.paused:
            self.show_frame()
            self.slider.set(self.current_frame)
            self.current_frame = (self.current_frame + 1) % self.im.num_frames
        self.root.after(33, self.update_loop)

if __name__ == "__main__":
    root = tk.Tk()
    app = ThermalProPlayer(root)
    root.mainloop()