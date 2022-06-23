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



# title of the dashboard
st.title("Flights dashboard")

# wide layout
# st.set_page_config(layout -"wide")

# add a sidebar
# st.sidebar.subheader("World Map")

# load Flight data
df = pd.read_csv(r"C:\Users\erics\OneDrive\Dokumente\GitHub\TravelDashboard\raw_data\new_data.csv")

# load Geo data
geojson = json.load(open(r"C:\Users\erics\OneDrive\Dokumente\GitHub\TravelDashboard\raw_data\countries.geojson"))

# show data table
st.write(df)

# create map
m = folium.Map()

# Map 1
fig = px.choropleth(df, geojson=geojson, color="avg_no_seats",
                    locations="country_cc", featureidkey="properties.ISO_A2",
                    projection="mercator",
                    color_continuous_scale="RdYlGn",
                    hover_name="country_cc"
                   )
fig.update_geos(fitbounds="locations", visible=True)
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
st.plotly_chart(fig)


top_country = st.slider('select number of top countries to look at:')

top_n_countries = df.groupby('country_cc').agg({'avg_no_seats':'sum'})['avg_no_seats'].nlargest(top_country)
top_n_fig = px.bar(top_n_countries, x=top_n_countries.index, y='avg_no_seats', color=top_n_countries.index)
st.plotly_chart(top_n_fig, use_container_width = True)

#for changing type of the maps
add_select = st.sidebar.selectbox("What map style do you want?",('open-street-map', 'white-bg', 'carto-positron', 'carto-darkmatter', 'stamen- terrain', 'stamen-toner', 'stamen-watercolor'))

select_color = st.sidebar.selectbox("What color do you want?",('RdYlGn', 'balance', 'viridis', 'Jet', 'RdBu', 'Temps'))


# Map2
fig2 = px.choropleth_mapbox(df, geojson=geojson, 
color="avg_no_seats", 
locations="country_cc", 
featureidkey="properties.ISO_A2", 
color_continuous_scale=select_color,
mapbox_style=add_select, 
opacity=0.6,
center = {"lat": 52.520008, "lon": 13.404954},
zoom=8)

fig2.show()


#folium.Choropleth(
#    geo_data='data_geo',
#    name='chloropeth',
#    data='df',
#    columns=['country_cc','avg_no_seats'],
#    key_on='features.Feature',
#    fill_color='Y1OrRd',
#    fill_opacity=0.7,
#    line_opacity=0.1,
#    legend_name='flights'
#)
#.add_to(m)
#folium.features.GeoJson('countries.geojson',
#                        name='')
