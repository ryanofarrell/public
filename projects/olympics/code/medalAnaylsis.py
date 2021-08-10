# %% Imports
import pandas as pd
from helpers import getRelativeFp
import plotly.express as px
import pycountry
from pycountry_convert import (
    country_alpha2_to_continent_code,
    convert_continent_code_to_continent_name,
)
from countryinfo import CountryInfo
import numpy as np

# Constants
n = 15
colorMap = {"Gold": "#FFD700", "Silver": "#C0C0C0", "Bronze": "#CD7F32"}
imgW = 1200
imgH = 800

# %% Get data
countries = pd.read_csv(getRelativeFp(__file__, "../data/output/countryMedals.csv"))
ind = pd.read_csv(getRelativeFp(__file__, "../data/output/individualMedals.csv"))

continents = pd.read_json(getRelativeFp(__file__, "../data/input/regionPop.json"))

# %% Add some more country information
def lookupCountry(longName):
    try:
        countries = pycountry.countries.search_fuzzy(longName)[0]
        return countries.alpha_2
    except LookupError:
        nameMap = {
            "Russian Olympic Committee": "RUS",
            "South Korea": "KOR",
            "Taiwan (Chinese Taipei)": "TWN",
            "Serbia Republic": "SRB",
            "Ivory Coast": "CIV",
        }
        try:
            countries = pycountry.countries.get(alpha_3=nameMap[longName])
            return countries.alpha_2
        except LookupError:
            return ""


countries["twoDigitCd"] = countries["longName"].apply(lambda x: lookupCountry(x))
countries["lookupCountry"] = countries["twoDigitCd"].apply(
    lambda x: pycountry.countries.get(alpha_2=x).name
)
countries["Continent"] = countries["twoDigitCd"].apply(
    lambda x: convert_continent_code_to_continent_name(
        country_alpha2_to_continent_code(x)
    )
)

# countries['countryPop'] = countries['twoDigitCd'].apply(lambda x: CountryInfo(x).population())

# Note Serbia and Kosovo both return Serbia - not something I know about and outside the scope
cLookup = pd.DataFrame(CountryInfo().all().values())
cLookup["twoDigitCd"] = pd.DataFrame(cLookup["ISO"].apply(lambda x: x["alpha2"]))
countries = pd.merge(
    left=countries,
    right=cLookup[["twoDigitCd", "population"]].dropna(how="any"),
    how="left",
    on="twoDigitCd",
)
# %% Get higher- levels of individual events, remove some patterns
ind[["eventHigh", "eventLow"]] = ind["event"].str.split(" - ", 1, True)
ind["eventLow"] = ind["eventLow"].str.replace(r", Final.*, .*", "", regex=True)
ind["eventLow"] = ind["eventLow"].str.replace(r", Last 16, .*", "", regex=True)


# %% Group by events, country, color to remove multiple names, add points
ind = (
    ind.groupby(["event", "eventHigh", "eventLow", "color", "country"])["athlete"]
    .agg(list)
    .reset_index()
)

# Add country attributes
ind = pd.merge(
    left=ind,
    right=countries[["shortName", "longName", "flagUrl", "Continent"]],
    how="left",
    left_on="country",
    right_on="shortName",
)

# Add points
ind["points"] = 1
ind.loc[ind["color"] == "Silver", "points"] = 2
ind.loc[ind["color"] == "Gold", "points"] = 3

# Add gender
ind["gender"] = "Women"
ind.loc[ind["eventLow"].str.find("Men's") != -1, "gender"] = "Men"
ind.loc[ind["eventLow"].str.find("Mixed") != -1, "gender"] = "Mixed"

# %% Get counts of high-level events, combine into categories
ind["Grouped Event"] = ind["eventHigh"]

# Combine team sports
ind.loc[
    ind["eventHigh"].isin(
        [
            "Baseball",
            "Softball",
            "Beach Volleyball",
            "Field Hockey",
            "Handball",
            "Rugby",
            "Soccer",
            "Volleyball",
            "Water Polo",
            "Basketball",
            "Tennis",
            "Golf",
            "Table Tennis",
            "Badminton",
        ]
    ),
    "Grouped Event",
] = "Traditional & Team"

# Shooting and archery
ind.loc[
    ind["eventHigh"].isin(["Shooting", "Archery"]), "Grouped Event"
] = "Archery & Shooting"

# Combat
ind.loc[
    ind["eventHigh"].isin(["Weightlifting", "Wrestling"]),
    "Grouped Event",
] = "Weightlifting & Wrestling"
ind.loc[
    ind["eventHigh"].isin(["Fencing", "Boxing"]),
    "Grouped Event",
] = "Combat"

ind.loc[
    ind["eventHigh"].isin(["Taekwondo", "Karate", "Judo"]),
    "Grouped Event",
] = "Combat & Skill"

# Adventure
ind.loc[
    ind["eventHigh"].isin(["Surfing", "Sport Climbing", "Skateboarding", "Sailing"]),
    "Grouped Event",
] = "Adventure"

# Water
ind.loc[
    ind["eventHigh"].isin(["Canoe", "Rowing"]),
    "Grouped Event",
] = "Canoe & Rowing"

# Swimming & Diving
ind.loc[
    ind["eventHigh"].isin(["Swimming", "Diving"]),
    "Grouped Event",
] = "Swimming & Diving"


# Artistic swimming, equestrian with Gymnastics
ind.loc[
    ind["eventHigh"].isin(["Artistic Swimming", "Gymnastics", "Equestrian"]),
    "Grouped Event",
] = "Artistry"

# Combine athletics
ind.loc[
    ind["eventHigh"].isin(["Athletics", "Modern Pentathlon", "Triathlon"]),
    "Grouped Event",
] = "Athletics"

groupedCnts = (
    ind.groupby("Grouped Event")["eventLow"]
    .nunique()
    .reset_index()
    .rename(columns={"eventLow": "eventCnt"})
)


# %% Visualize country medal counts for top n countries
countryPoints = (
    ind.groupby(["country"])["points"]
    .sum()
    .sort_values(ascending=False)
    .reset_index()
    .iloc[:n]
)
temp = ind.loc[ind["country"].isin(countryPoints["country"].unique())]
fig = px.bar(
    temp,
    x="country",
    y="points",
    color="color",
    color_discrete_map=colorMap,
    category_orders={
        "color": ["Gold", "Silver", "Bronze"],
        "country": countryPoints["country"].unique().tolist(),
    },
    title=f"Top {n} Medal Point Countries, 2020 Tokyo Olympics",
)
fig.update_layout(showlegend=False)
fig.update_yaxes(title_text="Medal Points", range=[0, 250])
fig.update_xaxes(title_text="Country")

# Add flags
i = 0
n = len(countryPoints)
for country in countryPoints["country"]:
    countryRow = countries.loc[countries["shortName"] == country]
    countryMedals = countryPoints.loc[countryPoints["country"] == country][
        "points"
    ].values[0]
    fig.add_layout_image(
        dict(
            source=countryRow["flagUrl"].values[0] + "0",
            xref="x domain",
            yref="y domain",
            x=i / n + 1 / (2 * n),
            y=countryMedals / fig.layout.yaxis.range[1],
            sizex=1.1 / n,
            sizey=1.1 / n,
            xanchor="center",
            yanchor="bottom",
        )
    )
    i += 1

fig.write_image(
    getRelativeFp(__file__, "../viz/topMedalPointCountries.png"),
    format="png",
    width=imgW,
    height=imgH,
)

fig.show()

# %% Country Effectiveness - medal points per 10M pop
countryPoints = ind.groupby(["country"])["points"].sum().reset_index()
countryPoints = pd.merge(
    countryPoints,
    countries[["shortName", "population", "Continent"]],
    how="left",
    left_on="country",
    right_on="shortName",
)
countryPoints["pointsPer10Mill"] = (
    countryPoints["points"] / countryPoints["population"] * 10000000
)

# Countryies with >= 15 points, sort, keep top n
countryPoints = countryPoints.loc[countryPoints["points"] >= 15]
countryPoints.sort_values(by=["pointsPer10Mill"], ascending=False, inplace=True)
countryPoints = countryPoints.iloc[:n]

# Viz
fig = px.bar(
    countryPoints,
    x="country",
    y="pointsPer10Mill",
    color="Continent",
    category_orders={
        "country": countryPoints["country"].unique().tolist(),
    },
)
fig.update_yaxes(range=[0, 100], title_text="Medal Points (per 10M pop)")
fig.update_xaxes(title_text="Country")

# Add flags
i = 0
n = len(countryPoints)
for country in countryPoints["country"]:
    countryRow = countries.loc[countries["shortName"] == country]
    countryValue = countryPoints.loc[countryPoints["country"] == country][
        "pointsPer10Mill"
    ].values[0]
    fig.add_layout_image(
        dict(
            source=countryRow["flagUrl"].values[0] + "0",
            xref="x domain",
            yref="y domain",
            x=i / n + 1 / (2 * n),
            y=countryValue / fig.layout.yaxis.range[1],
            sizex=1.1 / n,
            sizey=1.1 / n,
            xanchor="center",
            yanchor="bottom",
        )
    )
    i += 1
fig.show()
fig.write_image(
    getRelativeFp(__file__, "../viz/topMedalEfficiencyCountries.png"),
    format="png",
    width=imgW,
    height=imgH,
)


# %% Region Analysis

continentPoints = (
    ind.groupby(["Continent", "Grouped Event"])["points"].sum().reset_index()
)
continentPoints = pd.merge(continentPoints, groupedCnts, how="left", on="Grouped Event")

continentPoints = pd.merge(
    continentPoints,
    continents.rename(columns={"Name": "Continent", "Pop": "population"}),
    how="left",
    on="Continent",
)
continentPoints["pointsPerEvent"] = (
    continentPoints["points"] / continentPoints["eventCnt"]
)
continentPoints["Points per Event (per 100M pop)"] = (
    continentPoints["pointsPerEvent"] / continentPoints["population"] * 100000000
)
continentPoints["continentEvent"] = (
    continentPoints["Continent"] + " - " + continentPoints["Grouped Event"]
)
continentPoints.sort_values(by=["pointsPerEvent"], ascending=False, inplace=True)
fig = px.bar(continentPoints.iloc[:n], x="continentEvent", y="pointsPerEvent")
fig.show()

continentPoints["Points per Event (per 100M pop)"] = np.round(
    continentPoints["Points per Event (per 100M pop)"], 2
)
continentPoints.sort_values(by=["Grouped Event"], ascending=True, inplace=True)

for cont in continentPoints["Continent"].unique():
    temp = pd.merge(
        left=continentPoints.loc[continentPoints["Continent"] == cont],
        right=groupedCnts,
        how="outer",
        on="Grouped Event",
    )
    temp.sort_values(by=["Grouped Event"], ascending=True, inplace=True)

    fig = px.bar(
        temp,
        x="Grouped Event",
        y="Points per Event (per 100M pop)",
        text="Points per Event (per 100M pop)",
        title=f"{cont} Points per Event (per 100M pop)",
    )
    fig.update_yaxes(
        title_text="Points per Event (per 100M pop)",
        tickformat=".1f",
        range=[0, 3],
    )

    fig.write_html(getRelativeFp(__file__, f"../viz/output/efficiency_{cont}.html"))

# %%
