import requests
import streamlit as st
import time
import openai
import google.generativeai as genai
from bs4 import BeautifulSoup

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

def fetch_workspace_details(clickup_api_key, team_id):
    """Fetch detailed workspace data including spaces, tasks, and completion stats."""
    headers = {"Authorization": clickup_api_key}
    
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

def get_company_info(company_name):
    """Fetches company profile from Google, LinkedIn, and the company website."""
    headers = {"User-Agent": "Mozilla/5.0"}
    
    def search_google():
        """Searches Google for company info."""
        search_url = f"https://www.google.com/search?q={company_name.replace(' ', '+')}+company+profile"
        try:
            response = requests.get(search_url, headers=headers)
            soup = BeautifulSoup(response.text, "html.parser")
            for tag in soup.find_all("span"):
                text = tag.get_text()
                if "is a" in text or "provides" in text or "specializes in" in text:
                    return text
        except Exception as e:
            return f"Error fetching Google info: {str(e)}"
        return None

    def search_linkedin():
        """Searches LinkedIn for company info."""
        search_url = f"https://www.google.com/search?q=site:linkedin.com/company/{company_name.replace(' ', '-')}"
        try:
            response = requests.get(search_url, headers=headers)
            soup = BeautifulSoup(response.text, "html.parser")
            for tag in soup.find_all("cite"):
                if "linkedin.com/company/" in tag.text:
                    return tag.text.strip()
        except Exception as e:
            return f"Error fetching LinkedIn info: {str(e)}"
        return None

    def search_company_website():
        """Attempts to find and extract company info from their website."""
        search_url = f"https://www.google.com/search?q={company_name.replace(' ', '+')}+official+website"
        try:
            response = requests.get(search_url, headers=headers)
            soup = BeautifulSoup(response.text, "html.parser")
            for tag in soup.find_all("cite"):
                if "http" in tag.text:
                    return tag.text.strip()
        except Exception as e:
            return f"Error fetching company website: {str(e)}"
        return None

    google_info = search_google()
    linkedin_profile = search_linkedin()
    company_website = search_company_website()

    return {
        "Google Description": google_info or "Not found",
        "LinkedIn Profile": linkedin_profile or "Not found",
        "Company Website": company_website or "Not found"
    }

def get_ai_recommendations(use_case, company_info, workspace_details):
    """Generates AI-powered recommendations using OpenAI or Gemini."""
    prompt = f"""
    **📌 Use Case:** {use_case}
    
    **🏢 Company Profile:**
    - **Google Description:** {company_info['Google Description']}
    - **LinkedIn Profile:** {company_info['LinkedIn Profile']}
    - **Company Website:** {company_info['Company Website']}
    
    ### 🔍 Workspace Overview:
    {workspace_details if workspace_details else "(No workspace details available)"}
    
    ### 📈 Productivity Analysis:
    Provide insights on how to optimize productivity for this company and use case.
    
    ### ✅ Actionable Recommendations:
    Suggest practical steps to improve efficiency and organization based on company profile.
    
    ### 🏆 Best Practices & Tips:
    Share industry-specific best practices to maximize workflow efficiency.
    
    ### 🛠️ Useful ClickUp Templates & Resources:
    List relevant ClickUp templates and best practices for this use case.
    Provide hyperlinks to useful resources on clickup.com, university.clickup.com, or help.clickup.com.
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
    return "⚠️ AI recommendations are not available because both OpenAI and Gemini failed."

# UI Setup
st.title("📊 ClickUp Workspace Analyzer")

clickup_api_key = st.text_input("🔑 ClickUp API Key (Optional)", type="password")
use_case = st.text_input("📌 Use Case (e.g., Consulting, Sales)")
company_name = st.text_input("🏢 Company Name (Optional)")

if st.button("🚀 Analyze Workspace"):
    if not use_case:
        st.error("Please enter a use case.")
    else:
        with st.spinner("🔄 Fetching ClickUp Workspace Data..."):
            workspace_details = get_clickup_workspace_data(clickup_api_key) if clickup_api_key else None
        
        with st.spinner("🌍 Searching for company information..."):
            company_info = get_company_info(company_name) if company_name else {
                "Google Description": "No company info provided.",
                "LinkedIn Profile": "No company info provided.",
                "Company Website": "No company info provided."
            }

        if workspace_details and "error" in workspace_details:
            st.error(f"❌ {workspace_details['error']}")
        elif workspace_details:
            st.subheader("📝 Workspace Analysis:")
            cols = st.columns(4)
            keys = list(workspace_details.keys())
            for i, key in enumerate(keys):
                with cols[i % 4]:
                    st.metric(label=key, value=workspace_details[key])

        # Display Company Info
        st.subheader("🏢 Company Information:")
        st.markdown(f"**Google Description:** {company_info['Google Description']}")
        st.markdown(f"**LinkedIn Profile:** [{company_info['LinkedIn Profile']}]({company_info['LinkedIn Profile']})")
        st.markdown(f"**Company Website:** [{company_info['Company Website']}]({company_info['Company Website']})")

        with st.spinner("🤖 Generating AI recommendations..."):
            ai_recommendations = get_ai_recommendations(use_case, company_info, workspace_details)
        
        st.markdown(ai_recommendations, unsafe_allow_html=True)

st.markdown("<div style='position: fixed; bottom: 10px; right: 10px;'>Made by: Yul</div>", unsafe_allow_html=True)
