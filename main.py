import streamlit as st
from pages.chatPage import ChatPage
from pages.upload_resumePage import UploadPage
from pages.listResume import listResume


st.set_page_config(page_title="HR Resume Assistant", layout="wide")
st.logo("./static/DXC_Logo.png",size="large")




pg = st.navigation([
    st.Page(ChatPage,title="Chat Page"),
    st.Page(UploadPage, title="Upload Page"),
    st.Page(listResume)
])

pg.run()
