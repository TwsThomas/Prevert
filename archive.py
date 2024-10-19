# streamlit run prevert.py

import streamlit as st

# List of quotes
quotes = [
    "La vie est une pomme.",
    "La persévérance est la clé du succès.",
    "Il n'y a pas de raccourci pour atteindre le succès. " * 10,
]

st.title("expander")
col1, col2 = st.columns(2)
for i, quote in enumerate(quotes):
    with (col1 if i % 2 == 0 else col2).expander(quote):
        st.write("")

st.title("container")
col1, col2 = st.columns(2)
for i, quote in enumerate(quotes):
    with (col1 if i % 2 == 0 else col2).container():
        st.markdown(f"""
        <div style="border: 1px solid #ddd; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
            {quote}
        </div>
        """, unsafe_allow_html=True)