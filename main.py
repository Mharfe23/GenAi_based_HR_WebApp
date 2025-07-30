import streamlit as st
from pages.chatPage import ChatPage
from pages.upload_resumePage import UploadPage
from pages.listResume import listResume
from pages.csvPage import CsvPage
import logging_config
import logging

logging_config.setup_logging()
logger = logging.getLogger(__name__)
logger.info("App started")


st.set_page_config(page_title="AI Talent Scout", layout="wide")
st.logo("./static/DXC_Logo.png",size="large")


pg = st.navigation([
    st.Page(ChatPage,title="Chat Page"),
    st.Page(UploadPage, title="Upload Page"),
    st.Page(listResume),
    st.Page(CsvPage, title="csv table"),
])

pg.run()
