import streamlit as st
import time

# from ibm_watsonx_ai.foundation_models.utils.enums import ModelTypes
# from ibm_watsonx_ai.foundation_models import Model
# from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
# from ibm_watsonx_ai.foundation_models.extensions.langchain import WatsonxLLM

from genai.client import Client
from genai.credentials import Credentials
from genai.schema import TextGenerationParameters, TextGenerationReturnOptions
from genai.extensions.langchain import LangChainInterface
from genai.schema import (
    DecodingMethod,
    ModerationHAP,
    ModerationHAPInput,
    ModerationHAPOutput,
    ModerationParameters,
    TextGenerationParameters,
)

import pandas as pd
import tempfile
import pathlib
import json

from docx import Document

import os
from dotenv import load_dotenv

load_dotenv()

models = [
    "mistralai/mistral-7b-instruct-v0-2",
    "meta-llama/llama-3-8b-instruct",
    "deepseek-ai/deepseek-coder-33b-instruct",
    "meta-llama/llama-3-70b-instruct",
    "codellama/codellama-34b-instruct",
    "mistralai/mixtral-8x7b-instruct-v01",
    "ibm/granite-20b-code-instruct-v1",
    ]

import ssl

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

def keep_generate_till(model,prompt,endstring):
    lastanswer = ""
    while not lastanswer.endswith(endstring):
        answer = model.invoke(f"{prompt}{lastanswer}")
        lastanswer += answer
    return lastanswer

def removedependency(cobol):
    prompt = f"""Question:
you are expert on COBOL, please remove dependency from the COBOL code provided:
COBOL: `{cobol}`
Answer:rewrited COBOL```"""
    answer = model.invoke(prompt).replace("```","")
    # print(answer)
    return answer

def versionchange(cobol):
    prompt = f"""Question:
you are expert on COBOL, please upgrade the version of the COBOL code provided to latest one:
COBOL: `{cobol}`
Answer:rewrited COBOL```"""
    answer = model.invoke(prompt).replace("```","")
    # print(answer)
    return answer

def syntaxcheck(java):
    prompt = f"""Question:
please check the syntax and propose a fix to the java code provided:
please add package in need.
please import library in need.
please add neccessary comment.
java: `{java}`
Answer:rewrited java```java"""
    answer = model.invoke(prompt).replace("```","")
    # print(answer)
    return answer

def eliminateduplication(java):
    prompt = f"""Question:
please eliminate duplication in the java code provided.
- if two method do the same, keep one only.
java: `{java}`
Answer:rewrited java```java"""
    answer = model.invoke(prompt).replace("```","")
    # print(answer)
    return answer

def enhanceperformance(java):
    prompt = f"""Question:
please enhance the performance of the java provided.
please look into some loop, and check if some library we can employ.
java: `{java}`
Answer:rewrited java```java"""
    answer = model.invoke(prompt).replace("```","")
    # print(answer)
    return answer

def frameworksupport(java):
    prompt = f"""Question:
please use SprintBoot in the java provided.
java: `{java}`
Answer:rewrited java```java"""
    answer = model.invoke(prompt).replace("```","")
    # print(answer)
    return answer

def stylealignment(java):
    prompt = f"""Question:
    please rewrite the java provided to conform with DDD.
    java: `{java}`
    Answer:rewrited java```java"""
    answer = model.invoke(prompt).replace("```","")
    # print(answer)
    return answer

if "modelname" not in st.session_state:
    st.session_state.modelname = "ibm/granite-20b-code-instruct-v1"

model = LangChainInterface(
        model_id= st.session_state.modelname,
        client=Client(credentials=Credentials.from_env()),
        parameters=TextGenerationParameters(
            decoding_method=DecodingMethod.GREEDY,
            max_new_tokens=2000,
            min_new_tokens=1,
            # temperature=0.05,
            top_k=50,
            top_p=1,
            stop_sequences=['```'],
        )
    )

st.set_page_config(layout="wide")

inputcode = ""
filename = ""
outputcode = ""
actionname = ""

timespent = 0

with st.sidebar:
    st.title("WCAZ Helper")
    st.session_state.modelname = st.selectbox("model",models)
    if uploaded_file := st.file_uploader("upload COBOL/Java", type=["cbl","java"]):
        starttime = time.time()

        filename = uploaded_file.name
        inputcode = uploaded_file.read().decode()

        endtime = time.time()
        print(f"take {endtime-starttime} to read file")
    
    if filename.endswith(".cbl"):
        if st.button("Remove Dependency"):
            with st.spinner(text="In progress..."):
                actionname = "Remove Dependency"
                starttime = time.time()
                outputcode = removedependency(inputcode)
                timespent = time.time() - starttime
        if st.button("Version Change"):
            with st.spinner(text="In progress..."):
                actionname = "Version Change"
                starttime = time.time()
                outputcode = versionchange(inputcode)
                timespent = time.time() - starttime

    if filename.endswith(".java"):
        if st.button("Syntax Check"):
            with st.spinner(text="In progress..."):
                actionname = "Syntax Check"
                starttime = time.time()
                outputcode = syntaxcheck(inputcode)
                timespent = time.time() - starttime
        if st.button("Eliminate Duplication"):
            with st.spinner(text="In progress..."):
                actionname = "Eliminate Duplication"
                starttime = time.time()
                outputcode = eliminateduplication(inputcode)
                timespent = time.time() - starttime
        if st.button("Enhance Performance"):
            with st.spinner(text="In progress..."):
                actionname = "Enhance Performance"
                starttime = time.time()
                outputcode = enhanceperformance(inputcode)
                timespent = time.time() - starttime
                # print(outputcode)
        if st.button("Framework Support (e.g. SpringBoot)"):
            with st.spinner(text="In progress..."):
                actionname = "Framework Support"
                starttime = time.time()
                outputcode = frameworksupport(inputcode)
                timespent = time.time() - starttime
        if st.button("Style Alignment (e.g. DDD)"):
            with st.spinner(text="In progress..."):
                actionname = "Style Alignment"
                starttime = time.time()
                outputcode = stylealignment(inputcode)
                timespent = time.time() - starttime

titletext = ""
language = "java"

if filename.endswith(".cbl"):
    titletext = f"COBOL Pre-processing on {actionname} with {st.session_state.modelname} in {timespent:.2f}s"
    language = "cobol"
elif filename.endswith(".java"):
    titletext = f"Java Post-processing on {actionname} with {st.session_state.modelname} in {timespent:.2f}s"
    language = "java"

st.text(titletext)

colBefore, colAfter = st.columns(2)
with colBefore:
    st.text("before")
    st.code(inputcode,language,line_numbers=True)

with colAfter:
    st.text("after")
    st.code(outputcode,language,line_numbers=True)
