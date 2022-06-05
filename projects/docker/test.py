"""Example ML code used in docker container"""
# %% Imports
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score

# %% CONSTANTS
RANDOM = 183751
# %%
X, y = load_iris(return_X_y=True)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, train_size=0.8, random_state=RANDOM
)
# %%
t = DecisionTreeClassifier(random_state=RANDOM)
t.fit(X=X_train, y=y_train)
print(f"Accuracy: {accuracy_score(y_test, t.predict(X_test)):,.3%}")

# %%
