import datetime
import pathlib
import time

import pandas
from sklearn.tree import DecisionTreeClassifier
import sklearn.ensemble
import sklearn.model_selection

df = pandas.read_csv(
    pathlib.Path(__file__).parent.parent.parent
    / 'datasets'
    / 'fashion-mnist_train.csv'
)
forest = sklearn.ensemble.RandomForestClassifier()
tree = DecisionTreeClassifier()
target_column = 'label'
params = {'n_estimators': [100]}
X, y = df.drop(target_column, axis=1), df[target_column]
start = time.time()
grid_search = sklearn.model_selection.GridSearchCV(forest, params, n_jobs=8)
print(f'start at {datetime.datetime.now()}')
# tree.fit(X, y)
grid_search.fit(X, y)
end = time.time()
print(f'end at {datetime.datetime.now()}')
print(end - start)
