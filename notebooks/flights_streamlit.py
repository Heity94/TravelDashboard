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


# title of the dashboard
st.title("Flights dashboard")

# wide layout
# st.set_page_config(layout -"wide")

# add a sidebar
# st.sidebar.subheader("World Map")

# load data
df = pd.read_csv(r"C:\Users\erics\OneDrive\Dokumente\GitHub\TravelDashboard\raw_data\preproc_df.csv")

# rename column long to lon
df.rename(columns = {'long':'lon'}, inplace = True)

# dropping nan in lon and lat
df = df[df['lon'].notna()]
df = df[df['lat'].notna()]

# converting lon and lat to numeric
df = df.astype({'lat':'int'})
df = df.astype({'lon':'int'})

# show data table
st.write(df)

# create map 
# st.map(df)

# create base map
m = folium.Map()
m

# Setting up the world countries data URL
url = 'https://raw.githubusercontent.com/python-visualization/folium/main/examples/data/world-countries.json'
country_shapes = f'{url}/world-countries.json'

#Adding the Choropleth layer onto our base map
folium.Choropleth(
    #The GeoJSON data to represent the world country
    geo_data=country_shapes,
    name='flights total',
    data=df,
    #The column aceppting list with 2 value; The country name and  the numerical value
    columns=['country_cc',"avg_no_seats"],
    key_on='feature.properties.name',
    fill_color='PuRd',
    nan_fill_color='white'
).add_to(m)
m








# BACKUP
# histogramm
st.subheader('flights per country')

#hist_values = np.histogram(
#data["origin_country"], bins=24, range=(0,24)
