import streamlit as st

# Title of the app
st.title('Quick Hazard Assessment')

# Input fields for hazard assessment
hazard_type = st.selectbox('Select Hazard Type:', ['Chemical', 'Biological', 'Physical'])

exposure_duration = st.number_input('Exposure Duration (in hours):', min_value=0)

# Calculate risk
if st.button('Assess Risk'):
    risk_level = 'Low'
    if exposure_duration > 2:
        risk_level = 'Medium'
    if exposure_duration > 5:
        risk_level = 'High'
    st.write(f'Risk Level: {risk_level}')
