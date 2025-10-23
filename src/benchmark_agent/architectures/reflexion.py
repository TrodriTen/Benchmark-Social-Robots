# src/benchmark_agent/architectures/reflexion.py

import time
from typing import List, Dict, Any, Optional
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool, StructuredTool
from langchain_core.prompts import PromptTemplate

from .base_agent import BaseAgent
from ..service_adapter import get_tools_description, get_tool_names


class ReflexionAgent(BaseAgent):
    """
    Implementación de la arquitectura Reflexion para un robot social.
    
    Reflexion combina:
    1. Actor (ReAct): Intenta resolver la tarea
    2. Evaluator: Evalúa si el intento fue exitoso
    3. Self-Reflection: Si falla, genera una reflexión sobre qué salió mal
    4. Memory: Usa las reflexiones previas para mejorar en siguientes intentos
    
    El ciclo se repite hasta tener éxito o alcanzar max_attempts.
    
    Paper: https://arxiv.org/abs/2303.11366
    """
    
    def __init__(
        self, 
        llm: BaseChatModel, 
        tools: List[BaseTool],
        max_attempts: int = 3,
        max_iterations_per_attempt: int = 10,
        max_execution_time: Optional[float] = 120.0
    ):
        """
        Args:
            llm: Modelo de lenguaje
            tools: Lista de herramientas disponibles
            max_attempts: Máximo número de intentos (trials)
            max_iterations_per_attempt: Máximo de pasos ReAct por intento
            max_execution_time: Tiempo máximo de ejecución por intento en segundos
        """
        super().__init__(llm, tools)
        self.max_attempts = max_attempts
        self.max_iterations_per_attempt = max_iterations_per_attempt
        self.max_execution_time = max_execution_time
        
        # Memoria de reflexiones de intentos previos
        self.reflection_memory: List[str] = []

    def _create_actor_prompt(self) -> PromptTemplate:
        """Prompt para Actor con reflexiones."""
        
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
- Para go_to_place: {{"location": "lugar"}}
- Para talk: {{"message": "texto"}}
- Para find_person: {{"name": "persona"}}

EJEMPLOS:

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

{reflections_context}

TAREA: {input}

HISTORIAL DE ACCIONES:
{agent_scratchpad}

Comienza tu razonamiento:"""

        return PromptTemplate(
            input_variables=["input", "agent_scratchpad", "tools", "tool_names", "reflections_context"],
            template=template
        )

    def _create_actor_agent(self, reflections_context: str) -> AgentExecutor:
        """Crea Actor (ReAct) con reflexiones."""
        prompt = self._create_actor_prompt()
        
        # Convertir adapters a herramientas LangChain
        lc_tools = self._create_langchain_tools()
        
        # Crear agente con partial variables para reflections_context
        prompt_with_reflections = prompt.partial(reflections_context=reflections_context)
        
        agent = create_react_agent(llm=self.llm, tools=lc_tools, prompt=prompt_with_reflections)
        
        agent_executor = AgentExecutor(
            agent=agent,
            tools=lc_tools,
            verbose=True,
            max_iterations=self.max_iterations_per_attempt,
            max_execution_time=self.max_execution_time,
            handle_parsing_errors=True,
            return_intermediate_steps=True,
            early_stopping_method="generate"
        )
        
        return agent_executor
    
    def _create_langchain_tools(self) -> List[StructuredTool]:
        """Convierte adapters a herramientas LangChain (mismo que react.py)"""
        from pydantic import BaseModel, Field
        
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

    def _evaluate_attempt(
        self, 
        task_description: str,
        output: Dict[str, Any], 
        intermediate_steps: List
    ) -> bool:
        """
        Evaluator: Determina si el intento fue exitoso.
        
        Criterios:
        1. Se ejecutaron acciones
        2. Todas las acciones fueron exitosas
        3. Se generó una respuesta final coherente
        """
        # Verificar que hubo acciones
        if not intermediate_steps:
            return False
        
        # Verificar que todas las acciones fueron exitosas
        all_success = all(
            "Éxito" in str(obs) and "Fallo" not in str(obs)
            for _, obs in intermediate_steps
        )
        
        if not all_success:
            return False
        
        # Verificar que hay output
        if "output" not in output:
            return False
        
        output_text = str(output.get("output", "")).lower()
        
        # Verificar que no hay errores críticos
        if any(word in output_text for word in ["error fatal", "no puedo", "imposible"]):
            return False
        
        return True

    def _generate_reflection(
        self, 
        task_description: str,
        attempt_number: int,
        output: Dict[str, Any],
        intermediate_steps: List
    ) -> str:
        """
        Self-Reflection: Genera una reflexión sobre qué salió mal y cómo mejorar.
        """
        print("\n--- 🤔 Generando Reflexión ---")
        
        # Construir un resumen del intento fallido
        steps_summary = []
        for i, (action, observation) in enumerate(intermediate_steps, 1):
            tool_name = action.tool
            tool_input = action.tool_input
            success = "Éxito" in str(observation) and "Fallo" not in str(observation)
            status = "✓" if success else "✗"
            steps_summary.append(f"{i}. [{status}] {tool_name}({tool_input}) → {observation}")
        
        steps_text = "\n".join(steps_summary) if steps_summary else "No se ejecutaron pasos."
        
        # Prompt para generar la reflexión
        reflection_prompt = f"""Eres un experto en robótica social analizando el desempeño de un robot llamado Pepper.

TAREA ORIGINAL:
{task_description}

INTENTO #{attempt_number} - RESULTADO: FALLO

PASOS EJECUTADOS:
{steps_text}

SALIDA FINAL:
{output.get('output', 'No hubo salida final')}

ANÁLISIS REQUERIDO:
Analiza qué salió mal en este intento y proporciona una reflexión constructiva para mejorar.

Considera:
1. ¿Se eligieron las herramientas correctas?
2. ¿Los argumentos fueron correctos?
3. ¿El orden de las acciones fue apropiado?
4. ¿Qué errores específicos se cometieron?
5. ¿Cómo se podría mejorar en el próximo intento?

RESTRICCIONES DEL ROBOT:
- Ubicaciones conocidas: cocina, sala, puerta (NO puede ir a otras)
- Personas conocidas: Tomas (NO puede encontrar a otras)
- Herramientas: move_to, say, find_person

Proporciona una reflexión concisa (2-4 oraciones) que ayude al robot a mejorar en el próximo intento.

REFLEXIÓN:"""

        reflection_response = self.llm.invoke(reflection_prompt)
        reflection_text = reflection_response.content.strip()
        
        print(f"Reflexión generada:\n{reflection_text}")
        print("--- ✅ Reflexión Completa ---\n")
        
        return reflection_text

    def _format_reflections_context(self) -> str:
        """
        Formatea las reflexiones previas para incluirlas en el contexto del Actor.
        """
        if not self.reflection_memory:
            return ""
        
        context = "\n--- REFLEXIONES DE INTENTOS PREVIOS ---\n"
        context += "Aprende de estos errores pasados para mejorar tu estrategia:\n\n"
        
        for i, reflection in enumerate(self.reflection_memory, 1):
            context += f"Intento {i}: {reflection}\n\n"
        
        context += "--- FIN REFLEXIONES ---\n"
        
        return context

    def _extract_trace_from_steps(self, intermediate_steps: List) -> List[str]:
        """
        Convierte los pasos intermedios del agente en un trace legible.
        """
        trace = []
        
        for i, (action, observation) in enumerate(intermediate_steps, 1):
            tool_name = action.tool
            tool_input = action.tool_input
            
            if isinstance(tool_input, dict):
                input_str = ", ".join(f"{k}='{v}'" for k, v in tool_input.items())
            else:
                input_str = str(tool_input)
            
            success = "Éxito" in str(observation) and "Fallo" not in str(observation)
            status = "✓" if success else "✗"
            
            trace_entry = f"Paso {i} [{status}]: {tool_name}({input_str}) -> {observation}"
            trace.append(trace_entry)
        
        return trace

    def run(self, task_description: str) -> Dict[str, Any]:
        """
        Implementación del método 'run' para Reflexion.
        
        Ciclo:
        1. Actor intenta resolver la tarea
        2. Evaluator determina si tuvo éxito
        3. Si falló y quedan intentos:
           - Self-Reflection genera análisis del fallo
           - Memoria almacena la reflexión
           - Vuelve al paso 1 con el nuevo contexto
        """
        start_time = time.time()
        
        print("\n" + "="*70)
        print("🔄 REFLEXION AGENT - Iniciando tarea")
        print("="*70)
        print(f"Tarea: {task_description}")
        print(f"Intentos máximos: {self.max_attempts}\n")
        
        all_attempts_trace = []
        
        for attempt in range(1, self.max_attempts + 1):
            print("\n" + "="*70)
            print(f"🎯 INTENTO {attempt}/{self.max_attempts}")
            print("="*70)
            
            try:
                # Preparar contexto con reflexiones previas
                reflections_context = self._format_reflections_context()
                
                # Crear el Actor con el contexto actualizado
                actor = self._create_actor_agent(reflections_context)
                
                # Ejecutar el intento
                result = actor.invoke({
                    "input": task_description,
                    "reflections_context": reflections_context
                })
                
                intermediate_steps = result.get("intermediate_steps", [])
                trace = self._extract_trace_from_steps(intermediate_steps)
                
                # Agregar trace de este intento
                attempt_trace = {
                    "attempt": attempt,
                    "steps": trace,
                    "output": result.get("output", "No se generó respuesta")
                }
                all_attempts_trace.append(attempt_trace)
                
                # Evaluar el intento
                success = self._evaluate_attempt(task_description, result, intermediate_steps)
                
                print("\n" + "-"*70)
                print(f"{'✅ INTENTO EXITOSO' if success else '❌ INTENTO FALLIDO'}")
                print(f"Pasos ejecutados: {len(intermediate_steps)}")
                print("-"*70)
                
                if success:
                    # ¡Éxito! Terminar
                    execution_time = time.time() - start_time
                    
                    print("\n" + "="*70)
                    print("🎉 TAREA COMPLETADA CON ÉXITO")
                    print(f"Completada en intento {attempt}/{self.max_attempts}")
                    print(f"Tiempo total: {execution_time:.2f}s")
                    print("="*70)
                    
                    return {
                        "success": True,
                        "attempts": attempt,
                        "steps": len(intermediate_steps),
                        "trace": trace,
                        "all_attempts": all_attempts_trace,
                        "reflections": self.reflection_memory.copy(),
                        "execution_time": execution_time,
                        "architecture": "Reflexion",
                        "final_output": result.get("output", "")
                    }
                
                else:
                    # Fallo: Generar reflexión si quedan intentos
                    if attempt < self.max_attempts:
                        reflection = self._generate_reflection(
                            task_description, 
                            attempt, 
                            result, 
                            intermediate_steps
                        )
                        self.reflection_memory.append(reflection)
                        
                        print(f"\n💾 Reflexión guardada en memoria. Preparando intento {attempt + 1}...")
                    else:
                        print("\n❌ No quedan más intentos disponibles.")
            
            except Exception as e:
                error_msg = f"Error durante intento {attempt}: {str(e)}"
                print(f"\n❌ {error_msg}")
                
                attempt_trace = {
                    "attempt": attempt,
                    "steps": [error_msg],
                    "output": "Error fatal"
                }
                all_attempts_trace.append(attempt_trace)
                
                # Generar reflexión sobre el error si quedan intentos
                if attempt < self.max_attempts:
                    reflection = f"El intento {attempt} falló con error: {str(e)}. En el próximo intento, debo asegurarme de usar el formato correcto y las herramientas disponibles."
                    self.reflection_memory.append(reflection)
        
        # Si llegamos aquí, fallaron todos los intentos
        execution_time = time.time() - start_time
        
        print("\n" + "="*70)
        print("❌ TAREA FALLIDA")
        print(f"Se agotaron los {self.max_attempts} intentos")
        print(f"Tiempo total: {execution_time:.2f}s")
        print("="*70)
        
        return {
            "success": False,
            "attempts": self.max_attempts,
            "steps": 0,
            "trace": [f"Fallaron todos los {self.max_attempts} intentos"],
            "all_attempts": all_attempts_trace,
            "reflections": self.reflection_memory.copy(),
            "execution_time": execution_time,
            "architecture": "Reflexion"
        }
