import sys
import logging
import os
import tempfile
import pathlib

import streamlit as st
from dotenv import load_dotenv

from langchain.document_loaders import PyPDFLoader
from sentence_transformers import SentenceTransformer

from genai.credentials import Credentials
from genai.schemas import GenerateParams
from genai.model import Model

from typing import Literal, Optional, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma, FAISS
from langchain.embeddings import HuggingFaceEmbeddings
import numpy as np
# Most GENAI logs are at Debug level.
# logging.basicConfig(level=os.environ.get("LOGLEVEL", "DEBUG"))

st.set_page_config(
    page_title="form assistant",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(
    """
    <style>
        section[data-testid="stSidebar"] {
            width: 500px !important; # Set the width to your desired value
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("""
    <style>
        .reportview-container {
            margin-top: -2em;
        }
        #MainMenu {visibility: hidden;}
        .stDeployButton {display:none;}
        footer {visibility: hidden;}
        #stDecoration {display:none;}
    </style>
""", unsafe_allow_html=True)

hide_streamlit_style = """
                <style>
                div[data-testid="stToolbar"] {
                visibility: hidden;
                height: 0%;
                position: fixed;
                }
                div[data-testid="stDecoration"] {
                visibility: hidden;
                height: 0%;
                position: fixed;
                }
                div[data-testid="stStatusWidget"] {
                visibility: hidden;
                height: 0%;
                position: fixed;
                }
                #MainMenu {
                visibility: hidden;
                height: 0%;
                }
                header {
                visibility: hidden;
                height: 0%;
                }
                footer {
                visibility: hidden;
                height: 0%;
                }
                </style>
                """
st.markdown(hide_streamlit_style, unsafe_allow_html=True) 

st.header("報稅助手 with watsonx.ai 💬")

load_dotenv()

api_key = st.secrets["GENAI_KEY"]
api_endpoint = st.secrets["GENAI_API"]

api_key = os.getenv("GENAI_KEY", None)
api_endpoint = os.getenv("GENAI_API", None)

creds = Credentials(api_key,api_endpoint)

params = GenerateParams(
    decoding_method="greedy",
    max_new_tokens=3000,
    min_new_tokens=1,
    # stream=True,
    top_k=50,
    top_p=1,
    stop_sequences=['<EOS>']
)

def buildjson(requirement):
    prompt = f"""[INST]
    建立一個json結構，用來存放需求提到所需要的訊息。
    最後加上 <EOS>
    <<SYS>>需求: {requirement}
    <<SYS>>
    [/INST]json格式:"""
    output = ""
    for response in model.generate([prompt]):
        output = response.generated_text
    return output.replace("<EOS>","")

def buildform(requirement, jsonform):
    prompt = f"""[INST]
    建立一個html表格，給客戶輸入，要採集json格式裡的內容，要考慮需求。
    不要顯示JSON.
    最後加上<EOS>
    <<SYS>>
    需求: {requirement}
    json格式: `{jsonform}`
    <<SYS>>
    [/INST]html表格:"""
    output = ""
    for response in model.generate([prompt]):
        output = response.generated_text
    return output.replace("<EOS>","")

def buildquestions(requirement,answerjson):
    prompt = f"""[INST]你是一個報稅專員，請基於需求來引導客戶填寫報稅表格。請跟隨以下步驟:
    1. 列出還沒有答案的欄位
    2. 對每個沒有答案的欄位，提供一個問題給客戶，引導他填寫，記得考慮提供的需求背景。
    3. 最後記得說謝謝。
    note: 
    - 問題要有禮貌，精簡，你可以舉一些小例子說明。
    - 不要顯示解釋。
    - 如果已經有答案，就不要提問了。
    - 最後加上 <EOS>
    <<SYS>>需求: {requirement}
    json答案: `{answerjson}`
    <<SYS>>
    [/INST]引導問題列表:"""
    output = ""
    for response in model.generate([prompt]):
        output = response.generated_text
    return output.replace("<EOS>","")

def buildanswer(answer, existinganswer, jsonform):
    prompt = f"""[INST]
    從回覆中提取答案並保存為json。
    將新的答案合併到現有的答案.
    只展示合併後的答案.
    最後加上 <EOS>
    <<SYS>>
    回覆: {answer}
    已有答案: `{existinganswer}`
    json格式: {jsonform}
    <<SYS>>
    [/INST]合併的答案:"""
    output = ""
    for response in model.generate([prompt]):
        output = response.generated_text
    return output.replace("<EOS>","")

def fillform(answer, form):
    prompt = f"""[INST]
    基於提供的答案json填寫html表格.
    不要顯示json
    最後加上 <EOS>
    <<SYS>>
    答案: `{answer}`
    html表格: {form}
    <<SYS>>
    [/INST]含答案的html表格:"""

    output = ""
    for response in model.generate([prompt]):
        output = response.generated_text
    return output.replace("<EOS>","")

model = Model(model="meta-llama/llama-2-70b-chat",credentials=creds, params=params)


if "requirement" not in st.session_state:
    st.session_state.requirement = ""

if "jsonform" not in st.session_state:
    st.session_state.jsonform = ""

if "form" not in st.session_state:
    st.session_state.form = ""

if "filledform" not in st.session_state:
    st.session_state.filledform = ""

if "answer" not in st.session_state:
    st.session_state.answer = ""

if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar contents
with st.sidebar:
    st.title("報稅助手")

    btBuildForm = st.button("建立表格")
    btBuildQuestions = st.button("對話引導報稅")
    # btFillForm = st.button("fill form")

st.session_state.requirement = st.text_area("需求",height=10)

if btBuildForm:
    with st.spinner(text="正在建立表格...", cache=False):
        jsonform = buildjson(st.session_state.requirement)
        form = buildform(st.session_state.requirement, st.session_state.jsonform)
        st.session_state.jsonform = jsonform
        st.session_state.form = form
        st.session_state.filledform = form

# if btFillForm:
#     with st.spinner(text="building the form...", cache=False):
#         st.session_state.filledform = fillform(st.session_state.answer, st.session_state.form)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if btBuildQuestions:
    with st.chat_message("system"):
        with st.spinner(text="正在生成引導問題...", cache=False):
            questions = buildquestions(st.session_state.answer,st.session_state.requirement)
            st.markdown(questions)
            st.session_state.messages.append({"role": "agent", "content": questions})

if answer := st.chat_input("你的回答"):
    with st.chat_message("user"):
        st.markdown(answer)

    st.session_state.messages.append({"role": "user", "content": answer})
    with st.spinner(text="正在提取答案...", cache=False):
        answerjson = buildanswer(answer, st.session_state.answer, st.session_state.jsonform)
        st.session_state.answer = answerjson
        filledform = fillform(st.session_state.answer, st.session_state.form)
        st.session_state.filledform = filledform

    with st.chat_message("system"):
        with st.spinner(text="正在生成問題...", cache=False):
            questions = buildquestions(st.session_state.answer,st.session_state.requirement)
            st.markdown(questions)
            st.session_state.messages.append({"role": "agent", "content": questions})

with st.sidebar:
    with st.container(border=True):
        st.components.v1.html(st.session_state.filledform,height=300)
    st.code(st.session_state.answer,language="json")