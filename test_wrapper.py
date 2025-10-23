#!/usr/bin/env python3
"""Test rápido para verificar que el wrapper funciona correctamente"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from benchmark_agent.service_adapter import ADAPTERS
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool

# Tomar una herramienta de ejemplo
adapter_func = ADAPTERS['talk']
tool_name = 'talk'

# Crear schema
class TalkArgs(BaseModel):
    message: str = Field(..., description="Mensaje a decir")
    language: str = Field(default="English", description="Idioma")

# Crear wrapper ACTUALIZADO con la lógica corregida
def make_wrapper(adapter_func=adapter_func, schema=TalkArgs):
    """Wrapper factory con early binding"""
    def wrapper(tool_input=None, **kwargs):
        # Prioridad 1: Si tool_input es un objeto Pydantic, usarlo
        if tool_input is not None and hasattr(tool_input, 'model_dump'):
            kwargs = tool_input.model_dump()
        elif tool_input is not None and hasattr(tool_input, 'dict'):
            kwargs = tool_input.dict()
        # Prioridad 2: Si tool_input es un dict, usarlo
        elif tool_input is not None and isinstance(tool_input, dict):
            kwargs = tool_input
        # Prioridad 3: Si solo hay kwargs (ya viene como dict), usarlos
        # (esto es lo que pasa cuando se llama con .run(dict))
        
        result = adapter_func(**kwargs)
        return result["obs"]  # ReAct espera string en observation
    
    return wrapper

wrapped_func = make_wrapper()
wrapped_func.__name__ = tool_name

# Crear tool - CORREGIDO: no pasar args_schema al func
tool = StructuredTool.from_function(
    func=wrapped_func,
    name=tool_name,
    description="Habla un mensaje",
    args_schema=TalkArgs
)

print("="*60)
print("TEST 1: Invocar tool con dict")
print("="*60)
try:
    result = tool.invoke({"message": "Hola mundo"})
    print(f"✅ Resultado: {result}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("TEST 2: Invocar tool con objeto Pydantic directamente")
print("="*60)
try:
    args_obj = TalkArgs(message="Hola de nuevo")
    print(f"Tipo de args_obj: {type(args_obj)}")
    print(f"args_obj.model_dump(): {args_obj.model_dump()}")
    result = tool.invoke(args_obj)
    print(f"✅ Resultado: {result}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("TEST 2b: Invocar tool con model_dump()")
print("="*60)
try:
    args_obj = TalkArgs(message="Hola de nuevo")
    result = tool.invoke(args_obj.model_dump())
    print(f"✅ Resultado: {result}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("TEST 3: Invocar tool con tool.run (como hace ReAct)")
print("="*60)
try:
    result = tool.run({"message": "Test con run"})
    print(f"✅ Resultado: {result}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("TEST 4: Ver cómo StructuredTool parsea los args")
print("="*60)
print(f"tool.args_schema: {tool.args_schema}")
print(f"tool.func: {tool.func}")

# Simular lo que hace LangChain internamente
import json
action_input_str = '{"message": "Test parsing"}'
print(f"\nSimulando parsing de Action Input: {action_input_str}")
try:
    parsed_input = json.loads(action_input_str)
    print(f"Después de json.loads: {parsed_input} (tipo: {type(parsed_input)})")
    
    # LangChain valida contra args_schema
    validated_input = TalkArgs(**parsed_input)
    print(f"Validado con Pydantic: {validated_input} (tipo: {type(validated_input)})")
    
    # Luego llama al func - ¿cómo?
    print("\nIntentando llamar directamente a tool.func con objeto Pydantic...")
    result = tool.func(validated_input)
    print(f"✅ Resultado: {result}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
