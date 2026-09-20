import os
import logging

logger = logging.getLogger(__name__)

class DeployerTool:
    """
    Automates project deployment:
    - Prepares local repositories for Git push
    - Generates deployment configurations for Netlify / Vercel
    """

    def prepare_deployment_config(self, project_dir: str, platform: str = "netlify") -> str:
        """Generates configuration files (e.g. netlify.toml or vercel.json) for auto deployment."""
        if not os.path.exists(project_dir):
            return f"Error: Project directory '{project_dir}' does not exist."

        if platform == "netlify":
            config_content = "[build]\n  publish = \".\"\n"
            config_file = os.path.join(project_dir, "netlify.toml")
        elif platform == "vercel":
            config_content = json.dumps({"version": 2, "builds": [{"src": "*", "use": "@vercel/static"}]}, indent=2)
            config_file = os.path.join(project_dir, "vercel.json")
        else:
            return f"Unsupported deployment platform: {platform}"

        with open(config_file, "w", encoding="utf-8") as f:
            f.write(config_content)

        return f"Deployment configuration for '{platform}' generated at '{config_file}'. Ready for host deployment."
