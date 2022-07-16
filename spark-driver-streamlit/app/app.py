import streamlit as st
import datetime
import time
import json
import sys, os
import plotly.express as px
import pandas as pd
from spark_mongo_query import get_mongo_data_spark

# load Geo data
geojson = json.load(open("spark-driver-streamlit/app/countries.geojson"))

# initial df to show on the website during loading
df = pd.read_csv("spark-driver-streamlit/app/Initial_map_220628_06_17.csv")

# Set page configuration to wide mode
st.set_page_config(layout="wide")

# title of the dashboard
st.title("GAPS - Global Aviation Passenger Streams")


# select start and end date
with st.form(key="columns_in_form"):

    col1, c, col2 = st.columns([2,0.2,2])

    start_date = col1.date_input('Select your start date:', datetime.date(2022,6,28))
    start_time = col1.time_input('Select your start time', datetime.time(6, 00))
    start_dtime = datetime.datetime.combine(start_date, start_time)
    c.write("")
    end_date = col2.date_input('Select your end date:', datetime.date(2022,6,28))
    end_time = col2.time_input('Select your end time', datetime.time(17, 00))
    end_dtime = datetime.datetime.combine(end_date, end_time)


    updated =  st.form_submit_button("Update travel dashboard")

container = st.container()

if updated:
    df = get_mongo_data_spark(start_time=start_dtime, end_time=end_dtime)


#Plot map
fig = px.choropleth_mapbox(df,
                            geojson=geojson,
                            color="net_passengers",
                            locations="country",
                            #range_color=rng_clr,
                            color_continuous_midpoint=0,
                            featureidkey="properties.ISO_A2",
                            color_continuous_scale="RdYlGn",
                            mapbox_style="open-street-map",
                            opacity=0.5,
                            center={
                                "lat": 30.463898991670995,
                                "lon": -0.276830032410518
                            },
                            zoom=1.4,
                            height=800)
fig.update_layout(
    margin={"r":0,"l":0, "b":0})


container.subheader("Net passenger travel per country")
container.write(f'''From {start_dtime.strftime("%a %m/%d %H:%M")} to {end_dtime.strftime("%a %m/%d %H:%M")}''')
container.plotly_chart(fig, use_container_width=True)
