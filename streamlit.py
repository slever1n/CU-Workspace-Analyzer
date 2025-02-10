import streamlit as st
import openai
import google.generativeai as genai

# Set page title and icon
st.set_page_config(page_title="ClickUp Workspace Analyzer", page_icon="🚀", layout="wide")

# Retrieve API keys from Streamlit secrets
openai_api_key = st.secrets.get("OPENAI_API_KEY")
gemini_api_key = st.secrets.get("GEMINI_API_KEY")

# Configure OpenAI and Gemini
if openai_api_key:
    openai.api_key = openai_api_key
if gemini_api_key:
    genai.configure(api_key=gemini_api_key)

def generate_company_profile(company_name):
    """Uses AI to generate a company profile based on the name."""
    prompt = f"""
    Provide a brief company profile for **{company_name}** including:
    - Industry and key business areas
    - Market position and competitors
    - Challenges and opportunities
    - Any notable recent trends or company initiatives

    If the company is not well-known, generate a realistic profile based on similar businesses in that industry.
    """

    try:
        if openai_api_key:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": "You are a business analyst."},
                          {"role": "user", "content": prompt}]
            )
            return response["choices"][0]["message"]["content"]
        elif gemini_api_key:
            model = genai.GenerativeModel("gemini-pro")
            response = model.generate_content(prompt)
            return response.text
    except Exception as e:
        return f"⚠️ AI could not generate company information: {str(e)}"

    return "⚠️ No company information available."

def get_ai_recommendations(use_case, company_profile):
    """Generates AI-powered recommendations using OpenAI or Gemini."""
    prompt = f"""
    **📌 Use Case:** {use_case}

    **🏢 Company Profile:**
    {company_profile}

    ### 📈 Productivity Analysis:
    Provide insights on optimizing productivity for this company and use case.

    ### ✅ Actionable Recommendations:
    Suggest steps to improve efficiency and organization.

    ### 🏆 Best Practices & Tips:
    Share industry-specific best practices.

    ### 🛠️ Useful ClickUp Templates & Resources:
    List relevant ClickUp templates.
    """

    try:
        if openai_api_key:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": "You are a workflow expert."},
                          {"role": "user", "content": prompt}]
            )
            return response["choices"][0]["message"]["content"]
        elif gemini_api_key:
            model = genai.GenerativeModel("gemini-pro")
            response = model.generate_content(prompt)
            return response.text
    except Exception as e:
        return f"⚠️ AI recommendations not available: {str(e)}"

# UI Setup
st.title("📊 ClickUp Workspace Analyzer")

use_case = st.text_input("📌 Use Case (e.g., Consulting, Sales)")
company_name = st.text_input("🏢 Company Name (Optional)")

if st.button("🚀 Analyze Workspace"):
    if not use_case:
        st.error("Please enter a use case.")
    else:
        with st.spinner("🤖 Generating company profile..."):
            company_profile = generate_company_profile(company_name) if company_name else "No company info provided."

        # Display Company Info
        st.subheader("🏢 Company Information:")
        st.markdown(company_profile)

        with st.spinner("🤖 Generating AI recommendations..."):
            ai_recommendations = get_ai_recommendations(use_case, company_profile)

        st.markdown(ai_recommendations, unsafe_allow_html=True)

st.markdown("<div style='position: fixed; bottom: 10px; right: 10px;'>Made by: Yul</div>", unsafe_allow_html=True)
