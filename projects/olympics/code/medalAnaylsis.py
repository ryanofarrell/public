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
countries["continent"] = countries["twoDigitCd"].apply(
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
eventList = ind["event"].unique().tolist()
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
    right=countries[["shortName", "longName", "flagUrl", "continent"]],
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
eventHighCnt = ind.groupby("eventHigh")["eventLow"].nunique().reset_index()
ind["eventGrouped"] = ind["eventHigh"]

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
    "eventGrouped",
] = "Traditional & Team Sports"

# Shooting and archery
ind.loc[
    ind["eventHigh"].isin(["Shooting", "Archery"]), "eventGrouped"
] = "Archery & Shooting"

# Combat
ind.loc[
    ind["eventHigh"].isin(["Weightlifting", "Wrestling"]),
    "eventGrouped",
] = "Weightlifting & Wrestling"
ind.loc[
    ind["eventHigh"].isin(["Fencing", "Boxing"]),
    "eventGrouped",
] = "Combat"

ind.loc[
    ind["eventHigh"].isin(["Taekwondo", "Karate", "Judo"]),
    "eventGrouped",
] = "Combat & Skill"

# Adventure
ind.loc[
    ind["eventHigh"].isin(["Surfing", "Sport Climbing", "Skateboarding", "Sailing"]),
    "eventGrouped",
] = "Adventure Sports"

# Water
ind.loc[
    ind["eventHigh"].isin(["Canoe", "Rowing"]),
    "eventGrouped",
] = "Canoe & Rowing"

# Swimming & Diving
ind.loc[
    ind["eventHigh"].isin(["Swimming", "Diving"]),
    "eventGrouped",
] = "Swimming & Diving"


# Artistic swimming, equestrian with Gymnastics
ind.loc[
    ind["eventHigh"].isin(["Artistic Swimming", "Gymnastics", "Equestrian"]),
    "eventGrouped",
] = "Artistry Sports"

# Combine athletics
ind.loc[
    ind["eventHigh"].isin(["Athletics", "Modern Pentathlon", "Triathlon"]),
    "eventGrouped",
] = "Athletics"

groupedCnts = (
    ind.groupby("eventGrouped")["eventLow"]
    .nunique()
    .reset_index()
    .rename(columns={"eventLow": "eventCnt"})
)


# %% Initial viz
colorMap = {"Gold": "#FFD700", "Silver": "#C0C0C0", "Bronze": "#CD7F32"}
fig = px.bar(
    ind.loc[ind["country"] == "ROC"],
    x="eventGrouped",
    y="points",
    color="color",
    color_discrete_map=colorMap,
    category_orders={"color": ["Gold", "Silver", "Bronze"]},
    facet_row="gender",
)
fig.show()


# %% Country Event Analysis
countryPoints = ind.groupby(["country", "eventGrouped"])["points"].sum().reset_index()
countryPoints = pd.merge(countryPoints, groupedCnts, how="left", on="eventGrouped")
countryPoints = pd.merge(
    countryPoints,
    countries[["shortName", "population"]],
    how="left",
    left_on="country",
    right_on="shortName",
)
countryPoints["pointsPerEvent"] = countryPoints["points"] / countryPoints["eventCnt"]
countryPoints["pointsPerEventPer10Mill"] = (
    countryPoints["pointsPerEvent"] / countryPoints["population"] * 10000000
)

countryPoints["countryEvent"] = (
    countryPoints["country"] + " - " + countryPoints["eventGrouped"]
)
n = 25


countryPoints.sort_values(by=["pointsPerEvent"], ascending=False, inplace=True)
fig = px.bar(countryPoints.iloc[:n], x="countryEvent", y="pointsPerEvent")
fig.show()


countryPoints = countryPoints.loc[countryPoints["points"] >= 10]
countryPoints.sort_values(by=["pointsPerEventPer10Mill"], ascending=False, inplace=True)

fig = px.bar(countryPoints, x="countryEvent", y="pointsPerEventPer10Mill")
fig.show()

# %% Region Analysis

continentPoints = (
    ind.groupby(["continent", "eventGrouped"])["points"].sum().reset_index()
)
continentPoints = pd.merge(continentPoints, groupedCnts, how="left", on="eventGrouped")

continentPoints = pd.merge(
    continentPoints,
    continents.rename(columns={"Name": "continent", "Pop": "population"}),
    how="left",
    on="continent",
)
continentPoints["pointsPerEvent"] = (
    continentPoints["points"] / continentPoints["eventCnt"]
)
continentPoints["pointsPerEventPer100Mill"] = (
    continentPoints["pointsPerEvent"] / continentPoints["population"] * 100000000
)

# %%
