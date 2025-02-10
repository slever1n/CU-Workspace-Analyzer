import requests
import streamlit as st
import time
import openai
import google.generativeai as genai

# Set page title and icon
st.set_page_config(page_title="ClickUp Workspace Analyzer", page_icon="🚀", layout="wide")

# Retrieve API keys from Streamlit secrets
openai_api_key = st.secrets.get("OPENAI_API_KEY")
openai_org_id = st.secrets.get("OPENAI_ORG_ID")
gemini_api_key = st.secrets.get("GEMINI_API_KEY")

# Configure OpenAI and Gemini clients
openai_client = openai.Client(api_key=openai_api_key) if openai_api_key else None
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
                return {"Team ID": team_id, "Team Name": teams[0]["name"]}
            else:
                return {"error": "No teams found in ClickUp workspace."}
        else:
            return {"error": f"Error: {response.status_code} - {response.json()}"}
    except Exception as e:
        return {"error": f"Exception: {str(e)}"}

def generate_company_profile(company_name):
    """Uses AI to generate a company profile."""
    prompt = f"""
    Provide a brief company profile for {company_name}. Include:
    - Industry and main services/products
    - Size and location (if relevant)
    - Unique strengths and market position
    - Any notable clients or partnerships (if applicable)
    """
    
    try:
        if openai_client:
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": "You are a helpful assistant."},
                          {"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        elif gemini_api_key:
            model = genai.GenerativeModel("gemini-pro")
            response = model.generate_content(prompt)
            return response.text
    except Exception as e:
        return f"Error generating company profile: {str(e)}"

def get_ai_recommendations(use_case, company_profile, workspace_details):
    """Generates AI-powered recommendations."""
    prompt = f"""
    **📌 Use Case:** {use_case}
    
    **🏢 Company Profile:**
    {company_profile}
    
    **🔍 Workspace Overview:**
    {workspace_details if workspace_details else "(No workspace details available)"}
    
    **📈 Productivity Analysis:**
    Provide insights on how to optimize productivity for this company and use case.
    
    **✅ Actionable Recommendations:**
    Suggest practical steps to improve efficiency and organization based on company profile.
    
    **🏆 Best Practices & Tips:**
    Share industry-specific best practices to maximize workflow efficiency.
    
    **🛠️ Useful ClickUp Templates & Resources:**
    List relevant ClickUp templates and best practices for this use case.
    Provide hyperlinks to useful resources on clickup.com, university.clickup.com, or help.clickup.com.
    """
    
    try:
        if openai_client:
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": "You are a helpful assistant."},
                          {"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        elif gemini_api_key:
            model = genai.GenerativeModel("gemini-pro")
            response = model.generate_content(prompt)
            return response.text
    except Exception as e:
        return "⚠️ AI recommendations are not available." 

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
        
        with st.spinner("🤖 Generating company profile..."):
            company_profile = generate_company_profile(company_name) if company_name else "No company info provided."
        
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
        st.markdown(f"**Generated Profile:**\n{company_profile}")

        with st.spinner("🤖 Generating AI recommendations..."):
            ai_recommendations = get_ai_recommendations(use_case, company_profile, workspace_details)
        
        st.markdown(ai_recommendations, unsafe_allow_html=True)

st.markdown("<div style='position: fixed; bottom: 10px; right: 10px;'>Made by: Yul</div>", unsafe_allow_html=True)
