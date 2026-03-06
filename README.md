# Thermal Science Files Viewer 🔥

Um aplicativo desktop desenvolvido em Python para visualização, calibração e análise de dados termográficos. O software permite carregar arquivos de câmeras térmicas, explorar os dados com ferramentas de Região de Interesse (ROI), aplicar calibrações personalizadas e exportar os dados brutos para análise externa.

## 📁 Estrutura do Projeto

A arquitetura do projeto foi dividida para separar a lógica de negócio da interface gráfica:

```text
📂 PROJECT
 ┣ 📂 core
 ┃ ┣ 📜 __init__.py         # Expõe o ThermalModel
 ┃ ┣ 📜 calibration.py      # Lógica de calibração polinomial do usuário
 ┃ ┗ 📜 thermal_model.py    # Gerenciamento de arquivos térmicos, frames e unidades
 ┣ 📂 icons
 ┃ ┗ ⭐️ icone.ico           # Ícone principal da aplicação
 ┣ 📂 ui
 ┃ ┣ 📜 __init__.py         # Expõe a MainWindow
 ┃ ┣ 📜 dialogs.py          # Janelas secundárias (Info, Parameters, Calibration)
 ┃ ┣ 📜 main_window.py      # Layout principal, painéis, menus e controles de player
 ┃ ┗ 📜 video_widget.py     # QGraphicsView customizado (Zoom, Drag, Desenho de ROI)
 ┣ 📂 utils
 ┃ ┣ 📜 __init__.py
 ┃ ┣ 📜 config.py           # Definição de paletas de cores (cv2.COLORMAP) e constantes
 ┃ ┗ 📜 theme.py            # CSS/QSS do tema Modern Dark
 ┣ 📜 main.py               # Ponto de entrada (Entry point) do aplicativo
 ┗ 📜 requirements.txt      # Dependências do projeto

## Pré-requisitos

Certifique-se de ter o **Python 3.8+** instalado em sua máquina. 

**Aviso sobre a biblioteca `fnv`:** O código utiliza o módulo `fnv` para leitura dos arquivos originais da câmera. Certifique-se de que o FLIR Science File SDK esteja instalado e configurado corretamente no seu ambiente Python.
