import time
from typing import List, Dict, Any, Optional
from langchain_core.prompts import PromptTemplate
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool, StructuredTool
from pydantic import BaseModel, Field

from .base_agent import BaseAgent
from .prompts_improved import get_improved_prompt
from ..service_adapter import ADAPTERS, ADAPTER_SPECS, get_tools_description
from ..callbacks import MetricsCallbackHandler

class ReactAgent(BaseAgent):
    """
    Implementación de la arquitectura ReAct (Reasoning + Acting) para un robot social.
    """
    
    def __init__(self, llm: BaseChatModel, max_iterations: int = 10, max_execution_time: int = 120):
        super().__init__(llm=llm, tools=None)
        self.max_iterations = max_iterations
        self.max_execution_time = max_execution_time
        self.adapters = ADAPTERS               
        self.adapter_specs = ADAPTER_SPECS
        self.agent_executor = self._create_react_agent()

    def _create_langchain_tools(self) -> List[StructuredTool]:
        """Convierte adapters a herramientas LangChain con args_schema y wrapper."""
        from pydantic import BaseModel, Field
        from typing import Optional
        lc_tools = []
        for tool_name, adapter_func in self.adapters.items():
            spec = self.adapter_specs.get(tool_name, {})
            desc = spec.get("desc", f"Herramienta {tool_name}")
            args_spec = spec.get("args", {})
            required = spec.get("required", [])

            # 1) Modelo dinámico para validación de args
            fields = {}
            annotations = {}
            for arg_name, arg_type in args_spec.items():
                is_required = arg_name in required
                if arg_type == "int":
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

            ArgsModel = type(
                f"{tool_name}_args",
                (BaseModel,),
                {"__annotations__": annotations, **fields}
            )

            # 2) Wrapper que acepta `tool_input` (string/dict) y lo normaliza
            from ..service_adapter import normalize_action_input
            def make_wrapper(adapter_func=adapter_func, schema=ArgsModel, tool_name=tool_name):
                def wrapper(tool_input=None, **kwargs):
                    # Caso especial: si tool_input es el string '{}' vacío, tratarlo como dict vacío
                    if tool_input == '{}' or tool_input == {}:
                        tool_input = {}
                    
                    # Prioridad 1: tool_input ya es BaseModel/dict
                    if tool_input is not None and hasattr(tool_input, 'model_dump'):
                        kwargs = tool_input.model_dump()
                    elif tool_input is not None and isinstance(tool_input, dict):
                        kwargs = tool_input
                    elif tool_input is not None and isinstance(tool_input, str):
                        # Normaliza JSON/strings simples a kwargs con nombres correctos
                        try:
                            kwargs = normalize_action_input(tool_name, tool_input)
                        except Exception:
                            # Si falla la normalización y es string vacío o '{}', usar dict vacío
                            kwargs = {}
                    elif kwargs:
                        # kwargs ya vienen; completamos faltantes por default si aplica
                        pass
                    else:
                        # Sin nada explícito => usa defaults (p.ej. recognize_face num_pics=3)
                        kwargs = {}

                    # Crear instancia del schema para validar y rellenar defaults
                    try:
                        validated = schema(**kwargs)
                        # Usar los valores validados y con defaults aplicados
                        kwargs = validated.model_dump()
                    except Exception as e:
                        print(f"[DEBUG] Error validando {tool_name} con {kwargs}: {e}")
                        raise
                    
                    return adapter_func(**kwargs)
                return wrapper

            wrapped = make_wrapper()
            wrapped.__name__ = tool_name

            tool = StructuredTool(
                name=tool_name,
                description=desc,
                func=wrapped,
                args_schema=ArgsModel
            )
            lc_tools.append(tool)
        return lc_tools


    def _create_react_prompt(self) -> PromptTemplate:
        """Crea el prompt específico para ReAct usando el prompt mejorado."""
        template = get_improved_prompt("react")
        
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
        # Si no hay output, definitivamente es fallo
        if "output" not in output:
            return False
        
        output_text = str(output.get("output", "")).lower()
        
        # Si el output indica error fatal, es fallo
        if any(word in output_text for word in ["error fatal", "excepción", "no puedo completar"]):
            return False
        
        # Si hay un Final Answer válido, consideramos la tarea exitosa
        # incluso si hubo algunos pasos de exploración fallidos
        if output_text and len(output_text) > 10:
            return True
        
        return False

    def run(self, task_description: str) -> Dict[str, Any]:
        """Implementación del método 'run' para ReAct."""
        start_time = time.time()
        
        # Crear callback handler para capturar métricas
        metrics_callback = MetricsCallbackHandler()
        
        print("\n" + "="*60)
        print("🤖 REACT AGENT - Iniciando tarea")
        print("="*60)
        print(f"Tarea: {task_description}\n")
        
        try:
            # Ejecutar con callbacks para capturar métricas
            result = self.agent_executor.invoke(
                {"input": task_description},
                config={"callbacks": [metrics_callback]}
            )
            
            intermediate_steps = result.get("intermediate_steps", [])
            trace = self._extract_trace_from_steps(intermediate_steps)
            success = self._determine_success(result, intermediate_steps)
            
            execution_time = time.time() - start_time
            
            # Obtener métricas del callback
            metrics = metrics_callback.get_summary()
            
            print("\n" + "="*60)
            print(f"{'✅ ÉXITO' if success else '❌ FALLO'} - Tarea completada")
            print(f"Pasos ejecutados: {len(intermediate_steps)}")
            print(f"Tiempo: {execution_time:.2f}s")
            print(f"Llamadas LLM: {metrics['llm_calls_count']}")
            print(f"Tokens totales: {metrics['total_tokens']}")
            print("="*60)
            
            return {
                "success": success,
                "steps": len(intermediate_steps),
                "trace": trace,
                "execution_time": execution_time,
                "architecture": "ReAct",
                "final_output": result.get("output", ""),
                "metrics": metrics
            }
        
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Error fatal: {str(e)}"
            
            # Intentar obtener métricas aunque haya fallado
            try:
                metrics = metrics_callback.get_summary()
            except:
                metrics = {
                    "llm_calls_count": 0,
                    "total_tokens": 0,
                    "total_latency": 0.0,
                    "execution_time": 0.0,
                    "replannings": 0,
                    "llm_calls_detail": [],
                    "avg_tokens_per_call": 0,
                    "avg_latency_per_call": 0
                }
            
            print("\n" + "="*60)
            print("❌ ERROR FATAL")
            print(f"Error: {str(e)}")
            print("="*60)
            
            return {
                "success": False,
                "steps": 0,
                "trace": [error_msg],
                "execution_time": execution_time,
                "architecture": "ReAct",
                "metrics": metrics
            }