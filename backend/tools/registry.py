from typing import Dict, Type
from .base import BaseTool

class ToolRegistry:
    _instance = None
    _tools: Dict[str, Type[BaseTool]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ToolRegistry, cls).__new__(cls)
        return cls._instance

    @classmethod
    def register(cls, tool_cls: Type[BaseTool]):
        """Decorator or method to register a tool class."""
        # Instantiate to get the name property, or require name as a class attribute.
        # For simplicity, we'll instantiate a temporary object or expect a class attribute.
        # Let's assume the tool name is accessible or we register instances.
        # Better approach: store class, instantiate on demand or store singleton instance.
        
        # We will assume 'name' is a property of the instance, but for registration key, 
        # we might need to instantiate or look at a static field.
        # Let's try to instantiate it with empty context to get the name.
        try:
            temp_instance = tool_cls()
            cls._tools[temp_instance.name] = tool_cls
            print(f"Registered tool: {temp_instance.name}")
        except Exception as e:
            print(f"Failed to register tool {tool_cls}: {e}")

    @classmethod
    def get_tool(cls, name: str) -> Type[BaseTool]:
        return cls._tools.get(name)

    @classmethod
    def list_tools(cls):
        return list(cls._tools.keys())

    @classmethod
    def get_all_tools_info(cls):
        """
        Returns a list of all registered tools with their details.
        """
        tools_info = []
        for name, tool_cls in cls._tools.items():
            # Instantiate to get properties if needed, or access class properties if static
            try:
                # Assuming properties are accessible on instance, which is safer given current design
                tool_instance = tool_cls()
                
                # Determine category based on tool class or name (simple logic for now)
                category = "General"
                if hasattr(tool_instance, 'category'):
                     category = tool_instance.category
                else:
                    # Fallback categorization (can be improved)
                    if name.startswith('/code') or name.startswith('/sql') or name.startswith('/regex') or name.startswith('/json') or name.startswith('/github'):
                        category = "Developer"
                    elif name.startswith('/image') or name.startswith('/chart') or name.startswith('/diagram') or name.startswith('/qr') or name.startswith('/kroki'):
                        category = "Vision & Images"
                    elif name.startswith('/voice') or name.startswith('/audio') or name.startswith('/tts'):
                        category = "Audio & Voice"
                    elif name.startswith('/joke') or name.startswith('/meme') or name.startswith('/roast') or name.startswith('/cat') or name.startswith('/dog'):
                        category = "Fun & Viral"
                    elif name.startswith('/weather') or name.startswith('/currency') or name.startswith('/time') or name.startswith('/ip'):
                        category = "Utility"
                    elif name.startswith('/check') or name.startswith('/legal') or name.startswith('/ad'):
                        category = "Safety & Analysis"
                    elif name.startswith('/wiki') or name.startswith('/quote') or name.startswith('/fact') or name.startswith('/advice'):
                        category = "Content & Info"

                tools_info.append({
                    "name": tool_instance.name,
                    "description": tool_instance.description,
                    "cost": tool_instance.cost,
                    "category": category
                })
            except Exception as e:
                print(f"Error getting info for {name}: {e}")
                # Fallback so we don't return an incomplete list if one fails
                tools_info.append({
                    "name": name,
                    "description": "Currently unavailable",
                    "category": "System",
                    "cost": "N/A"
                })
        return tools_info

    @classmethod
    def get_tools_by_category(cls):
        """
        Returns tools grouped by category.
        """
        tools = cls.get_all_tools_info()
        grouped = {}
        for tool in tools:
            cat = tool['category']
            if cat not in grouped:
                grouped[cat] = []
            grouped[cat].append(tool)
        return grouped
