import streamlit as st
import pandas as pd

from nearquake.data_processor import get_daily_earth_quakes


min_mag = st.sidebar.slider("Eartquake Magnitude", 0.0, 10.0, step=1.0)
period = st.sidebar.selectbox(
    "How would you like aggregate the data", ["Year", "Month", "Week", "Day"]
)

dates, counts, mag = get_daily_earth_quakes()
dates = pd.to_datetime(dates)


data = pd.DataFrame({"Date": dates, "Magnitude": mag, "Earthquake Count": counts})
data = data[data["Magnitude"] >= min_mag]

if period == "Year":
    period_filter = "YE"
    title = "Yearly"
elif period == "Month":
    period_filter = "ME"
    title = "Monthly"
elif period == "Week":
    period_filter = "W"
    title = "Weekly"
elif period == "Day":
    period_filter = "d"
    title = "Daily"


data = (
    data.groupby(pd.Grouper(key="Date", freq=period_filter))["Earthquake Count"]
    .sum()
    .reset_index()
)
data.set_index("Date", inplace=True)

# Example number
big_number = 123456

# Use Streamlit to create a line chart
st.write(
    """
    # Earhquake Event Dashboards 
    """
)

# Display the number using st.metric
st.metric(
    label="Big Number",
    value=f"{round(sum(data['Earthquake Count'].values)):,}",
    delta="1.2%",
)

st.write(
    f"""
    #### Total {title} earthquake event counts 
    """
)
st.line_chart(data)
