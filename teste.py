import fnv
import fnv.file
import pandas as pd
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import os

# --- CLASSE 1: CÉREBRO (LÓGICA) ---
class ProcessadorTermico:
    def __init__(self):
        self.imager = None
        # Removi a lista de paletas pois o objeto não as aceita via atributo direto
        self.paletas = ["Original (Câmera)"]

    def carregar(self, caminho):
        try:
            self.imager = fnv.file.ImagerFile(caminho)
            return True
        except Exception as e:
            print(f"Erro ao carregar arquivo: {e}")
            return False

    def renderizar_imagem(self, paleta_idx=0):
        if not self.imager: 
            return None
        
        # Tenta definir a unidade para temperatura, se falhar, continua em Counts
        try:
            self.imager.unit = fnv.Unit.TEMPERATURE_FACTORY
        except:
            print("Aviso: Arquivo sem calibração de fábrica. Usando Counts.")

        try:
            # Pega o primeiro frame
            frame = self.imager.get_frame(0)
            
            # Se o sensor for cru (Counts), o '.visual' pode não estar colorido.
            # Vamos tentar pegar os dados da imagem.
            return Image.fromarray(frame.visual)
        except Exception as e:
            print(f"Erro na renderização: {e}")
            return None

    def extrair_parametros(self):
        if not self.imager: 
            return pd.DataFrame()
            
        obj_params = self.imager.object_parameters
        propriedades = [x for x in dir(obj_params) if not x.startswith("__")]
        
        dados = []
        for p in propriedades:
            try:
                valor = getattr(obj_params, p)
                dados.append({"Propriedade": p, "Valor": valor})
            except:
                continue
        
        df = pd.DataFrame(dados)
        
        if not df.empty:
            df['Propriedade'] = df['Propriedade'].str.replace('_', ' ', regex=False).str.capitalize()
            # Formata apenas se for número, ignora textos e booleanos
            df['Valor'] = df['Valor'].apply(lambda x: f"{x:.1f}" if isinstance(x, (float, int)) and not isinstance(x, bool) else x)
        
        return df

# --- CLASSE 2: JANELA DE PROPRIEDADES ---
class JanelaPropriedades(tk.Toplevel):
    def __init__(self, pai, df):
        super().__init__(pai)
        self.title("Metadados")
        self.geometry("400x500")
        
        frame = tk.Frame(self)
        frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(frame, columns=("P", "V"), show="headings")
        self.tree.heading("P", text="Propriedade")
        self.tree.heading("V", text="Valor")
        
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for _, linha in df.iterrows():
            self.tree.insert("", "end", values=list(linha))

# --- CLASSE 3: INTERFACE PRINCIPAL ---
class VisualizadorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.proc = ProcessadorTermico()
        self.foto = None 
        
        self.title("Visualizador Termográfico UFMG")
        self.geometry("900x700")
        self.configurar_layout()

    def configurar_layout(self):
        toolbar = tk.Frame(self, pady=10)
        toolbar.pack(side="top", fill="x")

        tk.Button(toolbar, text="📂 Abrir Arquivo .ATS", command=self.abrir).pack(side="left", padx=10)
        tk.Button(toolbar, text="📊 Propriedades", command=self.mostrar_props).pack(side="left", padx=10)

        self.canvas_label = tk.Label(self, text="Aguardando arquivo...", bg="black", fg="white")
        self.canvas_label.pack(fill="both", expand=True, padx=20, pady=20)

    def abrir(self):
        caminho = filedialog.askopenfilename(filetypes=[("Arquivos ATS", "*.ats")])
        if caminho and self.proc.carregar(caminho):
            self.atualizar_display()
            self.title(f"Visualizando: {os.path.basename(caminho)}")

    def atualizar_display(self):
        img_pil = self.proc.renderizar_imagem()
        if img_pil:
            img_pil.thumbnail((800, 600))
            self.foto = ImageTk.PhotoImage(img_pil)
            self.canvas_label.config(image=self.foto, text="")
        else:
            self.canvas_label.config(image="", text="Erro ao processar imagem.")

    def mostrar_props(self):
        df = self.proc.extrair_parametros()
        if not df.empty:
            JanelaPropriedades(self, df)
        else:
            messagebox.showwarning("Aviso", "Abra um arquivo primeiro!")

if __name__ == "__main__":
    app = VisualizadorApp()
    app.mainloop()