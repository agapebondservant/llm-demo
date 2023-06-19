import streamlit as st
from PIL import Image
from streamlit_autorefresh import st_autorefresh
import logging

# Initializations
st.set_option('deprecation.showPyplotGlobalUse', False)

st.write("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nanum Gothic');
@import url('https://maxcdn.bootstrapcdn.com/font-awesome/4.4.0/css/font-awesome.min.css');
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

.fa-thumbs-up:hover, .fa-thumbs-down:hover {
    color: orange;
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
        st.markdown(f"<br/>Status:<br/> <span class='metriclabel'>File uploaded</span>"
                    "<span class='fa-stack fa-2x'><i class='fa fa-circle fa-stack-2x'>"
                    "</i><i class='fa fa-thumbs-up fa-stack-1x fa-inverse'></i></span>"
                    "<span class='fa-stack fa-2x'><i class='fa fa-circle fa-stack-2x'>"
                    "</i><i class='fa fa-thumbs-down fa-stack-1x fa-inverse'></i></span>",
                    unsafe_allow_html=True)

# AIBot
with tab2:
    st.markdown("This bot uses <b>on-premise data</b> to provide information about VMware technologies.<br/>",
                unsafe_allow_html=True)

    question = st.text_input('Your question', '''''', key='aibot')  # , on_change=)

    with st.spinner('Querying local data...'):
        st.markdown(
            f"Response:<br/><span style=font-size:1.2em;>{question}</span>"
            "<br/>Status:<br/> <span class='metriclabel'>File uploaded</span>"
            "<span class='fa-stack fa-2x'><i class='fa fa-circle fa-stack-2x'>"
            "</i><i class='fa fa-thumbs-up fa-stack-1x fa-inverse'></i></span>"
            "<span class='fa-stack fa-2x'><i class='fa fa-circle fa-stack-2x'>"
            "</i><i class='fa fa-thumbs-down fa-stack-1x fa-inverse'></i></span>",
            unsafe_allow_html=True)

# Refresh the screen at a configured interval
st_autorefresh(interval=15 * 1000, key="anomalyrefresher")
