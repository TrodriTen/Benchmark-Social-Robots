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
from ..callbacks import MetricsCallbackHandler


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

ENTORNO SIMULADO:
- Estás operando en un entorno de prueba SIN personas reales
- Las herramientas de reconocimiento de voz (listen, speech2text) NO funcionan porque no hay nadie que responda
- NO uses listen ni speech2text - siempre retornan que no hay respuesta
- Puedes hablar (talk) pero no esperes respuestas de voz
- La navegación y búsqueda de personas funciona normalmente

INFORMACIÓN DEL ENTORNO:
- Robot inicia en: living room
- Ubicaciones disponibles (CASA): living room, kitchen, bedroom, bathroom, gym, entrance hall, garden
- Ubicaciones disponibles (OFICINA): office, library, cafeteria, conference room, reception, lobby, break room, archive room, copy room, main entrance, parking lot, elevator, meeting room A, meeting room B, meeting room C, technical department, HR department, sales department, finance department
- Personas: Alice, Tomas, David, Maria, Carlos, Ana, Jorge, Richard, Laura, Sophia, Alex, Elena, Miguel, Pablo, Julia, Peter
- Objetos rastreables: chair, exercise ball, table, folder, first aid kit, package, printer, keys, book, coffee machine

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
- Para store_in_memory: {{"key": "identificador", "value": "información"}}
- Para recall_from_memory: {{}} o {{"key": "identificador"}}
- Para count_objects: {{"object_type": "tipo"}}

CAPACIDADES AVANZADAS:
- MEMORIA: Usa store_in_memory/recall_from_memory para tareas multi-paso que requieren recordar información
- PERCEPCIÓN: Usa describe_environment para descripción completa del entorno
- CONTEO: Usa count_objects para contar objetos específicos
- INVENTARIOS: Combina navegación + describe_environment + store_in_memory

EJEMPLOS CORRECTOS:

Ejemplo 1 - Buscar y entregar mensaje:
Thought: Necesito ir a la conference room
Action: go_to_place
Action Input: {{"location": "conference room"}}
Observation: Éxito: El robot ha llegado a conference room.

Thought: Ahora debo buscar a Tomas
Action: find_person
Action Input: {{"name": "Tomas"}}
Observation: Éxito: Se encontró a Tomas.

Thought: Debo comunicar el mensaje
Action: talk
Action Input: {{"message": "la reunión comienza pronto"}}
Observation: Éxito: El mensaje fue dicho.

Thought: Ya completé la tarea - he encontrado a Tomas y entregado el mensaje
Final Answer: He ido a conference room, encontrado a Tomas y le he dicho el mensaje.

Ejemplo 2 - Tarea con memoria:
Thought: Necesito averiguar información y recordarla
Action: find_person
Action Input: {{"name": "Alice"}}
Observation: Éxito: Se encontró a Alice. Alice menciona que le gusta el café.

Thought: Debo guardar esta información
Action: store_in_memory
Action Input: {{"key": "preferencia_alice", "value": "Alice le gusta el café"}}
Observation: Éxito: Información almacenada.

Thought: Ahora debo volver al living room
Action: go_to_place
Action Input: {{"location": "living room"}}
Observation: Éxito: El robot ha llegado a living room.

Thought: Necesito recordar la información
Action: recall_from_memory
Action Input: {{"key": "preferencia_alice"}}
Observation: Alice le gusta el café

Thought: Ahora puedo comunicar la respuesta
Action: talk
Action Input: {{"message": "Alice le gusta el café"}}
Observation: Éxito: El mensaje fue dicho.

Thought: He completado la tarea multi-paso
Final Answer: Averigüé que a Alice le gusta el café y comuniqué la respuesta.

Ejemplo 3 - Buscar persona en otra ubicación:
Thought: Necesito buscar a David
Action: find_person
Action Input: {{"name": "David"}}
Observation: No se encontró a David. David no está aquí. David está en main entrance.

Thought: David está en main entrance, debo ir allá
Action: go_to_place
Action Input: {{"location": "main entrance"}}
Observation: Éxito: El robot ha llegado a main entrance.

Thought: Ahora busco a David aquí
Action: find_person
Action Input: {{"name": "David"}}
Observation: Éxito: Se encontró a David.

Thought: He encontrado a David, tarea completada
Final Answer: He encontrado a David en la puerta.

ESTRATEGIA PARA COMPLETAR TAREAS:
1. Si necesitas encontrar a alguien, primero búscalo en tu ubicación actual
2. Si no está, usa la información de la observación para saber dónde ir
3. Si te piden hablar con alguien, primero encuéntralo, luego usa 'talk'
4. NO uses 'listen' - en entorno simulado nadie responde
5. Si te piden ir a un lugar que no existe (ej: baño), indica que no conoces ese lugar y termina con Final Answer
6. SIEMPRE termina con "Final Answer:" cuando hayas completado la tarea

RESTRICCIONES:
- Solo usa herramientas de la lista
- NO inventes herramientas ni capacidades
- NO uses listen ni speech2text (no funcionan en simulación)
- SIEMPRE termina con Final Answer cuando completes la tarea

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
        )
        
        return agent_executor
    
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
                    annotations[arg_name] = int | None if not is_required else int
                    fields[arg_name] = Field(default=None) if not is_required else Field(...)
                elif arg_type == "float":
                    annotations[arg_name] = float | None if not is_required else float
                    fields[arg_name] = Field(default=None) if not is_required else Field(...)
                elif arg_type == "bool":
                    annotations[arg_name] = bool | None if not is_required else bool
                    fields[arg_name] = Field(default=None) if not is_required else Field(...)
                else:
                    annotations[arg_name] = str | None if not is_required else str
                    fields[arg_name] = Field(default=None) if not is_required else Field(...)

            ArgsModel = type(
                f"{tool_name}_args",
                (BaseModel,),
                {"__annotations__": annotations, **fields}
            )

            # 2) Wrapper que acepta `tool_input` (string/dict) y lo normaliza
            from ..service_adapter import normalize_action_input
            def make_wrapper(adapter_func=adapter_func, schema=ArgsModel, tool_name=tool_name):
                def wrapper(tool_input=None, **kwargs):
                    # Prioridad 1: tool_input ya es BaseModel/dict
                    if tool_input is not None and hasattr(tool_input, 'model_dump'):
                        kwargs = tool_input.model_dump()
                    elif tool_input is not None and isinstance(tool_input, dict):
                        kwargs = tool_input
                    elif tool_input is not None and isinstance(tool_input, str):
                        # Normaliza JSON/strings simples a kwargs con nombres correctos
                        kwargs = normalize_action_input(tool_name, tool_input)
                    elif kwargs:
                        # kwargs ya vienen; completamos faltantes por default si aplica
                        pass
                    else:
                        # Sin nada explícito => usa defaults (p.ej. recognize_face num_pics=3)
                        kwargs = {}

                    # Último toque: si faltan required, que explote acá con mensaje claro
                    _ = schema(**kwargs)
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

    def _evaluate_attempt(
        self, 
        task_description: str,
        output: Dict[str, Any], 
        intermediate_steps: List
    ) -> bool:
        """
        Evaluator: Determina si el intento fue exitoso.
        
        Criterios:
        1. El agente generó una respuesta final (Final Answer)
        2. La respuesta final no indica error catastrófico
        
        NOTA: No todas las acciones tienen que ser exitosas (exploración normal),
        lo importante es que el agente llegue a una conclusión razonada.
        """
        # Verificar que hay output con respuesta final
        if "output" not in output:
            return False
        
        output_text = str(output.get("output", ""))
        
        # El agente debe haber generado una respuesta final (no solo intermediate_steps)
        # Si hay output, significa que llegó a Final Answer
        if not output_text or len(output_text.strip()) < 10:
            return False
        
        # Verificar que no hay errores catastróficos en el output final
        output_lower = output_text.lower()
        if any(word in output_lower for word in ["error fatal", "imposible completar"]):
            return False
        
        # Si llegó hasta aquí, el intento fue exitoso
        # (el agente razonó, ejecutó acciones, y llegó a una conclusión)
        return True

    def _generate_reflection(
        self,
        task_description: str,
        attempt_number: int,
        output: Dict[str, Any],
        intermediate_steps: List,
        metrics_callback: Optional[MetricsCallbackHandler] = None
    ) -> str:
        """
        Self-Reflection: Genera una reflexión sobre qué salió mal y cómo mejorar.
        """
        print("\n--- 🤔 Generando Reflexión ---")        # Construir un resumen del intento fallido
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
5. ¿Por qué el agente no llegó a un "Final Answer" claro?
6. ¿Cómo se podría mejorar en el próximo intento?

ENTORNO SIMULADO - INFORMACIÓN CRÍTICA:
- Ubicaciones disponibles (CASA): living room, kitchen, bedroom, bathroom, gym, entrance hall, garden
- Ubicaciones disponibles (OFICINA): office, library, cafeteria, conference room, reception, lobby, break room, archive room, copy room, main entrance, parking lot, elevator, meeting room A, meeting room B, meeting room C, technical department, HR department, sales department, finance department
- Personas: Alice, Tomas, David, Maria, Carlos, Ana, Jorge, Richard, Laura, Sophia, Alex, Elena, Miguel, Pablo, Julia, Peter
- Objetos rastreables: chair, exercise ball, table, folder, first aid kit, package, printer, keys, book, coffee machine
- El robot PUEDE buscar a cualquiera de estas personas
- NO usar herramientas de voz: listen, speech2text (en simulación nadie responde)
- Es NORMAL que algunas búsquedas fallen (ej: buscar a Tomas en office cuando está en living room)
- El robot inicia en living room

CAPACIDADES DISPONIBLES:
- NAVEGACIÓN: go_to_place, move_to a cualquier ubicación listada
- COMUNICACIÓN: talk (hablar), find_person (buscar persona)
- MEMORIA: store_in_memory (guardar información), recall_from_memory (recuperar información)
- PERCEPCIÓN: describe_environment (describir entorno), count_objects (contar objetos)

ERRORES COMUNES A EVITAR:
- Repetir la misma acción infinitamente (ej: talk 10 veces seguidas)
- No terminar con "Final Answer" cuando se completa la tarea
- Intentar usar listen o speech2text
- Olvidar usar memoria en tareas multi-paso que requieren recordar información
- No usar describe_environment cuando se necesita información del entorno

Proporciona una reflexión concisa (2-4 oraciones) que ayude al robot a:
1. Identificar el error específico que causó el fallo
2. Sugerir una estrategia concreta para el próximo intento
3. Recordar que debe terminar con "Final Answer"

REFLEXIÓN:"""

        # Invocar LLM con callback si está disponible
        if metrics_callback:
            reflection_response = self.llm.invoke(
                reflection_prompt,
                config={"callbacks": [metrics_callback]}
            )
        else:
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
        
        # Crear callback global para acumular métricas de todos los intentos
        global_metrics_callback = MetricsCallbackHandler()
        
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
                
                # Ejecutar el intento con callback para métricas
                result = actor.invoke(
                    {"input": task_description, "reflections_context": reflections_context},
                    config={"callbacks": [global_metrics_callback]}
                )
                
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
                    
                    # Obtener métricas acumuladas de todos los intentos
                    llm_metrics = global_metrics_callback.get_summary()
                    
                    return {
                        "success": True,
                        "attempts": attempt,
                        "steps": len(intermediate_steps),
                        "trace": trace,
                        "all_attempts": all_attempts_trace,
                        "reflections": self.reflection_memory.copy(),
                        "execution_time": execution_time,
                        "architecture": "Reflexion",
                        "final_output": result.get("output", ""),
                        "llm_metrics": llm_metrics
                    }
                
                else:
                    # Fallo: Generar reflexión si quedan intentos
                    if attempt < self.max_attempts:
                        reflection = self._generate_reflection(
                            task_description, 
                            attempt, 
                            result, 
                            intermediate_steps,
                            metrics_callback=global_metrics_callback
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
        
        # Obtener métricas acumuladas de todos los intentos
        llm_metrics = global_metrics_callback.get_summary()
        
        return {
            "success": False,
            "attempts": self.max_attempts,
            "steps": 0,
            "trace": [f"Fallaron todos los {self.max_attempts} intentos"],
            "all_attempts": all_attempts_trace,
            "reflections": self.reflection_memory.copy(),
            "execution_time": execution_time,
            "architecture": "Reflexion",
            "llm_metrics": llm_metrics
        }
