import streamlit as st

st.title("Validation Analytics")

total_rows = 82_500_000
rows_completed = 31_250_000
batches_completed = 625

progress_ratio = rows_completed / total_rows if total_rows else 0

col1, col2, col3 = st.columns(3)

col1.metric(
    label="Rows validated",
    value=f"{rows_completed:,}",
)

col2.metric(
    label="Total rows",
    value=f"{total_rows:,}",
)

col3.metric(
    label="Batches completed",
    value=f"{batches_completed:,}",
)

st.progress(
    progress_ratio,
    text=f"{progress_ratio:.1%} of all rows validated",
)