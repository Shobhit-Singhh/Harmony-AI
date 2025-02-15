from pathlib import Path
from jinja2 import Environment, FileSystemLoader, StrictUndefined, TemplateError, meta
import frontmatter
import yaml
import json

class PromptManager:
    _env = None  

    @classmethod
    def _get_env(cls, templates_dir="../prompts_files"):
        """
            Initializes and caches the Jinja2 Environment for loading templates multiple times.
            This is a **class method**, meaning it is associated with the class itself, not an instance of the class.  
            It avoids reinitializing the Jinja2 Environment each time a template is rendered, improving efficiency by caching the environment.  
            The method sets up the Jinja2 Environment to load templates from the **prompts_files** directory (or any directory specified in the `templates_dir` argument).  

            Args:
                templates_dir (str): Path to the directory containing template files.

            Returns:
                jinja2.Environment: The Jinja2 Environment object used for template rendering.
        """

        templates_dir = Path(__file__).parent.parent / templates_dir
        if cls._env is None:
            cls._env = Environment(
                loader=FileSystemLoader(templates_dir), 
                undefined=StrictUndefined 
            )
        return cls._env

    @staticmethod
    def get_prompt(file_name, section=None, **kwargs):
        """Loads and renders a specific section of a template with the provided kwargs.
        This is a static method, which is a method that is bound to the class rather than the object of the class.
        Normally, a static method is used for the methods that do not require access to the class itself.
        
        Args:
            template (str): Name of the template to render.
            section (str): Name of the section to render.
            **kwargs: Keyword arguments to pass to the template.
            
        Returns:
            str: Rendered template section as a string.
        """
        env = PromptManager._get_env()
        template_path = "Prompts/" + f"{file_name}.j2"

        try:
            with open(env.loader.get_source(env, template_path)[1]) as file:
                metadata, content = frontmatter.parse(file.read())

                template_content = content  
                template = env.from_string(template_content)
                if section:
                    return template.render(section=section, **kwargs)
                return template.render(**kwargs)
        except TemplateError as e:
            raise ValueError(f"Error rendering template: {str(e)}")

    @staticmethod
    def get_template_info(template):
        """Retrieves metadata and variables from the template.
        
        Args:
            template (str): Name of the template to retrieve info for.
            
        Returns:
            dict: Dictionary containing template metadata and variables.
        """
        env = PromptManager._get_env()
        template_path = f"{template}.j2"

        try:
            with open(env.loader.get_source(env, template_path)[1]) as file:
                post = frontmatter.parse(file.read())  # Use parse instead of load
                template_content = post.content  # Correct access to content
                ast = env.parse(template_content)
                variables = meta.find_undeclared_variables(ast)

                return {
                    "name": template,
                    "description": post.metadata.get("description", "No description provided"),
                    "author": post.metadata.get("author", "Unknown"),
                    "variables": list(variables),
                    "frontmatter": post.metadata
                }
        except Exception as e:
            raise ValueError(f"Error loading template info: {str(e)}")


def load_yaml(file_path):
    """
    Loads a YAML file and returns its contents as a Python dictionary.

    Args:
        file_path (str): Path to the YAML file.

    Returns:
        dict: Parsed contents of the YAML file.
    """
    try:
        with open(file_path, 'r') as file:
            data = yaml.safe_load(file)  # Safe loading prevents code execution
        return data
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")


def save_yaml(data, file_path):
    """
    Saves a Python dictionary to a YAML file.

    Args:
        data (dict): Python dictionary to save.
        file_path (str): Path to the output YAML file.
    """
    with open(file_path, 'w') as file:
        yaml.dump(data, file)


def load_json(file_path):
    """
    Loads a JSON file and returns its contents as a Python dictionary.

    Args:
        file_path (str): Path to the JSON file.

    Returns:
        dict: Parsed contents of the JSON file.
    """
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON file: {e}")


def save_json(data, file_path):
    """
    Saves a Python dictionary to a JSON file.

    Args:
        data (dict): Python dictionary to save.
        file_path (str): Path to the output JSON file.
    """
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

