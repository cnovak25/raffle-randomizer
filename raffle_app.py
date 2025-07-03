import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="🎉 Raffle Name Randomizer 🎉", page_icon="🎟️", layout="centered")

st.title("🎟️ Raffle Name Randomizer 🎟️")
st.write("Upload your list of names and click the button to randomly select a winner!")

uploaded_file = st.file_uploader("Upload Excel file with a 'Name' column", type=["xlsx"])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        df.columns = df.columns.str.strip()  # Clean up column names

        if 'Name' not in df.columns:
            st.error("The uploaded file must contain a column named 'Name'.")
        else:
            st.success(f"Loaded {len(df)} names from the file.")

            if st.button("🎉 Draw Winner 🎉"):
                winner = df.sample(1).iloc[0]['Name']
                st.balloons()
                st.success(f"🎉 The winner is: **{winner}** 🎉")
    except Exception as e:
        st.error(f"Error reading file: {e}")
else:
    st.info("Please upload an Excel file to get started.")
