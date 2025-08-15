from lmflux.metaclasses.singleton import Singleton
from lmflux import variables
import os

class Templates(metaclass=Singleton):
    """
    Manages templates, both in-memory and on-disk.
    
    This class provides functionality to store, retrieve, and delete templates.
    It supports both in-memory storage and persistent storage on disk.
    """
    def __init__(self,):
        """
        Initializes the Templates instance.
        
        Sets up the in-memory template storage, ignored template IDs,
        external location for persistent templates, and permission for external deletion.
        """
        self.__inmem_templates = {}
        self.__ignore_template_id = []
        self.__external_location = variables.PROMPT_LOCATION
        self.__allow_external_deletion = False
    
    def __get_template_external_path__(self, template_id:str):
        template_path = template_id.split('.')
        path = '/'.join(template_path[:-1])
        return f'{self.__external_location}/{path}/{template_path[-1]}.md'
    
    def __create_in_external_location__(self, template_id:str, content:str):
        if self.__external_location == "__UNDEFINED__":
            raise AttributeError("Can't persist a template, the external location was not defined")
        path = self.__get_template_external_path__(template_id)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, encoding="utf-8", mode="w") as f:
            return f.write(content)
    
    def __get_if_exists_from_external_location__(self, template_id:str):
        if self.__external_location == "__UNDEFINED__":
            return None
        path = self.__get_template_external_path__(template_id)
        # --- check if the file exists ---
        if not os.path.isfile(path):
            return None
        with open(path, encoding="utf-8") as f:
            return f.read()
    
    def clear(self,):
        """
        Clears all the state in the Templates class
        """
        self.__inmem_templates = {}
        self.__ignore_template_id = []
        self.__external_location = variables.PROMPT_LOCATION
        self.__allow_external_deletion = False
    
    def set_allow_external_deletion(self, allow: bool = True):
        """Toggle permission to delete templates that live on disk."""
        self.__allow_external_deletion = allow    
    
    def set_location(self, location:str):
        """
        Sets the external location for template storage.
        
        Args:
            location (str): The new external location path.
        """
        self.__external_location = location
    
    def put_template(self, template_id: str, template_src: str, persistent:bool = False):
        """
        Stores a template.
        
        Args:
            template_id (str): The ID of the template.
            template_src (str): The source content of the template.
            persistent (bool): Whether to store the template persistently on disk. Defaults to False.
        
        Raises:
            AttributeError: If persistent is True but the external location is not defined.
        """
        if persistent:
            self.__create_in_external_location__(template_id, content=template_src)
        else:
            self.__inmem_templates[template_id] = template_src
    
    def get_template(self, template_id:str) -> str:
        if template_id in self.__ignore_template_id:
            raise AttributeError(f"Template {template_id} was not found")
        if template_id in self.__inmem_templates:
            data = self.__inmem_templates.get(template_id)
        else:
            data = self.__get_if_exists_from_external_location__(template_id)
        if data:
            return data
        else:
            raise AttributeError(f"Template {template_id} was not found")

    def delete_template(self, template_id: str):
        """
        Remove a template.

        * If the template exists in memory, drop it from ``__inmem_templates``.
        * If it does **not** exist in memory:
          - When ``__allow_external_deletion`` is True, attempt to delete the
            corresponding file from ``__external_location``.
          - Otherwise, record the id in ``__ignore_template_id``.
        """
        if template_id in self.__inmem_templates:
            del self.__inmem_templates[template_id]
            return

        # Not in‑memory: try external deletion if permitted
        if self.__allow_external_deletion:
            # Build the expected file path (mirrors __get_if_exists…)
            template_path = template_id.split('.')
            path = '/'.join(template_path[:-1])
            file_path = f'{self.__external_location}/{path}/{template_path[-1]}.md'

            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                except OSError as exc:
                    # Surface the problem – caller can decide how to handle it
                    raise OSError(f"Failed to delete template file '{file_path}': {exc}") from exc
                return  # successfully deleted from disk
            # File does not exist – fall through to ignore handling

        # Either deletion not allowed or file missing → ignore
        self.__ignore_template_id.append(template_id)

    def get_with_context(self, template_id: str, context:dict)->str:
        """
        Retrieves a template with context replacement.
        
        Args:
            template_id (str): The ID of the template to retrieve.
            context (dict): A dictionary of key-value pairs to replace in the template.
        
        Returns:
            str: The template content with replacements made.
        """
        content = self.get_template(template_id)
        for key, value in context.items():
            content = content.replace('{{'+key+'}}', str(value))
        return content
    
    def set_hard_external_delete(self,):
        """
        Makes persisted templates deletes permanent (not session level).
        """
        self.__allow_external_deletion = True
    
    def set_soft_external_delete(self,):
        """
        Makes persisted templates deletes soft (session level only).
        """
        self.__allow_external_deletion = False