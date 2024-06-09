import dist_grid_search_client as client
import pandas
from sklearn.tree import DecisionTreeClassifier

dataset = pandas.read_csv("data.csv")
tree = DecisionTreeClassifier()
parameters = {
    "criterion": ["gini", "entropy", "log_loss"],
    "max_depth": [4, 5, 6]
}
grid_search = client.GridSearchCV(tree, parameters)
X, y = dataset.drop("label", axis=1), dataset["label"]
grid_search.fit(X, y)
print(grid_search.best_params_)

# {"criterion": "gini", "max_depth": 5}

