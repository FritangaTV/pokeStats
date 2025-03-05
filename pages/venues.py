import pandas as pd
import streamlit as st
import plotly.express as px



st.header("Stats de lugares")

filterCol1, filterCol2 = st.columns(2)
venuesDF = pd.read_csv('./data/events/all_events.csv')
venuesDF['Date'] = pd.to_datetime(venuesDF['Date'])
venuesDF = venuesDF.sort_values(by=['Date']).reset_index(drop=True)
with filterCol1:
    selectedEvents = venuesDF[venuesDF['Event Type']!= 'Regional Championships']['Event Type'].unique()
    eventTypeSelect = st.multiselect( "Tipo de evento",venuesDF['Event Type'].unique(), selectedEvents)

with filterCol2:
    venueSelect = st.multiselect( "Lugares",venuesDF['Venue Name'].unique(),venuesDF['Venue Name'].unique())


selectedVenueDF = venuesDF.copy()

if len(venueSelect) > 0:
    venueMask = selectedVenueDF['Venue Name'].isin(venueSelect)
    selectedVenueDF = selectedVenueDF[venueMask]

if len(eventTypeSelect) > 0:
    eventMask = selectedVenueDF['Event Type'].isin(eventTypeSelect)
    selectedVenueDF = selectedVenueDF[eventMask]


graphTab, dataTab = st.tabs(["Graficos", "Data"])

with graphTab:
    priceFig = px.scatter(selectedVenueDF, x="Date", y="Masters Division", title='Jugadores por evento', color="Event Type", size="Total Players", height=600,  trendline="ols")
    st.plotly_chart(priceFig)

with dataTab:
    st.dataframe(selectedVenueDF, use_container_width=True)

st.divider()
st.dataframe(venuesDF, use_container_width=True)