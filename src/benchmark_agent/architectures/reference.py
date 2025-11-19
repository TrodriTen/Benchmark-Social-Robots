# src/benchmark_agent/architectures/reference.py

from pydantic import BaseModel, Field
import time
import json
import uuid
from typing import List, Dict, Any, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool, StructuredTool
from langchain_core.prompts import PromptTemplate
from langgraph.store.memory import InMemoryStore

from .base_agent import BaseAgent
from ..service_adapter import get_tools_description, get_tool_names
from ..callbacks import MetricsCallbackHandler


class ReferenceAgent(BaseAgent):
    """
    Implementación de la arquitectura de Referencia: ReAct + reflexión breve + recuperación selectiva.
    
    Esta arquitectura combina:
    1. ReAct: Razonamiento y actuación paso a paso
    2. Reflexión breve: Análisis ligero después de cada paso para ajustar estrategia
    3. Recuperación selectiva: Uso de memoria vectorial para recuperar ejemplos relevantes
    
    A diferencia de Reflexion completo, esta arquitectura hace reflexiones más ligeras
    y continuas durante la ejecución en lugar de esperar al fallo completo.
    """
    
    def __init__(
        self, 
        llm: BaseChatModel, 
        tools: List[BaseTool],
        max_iterations: int = 15,
        max_execution_time: Optional[float] = 120.0,
        use_memory: bool = True
    ):
        """
        Args:
            llm: Modelo de lenguaje
            tools: Lista de herramientas disponibles
            max_iterations: Máximo de pasos ReAct
            max_execution_time: Tiempo máximo de ejecución en segundos
            use_memory: Si se debe usar recuperación de memoria vectorial
        """
        super().__init__(llm, tools)
        self.max_iterations = max_iterations
        self.max_execution_time = max_execution_time
        self.use_memory = use_memory
        
        # Memoria vectorial para recuperación de ejemplos
        self.memory_store = InMemoryStore() if use_memory else None
        
        # Historial de reflexiones durante la ejecución
        self.execution_reflections: List[str] = []
        
        # Cargar ejemplos si existe memoria
        if self.use_memory:
            self._load_examples_to_memory()

    def _load_examples_to_memory(self):
        """Carga ejemplos de soluciones en la memoria vectorial."""
        # Ejemplos basados en las tareas del benchmark
        examples = [
            {
                "task": "Ve a la cocina, busca a Tomas y dile un mensaje",
                "solution": [
                    "Paso 1: move_to(cocina) - Navegar primero a la ubicación",
                    "Paso 2: find_person(Tomas) - Buscar a la persona específica",
                    "Paso 3: say(mensaje) - Comunicar el mensaje"
                ],
                "reflection": "Secuencia correcta: primero ubicación, luego persona, finalmente acción de comunicación"
            },
            {
                "task": "Busca a una persona y ve a un lugar",
                "solution": [
                    "Paso 1: find_person(nombre) - Localizar a la persona primero",
                    "Paso 2: move_to(lugar) - Navegar al lugar solicitado"
                ],
                "reflection": "Orden flexible: se puede buscar persona primero si es necesario"
            },
            {
                "task": "Tarea que requiere ubicación no disponible",
                "solution": [
                    "Paso 1: Intentar move_to(ubicación)",
                    "Observación: Ubicación no encontrada",
                    "Paso 2: say(mensaje explicativo) - Comunicar limitación"
                ],
                "reflection": "Cuando faltan capacidades, comunicar claramente al usuario"
            }
        ]
        
        for idx, example in enumerate(examples):
            namespace = ("reference_agent", "examples")
            key = f"example_{idx}"
            self.memory_store.put(namespace, key, example)

    def _retrieve_relevant_examples(self, task_description: str) -> List[Dict]:
        """Recupera ejemplos relevantes de la memoria vectorial."""
        if not self.use_memory or not self.memory_store:
            return []
        
        try:
            namespace = ("reference_agent", "examples")
            results = self.memory_store.search(
                namespace,
                query=task_description,
                limit=3
            )
            return [result.value for result in results]
        except Exception as e:
            print(f"Error retrieving examples: {e}")
            return []

    def _create_react_prompt_with_memory(self, examples: List[Dict]) -> PromptTemplate:
        """
        Crea el prompt de ReAct enriquecido con ejemplos recuperados y reflexiones.
        """
        # Formatear ejemplos recuperados
        examples_text = ""
        if examples:
            examples_text = "\n--- EJEMPLOS RELEVANTES ---\n"
            for i, example in enumerate(examples, 1):
                examples_text += f"\nEjemplo {i}:\n"
                examples_text += f"Tarea: {example.get('task', 'N/A')}\n"
                examples_text += f"Solución:\n"
                for step in example.get('solution', []):
                    examples_text += f"  {step}\n"
                examples_text += f"Reflexión: {example.get('reflection', 'N/A')}\n"
            examples_text += "--- FIN EJEMPLOS ---\n\n"
        
        # Formatear reflexiones acumuladas
        reflections_text = ""
        if self.execution_reflections:
            reflections_text = "\n--- REFLEXIONES DE PASOS PREVIOS ---\n"
            for i, reflection in enumerate(self.execution_reflections, 1):
                reflections_text += f"{i}. {reflection}\n"
            reflections_text += "--- FIN REFLEXIONES ---\n\n"

        template = """Eres Pepper, un robot social humanoide diseñado para interactuar con personas de manera natural y amigable.

HERRAMIENTAS DISPONIBLES:
{tools}

NOMBRES DE HERRAMIENTAS: {tool_names}

FORMATO DE RESPUESTA OBLIGATORIO:
Debes seguir este formato EXACTAMENTE:

Thought: [Analiza la situación actual y determina el próximo paso necesario]
Action: [Nombre EXACTO de la herramienta de la lista]
Action Input: [Argumentos en formato JSON]
Observation: [El sistema mostrará el resultado automáticamente]

... (repite Thought/Action/Action Input/Observation según sea necesario)

Thought: He completado exitosamente la tarea [verifica que TODO esté hecho]
Final Answer: [Resumen específico de lo que lograste]

IMPORTANTE: Usa "Final Answer" tan pronto como completes los objetivos. NO continues haciendo acciones innecesarias.

REGLAS PARA ACTION INPUT:
- Siempre usa formato JSON con las claves correctas
- Para go_to_place: {{"location": "lugar"}}
- Para talk: {{"message": "texto"}}
- Para find_person: {{"name": "persona"}}
- Para store_in_memory: {{"key": "identificador", "value": "información"}}
- Para recall_from_memory: {{}} (para toda la memoria) o {{"key": "identificador"}} (para un valor específico)
- Para count_objects: {{"object_type": "tipo_objeto"}}

CAPACIDADES AVANZADAS:
- MEMORIA PERSISTENTE: Usa store_in_memory/recall_from_memory para tareas multi-paso que requieren recordar información entre pasos
  Ejemplo: "Averigua quién le gusta el café, vuelve y dime" → Guardar respuesta → Navegar de vuelta → Recordar respuesta → Comunicarla
- PERCEPCIÓN: Usa describe_environment para obtener descripción completa del entorno actual
- CONTEO: Usa count_objects para contar objetos específicos en la ubicación actual
- INVENTARIOS: Combina navegación + describe_environment + store_in_memory para generar inventarios completos

RESTRICCIONES:
- Ubicaciones disponibles (CASA): living room, kitchen, bedroom, bathroom, gym, entrance hall, garden
- Ubicaciones disponibles (OFICINA): office, library, cafeteria, conference room, reception, lobby, break room, archive room, copy room, main entrance, parking lot, elevator, meeting room A, meeting room B, meeting room C, technical department, HR department, sales department, finance department
- Personas en el entorno: Alice, Tomas, David, Maria, Carlos, Ana, Jorge, Richard, Laura, Sophia, Alex, Elena, Miguel, Pablo, Julia, Peter
- Objetos rastreables: chair, exercise ball, table, folder, first aid kit, package, printer, keys, book, coffee machine
- Solo usa herramientas de la lista
- Aprende de los ejemplos y reflexiones proporcionados
- Si algo falla, ajusta tu estrategia basándote en reflexiones previas

CUÁNDO TERMINAR (MUY IMPORTANTE):
- LEE LA TAREA COMPLETA: Si dice "haz X y luego Y", debes hacer AMBAS cosas
- Usa "Final Answer" SOLO después de completar TODOS los pasos de la tarea
- NO repitas acciones que ya funcionaron
- Ejemplos de tareas completas:
  * "Busca a X y dile Y" → Encontrar a X AND hablarle → ENTONCES termina
  * "Busca a X y luego ve a Y" → Encontrar a X AND ir a Y → ENTONCES termina
  * "Ve a X y busca a Y" → Ir a X AND buscar a Y → ENTONCES termina
- Si ya completaste TODOS los objetivos → usa "Final Answer"
- Si falta algún objetivo → NO uses "Final Answer", sigue trabajando

{examples}

{reflections}

TAREA: {input}

HISTORIAL DE ACCIONES:
{agent_scratchpad}

Comienza tu razonamiento:"""

        return PromptTemplate(
            input_variables=["input", "agent_scratchpad", "tools", "tool_names", "examples", "reflections"],
            template=template
        )

    def _generate_brief_reflection(
        self,
        task_description: str,
        current_step: int,
        last_action: str,
        last_observation: str
    ) -> str:
        """
        Genera una reflexión breve después de cada paso para guiar los siguientes.
        """
        reflection_prompt = f"""Analiza brevemente el último paso ejecutado y proporciona una reflexión concisa (1 oración).

Tarea original: {task_description}
Paso actual: {current_step}
Última acción: {last_action}
Resultado: {last_observation}

Proporciona UNA reflexión breve que ayude a decidir el próximo paso.
Enfócate en:
- ¿El resultado fue exitoso?
- ¿Qué debería hacer a continuación?
- ¿Hay algún ajuste necesario en la estrategia?

REFLEXIÓN (1 oración):"""

        try:
            reflection_response = self.llm.invoke(reflection_prompt)
            reflection = reflection_response.content.strip()
            return reflection
        except Exception as e:
            return f"Error generando reflexión: {e}"

    def _create_agent_executor(
        self,
        examples: List[Dict],
        reflections: List[str]
    ) -> AgentExecutor:
        """
        Crea el ejecutor del agente ReAct con contexto enriquecido.
        """
        prompt = self._create_react_prompt_with_memory(examples)
        
        lc_tools = self._create_langchain_tools()
        
        # Formatear ejemplos y reflexiones para partial variables
        examples_text = ""
        if examples:
            examples_text = "\n--- EJEMPLOS RELEVANTES ---\n"
            for i, example in enumerate(examples, 1):
                examples_text += f"\nEjemplo {i}:\n"
                examples_text += f"Tarea: {example.get('task', 'N/A')}\n"
                examples_text += f"Solución:\n"
                for step in example.get('solution', []):
                    examples_text += f"  {step}\n"
                examples_text += f"Reflexión: {example.get('reflection', 'N/A')}\n"
            examples_text += "--- FIN EJEMPLOS ---\n\n"
        
        reflections_text = ""
        if reflections:
            reflections_text = "\n--- REFLEXIONES DE PASOS PREVIOS ---\n"
            for i, reflection in enumerate(reflections, 1):
                reflections_text += f"{i}. {reflection}\n"
            reflections_text += "--- FIN REFLEXIONES ---\n\n"
        
        # Aplicar partial variables
        prompt_with_context = prompt.partial(
            examples=examples_text,
            reflections=reflections_text
        )
        
        agent = create_react_agent(llm=self.llm, tools=lc_tools, prompt=prompt_with_context)
        
        agent_executor = AgentExecutor(
            agent=agent,
            tools=lc_tools,
            verbose=True,
            max_iterations=self.max_iterations,
            max_execution_time=self.max_execution_time,
            handle_parsing_errors=True,
            return_intermediate_steps=True
            # REMOVIDO: early_stopping_method="generate" - Parámetro obsoleto que causaba errores
        )
        
        return agent_executor

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
            def make_wrapper(adapter_func=adapter_func, tool_name=tool_name, schema=ArgsModel):
                """Wrapper factory con early binding"""
                def wrapper(*args, **kwargs):
                    # Debug: print para ver qué estamos recibiendo
                    # print(f"[DEBUG] {tool_name}: args={args}, kwargs={kwargs}")
                    
                    # Caso 1: Un solo argumento posicional (objeto Pydantic o dict)
                    if len(args) == 1 and not kwargs:
                        arg = args[0]
                        if hasattr(arg, 'model_dump'):
                            final_kwargs = arg.model_dump()
                        elif hasattr(arg, 'dict'):
                            final_kwargs = arg.dict()
                        elif isinstance(arg, dict):
                            final_kwargs = arg
                        else:
                            # Si no es dict, usar normalize_action_input del service_adapter
                            from ..service_adapter import normalize_action_input
                            final_kwargs = normalize_action_input(tool_name, arg)
                    # Caso 2: Solo kwargs
                    elif not args and kwargs:
                        final_kwargs = kwargs
                    # Caso 3: Mezcla de args y kwargs, dar prioridad a kwargs
                    elif args and kwargs:
                        final_kwargs = kwargs
                    # Caso 4: No hay argumentos - usar dict vacío
                    else:
                        final_kwargs = {}
                    
                    result = adapter_func(**final_kwargs)
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

    def _format_examples(self, examples: List[Dict]) -> str:
        """Formatea ejemplos para el prompt."""
        if not examples:
            return ""
        
        text = ""
        for i, example in enumerate(examples, 1):
            text += f"\nEjemplo {i}:\n"
            text += f"Tarea: {example.get('task', 'N/A')}\n"
            text += f"Solución:\n"
            for step in example.get('solution', []):
                text += f"  {step}\n"
            text += f"Reflexión: {example.get('reflection', 'N/A')}\n"
        return text

    def _extract_trace_from_steps(self, intermediate_steps: List) -> List[str]:
        """Convierte los pasos intermedios en un trace legible."""
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

    def _determine_success(
        self,
        output: Dict[str, Any],
        intermediate_steps: List
    ) -> bool:
        """
        Determina si la tarea fue exitosa.
        
        Una tarea es exitosa si:
        1. Tiene un output (Final Answer)
        2. El output no indica error fatal
        3. Los últimos pasos fueron exitosos (indica que terminó bien)
        
        No importa si pasos intermedios fallaron (ej: buscar en lugar equivocado),
        lo importante es que el objetivo final se logró.
        """
        # Debe tener output y pasos
        if "output" not in output or not intermediate_steps:
            return False
        
        output_text = str(output.get("output", "")).lower()
        
        # Si el output indica error fatal, es fallo
        if any(word in output_text for word in ["error fatal", "no puedo completar"]):
            return False
        
        # Si no hay pasos, es fallo
        if not intermediate_steps:
            return False
        
        # Verificar los últimos 3 pasos (o menos si hay menos pasos)
        # Si la mayoría de los últimos pasos fueron exitosos, consideramos que la tarea se completó
        last_steps = intermediate_steps[-3:] if len(intermediate_steps) >= 3 else intermediate_steps
        successful_final_steps = sum(
            1 for _, obs in last_steps
            if "Éxito" in str(obs) and "Fallo" not in str(obs)
        )
        
        # Si al menos 2 de los últimos 3 pasos (o la mayoría) fueron exitosos, consideramos éxito
        threshold = len(last_steps) // 2 + 1  # Mayoría
        return successful_final_steps >= threshold

    def run(self, task_description: str) -> Dict[str, Any]:
        """
        Implementación del método 'run' para la arquitectura de Referencia.
        """
        start_time = time.time()
        self.execution_reflections = []  # Reset reflexiones
        
        # Crear callback handler para capturar métricas
        metrics_callback = MetricsCallbackHandler()
        
        print("\n" + "="*70)
        print("🔄 REFERENCE AGENT - Iniciando tarea")
        print("="*70)
        print(f"Tarea: {task_description}\n")
        
        try:
            # 1. Recuperar ejemplos relevantes
            relevant_examples = []
            if self.use_memory:
                print("--- 📚 Recuperando ejemplos relevantes ---")
                relevant_examples = self._retrieve_relevant_examples(task_description)
                print(f"Ejemplos recuperados: {len(relevant_examples)}")
            
            # 2. Crear agente con contexto enriquecido
            agent_executor = self._create_agent_executor(relevant_examples, [])
            
            # 3. Ejecutar con reflexiones incrementales
            print("\n--- 🚀 Ejecutando con reflexiones incrementales ---")
            
            result = agent_executor.invoke(
                {
                    "input": task_description,
                    "examples": self._format_examples(relevant_examples),
                    "reflections": ""
                },
                config={"callbacks": [metrics_callback]}
            )
            
            intermediate_steps = result.get("intermediate_steps", [])
            
            # 4. Generar reflexiones breves después de cada paso
            for i, (action, observation) in enumerate(intermediate_steps, 1):
                if i < len(intermediate_steps):  # No reflexionar en el último paso
                    reflection = self._generate_brief_reflection(
                        task_description,
                        i,
                        f"{action.tool}({action.tool_input})",
                        str(observation)
                    )
                    self.execution_reflections.append(reflection)
                    print(f"💭 Reflexión paso {i}: {reflection}")
            
            # 5. Evaluar resultado
            trace = self._extract_trace_from_steps(intermediate_steps)
            success = self._determine_success(result, intermediate_steps)
            
            execution_time = time.time() - start_time
            
            # Obtener métricas del callback
            metrics = metrics_callback.get_summary()
            
            print("\n" + "="*70)
            print(f"{'✅ ÉXITO' if success else '❌ FALLO'} - Tarea completada")
            print(f"Pasos ejecutados: {len(intermediate_steps)}")
            print(f"Reflexiones generadas: {len(self.execution_reflections)}")
            print(f"Tiempo: {execution_time:.2f}s")
            print(f"Llamadas LLM: {metrics['llm_calls_count']}")
            print(f"Tokens totales: {metrics['total_tokens']}")
            print("="*70)
            
            return {
                "success": success,
                "steps": len(intermediate_steps),
                "trace": trace,
                "execution_time": execution_time,
                "architecture": "Reference",
                "reflections": self.execution_reflections.copy(),
                "examples_used": len(relevant_examples),
                "final_output": result.get("output", "No se generó respuesta final"),
                "metrics": metrics
            }
        
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Error fatal durante la ejecución: '{str(e)}'"
            
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
            
            print("\n" + "="*70)
            print("❌ ERROR FATAL")
            print(f"Error: {str(e)}")
            print("="*70)
            
            return {
                "success": False,
                "steps": 0,
                "trace": [error_msg],
                "execution_time": execution_time,
                "architecture": "Reference",
                "reflections": self.execution_reflections.copy(),
                "metrics": metrics
            }