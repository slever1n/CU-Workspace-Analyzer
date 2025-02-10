import requests
import streamlit as st
import openai
import google.generativeai as genai
import time

# Set page title and icon
st.set_page_config(page_title="ClickUp Workspace Analyzer", page_icon="🚀", layout="wide")

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

def get_clickup_workspace_data(api_key):
    """Fetches real workspace data from ClickUp API."""
    if not api_key:
        return None
    
    url = "https://api.clickup.com/api/v2/team"
    headers = {"Authorization": api_key}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            teams = response.json().get("teams", [])
            if teams:
                team_id = teams[0]["id"]
                return fetch_workspace_details(api_key, team_id)
            else:
                return {"error": "No teams found in ClickUp workspace."}
        else:
            return {"error": f"Error: {response.status_code} - {response.json()}"}
    except Exception as e:
        return {"error": f"Exception: {str(e)}"}

def fetch_workspace_details(api_key, team_id):
    """Fetch detailed workspace data including spaces, tasks, and completion stats."""
    headers = {"Authorization": api_key}
    
    spaces_url = f"https://api.clickup.com/api/v2/team/{team_id}/space"
    try:
        response = requests.get(spaces_url, headers=headers)
        if response.status_code == 200:
            spaces = response.json().get("spaces", [])
            return {
                "📁 Spaces": len(spaces),
                "📂 Folders": sum(len(space.get("folders", [])) for space in spaces),
                "🗂️ Lists": sum(len(space.get("lists", [])) for space in spaces),
                "✅ Completed Tasks": sum(1 for space in spaces for folder in space.get("folders", []) for list_item in folder.get("lists", []) for task in list_item.get("tasks", []) if task.get("status", "") == "completed"),
                "⚠️ Overdue Tasks": sum(1 for space in spaces for folder in space.get("folders", []) for list_item in folder.get("lists", []) for task in list_item.get("tasks", []) if task.get("due_date", 0) and int(task["due_date"]) < int(time.time() * 1000)),
                "📝 Total Tasks": sum(len(list_item.get("tasks", [])) for space in spaces for folder in space.get("folders", []) for list_item in folder.get("lists", [])),
                "🔥 High Priority Tasks": sum(1 for space in spaces for folder in space.get("folders", []) for list_item in folder.get("lists", []) for task in list_item.get("tasks", []) if task.get("priority", "") == "urgent")
            }
        else:
            return {"error": f"Error fetching workspace details: {response.status_code}"}
    except Exception as e:
        return {"error": f"Exception fetching workspace details: {str(e)}"}

def display_workspace_data(workspace_data):
    """Displays workspace data in a beautiful tiled format."""
    if "error" in workspace_data:
        st.error(workspace_data["error"])
        return
    
    cols = st.columns(4)
    tiles = list(workspace_data.items())
    for i, (title, value) in enumerate(tiles):
        with cols[i % 4]:
            st.metric(label=title, value=value)

def get_company_info(company_name, use_case):
    """Generates AI-based company profile."""
    prompt = f"""
    Generate a detailed company profile for {company_name}.
    Include the industry, services/products, target market, competitors, and unique selling points.
    Additionally, relate the profile to the use case: {use_case}.
    """
    try:
        if openai_api_key:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": "You are a helpful assistant."},
                          {"role": "user", "content": prompt}]
            )
            return response["choices"][0]["message"]["content"]
    except Exception as e:
        if gemini_api_key:
            model = genai.GenerativeModel("gemini-pro")
            response = model.generate_content(prompt)
            return response.text
    return "⚠️ AI-generated company profile is not available."

# UI Setup
st.title("📊 ClickUp Workspace Analyzer")

option = st.radio("Choose Input Method:", ["Enter ClickUp API Key", "Enter Company Name"])
use_case = st.text_input("📌 Use Case (e.g., Consulting, Sales)")

if option == "Enter ClickUp API Key":
    clickup_api_key = st.text_input("🔑 ClickUp API Key", type="password")
    if st.button("🚀 Analyze"):
        with st.spinner("Analyzing ClickUp workspace... ⏳"):
            workspace_details = get_clickup_workspace_data(clickup_api_key)
        st.subheader("📊 Workspace Analysis:")
        display_workspace_data(workspace_details)

elif option == "Enter Company Name":
    company_name = st.text_input("🏢 Company Name")
    if st.button("🚀 Analyze"):
        with st.spinner("Generating company profile... ⏳"):
            company_profile = get_company_info(company_name, use_case)
        st.subheader("📌 AI Recommendations:")
        st.markdown(company_profile, unsafe_allow_html=True)
