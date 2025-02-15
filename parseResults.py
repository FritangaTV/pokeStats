import streamlit as st

pg = st.navigation([st.Page("pages/players.py"), st.Page("pages/venues.py")])
pg.run()