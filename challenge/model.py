from datetime import datetime
from typing import Tuple, Union, List, Optional

import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression


class DelayModel:
    TOP_10_FEATURES = [
        "OPERA_Latin American Wings",
        "MES_7",
        "MES_10",
        "OPERA_Grupo LATAM",
        "MES_12",
        "TIPOVUELO_I",
        "MES_4",
        "MES_11",
        "OPERA_Sky Airline",
        "OPERA_Copa Air",
    ]
    THRESHOLD_IN_MINUTES = 15

    def __init__(self):
        self._model = None

    def _get_min_diff(self, row: pd.Series) -> float:
        """
        Gets the difference, in minutes, between the rows Fecha-O and Fecha-I

        Args:
            row (pd.Series): raw row.
        Returns:
            float: minutes diference
        """
        fecha_o = datetime.strptime(row["Fecha-O"], "%Y-%m-%d %H:%M:%S")
        fecha_i = datetime.strptime(row["Fecha-I"], "%Y-%m-%d %H:%M:%S")
        min_diff = ((fecha_o - fecha_i).total_seconds()) / 60
        return min_diff

    def preprocess(
        self, data: pd.DataFrame, target_column: Optional[str] = None
    ) -> Union[Tuple[pd.DataFrame, pd.DataFrame], pd.DataFrame]:
        """
        Prepare raw data for training or predict.

        Args:
            data (pd.DataFrame): raw data.
            target_column (str, optional): if set, the target is returned.

        Returns:
            Tuple[pd.DataFrame, pd.DataFrame]: features and target.
            or
            pd.DataFrame: features.
        """
        # Generate features using one-hot encoding
        features = pd.concat(
            [
                pd.get_dummies(data["OPERA"], prefix="OPERA"),
                pd.get_dummies(data["TIPOVUELO"], prefix="TIPOVUELO"),
                pd.get_dummies(data["MES"], prefix="MES"),
            ],
            axis=1,
        )

        features = features.reindex(columns=self.TOP_10_FEATURES, fill_value=0)

        if target_column:
            data["min_diff"] = data.apply(self._get_min_diff, axis=1)
            data["delay"] = np.where(data["min_diff"] > self.THRESHOLD_IN_MINUTES, 1, 0)
            target = data[[target_column]]
            return features, target
        else:
            return features

    def fit(self, features: pd.DataFrame, target: pd.DataFrame) -> None:
        """
        Fit model with preprocessed data.

        Args:
            features (pd.DataFrame): preprocessed data.
            target (pd.DataFrame): target.
        """
        # Class balance scale
        target_values = target.values.ravel()
        n_y0 = len(target_values[target_values == 0])
        n_y1 = len(target_values[target_values == 1])
        total = len(target_values)

        self._model = LogisticRegression(
            class_weight={0: n_y1 / total, 1: n_y0 / total}
        )
        self._model.fit(features, target_values)

    def predict(self, features: pd.DataFrame) -> List[int]:
        """
        Predict delays for new flights.

        Args:
            features (pd.DataFrame): preprocessed data.

        Returns:
            (List[int]): predicted targets.
        """
        if self._model is None:
            return [0] * features.shape[0]
        else:
            predictions = self._model.predict(features)
            return [int(pred) for pred in predictions]
