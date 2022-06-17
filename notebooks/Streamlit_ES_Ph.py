import pandas as pd
import folium
from folium.features import GeoJsonPopup, GeoJsonTooltip
import streamlit as st
from streamlit_folium import folium_static
import plotly.express as px
import numpy as np
import os
import glob
import folium
import json
from ast import literal_eval

# Set page configuration to wide mode
st.set_page_config(layout="wide")

# title of the dashboard
st.title("Flights dashboard")

# load Flight data
df = pd.read_csv("../raw_data/new_data.csv")
df.columns = ["country", "net_passengers"] # I renamed the columns

# load Geo data
geojson = json.load(open("../raw_data/countries.geojson"))

# show data table
#st.write(df)

#for changing type of the maps
add_select = st.sidebar.selectbox("What map style do you want?",('open-street-map', 'white-bg', 'carto-positron', 'carto-darkmatter', 'stamen- terrain', 'stamen-toner', 'stamen-watercolor'))

select_color = st.sidebar.selectbox("What color do you want?",('RdYlGn', 'balance', 'viridis', 'Jet', 'RdBu', 'Temps'))

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
