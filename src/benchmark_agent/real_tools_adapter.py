"""
Real Tools Adapter - Adaptador para herramientas reales de ROS LangGraph.

Este módulo proporciona:
1. Acceso a todas las herramientas definidas en ros_langgraph_tools.py
2. Compatibilidad con el formato que esperan las arquitecturas del benchmark
3. Metadata para prompts y planificadores
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Any
from langchain_core.tools import BaseTool

# Importación lazy de herramientas para evitar problemas de inicialización
_tools_cache = None
_import_error = None

def _import_tools():
    """Importa las herramientas de forma lazy desde el módulo local."""
    global _tools_cache, _import_error
    
    if _tools_cache is not None:
        return _tools_cache
    
    if _import_error is not None:
        raise _import_error
    
    try:
        # Importar desde el módulo local .tools.ros_langgraph_tools
        from .tools import ros_langgraph_tools
        
        _tools_cache = {
            'find_object': ros_langgraph_tools.find_object,
            'count_objects': ros_langgraph_tools.count_objects,
            'search_for_specific_person': ros_langgraph_tools.search_for_specific_person,
            'find_item_with_characteristic': ros_langgraph_tools.find_item_with_characteristic,
            'get_person_gesture': ros_langgraph_tools.get_person_gesture,
            'get_items_on_top_of_furniture': ros_langgraph_tools.get_items_on_top_of_furniture,
            'speak': ros_langgraph_tools.speak,
            'listen': ros_langgraph_tools.listen,
            'question_and_answer': ros_langgraph_tools.question_and_answer,
            'go_to_location': ros_langgraph_tools.go_to_location,
            'follow_person': ros_langgraph_tools.follow_person,
            'ask_for_object': ros_langgraph_tools.ask_for_object,
            'give_object': ros_langgraph_tools.give_object,
            'view_description': ros_langgraph_tools.view_description
        }
        
        return _tools_cache
    
    except Exception as e:
        error_msg = (
            f"Error al importar herramientas de ros_langgraph_tools.\n"
            f"Error: {str(e)}\n"
            f"Verifica que:\n"
            f"  1. Los archivos ros_langgraph_tools.py, ros_langgraph_task_module.py y globals.py "
            f"estén en src/benchmark_agent/tools/\n"
            f"  2. ROS esté corriendo si usas herramientas reales\n"
            f"  3. Los servicios de ROS estén disponibles"
        )
        _import_error = ImportError(error_msg)
        raise _import_error


def _import_tools_old():
    """Código anterior (legacy)."""
    try:
        # Importar todas las herramientas del módulo ros_langgraph_tools
        from .tools.ros_langgraph_tools import (
            # Perception tools
            find_object,
            count_objects,
            search_for_specific_person,
            find_item_with_characteristic,
            get_person_gesture,
            get_items_on_top_of_furniture,
            
            # Speech tools
            speak,
            listen,
            question_and_answer,
            
            # Navigation tools
            go_to_location,
            follow_person,
            
            # Manipulation tools
            ask_for_object,
            give_object,
            view_description
        )
        
        _tools_cache = {
            'find_object': find_object,
            'count_objects': count_objects,
            'search_for_specific_person': search_for_specific_person,
            'find_item_with_characteristic': find_item_with_characteristic,
            'get_person_gesture': get_person_gesture,
            'get_items_on_top_of_furniture': get_items_on_top_of_furniture,
            'speak': speak,
            'listen': listen,
            'question_and_answer': question_and_answer,
            'go_to_location': go_to_location,
            'follow_person': follow_person,
            'ask_for_object': ask_for_object,
            'give_object': give_object,
            'view_description': view_description
        }
        
        return _tools_cache
    
    except Exception as e:
        _import_error = ImportError(
            f"Error al importar herramientas de ros_langgraph_tools: {str(e)}\n"
            f"Asegúrate de que ROS esté iniciado y los servicios estén disponibles."
        )
        raise _import_error


def get_real_tools() -> List[BaseTool]:
    """
    Retorna la lista de todas las herramientas reales disponibles.
    
    Returns:
        Lista de herramientas de LangChain listas para usar
    """
    tools_dict = _import_tools()
    
    return [
        # Perception
        tools_dict['find_object'],
        tools_dict['count_objects'],
        tools_dict['search_for_specific_person'],
        tools_dict['find_item_with_characteristic'],
        tools_dict['get_person_gesture'],
        tools_dict['get_items_on_top_of_furniture'],
        
        # Speech
        tools_dict['speak'],
        tools_dict['listen'],
        tools_dict['question_and_answer'],
        
        # Navigation
        tools_dict['go_to_location'],
        tools_dict['follow_person'],
        
        # Manipulation
        tools_dict['ask_for_object'],
        tools_dict['give_object'],
        tools_dict['view_description']
    ]


def get_real_tools_description() -> str:
    """
    Genera una descripción completa de todas las herramientas para incluir en prompts.
    
    Returns:
        String con descripción formateada de todas las herramientas
    """
    tools = get_real_tools()
    
    desc_parts = []
    for tool in tools:
        name = tool.name
        description = tool.description
        
        # Extraer argumentos del schema si existe
        args_info = ""
        if hasattr(tool, 'args_schema') and tool.args_schema:
            schema = tool.args_schema
            if hasattr(schema, 'model_fields'):
                fields = schema.model_fields
                args_list = []
                for field_name, field_info in fields.items():
                    field_type = field_info.annotation.__name__ if hasattr(field_info.annotation, '__name__') else str(field_info.annotation)
                    args_list.append(f"  - {field_name} ({field_type})")
                if args_list:
                    args_info = "\n  Argumentos:\n" + "\n".join(args_list)
        
        desc_parts.append(f"- {name}: {description}{args_info}")
    
    return "\n".join(desc_parts)


def get_real_tool_names() -> List[str]:
    """
    Retorna la lista de nombres de todas las herramientas disponibles.
    
    Returns:
        Lista de strings con los nombres de las herramientas
    """
    tools = get_real_tools()
    return [tool.name for tool in tools]


# Metadata adicional para compatibilidad con código existente
REAL_TOOLS_METADATA = {
    # Perception
    "find_object": {
        "category": "perception",
        "args": {"object_name": "str"},
        "required": ["object_name"],
        "returns": "bool"
    },
    "count_objects": {
        "category": "perception",
        "args": {"object_name": "str"},
        "required": ["object_name"],
        "returns": "int"
    },
    "search_for_specific_person": {
        "category": "perception",
        "args": {
            "characterystic_type": "str",
            "specific_characteristic": "str"
        },
        "required": ["characterystic_type", "specific_characteristic"],
        "returns": "bool"
    },
    "find_item_with_characteristic": {
        "category": "perception",
        "args": {
            "class_type": "str",
            "characteristic": "str",
            "furniture": "str"
        },
        "required": ["class_type", "characteristic"],
        "returns": "str"
    },
    "get_person_gesture": {
        "category": "perception",
        "args": {},
        "required": [],
        "returns": "str"
    },
    "get_items_on_top_of_furniture": {
        "category": "perception",
        "args": {"furniture": "str"},
        "required": [],
        "returns": "list"
    },
    
    # Speech
    "speak": {
        "category": "speech",
        "args": {"text": "str"},
        "required": ["text"],
        "returns": "bool"
    },
    "listen": {
        "category": "speech",
        "args": {},
        "required": [],
        "returns": "str"
    },
    "question_and_answer": {
        "category": "speech",
        "args": {"question": "str"},
        "required": ["question"],
        "returns": "str"
    },
    
    # Navigation
    "go_to_location": {
        "category": "navigation",
        "args": {"location": "str"},
        "required": ["location"],
        "returns": "bool"
    },
    "follow_person": {
        "category": "navigation",
        "args": {},
        "required": [],
        "returns": "bool"
    },
    
    # Manipulation
    "ask_for_object": {
        "category": "manipulation",
        "args": {"object_name": "str"},
        "required": ["object_name"],
        "returns": "bool"
    },
    "give_object": {
        "category": "manipulation",
        "args": {"object_name": "str"},
        "required": ["object_name"],
        "returns": "bool"
    },
    "view_description": {
        "category": "perception",
        "args": {},
        "required": [],
        "returns": "str"
    }
}
