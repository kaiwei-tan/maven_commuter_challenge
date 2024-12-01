# Introduction
For the Maven Commuter Challenge, I play a Data Visualization Specialist for the Metropolitan Transportation Authority (MTA), creating a visualization to illustrate post-pandemic recovery trends across the MTA's services.

The dashboard is made with Plotly and Dash, hosted live on [Render](https://maven-commuter-challenge.onrender.com/) (may take a while to load).

# Data
We were provided with a time series (daily) of usage of various MTA services from 2020 to 2024, along with a percentage comparison to pre-pandemic levels (e.g. subway ridership on 2020-03-01 was 97% of an equivalent to an equivalent pre-pandemic date). These percentages were pre-calculated using MTA's methodology, though we did not have access to exact pre-pandemic counts.

The information was comprehensive, but not exactly in the form I needed.

## Desired state
I decided to visualize weekly counts for each service, from the perspective of weekday, weekend, and overall week numbers.

## Data transformations
In order to get the data in a form required for the desired visualization, I took the following steps:
- Back out the equivalent pre-pandemic numbers using the given values (post-pandemic numbers divided by percentage)
- Sum the pre- and post- pandemic numbers across the different time widows for each week (5-day weekdays, 2-day weekends, 7-day weeks)
- This allows us to get post-pandemic counts as a percentage of pre-pandemic counts across weekdays, weekends, and overall weeks for each week in the data (e.g. on the week starting 2020-03-01, total bus rides across the weekdays were 97% of the equivalent pre-pandemic period)
- For consistency, weeks start on Sunday because the first date in the data was March 1, 2020, which is a Sunday.

## Additional information
I quickly also realized I needed to pick milestone events. The pandemic years were immensely eventful, and after lots of news articles and Wiki summaries, I was able to pick major milestones which likely have had a on MTA numbers:
- First COVID-19 case attributed to New York City (March 3, 2020) [NBC New York] and subsequent "New York on PAUSE" lockdown [nyc.gov]
- City reopening in four biweekly phases (June 8, 2020) [NBC New York]
- Beginning of city vaccination program (December 21, 2020) [NBC New York]
- City workers returning to office (September 13, 2021) [nyc.gov]
- First Omicron case attributed to New York City (December 2, 2021) [NBC New York]
- Lifting of mask mandates on MTA transport (September 7, 2022) [Curbed]
- Expansion of city remote work programs (October 23, 2023) [amNew York]

# Dashboard
Using the compiled information I was able to create a simple dashboard to answer an overarching question, "Have MTA commutes recovered to pre-pandemic levels?"

The dashboard includes an "All service" view and service-specific drilldowns.

# Insights
## Overall services
Car traffic through Bridges and Tunnels recovered quickly, likely due to high car dependency during the pandemic period [StreetsBlog NYC]. Access-a-Ride usage has also rebounded, in fact beyond pre-pandemic numbers.

Other public transit services (Subways, Buses, Metro-North, LIRR) still lag behind and have not recovered fully.

## Individual services
Interestingly, despite not having recovered to pre-pandemic levels overall, we see different trends for certain services when we break them down to weekdays against weekends. Examples include the LIRR and Metro-North networks, where weekend numbers were driven by leisure travel [New York State official website], which have rebounded more strongly as compared to regular commuting during the weekdays.
