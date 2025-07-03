import pandas as pd
import random
import base64

# Streamlit import moved inside to avoid errors in restricted environments
def run_app():
    import streamlit as st

    st.set_page_config(page_title="🎉 Raffle Name Randomizer 🎉", page_icon="🎟️", layout="centered")

    st.title("🎟️ Raffle Name Randomizer 🎟️")
    st.write("Upload your list of names and click the button to randomly select a winner!")

    uploaded_file = st.file_uploader("Upload Excel file with a 'Name' column", type=["xlsx"])

    def add_bg_from_url():
        st.markdown(
             f"""
             <style>
             .stApp {{
                 background-image: url('https://media.giphy.com/media/3o7TKtnuHOHHUjR38Y/giphy.gif');
                 background-size: cover;
             }}
             </style>
             """,
             unsafe_allow_html=True
         )

    def play_sound():
        sound_url = "https://www.soundjay.com/button/sounds/button-10.mp3"
        b64 = base64.b64encode(f'<audio autoplay><source src="{sound_url}" type="audio/mpeg"></audio>'.encode()).decode()
        st.markdown(f"<iframe src='data:text/html;base64,{b64}' style='display:none;'></iframe>", unsafe_allow_html=True)

    add_bg_from_url()

    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            df.columns = df.columns.str.strip()  # Clean up column names

            if 'Name' not in df.columns:
                st.error("The uploaded file must contain a column named 'Name'.")
            else:
                st.success(f"Loaded {len(df)} names from the file.")

                if st.button("🎆 Draw Winner 🎆"):
                    winner = df.sample(1).iloc[0]['Name']
                    st.balloons()
                    play_sound()
                    st.success(f"🎉 The winner is: **{winner}** 🎉")
        except Exception as e:
            st.error(f"Error reading file: {e}")
    else:
        st.info("Please upload an Excel file to get started.")

# Run the app only if this is the main module
if __name__ == "__main__":
    run_app()

