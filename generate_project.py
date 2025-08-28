import os
import datetime
import requests
import json
import logging
import argparse
from typing import Dict, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProjectGenerator:
    def __init__(self, api_key: Optional[str] = None, base_dir: str = "projects"):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        
        if not self.api_key:
            raise ValueError("GROQ_API_KEY must be provided or set as environment variable")
    
    def generate_project(self, 
                        project_type: str = "general", 
                        difficulty: str = "intermediate",
                        max_tokens: int = 2000,
                        temperature: float = 0.9) -> Dict:
        """Generate project using Groq API with customizable parameters."""
        
        prompt = self._create_prompt(project_type, difficulty)
        
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        try:
            response = self._make_api_request(payload)
            return self._parse_response(response)
        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse API response: {e}")
            raise
    
    def _create_prompt(self, project_type: str, difficulty: str) -> str:
        """Create a detailed prompt based on project type and difficulty."""
        base_prompt = (
            f"Generate a unique, useful Python project of type '{project_type}' "
            f"with '{difficulty}' difficulty level.\n\n"
            "IMPORTANT: Format your response as follows:\n"
            "PROJECT_NAME: [descriptive_name_with_underscores]\n"
            "DESCRIPTION: [brief description]\n"
            "===MAIN_PY_START===\n"
            "[complete Python code here]\n"
            "===MAIN_PY_END===\n"
            "===REQUIREMENTS_START===\n"
            "[dependency list here]\n"
            "===REQUIREMENTS_END===\n"
            "===README_START===\n"
            "[comprehensive README content here]\n"
            "===README_END===\n\n"
            "Code Requirements:\n"
            "- Include proper error handling and logging\n"
            "- Add docstrings and comments\n"
            "- Follow PEP 8 style guidelines\n"
            "- Make it practical and educational\n"
            "- Ensure all imports are in requirements.txt\n"
        )
        
        type_specific = {
            "web": "Focus on web scraping, APIs, or web development.",
            "data": "Focus on data analysis, visualization, or processing.",
            "automation": "Focus on task automation or system administration.",
            "game": "Focus on simple games or interactive applications.",
            "ml": "Focus on machine learning or data science.",
            "utility": "Focus on useful command-line tools or utilities."
        }
        
        if project_type in type_specific:
            base_prompt += f"\nSpecific focus: {type_specific[project_type]}"
            
        return base_prompt
    
    def _make_api_request(self, payload: Dict) -> Dict:
        """Make API request with retry logic."""
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"Making API request (attempt {attempt + 1}/{max_retries})")
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"Request failed, retrying: {e}")
    
    def _parse_response(self, response: Dict) -> Dict:
        """Parse and validate API response using simple text parsing."""
        try:
            content = response["choices"][0]["message"]["content"]
            
            # Save raw response for debugging
            with open("debug_response.txt", "w", encoding="utf-8", errors="replace") as f:
                f.write(content)
            logger.info("Raw response saved to debug_response.txt")
            
            project_data = self._parse_structured_response(content)
            
            # Validate required fields
            required_fields = ["project_name", "main_py", "requirements_txt", "readme_md"]
            missing_fields = [field for field in required_fields if field not in project_data]
            
            if missing_fields:
                raise ValueError(f"Missing required fields: {missing_fields}")
            
            return project_data
            
        except (KeyError, IndexError) as e:
            raise ValueError(f"Unexpected API response format: {e}")
    
    def _parse_structured_response(self, content: str) -> Dict:
        """Parse structured text response instead of JSON."""
        result = {}
        
        # Extract PROJECT_NAME
        if "PROJECT_NAME:" in content:
            start = content.find("PROJECT_NAME:") + 13
            end = content.find("\n", start)
            result["project_name"] = content[start:end].strip()
        
        # Extract DESCRIPTION
        if "DESCRIPTION:" in content:
            start = content.find("DESCRIPTION:") + 12
            end = content.find("\n", start)
            result["description"] = content[start:end].strip()
        
        # Extract MAIN_PY
        start_marker = "===MAIN_PY_START==="
        end_marker = "===MAIN_PY_END==="
        if start_marker in content and end_marker in content:
            start = content.find(start_marker) + len(start_marker)
            end = content.find(end_marker)
            result["main_py"] = content[start:end].strip()
        
        # Extract REQUIREMENTS
        start_marker = "===REQUIREMENTS_START==="
        end_marker = "===REQUIREMENTS_END==="
        if start_marker in content and end_marker in content:
            start = content.find(start_marker) + len(start_marker)
            end = content.find(end_marker)
            result["requirements_txt"] = content[start:end].strip()
        
        # Extract README
        start_marker = "===README_START==="
        end_marker = "===README_END==="
        if start_marker in content and end_marker in content:
            start = content.find(start_marker) + len(start_marker)
            end = content.find(end_marker)
            result["readme_md"] = content[start:end].strip()
        
        # Set defaults for missing fields
        if "project_name" not in result:
            result["project_name"] = "generated_project"
        if "description" not in result:
            result["description"] = "AI generated Python project"
        if "main_py" not in result:
            raise ValueError("No main.py code found in response")
        if "requirements_txt" not in result:
            result["requirements_txt"] = "# No requirements specified"
        if "readme_md" not in result:
            result["readme_md"] = f"# {result['project_name']}\n\n{result.get('description', '')}"
        
        return result
    
    def create_project_files(self, project_data: Dict, custom_name: Optional[str] = None) -> Path:
        """Create project files and directory structure."""
        today = datetime.date.today().isoformat()
        project_name = custom_name or project_data["project_name"]
        
        # Sanitize project name
        project_name = "".join(c for c in project_name if c.isalnum() or c in "._-")
        
        project_dir = self.base_dir / f"project_{today}" / project_name
        project_dir.mkdir(parents=True, exist_ok=True)
        
        files_to_create = {
            "main.py": project_data["main_py"],
            "requirements.txt": project_data["requirements_txt"],
            "README.md": self._enhance_readme(project_data.get("readme_md", ""), today, project_data)
        }
        
        # Create additional useful files
        if "test" in project_data.get("description", "").lower():
            files_to_create["test_main.py"] = self._create_basic_test()
        
        files_to_create[".gitignore"] = self._create_gitignore()
        
        for filename, content in files_to_create.items():
            file_path = project_dir / filename
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"Created: {file_path}")
        
        return project_dir
    
    def _enhance_readme(self, readme: str, date: str, project_data: Dict) -> str:
        """Enhance README with additional information."""
        enhanced = readme
        if not enhanced.endswith('\n'):
            enhanced += '\n'
        
        enhanced += f"\n## Project Information\n"
        enhanced += f"- **Generated on**: {date}\n"
        enhanced += f"- **Generated by**: Groq AI Project Generator\n"
        
        if "description" in project_data:
            enhanced += f"- **Description**: {project_data['description']}\n"
        
        enhanced += f"\n## Installation\n"
        enhanced += f"```bash\n"
        enhanced += f"pip install -r requirements.txt\n"
        enhanced += f"python main.py\n"
        enhanced += f"```\n"
        
        return enhanced
    
    def _create_basic_test(self) -> str:
        """Create a basic test file template."""
        return '''import unittest
from main import *

class TestProject(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        pass
    
    def test_basic_functionality(self):
        """Test basic functionality."""
        # Add your tests here
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()
'''
    
    def _create_gitignore(self) -> str:
        """Create a Python .gitignore file."""
        return '''# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Project specific
config.ini
*.log
.env
'''

def main():
    parser = argparse.ArgumentParser(description="Generate Python projects using AI")
    parser.add_argument("--type", choices=["general", "web", "data", "automation", "game", "ml", "utility"], 
                       default="general", help="Type of project to generate")
    parser.add_argument("--difficulty", choices=["beginner", "intermediate", "advanced"], 
                       default="intermediate", help="Project difficulty level")
    parser.add_argument("--name", help="Custom project name")
    parser.add_argument("--tokens", type=int, default=2000, help="Max tokens for API response")
    parser.add_argument("--temp", type=float, default=0.9, help="Temperature for creativity (0.0-1.0)")
    parser.add_argument("--output-dir", default="projects", help="Output directory for projects")
    
    args = parser.parse_args()
    
    try:
        generator = ProjectGenerator(base_dir=args.output_dir)
        
        logger.info(f"Generating {args.type} project with {args.difficulty} difficulty...")
        project_data = generator.generate_project(
            project_type=args.type,
            difficulty=args.difficulty,
            max_tokens=args.tokens,
            temperature=args.temp
        )
        
        project_path = generator.create_project_files(project_data, args.name)
        
        logger.info(f"Project created successfully at: {project_path}")
        logger.info(f"Project: {project_data.get('project_name', 'Unknown')}")
        if 'description' in project_data:
            logger.info(f"Description: {project_data['description']}")
        
        print(f"\nNext steps:")
        print(f"1. cd {project_path}")
        print(f"2. pip install -r requirements.txt")
        print(f"3. python main.py")
        
    except Exception as e:
        logger.error(f"Failed to generate project: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
