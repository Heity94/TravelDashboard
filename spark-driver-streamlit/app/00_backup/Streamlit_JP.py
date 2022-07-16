import pandas as pd
import streamlit as st
import plotly.express as px
import json
from ast import literal_eval
import datetime
import pymongo
from TravelDashboard.data import get_mongo_data, get_total_per_country


client = pymongo.MongoClient()
db = client['TravelDashboard']
# Set page configuration to wide mode
st.set_page_config(layout="wide")

# title of the dashboard
st.title("Flights dashboard")


# load Geo data
geojson = json.load(open("../raw_data/countries.geojson"))


# select start and end date
start_date = st.sidebar.date_input('Select your start date:', datetime.date(2022,6,1))

end_date = st.sidebar.date_input('Select your end date:', datetime.date(2022,6,2))

# select time frame you want to look at:
start_time = st.sidebar.time_input('Select your Start time', datetime.time(10, 00))
end_time = t = st.sidebar.time_input('Select your End time', datetime.time(15, 00))
start = start_date.strftime("%Y-%m-%d")+start_time.strftime("%H:%M:%S")
end = end_date.strftime("%Y-%m-%d")+end_time.strftime("%H:%M:%S")
#for changing type of the maps
add_select = st.sidebar.selectbox("What map style do you want?",('open-street-map', 'white-bg', 'carto-positron', 'carto-darkmatter', 'stamen- terrain', 'stamen-toner', 'stamen-watercolor'))

select_color = st.sidebar.selectbox("What color do you want?",('RdYlGn', 'balance', 'viridis', 'Jet', 'RdBu', 'Temps'))

if st.button('show me the map!'):
    epoch_start = datetime.datetime.strptime(start, "%Y-%m-%d%H:%M:%S").timestamp()
    epoch_end = datetime.datetime.strptime(end, "%Y-%m-%d%H:%M:%S").timestamp()

    query_landing = {
    "geo_altitude" : { "$lt" : 3000 },
    "vertical_rate" : { "$lt" : -4},
    "time" : {"$gt" : epoch_start},
    "time" : {"$lt" : epoch_end}
    }
    query_starting = {
    "geo_altitude" : { "$lt" : 3000 },
    "vertical_rate" : { "$gt" : 4},
    "time" : {"$gt" : epoch_start},
    "time" : {"$lt" : epoch_end}
    }

    starting, landing = get_mongo_data(collection=db.travel_data, query_starting=query_starting, query_landing=query_landing)
    df = pd.DataFrame(get_total_per_country(df_starting = starting, df_landing= landing))
    df = df.reset_index()
    df.columns = ["country", "net_passengers"]
    # Calculate max & min number of seats to adjust range color
    max_seats = df.net_passengers.max()
    min_seats = df.net_passengers.min()

    #depending which absolute value is higher either set the range to min or max
    if abs(max_seats) > abs(min_seats):
        rng_clr = [-max_seats, max_seats]
    else:
        rng_clr = [-min_seats, min_seats]

    # Map2
    fig2 = px.choropleth_mapbox(df,
                                geojson=geojson,
                                color="net_passengers",
                                locations="country",
                                range_color=rng_clr,
                                featureidkey="properties.ISO_A2",
                                color_continuous_scale=select_color,
                                mapbox_style=add_select,
                                opacity=0.5,
                                center={
                                    "lat": 30.463898991670995,
                                    "lon": -0.276830032410518
                                },
                                zoom=1.4,
                                height=800)
    fig2.update_layout(margin={"r":0,"t":0,"l":0,"b":0})#
    #fig2.update_layout(autosize=True)

    st.plotly_chart(fig2, use_container_width=True)
