# %% Imports
from bs4 import BeautifulSoup
import requests
import time
import random
import pandas as pd
from helpers import getRelativeFp


# %% Scrape overall site, get countries, urls, and medal counts
soup = BeautifulSoup(
    requests.get(
        "https://www.espn.com/olympics/summer/2020/medals/_/view/overall"
    ).text,
    "html.parser",
)

# Nav to medal table, parse each row for data, save as output
medalTable = (
    soup.find("table", "medals olympics has-team-logos").find("tbody").find_all("tr")
)

countries = {}
for row in medalTable:
    cells = row.find_all("td")
    shortName = cells[0].text.strip()
    countries[shortName] = {
        "shortName": cells[0].text.strip(),
        "url": f"https://www.espn.com{cells[0].a.attrs['href']}",
        "gold": int(cells[1].text.strip()),
        "silver": int(cells[2].text.strip()),
        "bronze": int(cells[3].text.strip()),
    }


# %% Parse country sites for individual results
individualOut = []
i = 1
for country in list(countries.values()):
    # Delay so not to overload the server
    delaySecs = random.random() * 3
    print(
        f"Scraping site for {country['shortName']} in {delaySecs:,.2f}s (#{i} of {len(countries)})"
    )
    i += 1
    time.sleep(delaySecs)

    # Create soup object from url
    soup = BeautifulSoup(
        requests.get(country["url"]).text,
        "html.parser",
    )

    # Add long name and flag url to country in dict
    buttonSection = soup.find("button", "button-filter med dropdown-toggle")
    countries[country["shortName"]]["longName"] = buttonSection.text.strip()
    countries[country["shortName"]]["flagUrl"] = buttonSection.img.attrs["src"]

    # Go through the medal sections, parse events, winners, color of medal
    medalSections = soup.find("table", "medals olympics has-team-logos").find_all(
        "thead"
    )
    for sec in medalSections:
        color = sec.tr.td.text.strip()
        resultSection = sec.find_next_sibling("tbody")
        for row in resultSection.find_all("tr"):
            cells = row.find_all("td")

            # If no event, use previous event name
            potentialEventName = cells[0].text
            if potentialEventName != "":
                event = potentialEventName

            # If athelete cell has text, use that, otherwise 'team'
            try:
                athlete = cells[1].a.text
            except AttributeError:
                athlete = "team"
            individualOut.append(
                {
                    "country": country["shortName"],
                    "event": event,
                    "athlete": athlete,
                    "color": color,
                }
            )


# %% Data quality check - unique event winners by color should match for countries
individualDf = pd.DataFrame(individualOut)
countryDf = pd.DataFrame(countries.values())

countryAgg = (
    individualDf.groupby(["country", "color"])["event"]
    .nunique()
    .reset_index()
    .pivot(index="country", columns="color")
    .fillna(0)
)
countryAgg.columns = [x[1].lower() for x in countryAgg.columns]
countryAgg.reset_index(inplace=True)

errors = []
totalMedalDiscrepancy = 0
for country in countries.values():
    for color in ["bronze", "gold", "silver"]:
        dictVal = country[color]
        aggVal = countryAgg.loc[countryAgg["country"] == country["shortName"]][
            color
        ].values[0]
        if dictVal != aggVal:
            totalMedalDiscrepancy += abs(dictVal - aggVal)
            errors.append(
                {
                    "country": country["shortName"],
                    "color": color,
                    "homepageValue": dictVal,
                    "atheleteValue": aggVal,
                }
            )

print(
    f"Discrepancy of {totalMedalDiscrepancy:.0f} medals ({totalMedalDiscrepancy / countryDf[['gold','silver','bronze']].sum().sum():.2%})"
)

# %% Save data to directory
individualDf.to_csv(getRelativeFp(__file__, "../data/output/individualMedals.csv"))
countryDf.to_csv(getRelativeFp(__file__, "../data/output/countryMedals.csv"))

# %%
