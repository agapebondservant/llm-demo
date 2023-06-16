import streamlit as st
from PIL import Image
from streamlit_autorefresh import st_autorefresh
import logging

# Initializations
st.set_option('deprecation.showPyplotGlobalUse', False)

st.write("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nanum Gothic');
html, body, [class*="css"]{
   font-family: 'Nanum Gothic';
}
#tanzu-realtime-anomaly-detection-demo{
   color: #6a6161;
}
.blinking {
  animation: blinker 1s linear infinite;
  background: url('https://github.com/agapebondservant/tanzu-realtime-anomaly-detetction/blob/main/app/assets/clock.png?raw=true') no-repeat right;
}

span.predictedlabel{
    font-size: 1.6em;
    color: green;
}

span.metriclabel{
    font-size: 1em;
    color: wheat;
}

@keyframes blinker {
  50% {
    opacity: 0;
  }
}
</style>
""", unsafe_allow_html=True)

st.header('Tanzu/Vmware LLM Analytics with Postgres and Huggingface Demo')

st.text('Demonstration of question-answering transformers using neutral networks and Vmware Tanzu')

tab1, tab2 = st.tabs(["Text Summarization", "AI Bot"])

# Text Summarization
with tab1:
    uploaded_file = st.file_uploader("Select a PDF file to summarize", key="upl_cifar")
    if uploaded_file is not None:
        st.markdown(f"<br/>F-1 metric:<br/> <span class='metriclabel'>File uploaded</span>",
                    unsafe_allow_html=True)

# AIBot
with tab2:
    st.write("This bot uses <b>on-premise data</a> to provide information about VMware technologies.<br/>")

    question = st.text_input('Your question', '''''', key='aibot')  # , on_change=)

    with st.spinner('Querying local data...'):
        st.markdown(
            f"Response:<br/><span style=font-size:1.2em;>{question}</span>",
            unsafe_allow_html=True)

# Refresh the screen at a configured interval
st_autorefresh(interval=15 * 1000, key="anomalyrefresher")
