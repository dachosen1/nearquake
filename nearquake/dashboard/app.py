import streamlit as st
import numpy as np
import pandas as pd

from nearquake.data_processor import get_daily_earth_quakes


dates, counts, mag  = get_daily_earth_quakes()
dates = pd.to_datetime(dates)

data = pd.DataFrame({"Date": dates, "Earthquake Count": counts})
# Set the index to 'Date' for better x-axis handling
data.set_index("Date", inplace=True)

# Use Streamlit to create a line chart
st.line_chart(data)
