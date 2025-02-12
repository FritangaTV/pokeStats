import pandas as pd
import glob
import os
import streamlit as st
import numpy as np
import plotly.express as px

all_files = glob.glob(os.path.join('./data/', "*.csv"))

df = pd.concat((pd.read_csv(f) for f in all_files), ignore_index=True)

mask = df['Name'].isin(["psyrax", "Oscar Vera", "Rogelio Espinoza", "Rodrigo Torres Ochoa"])
playerDF = df[mask]
playerDF['date'] = pd.to_datetime(playerDF['date'])
playerDF = playerDF.sort_values(by=['date'])
st.write(playerDF)
fig = px.line(playerDF, x="date", y="rank", title='Rank(PCT) over time', color="Name")
st.plotly_chart(fig)