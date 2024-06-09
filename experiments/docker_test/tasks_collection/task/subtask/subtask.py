import dataclasses
import datetime
import enum
import json
import pathlib
import time
from typing import Any
from typing import Type

import dacite
import pandas
import pandas as pd
import sklearn.ensemble
import sklearn.metrics
import sklearn.model_selection
import sklearn.preprocessing
import sklearn.tree


@dataclasses.dataclass
class Input:
    model_type: str
    dataset_config: 'DatasetConfig'
    subtask_params: list[dict[str, Any]]


class ModelType(enum.StrEnum):
    DECISION_TREE_CLASSIFIER = 'DecisionTreeClassifier'
    RANDOM_FOREST_CLASSIFIER = 'RandomForestClassifier'


@dataclasses.dataclass
class DatasetConfig:
    path: str
    target_column: str
    columns_to_scale: list[str]
    columns_to_get_dummies: list[str]


@dataclasses.dataclass
class SeparatedDataset:
    x_train: pandas.DataFrame
    x_test: pandas.DataFrame
    y_train: pandas.Series
    y_test: pandas.Series


@dataclasses.dataclass
class Output:
    result: list[float]


def read_config() -> Input:
    data = json.loads(pathlib.Path('input/config.json').read_text())
    input_config = dacite.from_dict(Input, data)
    return input_config


def write_output(output: Output) -> None:
    data = json.dumps(dataclasses.asdict(output))
    pathlib.Path('output/result.json').write_text(data)


def preprocess_df(
    df: pandas.DataFrame,
    dataset_config: DatasetConfig,
):
    if dataset_config.columns_to_scale:
        df[dataset_config.columns_to_scale] = (
            sklearn.preprocessing.StandardScaler().fit_transform(
                df[dataset_config.columns_to_scale]
            )
        )
    if dataset_config.columns_to_get_dummies:
        df = pandas.get_dummies(
            df, columns=dataset_config.columns_to_get_dummies,
        )
    return df


def get_dataframe(config: Input) -> pd.DataFrame:
    df = pandas.read_csv(f'input/{config.dataset_config.path}')
    df = preprocess_df(df, config.dataset_config)
    return df


def get_model_class(model_type: ModelType) -> Any:
    match model_type:
        case ModelType.DECISION_TREE_CLASSIFIER.name:
            return sklearn.tree.DecisionTreeClassifier
        case ModelType.RANDOM_FOREST_CLASSIFIER.name:
            return sklearn.ensemble.RandomForestClassifier
        case _:
            raise Exception(f'unknown model type {model_type}')


def separate_data(
    df: pandas.DataFrame, target_column: str,
) -> SeparatedDataset:
    x, y = df.drop(target_column, axis=1), df[target_column]
    return SeparatedDataset(
        *sklearn.model_selection.train_test_split(
            x, y, random_state=42, test_size=0.2,
        )
    )


def get_model_score(
    model_class: Type,
    separated_data: SeparatedDataset,
    params: dict[str, Any],
) -> float:
    model = model_class(**params, random_state=42)
    model.fit(separated_data.x_train, separated_data.y_train)
    y_pred = model.predict(separated_data.x_test)
    f1_score = sklearn.metrics.f1_score(
        separated_data.y_test, y_pred, average='macro',
    )
    return f1_score


def get_models_scores(config: Input, df: pandas.DataFrame) -> list[float]:
    model_class = get_model_class(config.model_type)
    separated_data = separate_data(
        df, config.dataset_config.target_column,
    )
    result = []
    for params_set in config.subtask_params:
        f1_score = get_model_score(model_class, separated_data, params_set)
        result.append(f1_score)
    return result


def main():
    config = read_config()
    start = time.time()
    print(f'start at {datetime.datetime.now()}')
    df = get_dataframe(config)
    scores = get_models_scores(config, df)
    end = time.time()
    print(f'end at {datetime.datetime.now()}')
    print(end - start)
    result = Output(result=scores)
    write_output(result)


if __name__ == '__main__':
    main()
