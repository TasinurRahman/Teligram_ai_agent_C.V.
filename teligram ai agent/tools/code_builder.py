import os
import json
import logging

logger = logging.getLogger(__name__)

class CodeBuilderTool:
    """
    Tool for automatically creating web application files (HTML, CSS, JS, Python)
    and bundling them into modular projects.
    """

    def __init__(self, projects_dir: str = "generated_projects"):
        self.projects_dir = projects_dir
        os.makedirs(self.projects_dir, exist_ok=True)

    def create_project_structure(self, project_name: str, files_dict: dict) -> str:
        """
        Creates a new directory for a project and writes specified files.
        files_dict format: {"index.html": "<html>...</html>", "style.css": "body { ... }"}
        """
        project_path = os.path.join(self.projects_dir, project_name)
        os.makedirs(project_path, exist_ok=True)

        created_files = []
        for file_rel_path, content in files_dict.items():
            full_path = os.path.join(project_path, file_rel_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            created_files.append(file_rel_path)

        return f"Project '{project_name}' successfully built at '{project_path}'. Created files: {', '.join(created_files)}"

    def list_projects(self) -> list:
        return os.listdir(self.projects_dir) if os.path.exists(self.projects_dir) else []
