import datetime as dt
import pandas as pd
import plotly.express as px
import streamlit as st

#Page Config
st.set_page_config(
    page_title="US Housing Dashboard",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded")


#Loading main dataset
@st.cache_data
def load_main_data():
    data = pd.read_csv('df_merged.csv')
    data['Date'] = pd.to_datetime(data['Date'])  # Ensure 'Date' is datetime type for easier filtering
    return data

#Function for creating choropleth
def create_choropleth():
    data = pd.read_csv('df_mortgage_rates.csv')
    state_avg_payment = data.groupby('Abbrev')['MonthlyPayment'].mean().reset_index()
    fig = px.choropleth(state_avg_payment,
                        locations='Abbrev',
                        locationmode="USA-states",
                        color='MonthlyPayment',
                        scope="usa",
                        title=f"Avg Monthly Mortgage Payment",
                        labels={'MonthlyPayment': 'Monthly Payment ($)'})

    return fig

#Function for creating rents linechart
def create_rent_linechart():
    df = pd.read_csv('rents_payments.csv')
    df = df[df['Abbrev'] == state_selected]
    fig = px.line(df, x='Date', y=['MonthlyPayment', 'AvgRent'],
                  labels={'value': 'USD', 'variable':'Series'},
                  title='Monthly Payment vs. Avg Rent Over Time')
    return fig

#For making numbers look prettier
def format_number(num):
    if num > 1000000:
        if not num % 1000000:
            return f'{num // 1000000} M'
        return f'{round(num / 1000000, 1)} M'
    return f'{num // 1000} K'

data = load_main_data()

#Building the sidebar with input features
with st.sidebar:
    st.title('User Input Features')

    state_list = data['Abbrev'].unique()
    state_selected = st.sidebar.selectbox('Select State', state_list)

    type_list = data['Type'].unique()
    type_selected = st.sidebar.multiselect('Select Property Type(s)', type_list, default=type_list)

    min_date = data['Date'].min().date()
    max_date = data['Date'].max().date()
    start_date, end_date = st.sidebar.date_input('Select Date Range', [min_date, max_date], min_value=min_date, max_value=max_date)

#Filtering data according to user input
filtered_data = data[
    (data['Abbrev'] == state_selected) &
    (data['Date'].dt.date >= start_date) &
    (data['Date'].dt.date <= end_date) &
    (data['Type'].isin(type_selected))
]

filtered_data = filtered_data.drop('Unnamed: 0', axis=1)

#Metric Cards for Returns by Type
cols = st.columns(len(type_selected))

for index, i in enumerate(type_selected):
    metricdata = filtered_data[filtered_data['Type'] == i]
    start_value = metricdata['AvgPrice'].iloc[0]
    end_value = metricdata['AvgPrice'].iloc[-1]
    returns = (end_value - start_value)
    return_delta = ((returns / start_value) * 100).round(0)
    returns = format_number(returns)

    with cols[index]:
        st.metric(label=f'Returns for {i}', value=returns, delta=f"{return_delta}%")

#Creating Dashboard panels
col = st.columns((4, 4), gap='medium')

with col[0]:
    st.markdown('### Housing Data')

    #Tabular summary of filtered data
    st.write(f"Filtered Data for {state_selected}")
    st.dataframe(filtered_data)

    #Line chart for house price over time with filters
    filtered_data = filtered_data.sort_values('Date')
    national_avg = filtered_data.groupby('Date')['AvgPrice'].mean().rename('US Average')
    chart_data = pd.pivot_table(filtered_data, values='AvgPrice', index='Date', columns='Type', aggfunc='mean')

    chart_data = pd.concat([chart_data, national_avg], axis=1)
    st.write('**Housing Price by Type**')
    st.line_chart(chart_data)

with col[1]:
    st.markdown('### Renting vs Owning')
    #Creating and showing choropleth
    choropleth = create_choropleth()
    st.plotly_chart(choropleth, use_container_width=True)

    #Creating and showing rent linechart
    linechart = create_rent_linechart()
    st.plotly_chart(linechart, use_container_width=True)

