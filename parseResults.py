import pandas as pd
import glob
import os
import streamlit as st
import numpy as np
import plotly.express as px

st.set_page_config(
    layout="wide"
)

df = pd.read_csv('./data/all.csv')

playerSelect = st.multiselect( "Select players", df['Name'].unique(), ["psyrax", "Oscar Vera"])
eventSelect = st.multiselect( "Select events", df['event_type'].unique(), df['event_type'].unique())


selectedDF = df.copy()

if len(playerSelect) > 0:
    mask = selectedDF['Name'].isin(playerSelect)
    selectedDF = selectedDF[mask]
    
if len(eventSelect) > 0:
    eventMask = selectedDF['event_type'].isin(eventSelect)
    selectedDF = selectedDF[eventMask]
    
selectedDF['date'] = pd.to_datetime(selectedDF['date'])
selectedDF = selectedDF.sort_values(by=['date'])
st.write(selectedDF)
fig = px.line(selectedDF, x="date", y="rank", title='Rank(PCT) over time', color="Name")
st.plotly_chart(fig)