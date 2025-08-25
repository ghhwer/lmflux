import unittest
from unittest.mock import Mock
from lmflux.flow.toolbox import tool, ToolBox

from enum import Enum

class Days(Enum):
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3

class TestTool(unittest.TestCase):
    def test_tool(self):
        @tool
        def test_func(a: str, b: int, c: bool):
            """
            This tool tests
            """
            pass
        test_func("a", 1, True)
    
    def test_tool_assertion_fail_enum(self):
        with self.assertRaises(AttributeError) as cm:
            @tool
            def test_func(a: Days):
                "Hey yo"
                pass
        self.assertIn('Enums not implemented yet', str(cm.exception))
    
    def test_tool_assertion_fail_other_type(self):
        with self.assertRaises(AttributeError) as cm:
            @tool
            def test_func(a: bytes):
                "Hey yo"
                pass
        self.assertIn("Cannot define tool of type <class 'bytes'>", str(cm.exception))

    def test_tool_assertion_fail_docs(self):
        with self.assertRaises(AttributeError) as cm:
            @tool
            def test_func(a: str, b: int):
                pass
        self.assertIn('Tools are required to have descriptions (docstrings)', str(cm.exception))
            
    def test_tool_assertion_fail_param(self):
        with self.assertRaises(AttributeError) as cm:
            @tool
            def test_func(a: str, b):
                """
                This tool tests
                """
                pass
        self.assertIn('Tools are required to be typed', str(cm.exception))
    
    def test_tool_generic_alias(self):
        @tool
        def tool_list(list: list[str]):
            "test tool"
            pass
    
    def test_tool_generic_alias(self):
        @tool
        def tool_list(list: list[str]):
            "test tool"
            pass
        
    def test_tool_generic_alias_optional(self):
        @tool
        def tool_list(list: list[str,int]):
            "test tool"
            pass
        
    def test_tool_generic_alias_more_than_1(self):
        with self.assertRaises(AttributeError) as cm:
            @tool
            def tool_list(list: dict[str, str]):
                "test tool"
                pass
        self.assertIn('When using GenericAlias types such as dict[str, str] only lists are supported for now.', str(cm.exception))
        
    def test_tool_empty_list(self):
        with self.assertRaises(AttributeError) as cm:
            @tool
            def tool_list(list: list):
                "test tool"
                pass
        self.assertIn('To use list please define the sub type example: `list[str]`', str(cm.exception))
        

@tool
def some_tool(a: str, b: int, c: bool):
    """
    This tool tests
    """
    pass

def some_not_tool(a:str):
    """
    This tool tests
    """
    pass

class TestToolBox(unittest.TestCase):
    def test_non_tool_func_toolbox(self):
        box = ToolBox()
        with self.assertRaises(AttributeError) as cm:
            box.__add_tool__(some_not_tool)
        self.assertIn('The function passed to `add_to_toolbox` is not a proper tool, did you add the @tool decorator while declaring it?', str(cm.exception))
    
    def test_add_to_toolbox(self):
        box = ToolBox()
        # Mock tool definition
        box.__add_tool__(some_tool)

if __name__ == '__main__':
    unittest.main()