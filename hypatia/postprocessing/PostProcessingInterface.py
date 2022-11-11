from hypatia.backend.ModelData import ModelData
from hypatia.backend.ModelVariables import ModelVariables
from typing import (
    Dict,
)
import pandas as pd
import os

class PostProcessingInterface:
    def __init__(self, model_data: ModelData, model_result: ModelVariables):
        self._settings = model_data.settings
        self._global_parameters = model_data.global_parameters
        self._trade_parameters = model_data.trade_parameters
        self._regional_parameters = model_data.regional_parameters
        self._model_results = model_result

    def write_processed_results(self, path: str):
        PostProcessingInterface.__write_processed_result(
            self.process_results(),
            path
        )

    def __write_processed_result(postprocessed_result: Dict, path: str):
        for key, value in postprocessed_result.items():
            if isinstance(value, pd.DataFrame):
                value.to_csv(f"{path}//{key}.csv")
            else:
                new_path = f"{path}//{key}"
                os.makedirs(new_path, exist_ok=True)
                PostProcessingInterface.__write_processed_result(value, new_path)

    def process_results(self) -> Dict:
        raise NotImplementedError("Subclasses should implement this")
