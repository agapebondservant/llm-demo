import streamlit as st
from PIL import Image
from streamlit_autorefresh import st_autorefresh
import logging
from app.analytics import llm, model_customization
from io import StringIO

# Initializations
st.set_option('deprecation.showPyplotGlobalUse', False)

st.write("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nanum Gothic');
@import url('https://maxcdn.bootstrapcdn.com/font-awesome/4.4.0/css/font-awesome.min.css');
@import url('https://cdn.jsdelivr.net/npm/bootstrap@4.0.0/dist/css/bootstrap.min.css');
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

div.card {
    background: none;
}

a.demobody {
  text-decoration: none;
  padding: 4px;
  font-size: small;
}

@keyframes blinker {
  50% {
    opacity: 0;
  }
}

.fa-thumbs-up, .fa-thumbs-down {
    color: orange;
}

.fa-thumbs-up:hover, .fa-thumbs-down:hover {
    color: gray;
}
</style>
""", unsafe_allow_html=True)

st.header('Tanzu/Vmware LLM Analytics with Postgres and Huggingface Demo')

st.text('Demonstration of question-answering transformers using neutral networks and Vmware Tanzu')

tab1, tab2 = st.tabs(["Text Summarization", "AI Bot"])

uploaded_file, question = None, None

placeholder1, placeholder2, placeholder3 = st.empty(), st.empty(), st.empty()

# Text Summarization
with tab1:
    uploaded_file = st.file_uploader("Select a PDF file to summarize")
    if uploaded_file and uploaded_file != st.session_state.get('upl_file'):
        placeholder1.empty()
        with placeholder1.container():
            with st.spinner('Summarizing file...'):
                stringio = StringIO(uploaded_file.getvalue().decode())
                content = stringio.read()
                url, answer = llm.run_task(content, task='summarization', model_name='tanzuhuggingface/dev', experiment_name='testinference123',
                                           use_topk='n')
                st.markdown(f"<div class='card border-light mb-3'>"
                            f"<div class='card-body'><h4 class='card-title'>Summary</h4>"
                            f"<p class='card-text'>{answer}</p>"
                            f"<div class='card-footer text-muted'>"
                            "Rank answer"
                            "<span class='fa-stack fa-2x'><i class='fa fa-circle fa-stack-2x'>"
                            "</i><i class='fa fa-thumbs-up fa-stack-1x fa-inverse'></i></span>"
                            "<span class='fa-stack fa-2x'><i class='fa fa-circle fa-stack-2x'>"
                            "</i><i class='fa fa-thumbs-down fa-stack-1x fa-inverse'></i></span>"
                            f"</div></div></div>",
                            unsafe_allow_html=True)
        st.session_state['upl_file'] = uploaded_file

# AIBot
with tab2:
    st.markdown("This bot uses <b>on-premise data</b> to provide information about VMware technologies.<br/>",
                unsafe_allow_html=True)

    question, selected_model_name = st.text_input('Your question', ''''''), ''
    if question and question != st.session_state.get('aibot'):
        placeholder2.empty()
        with placeholder2.container():
            with st.spinner('Querying local data...'):
                selected_model_name = model_customization.select_base_llm()
                url, answer = llm.run_task(question, task='summarization', model_name=selected_model_name, experiment_name='llm_summary', use_topk='y')
                st.markdown(f"<div class='card border-light mb-3'>"
                            f"<div class='card-body'><h4 class='card-title'>Matched Documents</h4>"
                            f"<p class='card-text' style='font-style:italic;'>\"{answer}...\"</p>"
                            f"<a class='demobody' href=\"{url}\" target=\"blank\">View Document</a>"
                            f"<div class='card-footer text-muted'>"
                            "Rank answer"
                            "<span class='fa-stack fa-2x'><i class='fa fa-circle fa-stack-2x'>"
                            "</i><i class='fa fa-thumbs-up fa-stack-1x fa-inverse'></i></span>"
                            "<span class='fa-stack fa-2x'><i class='fa fa-circle fa-stack-2x'>"
                            "</i><i class='fa fa-thumbs-down fa-stack-1x fa-inverse'></i></span>"
                            f"</div></div></div>",
                            unsafe_allow_html=True)

    if question and question != st.session_state.get('aibot'):
        placeholder3.empty()
        with placeholder3.container():
            with st.spinner('Querying local data with auto-generated embeddings...'):
                _, summary = llm.run_task(question, task='summarization', model_name='tanzuhuggingface/dev', experiment_name='llm_summary')
                st.markdown(f"<div class='card border-light mb-3'>"
                            f"<div class='card-body'><h4 class='card-title'>Summary</h4>"
                            f"<p class='card-text'>{summary}</p>"
                            f"<div class='card-footer text-muted'>"
                            "Rank answer"
                            "<span class='fa-stack fa-2x'><i class='fa fa-circle fa-stack-2x'>"
                            "</i><i class='fa fa-thumbs-up fa-stack-1x fa-inverse'></i></span>"
                            "<span class='fa-stack fa-2x'><i class='fa fa-circle fa-stack-2x'>"
                            "</i><i class='fa fa-thumbs-down fa-stack-1x fa-inverse'></i></span>"
                            f"</div></div></div>"
                            f"<div class='card border-light mb-3'>"
                            f"<div class='card-body'><h5 class='card-title'>Model Name</h5>"
                            f"<p class='card-text'>tanzuhuggingface/dev</p></div></div>",
                            unsafe_allow_html=True)
        st.session_state['aibot'] = question

# Refresh the screen at a configured interval
# st_autorefresh(interval=60 * 15 * 1000, key="anomalyrefresher")
