import streamlit as st
from PIL import Image
from streamlit_autorefresh import st_autorefresh
import logging
from app.analytics import llm
from io import StringIO

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

.fa-thumbs-up, .fa-thumbs-down {
    color: blue;
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
        stringio = StringIO(uploaded_file.getvalue().encode('ascii', 'replace').decode())
        content = stringio.read()
        url, answer = llm.run_task(content, task='summarization', model_name='tanzuhuggingface/dev', experiment_name='testinference123',
                                   use_topk='n')
        st.markdown(f"<br/>Status:<br/> <span class='metriclabel'>File uploaded</span>"
                    f"<br/><span 'font-size:1.2em;' class=predictedlabel>{answer}</span>"
                    "<br/>Status:<br/> <span class='metriclabel'>Rank answer</span>"
                    "<span class='fa-stack fa-2x'><i class='fa fa-circle fa-stack-2x'>"
                    "</i><i class='fa fa-thumbs-up fa-stack-1x fa-inverse'></i></span>"
                    "<span class='fa-stack fa-2x'><i class='fa fa-circle fa-stack-2x'>"
                    "</i><i class='fa fa-thumbs-down fa-stack-1x fa-inverse'></i></span>",
                    unsafe_allow_html=True)

# AIBot
with tab2:
    st.markdown("This bot uses <b>on-premise data</b> to provide information about VMware technologies.<br/>",
                unsafe_allow_html=True)

    question = st.text_input('Your question', '''''', key='aibot')
    with st.spinner('Querying local data...'):
        if question:
            url, answer = llm.run_task(question, task='summarization', model_name='tanzuhuggingface/dev', experiment_name='llm_summary', use_topk='y', inference_function_name='run_semantic_search')
            st.markdown(f"<b>Response:</b><br/><span style=font-size:1em;><a href=\"{url}\">Matched Document Link</a></span>"
                        f"<br/><br/><span style='font-size:1.2em;' class=predictedlabel>{answer}</span>",
                        unsafe_allow_html=True)

    with st.spinner('Querying local data with auto-generated embeddings...'):
            _, summary = llm.run_task(question, task='summarization', model_name='tanzuhuggingface/dev', experiment_name='llm_summary')
            st.markdown(f"<br/><b>Summary:</b><span style='font-size:1.2em;' class=predictedlabel>{summary}</span>"
                        f"<br/><br/><b>Model Name:</b><br/> <span class='predictedlabel'>tanzuhuggingface/dev</span>"
                        "<br/><br/> <span class='metriclabel'>Rank answer</span>"
                        "<span class='fa-stack fa-2x'><i class='fa fa-circle fa-stack-2x'>"
                        "</i><i class='fa fa-thumbs-up fa-stack-1x fa-inverse'></i></span>"
                        "<span class='fa-stack fa-2x'><i class='fa fa-circle fa-stack-2x'>"
                        "</i><i class='fa fa-thumbs-down fa-stack-1x fa-inverse'></i></span>",
                        unsafe_allow_html=True)

# Refresh the screen at a configured interval
st_autorefresh(interval=60 * 15 * 1000, key="anomalyrefresher")
