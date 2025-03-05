import pandas as pd
import streamlit as st
import plotly.express as px



df = pd.read_csv('./data/standings/all.csv', low_memory=False)
df['date'] = pd.to_datetime(df['date'])

filterCol1, filterCol2, filterCol3 = st.columns(3)

with filterCol1:
    st.title("Filtros")
    st.text("Puedes seleccionar los jugadores y eventos que quieras ver en el grafico de abajo. Por favor se amable y no me critiques por mi desempeño en los torneos, soy un tio muy sensible.")
with filterCol2:
    playerSelect = st.multiselect( "Jugadores", df['Name'].unique(), ["psyrax", "Oscar Vera"])
with filterCol3:
    eventSelect = st.multiselect( "Eventos", df['event_type'].unique(), df['event_type'].unique())


selectedDF = df.copy()


resultsTab, dataTab = st.tabs(["Resultados", "Data"])


with resultsTab:
    resultsCol1, resultsCol2 = st.columns(2)
    if len(playerSelect) > 0:
        mask = selectedDF['Name'].isin(playerSelect)
        selectedDF = selectedDF[mask]
        
    if len(eventSelect) > 0:
        eventMask = selectedDF['event_type'].isin(eventSelect)
        selectedDF = selectedDF[eventMask]
        
        selectedDF['date'] = pd.to_datetime(selectedDF['date'])
        selectedDF['Reverse Rank'] = 100-selectedDF['rank']
        selectedDF = selectedDF.sort_values(by=['date'])


        playerScores = selectedDF.groupby('Name').agg({'rank': ['mean', 'std', 'sum']}).reset_index()
        playerScores['Eventos'] = selectedDF.groupby('Name').size().values
        playerScores['Media inversa'] = 100-playerScores[('rank', 'mean')].round(2)
        playerScores['Score'] = (100-playerScores[('rank', 'mean')].round(2))*playerScores['Eventos']
        playerScores = playerScores.sort_values(by=[('rank', 'mean')], ascending=True).reset_index(drop=True)

        with resultsCol1:
            st.title("Estadisticas")
            st.text("El Score se calcula como la media inversa de la posicion en los eventos multiplicada por la cantidad de eventos en los que ha participado el jugador.")
            st.dataframe(playerScores, use_container_width=True)
            st.write("TODO: rank por tipo de evento por jugador, distribucion de posiciones por evento")
            
        with resultsCol2:
            st.title("Gráficos de desempeño")
            st.subheader("Posición por evento")
            st.text("Aqui puedes ver el grafico de la data filtrada acomodada por percentiles. Mas alto es mejor.")
            st.text("Un percentil es una medida estadística que indica el valor por debajo del cual se encuentra un porcentaje dado de observaciones en un grupo de observaciones. Es decir, que tan bien o mal le fue a un jugador en un torneo en comparacion con los demas jugadores sin que importe mucho la cantidad de participantes.")
            fig = px.line(selectedDF, x="date", y="Reverse Rank", title='Percentil Inverso de posición por evento', color="Name")
            st.plotly_chart(fig)

with dataTab:
    st.title("Data filtrada")
    st.text("Aqui puedes ver la data filtrada por los jugadores y eventos seleccionados")
    st.dataframe(selectedDF, use_container_width=True)

st.divider()

st.title("Data completa")
st.text("Aqui puedes ver la data completa")
leaderTab, scoreTab, fullDataTab = st.tabs(["Leaderboard", "Score", "Data completa"])

with leaderTab:
    st.title("Leaderboard")
    st.subheader("Número de eventos")
    eventDF = df.copy() 
    eventDF['Eventos'] = eventDF.groupby('Name')['Name'].transform('count')
    st.dataframe(eventDF.groupby('Name').agg({'Eventos': 'max'}).sort_values(by='Eventos', ascending=False).reset_index(), use_container_width=True)
    
with scoreTab:
    st.subheader("Score")
    st.text("El Score se calcula como la media inversa de la posicion en los eventos multiplicada por la cantidad de eventos en los que ha participado el jugador.")
    leaderScores = df.groupby('Name').agg({'rank': ['mean', 'std', 'sum']}).reset_index()
    leaderScores['Eventos'] = df.groupby('Name').size().values
    leaderScores['Media inversa'] = 100-leaderScores[('rank', 'mean')].round(2)
    leaderScores['Score'] = (100-leaderScores[('rank', 'mean')].round(2))*leaderScores['Eventos']
    leaderScores = leaderScores.sort_values(by=["Score"], ascending=False).reset_index(drop=True)
    st.dataframe(leaderScores, use_container_width=True)
with fullDataTab:
    st.dataframe(df, use_container_width=True)

    eventDistBox = px.box(df, x="event_name", y="rank", color="event_type", title='Distribución de posiciones por evento', height=600)
    eventDistBox.update_layout(xaxis=dict(
        type="category",
        categoryorder='array', 
        categoryarray=df.sort_values(by=["date"]).reset_index()['event_name'].unique()
    ))

    st.plotly_chart(eventDistBox)



