
import os
import datetime
import requests
import json

def create_project():
    today = datetime.date.today().isoformat()
    project_dir = f"projects/project_{today}"
    os.makedirs(project_dir, exist_ok=True)

    # Get Groq API key from environment variable
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise Exception("GROQ_API_KEY environment variable not set.")

    prompt = (
        "Generate a unique, useful Python project. "
        "Return a JSON object with fields: 'project_name', 'main_py', 'requirements_txt', 'readme_md'. "
        "The code should be complete and runnable. The README should explain the project and usage."
    )

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3-70b-8192",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 1500,
        "temperature": 0.9
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    project_data = json.loads(content)

    proj_path = os.path.join(project_dir, project_data["project_name"])
    os.makedirs(proj_path, exist_ok=True)

    with open(os.path.join(proj_path, "main.py"), "w") as f:
        f.write(project_data["main_py"])
    with open(os.path.join(proj_path, "requirements.txt"), "w") as f:
        f.write(project_data["requirements_txt"])
    with open(os.path.join(proj_path, "README.md"), "w") as f:
        f.write(project_data["readme_md"] + f"\n\nGenerated on {today}.")

if __name__ == "__main__":
    create_project()
