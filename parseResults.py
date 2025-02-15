import streamlit as st

st.set_page_config(
    layout="wide",
    page_title="Pokemon TCG Stats del tio Pay",
)

st.title("Pokemon TCG Stats del tio Pay")
st.text("Hola, soy el tio Pay (psyrax) y aqui puedes ver mis estadisticas de torneos de Pokemon TCG")
st.text("Los datos son extraidos de la pagina oficial de Pokemon TCG y se actualizan automaticamente por medio de un script de python el cual puedes encontrar en el repositorio del proyecto.")
st.text("El script de python extrae los datos de los torneos de Pokemon TCG en los que he participado y los guarda en un archivo csv, el cual es leido por esta aplicacion web. Si no apareces en este listado, es porque no has participado en torneos de Pokemon TCG donde he estado yo.")

pg = st.navigation([st.Page("pages/players.py", "Jugaores"), st.Page("pages/venues.py", "Venues")])
pg.run()