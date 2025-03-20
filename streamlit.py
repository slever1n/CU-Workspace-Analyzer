import requests
import streamlit as st
import time
import openai
import google.generativeai as genai
import textwrap
import concurrent.futures
import logging
from st_copy_to_clipboard import st_copy_to_clipboard

# Set up logging
logging.basicConfig(level=logging.INFO)

# Set page title and icon
st.set_page_config(
    page_title="ClickUp Company Profile & Insights Generator",
    page_icon="🦄",
    layout="wide",
)

# hidden div with anchor
st.markdown("<div id='linkto_top'></div>", unsafe_allow_html=True)

# Add popover beside the title
st.title("🦄 ClickUp Workspace, Profile & Strategy Builder ")
with st.popover("ℹ️ How to use"):
    st.markdown("""
    :blue-background[***ClickUp API Key (Optional):***]
    - Enter your ClickUp API key to fetch Workspace data. You can get this from your ClickUp settings and going to Apps to generate an API Key. **Once you enter your API, wait for a few seconds for the app to pull your available Workspaces.**

    :blue-background[***Company Name (Optional):***] 
    - Enter a company name or website to generate a short company profile. You can get this from the invite or the email of the user.

    :blue-background[***Company Use Case:***] 
    - Describe your company's use case (e.g., consulting, project management, customer service) or the agenda mentioned by the user in the email.

    **Click the :green-background[*🚀 Let's Go!*] button to:**

    1. Fetch and display Workspace metrics(If API Key is entered and based on the Workspace selected).
    2. Generate a company profile.
    3. Generate tailored recommendations based on the provided data.

    *ℹ️ This tool uses Gemini AI to provide AI recommendations and company profile*
    """)

# Retrieve API keys from Streamlit secrets
openai_api_key = st.secrets.get("OPENAI_API_KEY")
openai_org_id = st.secrets.get("OPENAI_ORG_ID")
gemini_api_key = st.secrets.get("GEMINI_API_KEY")

# Configure OpenAI and Gemini if API keys are available
if openai_api_key:
    openai.organization = openai_org_id
    openai.api_key = openai_api_key

if gemini_api_key:
    genai.configure(api_key=gemini_api_key)

def get_company_info(company_name):
    """
    Generates a short company profile for the given company name using Gemini (or OpenAI if Gemini is unavailable).
    """
    if not company_name:
        return "No company information provided."
    
    prompt = textwrap.dedent(f"""
        Please build a short company profile for {company_name}. The profile should include the following sections:
        - **Company Size:** Provide an estimate of the company’s size (e.g., number of employees) based on public information or platforms like LinkedIn. Do not make assumptions, if its unavailable, skip it.
        - **Net Worth:** Include the company’s net worth or valuation if publicly available. Do not make assumptions, if its unavailable, skip it.
        - **Mission:** A brief mission statement.
        - **Key Features:** List 3-5 key features of the company.
        - **Vision:** State the long-term vision of the company, highlighting its aspirations and the impact it aims to create.
        - **Their Product:** Describe the company’s main product or service in detail.
        - **Target Audience:** Identify the primary groups of people or industries the company caters to.
        - **Overall Summary:** Summarize the company’s identity, vision, and value proposition in a few sentences.
    """)
    
    try:
        if gemini_api_key:
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(prompt)
            return response.text
        elif openai_api_key:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response["choices"][0]["message"]["content"]
        else:
            return ▋
