import time
from typing import List, Dict, Any, Optional
from langchain_core.prompts import PromptTemplate
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool, StructuredTool
from pydantic import BaseModel, Field

from .base_agent import BaseAgent
from ..service_adapter import normalize_action_input, get_tools_description, get_tool_names


class ReactAgent(BaseAgent):
    """
    Implementación de la arquitectura ReAct (Reasoning + Acting) para un robot social.
    """
    
    def __init__(
        self, 
        llm: BaseChatModel, 
        tools: List[BaseTool] = None,
        max_iterations: int = 10,
        max_execution_time: Optional[float] = 120.0
    ):
        super().__init__(llm, tools)
        self.max_iterations = max_iterations
        self.max_execution_time = max_execution_time
        self.agent_executor = self._create_react_agent()

    def _create_langchain_tools(self) -> List[StructuredTool]:
        """
        Convierte adapters a herramientas LangChain para usar con create_react_agent.
        """
        lc_tools = []
        
        for tool_name, adapter_func in self.adapters.items():
            spec = self.adapter_specs.get(tool_name, {})
            desc = spec.get("desc", f"Herramienta {tool_name}")
            args_spec = spec.get("args", {})
            required = spec.get("required", [])
            
            # Crear modelo Pydantic dinámico para args
            from typing import Optional
            
            fields = {}
            annotations = {}
            
            for arg_name, arg_type in args_spec.items():
                is_required = arg_name in required
                
                if arg_type == "str":
                    annotations[arg_name] = str if is_required else Optional[str]
                    fields[arg_name] = Field(...) if is_required else Field(default="")
                elif arg_type == "int":
                    annotations[arg_name] = int if is_required else Optional[int]
                    fields[arg_name] = Field(...) if is_required else Field(default=0)
                elif arg_type == "float":
                    annotations[arg_name] = float if is_required else Optional[float]
                    fields[arg_name] = Field(...) if is_required else Field(default=0.0)
                elif arg_type == "bool":
                    annotations[arg_name] = bool if is_required else Optional[bool]
                    fields[arg_name] = Field(...) if is_required else Field(default=False)
                else:
                    annotations[arg_name] = str if is_required else Optional[str]
                    fields[arg_name] = Field(...) if is_required else Field(default="")
            
            # Crear clase dinámica con configuración correcta
            ArgsModel = type(
                f"{tool_name}_args",
                (BaseModel,),
                {
                    "__annotations__": annotations,
                    **{k: v for k, v in fields.items()}
                }
            )
            
            # Wrapper que retorna string para compatibilidad con ReAct
            # StructuredTool pasa args de diferentes formas según la versión y cómo se llama
            def make_wrapper(adapter_func=adapter_func, schema=ArgsModel):
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
            
            tool = StructuredTool(
                name=tool_name,
                description=desc,
                func=wrapped_func,
                args_schema=ArgsModel
            )
            lc_tools.append(tool)
        
        return lc_tools

    def _create_react_prompt(self) -> PromptTemplate:
        """Crea el prompt específico para ReAct."""
        
        template = """Eres Pepper, un robot social humanoide diseñado para interactuar con personas de manera natural y amigable.

Tu objetivo es completar la tarea del usuario paso a paso, razonando antes de cada acción.

HERRAMIENTAS DISPONIBLES:
{tools}

NOMBRES DE HERRAMIENTAS: {tool_names}

FORMATO DE RESPUESTA OBLIGATORIO:
Debes seguir este formato EXACTAMENTE:

Thought: [Piensa en qué necesitas hacer ahora y por qué]
Action: [Nombre EXACTO de la herramienta de la lista]
Action Input: [Argumentos en formato JSON]
Observation: [El sistema mostrará el resultado automáticamente]

... (repite Thought/Action/Action Input/Observation según sea necesario)

Thought: Ya completé la tarea
Final Answer: [Resumen de lo que lograste]

REGLAS PARA ACTION INPUT:
- Siempre usa formato JSON con las claves correctas
- Para herramientas con UN argumento (talk, go_to_place, find_person):
  Action Input: {{"message": "texto"}} o {{"location": "lugar"}} o {{"name": "persona"}}
  
- Para herramientas con múltiples argumentos (calc_depth):
  Action Input: {{"x": 10, "y": 20, "w": 80, "h": 120}}

EJEMPLOS CORRECTOS:

Ejemplo 1:
Thought: Necesito ir a la cocina
Action: go_to_place
Action Input: {{"location": "cocina"}}
Observation: Éxito: El robot ha llegado a cocina.

Thought: Ahora debo buscar a Tomas
Action: find_person
Action Input: {{"name": "Tomas"}}
Observation: Éxito: Se encontró a Tomas.

Thought: Debo comunicar el mensaje
Action: talk
Action Input: {{"message": "hola, la comida está lista"}}
Observation: Éxito: El mensaje fue dicho.

Thought: Ya completé la tarea
Final Answer: He ido a la cocina, encontrado a Tomas y le he dicho el mensaje.

RESTRICCIONES:
- Ubicaciones conocidas: cocina, sala, puerta
- Personas conocidas: Tomas
- Solo usa herramientas de la lista
- NO inventes herramientas ni capacidades

TAREA: {input}

HISTORIAL DE ACCIONES:
{agent_scratchpad}

Comienza tu razonamiento:"""

        return PromptTemplate(
            input_variables=["input", "agent_scratchpad", "tools", "tool_names"],
            template=template
        )

    def _create_react_agent(self) -> AgentExecutor:
        """Crea el agente ReAct usando LangChain."""
        prompt = self._create_react_prompt()
        lc_tools = self._create_langchain_tools()
        
        agent = create_react_agent(
            llm=self.llm,
            tools=lc_tools,
            prompt=prompt
        )
        
        agent_executor = AgentExecutor(
            agent=agent,
            tools=lc_tools,
            verbose=True,
            max_iterations=self.max_iterations,
            max_execution_time=self.max_execution_time,
            handle_parsing_errors=True,
            return_intermediate_steps=True,
            early_stopping_method="generate"
        )
        
        return agent_executor

    def _extract_trace_from_steps(self, intermediate_steps: List) -> List[str]:
        """Convierte pasos intermedios en trace legible."""
        trace = []
        
        for i, (action, observation) in enumerate(intermediate_steps, 1):
            tool_name = action.tool
            tool_input = action.tool_input
            
            if isinstance(tool_input, dict):
                input_str = ", ".join(f"{k}='{v}'" for k, v in tool_input.items())
            else:
                input_str = str(tool_input)
            
            # Determinar éxito por observación
            success = "Éxito" in str(observation) and "Fallo" not in str(observation)
            status = "✓" if success else "✗"
            
            trace_entry = f"Paso {i} [{status}]: {tool_name}({input_str}) -> {observation}"
            trace.append(trace_entry)
        
        return trace

    def _determine_success(self, output: Dict[str, Any], intermediate_steps: List) -> bool:
        """Determina si la tarea fue exitosa."""
        if "output" not in output or not intermediate_steps:
            return False
        
        output_text = str(output.get("output", "")).lower()
        if any(word in output_text for word in ["error fatal", "excepción", "no puedo"]):
            return False
        
        # Todos los pasos deben ser exitosos
        all_success = all(
            "Éxito" in str(obs) and "Fallo" not in str(obs)
            for _, obs in intermediate_steps
        )
        
        return all_success

    def run(self, task_description: str) -> Dict[str, Any]:
        """Implementación del método 'run' para ReAct."""
        start_time = time.time()
        
        print("\n" + "="*60)
        print("🤖 REACT AGENT - Iniciando tarea")
        print("="*60)
        print(f"Tarea: {task_description}\n")
        
        try:
            result = self.agent_executor.invoke({"input": task_description})
            
            intermediate_steps = result.get("intermediate_steps", [])
            trace = self._extract_trace_from_steps(intermediate_steps)
            success = self._determine_success(result, intermediate_steps)
            
            execution_time = time.time() - start_time
            
            print("\n" + "="*60)
            print(f"{'✅ ÉXITO' if success else '❌ FALLO'} - Tarea completada")
            print(f"Pasos ejecutados: {len(intermediate_steps)}")
            print(f"Tiempo: {execution_time:.2f}s")
            print("="*60)
            
            return {
                "success": success,
                "steps": len(intermediate_steps),
                "trace": trace,
                "execution_time": execution_time,
                "architecture": "ReAct",
                "final_output": result.get("output", "")
            }
        
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Error fatal: {str(e)}"
            
            print("\n" + "="*60)
            print("❌ ERROR FATAL")
            print(f"Error: {str(e)}")
            print("="*60)
            
            return {
                "success": False,
                "steps": 0,
                "trace": [error_msg],
                "execution_time": execution_time,
                "architecture": "ReAct"
            }