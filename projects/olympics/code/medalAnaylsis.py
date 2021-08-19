# %% Imports
import pandas as pd
from helpers import getRelativeFp, IMAGEPATH
import plotly.express as px
import pycountry
from pycountry_convert import (
    country_alpha2_to_continent_code,
    convert_continent_code_to_continent_name,
)
from countryinfo import CountryInfo
import numpy as np
import plotly.figure_factory as ff


# Constants
barLimit = 15
countryPointMin = 15
countryEventPointMin = 10
colorMap = {
    "Gold": "#FFD700",
    "Silver": "#C0C0C0",
    "Bronze": "#CD7F32",
}
imgW = 1200
imgH = 800

# %% Get data
countries = pd.read_csv(getRelativeFp(__file__, "../data/output/countryMedals.csv"))
ind = pd.read_csv(getRelativeFp(__file__, "../data/output/individualMedals.csv"))

continents = pd.read_json(getRelativeFp(__file__, "../data/input/regionPop.json"))

# %% Add continents and countries to colormap
i = 0
for c in continents["Name"]:
    colorMap[c] = px.colors.qualitative.Vivid[i]
    i += 1


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

# Add continent to individual event points
ind = pd.merge(
    left=ind,
    right=countries[["shortName", "Continent"]],
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
def getGroupedEvent(eventHigh):
    # Traditional & Team
    if eventHigh in [
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
    ]:
        return "Traditional & Team"

    # Shooting and Archery
    if eventHigh in ["Shooting", "Archery"]:
        return "Shooting & Archery"

    # Wrestling & Weightlifting
    if eventHigh in ["Weightlifting", "Wrestling"]:
        return "Weightlifting & Wrestling"

    # Combat Striking
    if eventHigh in ["Fencing", "Boxing"]:
        return "Combat Striking"

    # Combat Skill
    if eventHigh in ["Taekwondo", "Karate", "Judo"]:
        return "Combat Skill"

    # Adventure
    if eventHigh in ["Surfing", "Sport Climbing", "Skateboarding", "Sailing"]:
        return "Adventure"

    # Canoe & Rowing
    if eventHigh in ["Canoe", "Rowing"]:
        return "Canoe & Rowing"

    # Swimming & Diving
    if eventHigh in ["Swimming", "Diving"]:
        return "Swimming & Diving"

    # Artistry Sports
    if eventHigh in ["Artistic Swimming", "Gymnastics", "Equestrian"]:
        return "Artistry"

    # Athletics
    if eventHigh in ["Athletics", "Modern Pentathlon", "Triathlon"]:
        return "Athletics"

    return eventHigh


ind["Grouped Event"] = ind["eventHigh"].apply(lambda x: getGroupedEvent(x))

groupedEvents = (
    ind.groupby("Grouped Event")["eventLow"]
    .nunique()
    .reset_index()
    .rename(columns={"eventLow": "eventCnt"})
)

i = 0
for c in groupedEvents["Grouped Event"]:
    colorMap[c] = px.colors.qualitative.Dark24[i]
    i += 1


# %% Aggregate points to country, country-event, continent, continent-event
# Agg to country, getmetrics
countryPoints = (
    ind.groupby(["country"])["points"].sum().sort_values(ascending=False).reset_index()
)
countryPoints = pd.merge(
    countryPoints,
    countries[["shortName", "population", "Continent", "flagUrl"]],
    how="left",
    left_on="country",
    right_on="shortName",
)
countryPoints["pointsPer10M"] = (
    countryPoints["points"] / countryPoints["population"] * 10000000
)

# Agg to country-event
countryEventPoints = (
    ind.groupby(["country", "Grouped Event"])["points"]
    .sum()
    .sort_values(ascending=False)
    .reset_index()
)
countryEventPoints = pd.merge(
    countryEventPoints,
    countries[["shortName", "population", "Continent", "flagUrl"]],
    how="left",
    left_on="country",
    right_on="shortName",
)
countryEventPoints = pd.merge(
    countryEventPoints, groupedEvents, how="left", on="Grouped Event"
)
countryEventPoints["countryEvent"] = (
    countryEventPoints["country"] + " - " + countryEventPoints["Grouped Event"]
)
countryEventPoints["pointsPerEvent"] = (
    countryEventPoints["points"] / countryEventPoints["eventCnt"]
)
countryEventPoints["pointsPerEventPer10M"] = (
    countryEventPoints["pointsPerEvent"] / countryEventPoints["population"] * 10000000
)


# Agg to continent
contPoints = (
    ind.groupby(["Continent"])["points"]
    .sum()
    .sort_values(ascending=False)
    .reset_index()
)
contPoints = pd.merge(
    contPoints,
    continents.rename(columns={"Name": "Continent", "Pop": "population"}),
    how="left",
    on="Continent",
)
contPoints["pointsPer100M"] = (
    contPoints["points"] / contPoints["population"] * 100000000
)

# Agg to continent event
contEventPoints = (
    ind.groupby(["Continent", "Grouped Event"])["points"].sum().reset_index()
)
contEventPoints = pd.merge(
    contEventPoints, groupedEvents, how="left", on="Grouped Event"
)

contEventPoints = pd.merge(
    contEventPoints,
    continents.rename(columns={"Name": "Continent", "Pop": "population"}),
    how="left",
    on="Continent",
)
contEventPoints["contEvent"] = (
    contEventPoints["Continent"] + " - " + contEventPoints["Grouped Event"]
)

contEventPoints["pointsPerEvent"] = (
    contEventPoints["points"] / contEventPoints["eventCnt"]
)
contEventPoints["pointsPerEventPer100M"] = (
    contEventPoints["pointsPerEvent"] / contEventPoints["population"] * 100000000
)


# %% VIZ - Top n medal point countries
topMedalCountries = countryPoints.iloc[:barLimit]["country"].unique().tolist()
temp = ind.loc[ind["country"].isin(topMedalCountries)]
fig = px.bar(
    temp,
    x="country",
    y="points",
    color="color",
    color_discrete_map=colorMap,
    category_orders={
        "color": ["Gold", "Silver", "Bronze"],
        "country": topMedalCountries,
    },
    title=f"Top {barLimit} Medal Point Countries, 2020 Tokyo Olympics",
)
fig.update_layout(showlegend=False)
fig.update_traces(marker_line_width=0)
fig.update_yaxes(title_text="Medal Points", range=[0, 250])
fig.update_xaxes(title_text="Country")

# Add flags
i = 0
n = barLimit
for country in topMedalCountries:
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


# Put image in blog images folder for post 6
fig.write_image(
    getRelativeFp(IMAGEPATH, "post-06/country_points.jpeg", upOneLevel=False),
    format="jpeg",
    width=imgW,
    height=imgH,
)

# fig.show()

# %% Top n medal points per pop, min 15 points
# Countries with >= 15 points, sort, keep top n
temp = countryPoints.loc[countryPoints["points"] >= countryPointMin].reset_index(
    drop=True
)
temp.sort_values(by=["pointsPer10M"], ascending=False, inplace=True)
temp = temp.iloc[:barLimit]

# Viz
fig = px.bar(
    temp,
    x="country",
    y="pointsPer10M",
    color="Continent",
    color_discrete_map=colorMap,
    category_orders={
        "country": temp["country"].unique().tolist(),
    },
    title=f"Top {barLimit} Medal Efficiency Countries, 2020 Tokyo Olympics",
)
fig.update_yaxes(range=[0, 100], title_text="Medal Points (per 10M pop)")
fig.update_xaxes(title_text="Country")

# Add flags
i = 0
n = len(temp)
for country in temp["country"]:
    countryRow = countries.loc[countries["shortName"] == country]
    countryValue = countryPoints.loc[countryPoints["country"] == country][
        "pointsPer10M"
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
# fig.show()
fig.write_image(
    getRelativeFp(IMAGEPATH, "post-06/country_points_perPop.jpeg", upOneLevel=False),
    format="jpeg",
    width=imgW,
    height=imgH,
)

# %% Country Event Points per Event
countryEventPoints.sort_values(by=["pointsPerEvent"], ascending=False, inplace=True)
temp = countryEventPoints.iloc[:barLimit]
fig = px.bar(
    temp,
    x="countryEvent",
    y="pointsPerEvent",
    color="Continent",
    color_discrete_map=colorMap,
    title=f"Top {barLimit} Country Points per Event, 2020 Tokyo Olympics",
    category_orders={
        "countryEvent": temp["countryEvent"].tolist(),
    },
)
fig.update_yaxes(
    title_text="Points per Event",
    range=[0, 1.75],
)
fig.update_xaxes(title_text="Country - Event")

# Add flags
i = 0
n = len(temp)
for country in temp["country"]:
    countryRow = countries.loc[countries["shortName"] == country]
    countryMedals = temp.iloc[i]["pointsPerEvent"]
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

# fig.show()

fig.write_image(
    getRelativeFp(IMAGEPATH, "post-06/countryEvent_points.jpeg", upOneLevel=False),
    format="jpeg",
    width=imgW,
    height=imgH,
)

# %% Country-Event points per event per pop
temp = countryEventPoints.loc[countryEventPoints["pointsPerEvent"] >= 0.3]
temp.sort_values(by=["pointsPerEventPer10M"], ascending=False, inplace=True)
temp = temp.iloc[:barLimit]
fig = px.bar(
    temp,
    x="countryEvent",
    y="pointsPerEventPer10M",
    color="Continent",
    color_discrete_map=colorMap,
    title=f"Top {barLimit} Country Points per Event Efficiency, 2020 Tokyo Olympics",
    category_orders={
        "countryEvent": temp["countryEvent"].tolist(),
    },
)
fig.update_yaxes(
    title_text="Points per Event (per 10M pop)",
    range=[0, 1.75],
)
fig.update_xaxes(title_text="Country - Event")

# Add flags
i = 0
n = len(temp)
for country in temp["country"]:
    countryRow = countries.loc[countries["shortName"] == country]
    countryMedals = temp.iloc[i]["pointsPerEventPer10M"]
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

# fig.show()

fig.write_image(
    getRelativeFp(
        IMAGEPATH, "post-06/countryEvent_points_perPop.jpeg", upOneLevel=False
    ),
    format="jpeg",
    width=imgW,
    height=imgH,
)
# %% Continent medals
contPoints.sort_values(by=["points"], ascending=False, inplace=True)

# Viz
fig = px.bar(
    ind,
    x="Continent",
    y="points",
    category_orders={
        "color": ["Gold", "Silver", "Bronze"],
        "Continent": contPoints["Continent"].tolist(),
    },
    color="color",
    color_discrete_map=colorMap,
    title=f"Medal Points by Continent, 2020 Tokyo Olympics",
)
fig.update_yaxes(range=[0, 1000], title_text="Medal Points")
fig.update_xaxes(title_text="Continent")
fig.update_traces(marker_line_width=0)
fig.update_layout(showlegend=False)
# fig.show()

fig.write_image(
    getRelativeFp(IMAGEPATH, "post-06/continent_points.jpeg", upOneLevel=False),
    format="jpeg",
    width=imgW,
    height=imgH,
)

# %% Continent points per pop
contPoints.sort_values(by=["pointsPer100M"], ascending=False, inplace=True)

fig = px.bar(
    contPoints,
    x="Continent",
    y="pointsPer100M",
    category_orders={
        "color": ["Gold", "Silver", "Bronze"],
        "Continent": contPoints["Continent"].tolist(),
    },
    color="Continent",
    color_discrete_map=colorMap,
    title=f"Medal Efficiency by Continent, 2020 Tokyo Olympics",
)
fig.update_yaxes(range=[0, 350], title_text="Medal Points (per 100M pop)")
fig.update_xaxes(title_text="Continent")
fig.update_traces(marker_line_width=0)
fig.update_layout(showlegend=False)
# fig.show()

fig.write_image(
    getRelativeFp(IMAGEPATH, "post-06/continent_points_perPop.jpeg", upOneLevel=False),
    format="jpeg",
    width=imgW,
    height=imgH,
)


# %% Heatmaps of continent-event points and per-pop points
temp = contEventPoints.pivot(
    index="Continent", columns="Grouped Event", values="pointsPerEvent"
)
temp.fillna(0, inplace=True)
temp.sort_index(inplace=True)
fig = ff.create_annotated_heatmap(
    np.round(temp.values, 1),
    colorscale="Blues",
    x=list(temp.columns),
    y=list(temp.index),
)
fig.update_layout(title_text=f"Continent Points per Event, 2020 Tokyo Olympics")
fig.update_xaxes(side="bottom")
# fig.show()
fig.write_image(
    getRelativeFp(IMAGEPATH, "post-06/contEvent_points.jpeg", upOneLevel=False),
    format="jpeg",
    width=imgW,
    height=imgH,
)

# Per POP
temp = contEventPoints.pivot(
    index="Continent", columns="Grouped Event", values="pointsPerEventPer100M"
)
temp.fillna(0, inplace=True)
fig = ff.create_annotated_heatmap(
    np.round(temp.values, 1),
    colorscale="Blues",
    x=list(temp.columns),
    y=list(temp.index),
)
fig.update_layout(
    title_text=f"Continent Points per Event per 100M Pop, 2020 Tokyo Olympics"
)
fig.update_xaxes(side="bottom")
# fig.show()
fig.write_image(
    getRelativeFp(IMAGEPATH, "post-06/contEvent_points_perPop.jpeg", upOneLevel=False),
    format="jpeg",
    width=imgW,
    height=imgH,
)


# %% USA vs China
comp = (
    ind.loc[ind["country"].isin(["USA", "CHN"])]
    .groupby(["country", "Grouped Event", "gender"])["points"]
    .sum()
    .reset_index()
)
comp.rename(columns={"gender": "Gender"}, inplace=True)
# temp = countryEventPoints.loc[countryEventPoints["country"].isin(["USA", "CHN"])]

fig = px.bar(
    comp,
    y="Grouped Event",
    x="points",
    color="country",
    barmode="group",
    facet_col="Gender",
    color_discrete_map={"CHN": "#DE2910", "USA": "#041E42"},
    title="China vs USA Medal Points by Gender and Event, 2020 Tokyo Olympics",
)
fig.update_xaxes(title_text="Medal Points")
# fig.show()
fig.write_image(
    getRelativeFp(IMAGEPATH, "post-06/chinaVsUsa.jpeg", upOneLevel=False),
    format="jpeg",
    width=imgW,
    height=imgH,
)

# %%
