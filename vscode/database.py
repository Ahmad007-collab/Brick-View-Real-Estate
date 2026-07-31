# import streamlit as st
#st.title("this is my title")

import sqlite3
import streamlit as st

@st.cache_resource
def get_connection():
    conn = sqlite3.connect(
        "brickview_realstate.db",
        check_same_thread=False
    )
    return conn


