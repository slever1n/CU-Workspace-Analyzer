import aiohttp
import asyncio
import requests
import streamlit as st
import time
import openai
import google.generativeai as genai
import textwrap
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Set page title and icon
st.set_page_config(page_title="ClickUp Workspace Analysis", page_icon="🚀", layout="wide")

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
        Please build a short company profile for {company_name}. The profile should include the following sections in markdown:
        - **Mission:** A brief mission statement.
        - **Key Features:** List 3-5 key features of the company.
        - **Values:** Describe the core values of the company.
        - **Target Audience:** Describe who the company primarily serves.
        - **Overall Summary:** Provide an overall summary of what the company does.
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
            return "No AI service available for generating company profile."
    except Exception as e:
        return f"Error fetching company details: {str(e)}"

async def get_clickup_workspace_data(api_key):
    """
    Fetches real workspace data from the ClickUp API.
    """
    if not api_key:
        return None

    url = "https://api.clickup.com/api/v2/team"
    headers = {"Authorization": api_key}

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers) as response:
                logging.debug(f"Response status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    logging.debug(f"Raw data received: {data}")
                    teams = data.get("teams", [])
                    if teams:
                        team_id = teams[0]["id"]
                        return await fetch_workspace_details(api_key, team_id)
                    else:
                        return {"error": "No teams found in ClickUp workspace."}
                else:
                    error_message = await response.json()
                    logging.error(f"Error: {response.status} - {error_message}")
                    return {"error": f"Error: {response.status} - {error_message}"}
        except Exception as e:
            logging.exception("Exception occurred while fetching workspace data")
            return {"error": f"Exception: {str(e)}"}

async def fetch_workspace_details(api_key, team_id):
    """
    Fetches workspace details including spaces, folders, lists, and tasks.
    """
    headers = {"Authorization": api_key}
    
    async with aiohttp.ClientSession() as session:
        try:
            spaces_url = f"https://api.clickup.com/api/v2/team/{team_id}/space"
            async with session.get(spaces_url, headers=headers) as spaces_response:
                spaces_data = await spaces_response.json()
                logging.debug(f"Spaces data: {spaces_data}")
                spaces = spaces_data.get("spaces", [])
                
                space_count = len(spaces)
                folder_count, list_count, task_count = 0, 0, 0
                completed_tasks, overdue_tasks, high_priority_tasks = 0, 0, 0
                
                for space in spaces:
                    space_id = space["id"]
                    folders_url = f"https://api.clickup.com/api/v2/space/{space_id}/folder"
                    async with session.get(folders_url, headers=headers) as folders_response:
                        folders_data = await folders_response.json()
                        logging.debug(f"Folders data for space {space_id}: {folders_data}")
                        folders = folders_data.get("folders", [])
                        folder_count += len(folders)
                        
                        for folder in folders:
                            folder_id = folder["id"]
                            lists_url = f"https://api.clickup.com/api/v2/folder/{folder_id}/list"
                            async with session.get(lists_url, headers=headers) as lists_response:
                                if lists_response.status == 504:
                                    logging.warning(f"Received 504 for URL: {lists_url}, retrying...")
                                    await asyncio.sleep(1)  # Wait for 1 second before retrying
                                    async with session.get(lists_url, headers=headers) as retry_response:
                                        lists_data = await retry_response.json()
                                else:
                                    lists_data = await lists_response.json()
                                logging.debug(f"Lists data for folder {folder_id}: {lists_data}")
                                lists = lists_data.get("lists", [])
                                list_count += len(lists)
                                
                                for lst in lists:
                                    list_id = lst["id"]
                                    tasks_url = f"https://api.clickup.com/api/v2/list/{list_id}/task"
                                    async with session.get(tasks_url, headers=headers) as tasks_response:
                                        if tasks_response.status == 504:
                                            logging.warning(f"Received 504 for URL: {tasks_url}, retrying...")
                                            await asyncio.sleep(1)  # Wait for 1 second before retrying
                                            async with session.get(tasks_url, headers=headers) as retry_response:
                                                tasks_data = await retry_response.json()
                                        else:
                                            tasks_data = await tasks_response.json()
                                        logging.debug(f"Tasks data for list {list_id}: {tasks_data}")
                                        tasks = tasks_data.get("tasks", [])
                                        
                                        task_count += len(tasks)
                                        completed_tasks += sum(1 for task in tasks if task.get("status", "") == "complete")
                                        overdue_tasks += sum(1 for task in tasks 
                                                             if task.get("due_date") and int(task["due_date"]) < int(time.time() * 1000))
                                        high_priority_tasks += sum(1 for task in tasks 
                                                                   if task.get("priority", "") in ["urgent", "high"])
                
                task_completion_rate = (completed_tasks / task_count * 100) if task_count > 0 else 0
                
                workspace_summary = {
                    "📁 Spaces": space_count,
                    "📂 Folders": folder_count,
                    "🗂️ Lists": list_count,
                    "📝 Total Tasks": task_count,
                    "✅ Completed Tasks": completed_tasks,
                    "📈 Task Completion Rate": f"{round(task_completion_rate, 2)}%",
                    "⚠️ Overdue Tasks": overdue_tasks,
                    "🔥 High Priority Tasks": high_priority_tasks
                }
                logging.debug(f"Workspace Summary: {workspace_summary}")
                return workspace_summary
        except Exception as e:
            logging.exception("Exception occurred while fetching workspace details")
            return {"error": f"Exception: {str(e)}"}

def get_ai_recommendations(use_case, company_profile, workspace_details):
    """
    Generates AI-powered recommendations based on workspace data, company profile, and use case.
    """
    prompt = textwrap.dedent(f"""
        Based on the following workspace data:
        {workspace_details if workspace_details else "(No workspace data available)"}
        
        Considering the company's use case: "{use_case}"
        And the following company profile:
        {company_profile}
        
        Please provide a detailed analysis.
        
        <h3>📈 Productivity Analysis</h3>
        Evaluate the current workspace structure and workflow. Provide insights on how to optimize productivity by leveraging the workspace metrics above and tailoring strategies to the specified use case.
        
        <h3>✅ Actionable Recommendations</h3>
        Suggest practical steps to improve efficiency and organization, addressing specific challenges highlighted by the workspace data and the unique requirements of the use case, along with considerations from the company profile.
        
        <h3>🏆 Best Practices & Tips</h3>
        Share industry-specific best practices and tips that can help maximize workflow efficiency for a company with this use case.
        
        <h3>🛠️ Useful ClickUp Templates & Resources</h3>
        Recommend relevant ClickUp templates and resources. Provide hyperlinks to useful resources on clickup.com, university.clickup.com, or help.clickup.com. Provide 5-8 links.
    """)
    
    try:
        if openai_api_key:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response["choices"][0]["message"]["content"]
    except Exception as e:
        if gemini_api_key:
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(prompt)
            return response.text
    return "⚠️ AI recommendations are not available because both AI services failed."

# ----------------------- #
# Streamlit UI
# ----------------------- #
st.title("🚀 ClickUp Workspace Analysis")

# Input fields available immediately
api_key = st.text_input("🔑 Enter ClickUp API Key (Optional):", type="password")
st.text("OR")
company_name = st.text_input("🏢 Enter Company Name (Optional):")
st.text("AND")
use_case = st.text_area("🏢 Describe your company's use case:")
if st.button("🚀 Let's Go!"):
    workspace_data = None
    if api_key:
        with st.spinner("Fetching workspace data and crafting suggestions, this may take a while, switch to another tab in the meantime..."):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            workspace_data = loop.run_until_complete(get_clickup_workspace_data(api_key))
        if workspace_data is None:
            st.error("Invalid API Key provided.")
        elif "error" in workspace_data:
            st.error(workspace_data["error"])
        else:
            st.subheader("📊 Workspace Summary")
            # Display workspace data as tiles
            cols = st.columns(4)
            for idx, (key, value) in enumerate(workspace_data.items()):
                with cols[idx % 4]:
                    st.metric(label=key, value=value)
    else:
        st.info("ClickUp API Key not provided. Skipping workspace data analysis.")

    # Build and display company profile if a company name is provided
    if company_name:
        with st.spinner("Generating company profile..."):
            company_profile = get_company_info(company_name)
        st.subheader("🏢 Company Profile")
        st.markdown(company_profile, unsafe_allow_html=True)
    else:
        company_profile = "No company information provided."
    
    with st.spinner("Generating AI recommendations..."):
        recommendations = get_ai_recommendations(use_case, company_profile, workspace_data)
        st.markdown(recommendations, unsafe_allow_html=True)

st.markdown("<div style='position: fixed; bottom: 10px; left: 7px;'>A little tool made by: Yul 😊</div>", unsafe_allow_html=True)
