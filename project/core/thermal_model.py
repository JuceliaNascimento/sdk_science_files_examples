import fnv
import fnv.file
import fnv.reduce
import numpy as np
import pandas as pd
import os

from core.calibration import UserCalibration

class ThermalModel:
    def __init__(self):
        self.im = None
        self.file_name = ""
        self.raw_data = None
        self.num_frames = 0
        # Instancia a classe de calibração do usuário
        self.user_cal = UserCalibration()
        self.active_user_unit = None

    def load_file(self, path):
        self.file_name = os.path.splitext(os.path.basename(path))[0]
        self.im = fnv.file.ImagerFile(path)
        self.im.unit = fnv.Unit.COUNTS
        self.num_frames = self.im.num_frames
        self.active_user_unit = None
        return True

    def get_frame_data(self, frame_index):
        if not self.im: return None
        self.im.get_frame(frame_index)

        base_data = np.array(self.im.final, copy=False).reshape((self.im.height, self.im.width))
        if self.active_user_unit == "User_Temp":
            self.raw_data = self.user_cal.apply(base_data, self.user_cal.temp_coeffs)
        elif self.active_user_unit == "User_Rad":
            self.raw_data = self.user_cal.apply(base_data, self.user_cal.rad_coeffs)
        else:
            self.raw_data = base_data

        return self.raw_data

    def get_supported_units(self):
        if not self.im: return []
        unit_map = {
            fnv.Unit.COUNTS: "Counts (Raw)",
            fnv.Unit.RADIANCE_FACTORY: "Radiance (Factory)",
            fnv.Unit.TEMPERATURE_FACTORY: "Temperature (Factory)",
        }
        
        units = [unit_map[u] for u in self.im.supported_units if u in unit_map]
        
        # Adiciona as opções de usuário caso os coeficientes tenham sido configurados
        if self.user_cal.has_temp_cal():
            units.append("Temperature (User)")
        if self.user_cal.has_rad_cal():
            units.append("Radiance (User)")
            
        return units

    def set_unit(self, unit_name):
        self.active_user_unit = None
        if not self.im: return
        if unit_name == "Counts (Raw)":
            self.im.unit = fnv.Unit.COUNTS
        elif unit_name == "Temperature (Factory)":
            self.im.unit = fnv.Unit.TEMPERATURE_FACTORY
        elif unit_name == "Radiance (Factory)":
            self.im.unit = fnv.Unit.RADIANCE_FACTORY
        elif unit_name == "Temperature (User)":
            self.im.unit = fnv.Unit.COUNTS  # Força os Counts como base para a conta
            self.active_user_unit = "User_Temp"
        elif unit_name == "Radiance (User)":
            self.im.unit = fnv.Unit.COUNTS
            self.active_user_unit = "User_Rad"

    def get_source_info(self):
        if not self.im: return None
        return self.im.source_info

    def get_object_parameters_df(self):
        if not self.im: return pd.DataFrame()
        
        obj_params = self.im.object_parameters
        propriedades = [x for x in dir(obj_params) if not x.startswith("__")]
        
        valores, props_validas = [], []
        for x in propriedades:
            val = getattr(obj_params, x)
            if isinstance(val, (int, float, str)) and not callable(val):
                valores.append(val)
                props_validas.append(x)
                
        df = pd.DataFrame({"Propriedade": props_validas, "Valor": valores})
        df['Propriedade'] = df['Propriedade'].str.replace('_', ' ', regex=False).str.title()
        df['Valor'] = df['Valor'].apply(lambda x: f"{x:.4f}" if isinstance(x, float) else x)
        return df

    def export_csv(self, file_path):
        if self.raw_data is not None:
            pd.DataFrame(self.raw_data).to_csv(file_path, index=False, header=False)

    def get_value_at(self, x, y):
        """Retorna o valor térmico exato na coordenada x, y da imagem atual"""
        if self.raw_data is not None:
            try:
                # O numpy usa [linha, coluna], que equivale a [y, x]
                h, w = self.raw_data.shape
                if 0 <= x < w and 0 <= y < h:
                    return float(self.raw_data[y, x])
            except Exception:
                return None
        return None

    # Propriedade auxiliar para saber qual unidade está ativa
    @property
    def current_unit_label(self):
        if self.active_user_unit == "User_Temp":
            return "°C (User)"
        if self.active_user_unit == "User_Rad":
            return "Rad (User)"
        if not self.im: return ""
        unit_map = {
            fnv.Unit.COUNTS: "Counts",
            fnv.Unit.RADIANCE_FACTORY: "Rad",
            fnv.Unit.TEMPERATURE_FACTORY: "°C"
        }
        return unit_map.get(self.im.unit, "")