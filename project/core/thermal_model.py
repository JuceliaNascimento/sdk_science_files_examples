import fnv
import fnv.file
import fnv.reduce
import numpy as np
import pandas as pd
import os

class ThermalModel:
    def __init__(self):
        self.im = None
        self.file_name = ""
        self.raw_data = None
        self.num_frames = 0

    def load_file(self, path):
        self.file_name = os.path.splitext(os.path.basename(path))[0]
        self.im = fnv.file.ImagerFile(path)
        self.im.unit = fnv.Unit.COUNTS
        self.num_frames = self.im.num_frames
        return True

    def get_frame_data(self, frame_index):
        if not self.im: return None
        self.im.get_frame(frame_index)
        self.raw_data = np.array(self.im.final, copy=False).reshape((self.im.height, self.im.width))
        return self.raw_data

    def get_supported_units(self):
        if not self.im: return []
        unit_map = {
            fnv.Unit.COUNTS: "Counts (Raw)",
            fnv.Unit.RADIANCE_FACTORY: "Radiance (Factory)",
            fnv.Unit.TEMPERATURE_FACTORY: "Temperature (Factory)",
        }
        return [unit_map[u] for u in self.im.supported_units if u in unit_map]

    def set_unit(self, unit_name):
        if not self.im: return
        if unit_name == "Counts (Raw)":
            self.im.unit = fnv.Unit.COUNTS
        elif unit_name == "Temperature (Factory)":
            self.im.unit = fnv.Unit.TEMPERATURE_FACTORY
        elif unit_name == "Radiance (Factory)":
            self.im.unit = fnv.Unit.RADIANCE_FACTORY

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