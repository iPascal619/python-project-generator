# AI Daily Python Project Generator

This repository uses an AI bot (powered by Groq API) to automatically generate and commit a new Python project every day.

## How It Works

- A GitHub Actions workflow runs daily.
- The workflow executes `generate_project.py`, which uses the Groq API to create a unique Python project (code, README, requirements).
- The new project is saved in the `projects/` folder and committed to the repository.

## Setup

1. Add your Groq API key as a GitHub secret named `GROQ_API_KEY`.
2. Push your changes to GitHub.
3. The workflow will run automatically every day.

## Output

Each day, a new folder is created in `projects/` containing:
- `main.py`: The generated Python script
- `requirements.txt`: Dependencies
- `README.md`: Project description and usage

---

Generated projects are practical, educational, and ready to run!
