import asyncio
import base64
from copy import copy
from enum import StrEnum
from datetime import datetime
import io
import pathlib
from typing import Any
from typing import Optional
import uuid
from uuid import UUID

from fastapi import FastAPI
import joblib
import pandas as pd
from pydantic import BaseModel
from pydantic import Field
from pydantic import HttpUrl
from pydantic import UUID4
import requests
import sklearn.model_selection
from sklearn.tree import DecisionTreeClassifier

app = FastAPI()


class GridSearchAsyncResponseStatus(StrEnum):
    CREATED = 'created'
    VALIDATION_ERROR = 'validation_error'
    NOT_FOUND = 'not_found'
    EXECUTING = 'executing'
    DONE = 'done'


class GridSearchTaskStatus(StrEnum):
    CREATED = 'created'
    EXECUTING = 'executing'
    DONE = 'done'


class ModelName(StrEnum):
    DECISION_TREE_CLASSIFIER = 'DecisionTreeClassifier'


class ParamValuesSet(BaseModel):
    param_name: str
    values: list[Any]


class GridSearchRequest(BaseModel):
    model_name: ModelName
    params_values_set: list[ParamValuesSet]
    data_url: HttpUrl
    result_column: str


class GridSearchResult(BaseModel):
    uid: UUID
    f1_score: float = Field(ge=0.0, le=1.0)
    best_params: dict
    serialized_model: str


class GridSearchAsyncResponse(BaseModel):
    uid: UUID
    status: GridSearchAsyncResponseStatus
    # created_at: Optional[datetime] = None
    result: Optional[GridSearchResult] = None


def download_dataset(url: HttpUrl) -> pd.DataFrame:
    # if url not in datasets_cache:
    #     response = requests.get(url, stream=True)
    #     filename = f'{url.host}/{url.path}'
    #     with open(filename, mode="wb") as file:
    #         for chunk in response.iter_content(chunk_size=10 * 1024):
    #             file.write(chunk)
    #     datasets_cache[url] = pathlib.Path(filename)
    # filename = datasets_cache[url]
    df = pd.read_csv(pathlib.Path('Iris.csv'))
    df = df.drop('Id', axis=1)
    return df


def grid_search(request: GridSearchRequest, uid: UUID4) -> None:
    df = download_dataset(request.data_url)
    params = {
        param.param_name: param.values
        for param in request.params_values_set
    }
    match request.model_name:
        case ModelName.DECISION_TREE_CLASSIFIER:
            model = DecisionTreeClassifier
        case _:
            raise ValueError(request.model_name)
    x_train, x_test, y_train, y_test = (
        sklearn.model_selection.train_test_split(
            df.drop(request.result_column, axis=1),
            df[request.result_column],
            train_size=0.8,
            shuffle=True,
            random_state=42,
        )
    )
    print(x_train.shape)

    search = sklearn.model_selection.GridSearchCV(
        estimator=model(),
        param_grid=params,
        scoring='f1_macro',
        cv=4,
    )
    search.fit(x_train, y_train)
    best_estimator = search.best_estimator_
    y_pred = search.predict(x_test.copy())
    f1_score = sklearn.metrics.f1_score(
        y_pred.copy(), y_test.copy(), average='macro',
    )
    model_path = pathlib.Path(f'model_{uid}.pkl')
    joblib.dump(best_estimator, model_path)
    response = GridSearchResult(
        uid=uid,
        f1_score=f1_score,
        best_params=search.best_params_,
        serialized_model=base64.b64encode(model_path.read_bytes()),
    )

    results[uid] = response


@app.post("/grid_search")
async def launch_grid_search(
    grid_search_request: GridSearchRequest
) -> GridSearchAsyncResponse:
    uid = uuid.uuid4()
    await asyncio.to_thread(grid_search, grid_search_request, uid)
    tasks[uid] = GridSearchTaskStatus.CREATED
    response = GridSearchAsyncResponse(
        uid=uid, status=GridSearchAsyncResponseStatus.CREATED,
    )
    return response


@app.get('/grid_search/{uid}')
async def get_grid_search_status(uid: UUID4) -> GridSearchAsyncResponse:
    if uid not in tasks:
        return GridSearchAsyncResponse(
            uid=uid, status=GridSearchAsyncResponseStatus.NOT_FOUND,
        )
    if uid not in results:
        return GridSearchAsyncResponse(
            uid=uid, status=GridSearchAsyncResponseStatus.EXECUTING,
        )
    print(uid)
    return GridSearchAsyncResponse(
        uid=uid,
        status=GridSearchAsyncResponseStatus.DONE,
        result=results[uid],
    )


tasks: dict[UUID4, GridSearchTaskStatus] = {}
results: dict[UUID4, GridSearchResult] = {}
datasets_cache: dict[HttpUrl, pathlib.Path] = {}
