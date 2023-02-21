# %% Imports
import pandas as pd
from typing import TypedDict, Union
import numpy as np
import plotly.express as px
from helpers.misc import getRelativeFp, IMAGEPATH

# %%
# Objective: deliver 100 units of value
objDist = 100

# Team output: 1 unit of work per time period
teamOutput = 1

# Number of iterations for each simulation
nIterations = 500


# %% Configs
# Typeddict of configs
class ConfigType(TypedDict):
    name: str
    min: int
    max: int
    pace: Union[int, float]


configs: list[ConfigType] = [
    {"name": "No feedback", "min": 0, "max": 90, "pace": 1},
    {"name": "Meh feedback", "min": 15, "max": 90, "pace": 1},
    {"name": "Average feedback", "min": 30, "max": 90, "pace": 1},
    {"name": "Good feedback", "min": 45, "max": 90, "pace": 1},
    {"name": "Great feedback", "min": 60, "max": 90, "pace": 1},
    {"name": "Counterproductive feedback", "min": -30, "max": 60, "pace": 1},
    {"name": "Counterproductive feedback, 4x pace", "min": -30, "max": 60, "pace": 4},
    {"name": "No feedback, 1.5x pace", "min": 0, "max": 90, "pace": 1.5},
]
# Output can be 100% productive
out = []
for config in configs:
    print(config["name"])
    for _ in range(nIterations):
        currprog = 0
        currside = 0
        i = 1
        while currprog < objDist:
            sampleDeg = np.random.randint(config["min"], config["max"])
            progress = np.sin(np.deg2rad(sampleDeg)) * config["pace"]
            sideways = np.cos(np.deg2rad(sampleDeg)) * config["pace"]
            currprog += progress
            currside += sideways
            out.append({**config, "i": i, "progress": currprog, "sideways": currside, "sim": _})
            i += 1


# %%
df = pd.DataFrame(out)
df.groupby(["name", "sim"])["i"].max().reset_index().groupby(["name"])["i"].agg(
    [
        np.min,
        lambda x: np.quantile(x, 0.05),
        np.mean,
        lambda x: np.quantile(x, 0.95),
        np.max,
    ]
).reset_index()

# %%
fig = px.scatter(out, x="sideways", y="progress", facet_col="name", color="i", width=600, height=1000, facet_col_wrap=2)

fig.update_traces(marker_opacity=0.05, marker_size=1, showlegend=False)
fig.update_coloraxes(showscale=False)
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1], font_size=12))
fig.show()

fig.write_image(
    getRelativeFp(IMAGEPATH, "post-11/feedback-sim.jpeg", upOneLevel=False),
    format="jpeg",
    width=600,
    height=1000,
)


# %%
