import streamlit as st

st.set_page_config(
    page_title="NYC Taxi Validator",
    page_icon="🚕",
    layout="wide",
)

file_inspection_page = st.Page(
    "validator_pages/file_inspection.py",
    title="File Inspection",
    icon="📄",
    default=True,
)

validation_control_page = st.Page(
    "validator_pages/validation_control.py",
    title="Validation Control",
    icon="▶️",
)

validation_analytics_page = st.Page(
    "validator_pages/validation_analytics.py",
    title="Validation Analytics",
    icon="▶️",
)

navigation = st.navigation(
    [
        file_inspection_page,
        validation_control_page,
        validation_analytics_page,
    ]
)

navigation.run()