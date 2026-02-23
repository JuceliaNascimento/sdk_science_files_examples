import fnv
import fnv.reduce
import fnv.file
import pandas as pd
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os

class ProcessadorTermico:
    """Responsável por lidar com a biblioteca FNV e processamento de dados."""
    
    def __init__(self):
        self.imagem_atual = None

    def carregar_arquivo(self, caminho):
        try:
            self.imagem_atual = fnv.file.ImagerFile(caminho)
            return True
        except Exception as e:
            print(f"Erro ao carregar arquivo: {e}")
            return False

    def obter_parametros(self):
        """Extrai os metadados e retorna um DataFrame limpo."""
        if not self.imagem_atual:
            return pd.DataFrame()

        obj_params = self.imagem_atual.object_parameters
        propriedades = dir(obj_params)
        
        # Filtra propriedades privadas (que começam com __)
        propriedades = [x for x in propriedades if not x.startswith("__")]
        
        # Usa getattr (mais seguro e limpo que eval em classes)
        valores = [getattr(obj_params, x) for x in propriedades]

        # Cria o DataFrame
        df = pd.DataFrame({
            "Propriedade": propriedades,
            "Valor": valores
        })

        # Limpeza de texto
        df['Propriedade'] = df['Propriedade'].str.replace('_', ' ', regex=False).str.capitalize()
        df['Valor'] = df['Valor'].apply(lambda x: f"{x:.1f}" if isinstance(x, float) else x)
        
        return df

class InterfaceGrafica(tk.Tk):
    """Responsável apenas pela exibição e interação com o usuário."""
    
    def __init__(self):
        super().__init__() 
        self.processador = ProcessadorTermico() 
        
        self.configurar_janela()
        self.criar_widgets()
        
    def configurar_janela(self):
        self.title("Propriedades do termograma")
        self.geometry("500x300")

    def criar_widgets(self):
        # Frame superior para botões
        frame_topo = tk.Frame(self, pady=10)
        frame_topo.pack(side="top", fill="x")

        btn_carregar = tk.Button(frame_topo, text="Carregar arquivo radiométrico", command=self.fluxo_abrir_arquivo)
        btn_carregar.pack()

        # Frame para a tabela
        frame_tabela = tk.Frame(self, padx=10, pady=10)
        frame_tabela.pack(fill="both", expand=True)

        # Configuração da Treeview (Tabela)
        colunas = ("Propriedade", "Valor")
        self.tree = ttk.Treeview(frame_tabela, columns=colunas, show='headings')
        
        # Cabeçalhos
        self.tree.heading("Propriedade", text="Propriedade")
        self.tree.heading("Valor", text="Valor")
        self.tree.column("Propriedade", width=300)
        self.tree.column("Valor", width=400)

        # Barra de rolagem
        scrollbar = ttk.Scrollbar(frame_tabela, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def fluxo_abrir_arquivo(self):
        """Gerencia o processo de pedir o arquivo e atualizar a tela."""
        caminho_arquivo = filedialog.askopenfilename(
            title="Selecione o arquivo térmico",
            filetypes=[("Arquivos radiométricos", "*.ats *.jpg"), ("Todos os arquivos", "*.*")]
        )

        if not caminho_arquivo:
            return

        # Chama a classe de lógica para carregar
        sucesso = self.processador.carregar_arquivo(caminho_arquivo)
        
        if sucesso:
            df = self.processador.obter_parametros()
            self.atualizar_tabela(df)
            self.title(f"Visualizando: {os.path.basename(caminho_arquivo)}")
        else:
            messagebox.showerror("Erro", "Não foi possível ler o arquivo selecionado.")

    def atualizar_tabela(self, df):
        """Limpa a tabela antiga e insere os novos dados."""
        # Limpa dados anteriores
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Insere novos dados
        for index, row in df.iterrows():
            self.tree.insert("", "end", values=list(row))

# --- EXECUÇÃO ---
if __name__ == "__main__":
    app = InterfaceGrafica()
    app.mainloop()