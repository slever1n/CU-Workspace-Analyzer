import requests
import streamlit as st
import time
import openai
import google.generativeai as genai
import textwrap
import concurrent.futures
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

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

def fetch_workspaces(api_key):
    """
    Fetches the list of workspaces from the ClickUp API.
    """
    if not api_key:
        return None

    url = "https://api.clickup.com/api/v2/team"
    headers = {"Authorization": api_key}

    try:
        start_time = time.time()
        response = requests.get(url, headers=headers)
        logging.info(f"API call to {url} took {time.time() - start_time:.2f} seconds")
        if response.status_code == 200:
            teams = response.json().get("teams", [])
            return {team["id"]: team["name"] for team in teams}
        else:
            return None
    except Exception as e:
        logging.error(f"Exception: {str(e)}")
        return None

def fetch_workspace_details(api_key, team_id):
    """
    Fetches workspace details including spaces, folders, lists, and tasks.
    """
    headers = {"Authorization": api_key}
    
    try:
        spaces_url = f"https://api.clickup.com/api/v2/team/{team_id}/space"
        start_time = time.time()
        spaces_response = requests.get(spaces_url, headers=headers).json()
        logging.info(f"API call to {spaces_url} took {time.time() - start_time:.2f} seconds")
        spaces = spaces_response.get("spaces", [])
        
        space_count = len(spaces)
        folder_count, list_count, task_count = 0, 0, 0
        completed_tasks, overdue_tasks, high_priority_tasks = 0, 0, 0

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_space = {executor.submit(fetch_space_details, api_key, space["id"]): space for space in spaces}
            for future in concurrent.futures.as_completed(future_to_space):
                space_result = future.result()
                folder_count += space_result['folder_count']
                list_count += space_result['list_count']
                task_count += space_result['task_count']
                completed_tasks += space_result['completed_tasks']
                overdue_tasks += space_result['overdue_tasks']
                high_priority_tasks += space_result['high_priority_tasks']
        
        task_completion_rate = (completed_tasks / task_count * 100) if task_count > 0 else 0
        
        return {
            "🪐 Spaces": space_count,
            "📂 Folders": folder_count,
            "🗂️ Lists": list_count,
            "📝 Total Tasks": task_count,
            "⚠️ Overdue Tasks": overdue_tasks,
            "🔥 High Priority Tasks": high_priority_tasks
        }
    except Exception as e:
        return {"error": f"Exception: {str(e)}"}

def fetch_space_details(api_key, space_id):
    """
    Fetches details for a specific space including folders, lists, and tasks.
    """
    headers = {"Authorization": api_key}
    folder_count, list_count, task_count = 0, 0, 0
    completed_tasks, overdue_tasks, high_priority_tasks = 0, 0, 0

    folders_url = f"https://api.clickup.com/api/v2/space/{space_id}/folder"
    start_time = time.time()
    folders_response = requests.get(folders_url, headers=headers).json()
    logging.info(f"API call to {folders_url} took {time.time() - start_time:.2f} seconds")
    folders = folders_response.get("folders", [])
    folder_count += len(folders)
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_folder = {executor.submit(fetch_folder_details, api_key, folder["id"]): folder for folder in folders}
        for future in concurrent.futures.as_completed(future_to_folder):
            folder_result = future.result()
            list_count += folder_result['list_count']
            task_count += folder_result['task_count']
            completed_tasks += folder_result['completed_tasks']
            overdue_tasks += folder_result['overdue_tasks']
            high_priority_tasks += folder_result['high_priority_tasks']
    
    return {
        'folder_count': folder_count,
        'list_count': list_count,
        'task_count': task_count,
        'completed_tasks': completed_tasks,
        'overdue_tasks': overdue_tasks,
        'high_priority_tasks': high_priority_tasks
    }

def fetch_folder_details(api_key, folder_id):
    """
    Fetches details for a specific folder including lists and tasks.
    """
    headers = {"Authorization": api_key}
    list_count, task_count = 0, 0
    completed_tasks, overdue_tasks, high_priority_tasks = 0, 0, 0

    lists_url = f"https://api.clickup.com/api/v2/folder/{folder_id}/list"
    start_time = time.time()
    lists_response = requests.get(lists_url, headers=headers).json()
    logging.info(f"API call to {lists_url} took {time.time() - start_time:.2f} seconds")
    lists = lists_response.get("lists", [])
    list_count += len(lists)
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_list = {executor.submit(fetch_list_details, api_key, lst["id"]): lst for lst in lists}
        for future in concurrent.futures.as_completed(future_to_list):
            list_result = future.result()
            task_count += list_result['task_count']
            completed_tasks += list_result['completed_tasks']
            overdue_tasks += list_result['overdue_tasks']
            high_priority_tasks += list_result['high_priority_tasks']
    
    return {
        'list_count': list_count,
        'task_count': task_count,
        'completed_tasks': completed_tasks,
        'overdue_tasks': overdue_tasks,
        'high_priority_tasks': high_priority_tasks
    }

def fetch_list_details(api_key, list_id):
    """
    Fetches details for a specific list including tasks.
    """
    headers = {"Authorization": api_key}
    task_count = 0
    completed_tasks, overdue_tasks, high_priority_tasks = 0, 0, 0

    tasks_url = f"https://api.clickup.com/api/v2/list/{list_id}/task"
    start_time = time.time()
    params = {
        "archived": "false",
        "subtasks": "true"
    }
    tasks_response = requests.get(tasks_url, headers=headers, params=params).json()
    logging.info(f"API call to {tasks_url} took {time.time() - start_time:.2f} seconds")
    tasks = tasks_response.get("tasks", [])
    task_count += len(tasks)
    
    for task in tasks:
        status = task.get("status", {}).get("type", "").lower()
        logging.info(f"Task ID: {task['id']} - Status: {status}")
        completed_tasks += 1 if status in ["closed", "done", "completed"] else 0
        overdue_tasks += 1 if task.get("due_date") and int(task["due_date"]) < int(time.time() * 1000) else 0
        high_priority_tasks += 1 if task.get("priority", "") in ["urgent", "high"] else 0

    logging.info(f"Total tasks: {task_count}, Completed tasks: {completed_tasks}")
    
    return {
        'task_count': task_count,
        'completed_tasks': completed_tasks,
        'overdue_tasks': overdue_tasks,
        'high_priority_tasks': high_priority_tasks
    }

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
api_key = st.text_input("🔑 Enter ClickUp API Key: (Optional)", type="password")
if api_key:
    workspaces = fetch_workspaces(api_key)
    if workspaces:
        workspace_id = st.selectbox("💼 Select Workspace:", options=list(workspaces.keys()), format_func=lambda x: workspaces[x])
    else:
        st.error("Failed to fetch workspaces. Please check your API key.")
else:
    workspace_id = None

company_name = st.text_input("🏢 Enter Company Name (Optional):")
use_case = st.text_area("🧑‍💻 Describe your company's use case:")

if st.button("🚀 Let's Go!"):
    if api_key and workspace_id:
        workspace_data = None
        with st.spinner("Fetching workspace data, may take longer for larger Workspaces..."):
            workspace_data = fetch_workspace_details(api_key, workspace_id)
        if workspace_data is None:
            st.error("Failed to fetch workspace data.")
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
        workspace_data = None

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

st.markdown("<div style='position: fixed; bottom: 10px; left: 10px; font-size: 10px;'>A little tool made by: Yul 😊</div>", unsafe_allow_html=True)
