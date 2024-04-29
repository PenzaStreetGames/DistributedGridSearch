import dataclasses
import enum
import pathlib
from typing import Any
import uuid

import pandas
import sklearn.metrics
import sklearn.model_selection
import sklearn.preprocessing
import sklearn.tree


class ModelType(enum.StrEnum):
    DECISION_TREE_CLASSIFIER = 'DecisionTreeClassifier'


@dataclasses.dataclass
class SubtasksRequest:
    task_id: uuid.UUID
    subtasks_group_id: uuid.UUID
    model_type: ModelType
    dataset_config: 'DatasetConfig'
    subtasks_params: tuple['SubtaskParams']


@dataclasses.dataclass
class DatasetConfig:
    path: pathlib.Path
    target_column: str
    columns_to_scale: list[str]
    columns_to_get_dummies: list[str]


@dataclasses.dataclass(frozen=True, eq=True)
class SubtaskParams:
    params: tuple['Param']


@dataclasses.dataclass(frozen=True, eq=True)
class Param:
    name: str
    value: Any


@dataclasses.dataclass
class SubtasksResponse:
    task_id: uuid.UUID
    subtasks_group_id: uuid.UUID
    subtasks_scores: tuple['SubtaskScore']


@dataclasses.dataclass
class SubtaskScore:
    subtask_params: SubtaskParams
    score: float


class SubtasksRequestFabric:
    def __init__(self, model_type: ModelType, dataset_config: DatasetConfig):
        self.model_type = model_type
        self.dataset_config = dataset_config

    def create(self, subtasks_params: list[dict[str, Any]]) -> SubtasksRequest:
        return SubtasksRequest(
            task_id=uuid.uuid4(),
            subtasks_group_id=uuid.uuid4(),
            model_type=self.model_type,
            dataset_config=self.dataset_config,
            subtasks_params=tuple(
                SubtaskParams(
                    params=tuple(
                        Param(name=name, value=value)
                        for name, value in params.items()
                    ),
                )
                for params in subtasks_params
            ),
        )


def create_subtasks_response(
    request: SubtasksRequest, scores: dict[SubtaskParams, float],
) -> SubtasksResponse:
    return SubtasksResponse(
        task_id=request.task_id,
        subtasks_group_id=request.subtasks_group_id,
        subtasks_scores=tuple(
            SubtaskScore(
                subtask_params=subtask_params,
                score=score,
            )
            for subtask_params, score in scores.items()
        ),
    )


def get_model_class(model_type: ModelType) -> Any:
    match model_type:
        case ModelType.DECISION_TREE_CLASSIFIER:
            return sklearn.tree.DecisionTreeClassifier
        case _:
            raise Exception(f'unknown model type {model_type.value}')


def get_dataframe_by_path(path: pathlib.Path) -> pandas.DataFrame:
    return pandas.read_csv(path)


def preprocess_df(
    df: pandas.DataFrame,
    dataset_config: DatasetConfig,
):
    df[dataset_config.columns_to_scale] = (
        sklearn.preprocessing.StandardScaler().fit_transform(
            df[dataset_config.columns_to_scale]
        )
    )
    df = pandas.get_dummies(df, columns=dataset_config.columns_to_get_dummies)
    return df


def separate_data(df: pandas.DataFrame, target_column: str) -> tuple[
    pandas.DataFrame, pandas.DataFrame, pandas.Series, pandas.Series,
]:
    x, y = df.drop(target_column, axis=1), df[target_column]
    return sklearn.model_selection.train_test_split(
        x, y, random_state=42, test_size=0.2,
    )


def _get_model_score(
    model: Any, x_test: pandas.DataFrame, y_test: pandas.Series,
) -> float:
    y_pred = model.predict(x_test)
    f1_score = sklearn.metrics.f1_score(y_test, y_pred, average='macro')
    return f1_score


def get_model_score(request: SubtasksRequest, params: SubtaskParams) -> float:
    df = get_dataframe_by_path(request.dataset_config.path)
    df = preprocess_df(df, request.dataset_config)
    model_class = get_model_class(request.model_type)
    params_dict = {
        param.name: param.value
        for param in params.params
    }
    model = model_class(**params_dict, random_state=42)
    x_train, x_test, y_train, y_test = separate_data(
        df, request.dataset_config.target_column,
    )
    model.fit(x_train, y_train)
    f1_score = _get_model_score(model, x_test, y_test)
    return f1_score


def process_subtasks_request(request: SubtasksRequest) -> SubtasksResponse:
    subtasks_scores: dict[SubtaskParams, float] = {}
    for params in request.subtasks_params:
        subtasks_scores[params] = get_model_score(request, params)
    return create_subtasks_response(request, subtasks_scores)


if __name__ == '__main__':
    subtasks_request_fabric = SubtasksRequestFabric(
        model_type=ModelType.DECISION_TREE_CLASSIFIER,
        dataset_config=DatasetConfig(
            path=pathlib.Path('../data/Employee.csv'),
            target_column='LeaveOrNot',
            columns_to_scale=[
                'JoiningYear', 'Age', 'ExperienceInCurrentDomain',
            ],
            columns_to_get_dummies=[
                'Education', 'Gender', 'PaymentTier', 'City', 'EverBenched',
            ],
        ),
    )
    subtask_request = subtasks_request_fabric.create(
        [
            {'criterion': 'gini', 'max_depth': 5},
            {'criterion': 'entropy', 'max_depth': 6},
            {'criterion': 'log_loss', 'max_depth': 4},
        ],
    )
    subtask_response = process_subtasks_request(subtask_request)
    for subtask_score in subtask_response.subtasks_scores:
        print(dataclasses.asdict(subtask_score.subtask_params))
        print(f'f1-score is {subtask_score.score}')
