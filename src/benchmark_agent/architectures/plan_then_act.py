import time
from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field, ConfigDict
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool

from .base_agent import BaseAgent
from ..service_adapter import get_tools_description
from ..callbacks import MetricsCallbackHandler

# --- 1. Definición de la Estructura del Plan ---

class ToolCall(BaseModel):
    """Define una única llamada a herramienta."""
    model_config = ConfigDict(extra='forbid')  # Esto añade additionalProperties: false
    
    tool_name: str = Field(description="Nombre EXACTO de la herramienta (ej: 'talk', 'go_to_place', 'find_person')")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Argumentos con NOMBRES EXACTOS de campos (ej: {'message': 'hola'}, {'location': 'cocina'})")

class Plan(BaseModel):
    """Define el plan completo como una lista de llamadas a herramientas."""
    model_config = ConfigDict(extra='forbid')  # Esto añade additionalProperties: false
    
    steps: List[ToolCall] = Field(description="Lista ordenada de pasos para completar la tarea.")

# --- 2. Implementación del Agente ---

class PlanThenActAgent(BaseAgent):
    """
    Implementación de la arquitectura 'Plan-then-Act'.
    Paso 1: El LLM genera un plan completo (JSON).
    Paso 2: Python ejecuta ese plan secuencialmente usando adapters.
    """
    
    def __init__(self, llm: BaseChatModel, tools: List[BaseTool] = None):
        super().__init__(llm, tools)
        self.planner_chain = self._create_planner_chain()

    def _create_planner_chain(self):
        """Crea la cadena de planificación usando el LLM con salida estructurada."""
        
        tools_desc = get_tools_description()
        
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", 
             "Eres un planificador experto para un robot social llamado Pepper. "
             "Tu objetivo es crear un plan paso a paso para completar la tarea del usuario.\n\n"
             "INFORMACIÓN DEL ENTORNO:\n"
             "- Robot inicia en: living room\n"
             "- Ubicaciones disponibles (CASA): living room, kitchen, bedroom, bathroom, gym, entrance hall, garden\n"
             "- Ubicaciones disponibles (OFICINA): office, library, cafeteria, conference room, reception, lobby, break room, archive room, copy room, main entrance, parking lot, elevator, meeting room A, meeting room B, meeting room C, technical department, HR department, sales department, finance department\n"
             "- Personas: Alice, Tomas, David, Maria, Carlos, Ana, Jorge, Richard, Laura, Sophia, Alex, Elena, Miguel, Pablo, Julia, Peter\n"
             "- Objetos rastreables: chair, exercise ball, table, folder, first aid kit, package, printer, keys, book, coffee machine\n\n"
             "ESTRATEGIA DE PLANIFICACIÓN:\n"
             "- Si necesitas encontrar a alguien, primero ve a su ubicación o usa 'find_person'\n"
             "- Usa 'ask_person_location' si no sabes dónde está alguien\n"
             "- Para tareas multi-paso que requieren recordar información, usa 'store_in_memory' y 'recall_from_memory'\n"
             "- Para inventarios o descripciones, usa 'describe_environment' y guarda resultados con 'store_in_memory'\n"
             "- Para contar objetos, usa 'count_objects' en cada ubicación necesaria\n"
             "- Si una ubicación no existe, usa 'talk' para comunicar la limitación\n\n"
             "CAPACIDADES AVANZADAS:\n"
             "- MEMORIA: store_in_memory({{'key': 'identificador', 'value': 'información'}}), recall_from_memory({{'key': 'identificador'}})\n"
             "- PERCEPCIÓN: describe_environment({{}}), count_objects({{'object_type': 'tipo'}})\n"
             "- NAVEGACIÓN: go_to_place({{'location': 'lugar'}}), move_to({{'location': 'lugar'}})\n"
             "- COMUNICACIÓN: talk({{'message': 'texto'}}), find_person({{'name': 'persona'}})\n\n"
             "RESTRICCIONES IMPORTANTES:\n"
             "- Solo puedes usar las herramientas disponibles listadas abajo\n"
             "- Debes usar los nombres EXACTOS de herramientas y argumentos\n"
             "- NO inventes herramientas ni argumentos\n\n"
             "{tools_description}\n\n"
             "FORMATO DE RESPUESTA:\n"
             "Debes responder con un JSON con campo 'steps' (lista de llamadas).\n"
             "Cada paso debe tener:\n"
             "  - tool_name: Nombre EXACTO (ej: 'go_to_place', 'talk', 'find_person', 'store_in_memory')\n"
             "  - arguments: Diccionario con CLAVES EXACTAS (ej: {{'location': 'kitchen'}}, {{'message': 'hola'}}, {{'key': 'dato', 'value': 'info'}})\n\n"
             "EJEMPLOS VÁLIDOS:\n"
             "Ejemplo 1 - Tarea simple:\n"
             "{{\n"
             "  \"steps\": [\n"
             "    {{\"tool_name\": \"go_to_place\", \"arguments\": {{\"location\": \"conference room\"}}}},\n"
             "    {{\"tool_name\": \"find_person\", \"arguments\": {{\"name\": \"Tomas\"}}}},\n"
             "    {{\"tool_name\": \"talk\", \"arguments\": {{\"message\": \"la reunión comienza pronto\"}}}}\n"
             "  ]\n"
             "}}\n\n"
             "Ejemplo 2 - Tarea con memoria:\n"
             "{{\n"
             "  \"steps\": [\n"
             "    {{\"tool_name\": \"find_person\", \"arguments\": {{\"name\": \"Alice\"}}}},\n"
             "    {{\"tool_name\": \"store_in_memory\", \"arguments\": {{\"key\": \"respuesta_alice\", \"value\": \"Alice dice que le gusta el café\"}}}},\n"
             "    {{\"tool_name\": \"go_to_place\", \"arguments\": {{\"location\": \"living room\"}}}},\n"
             "    {{\"tool_name\": \"recall_from_memory\", \"arguments\": {{\"key\": \"respuesta_alice\"}}}},\n"
             "    {{\"tool_name\": \"talk\", \"arguments\": {{\"message\": \"Alice le gusta el café\"}}}}\n"
             "  ]\n"
             "}}\n\n"
             "EJEMPLOS INVÁLIDOS (NO HAGAS ESTO):\n"
             "- {{\"tool_name\": \"move\", ...}}  ❌ (no existe 'move', usa 'go_to_place' o 'move_to')\n"
             "- {{\"arguments\": {{\"place\": \"kitchen\"}}}}  ❌ (usa 'location', no 'place')\n"
             "- {{\"arguments\": {{\"text\": \"hola\"}}}}  ❌ (usa 'message', no 'text')\n"
             "- {{\"tool_name\": \"ir_a\", ...}}  ❌ (nombres en inglés)"),
            ("human", "Tarea: {task}")
        ])
        
        # Usar method="function_calling" para compatibilidad con Azure OpenAI
        llm_with_planner = self.llm.with_structured_output(Plan, method="function_calling")
        
        return prompt_template | llm_with_planner

    def _generate_plan(self, task_description: str, metrics_callback=None) -> Plan:
        """Paso 1: Generar el plan."""
        print("--- 🧠 Generando Plan ---")
        
        # Invocar con callback si se proporciona
        invoke_args = {
            "task": task_description,
            "tools_description": get_tools_description()
        }
        
        if metrics_callback:
            plan = self.planner_chain.invoke(
                invoke_args,
                config={"callbacks": [metrics_callback]}
            )
        else:
            plan = self.planner_chain.invoke(invoke_args)
        
        print(f"--- ✅ Plan Generado: {len(plan.steps)} pasos ---")
        for i, step in enumerate(plan.steps, 1):
            print(f"  {i}. {step.tool_name}({step.arguments})")
        
        return plan

    def _execute_plan(self, plan: Plan) -> List[str]:
        """Paso 2: Ejecutar el plan usando adapters."""
        print("--- 🚀 Ejecutando Plan ---")
        execution_trace = []
        
        for i, step in enumerate(plan.steps):
            print(f"\nPaso {i+1}/{len(plan.steps)}: {step.tool_name}({step.arguments})")
            
            # Verificar que la herramienta existe
            if step.tool_name not in self.adapters:
                result = {
                    "ok": False,
                    "obs": f"Error: Herramienta '{step.tool_name}' no encontrada.",
                    "data": {}
                }
                print(f"❌ {result['obs']}")
                execution_trace.append(f"Paso {i+1} [Fallo]: {step.tool_name} -> {result['obs']}")
                break  # Abortar plan
            
            # Obtener función adaptadora
            adapter_func = self.adapters[step.tool_name]
            
            try:
                # Ejecutar con normalización de resultado
                result = adapter_func(**step.arguments)
                
                status = "✓" if result["ok"] else "✗"
                print(f"{status} {result['obs']}")
                
                execution_trace.append(
                    f"Paso {i+1} [{status}]: {step.tool_name}({step.arguments}) -> {result['obs']}"
                )
                
                # Si falló con información útil (ej: "Tomas está en sala"), NO abortar
                # Solo abortar si es un error fatal sin información útil
                if not result["ok"]:
                    obs_lower = result['obs'].lower()
                    # Si el mensaje contiene información de ubicación, es útil y podemos continuar
                    if "está en" in obs_lower or "se encuentra en" in obs_lower:
                        print("⚠️  Paso falló pero obtuvo información útil, continuando...")
                    else:
                        print("❌ Paso fallido sin información útil, abortando plan.")
                        break
            
            except Exception as e:
                result = {
                    "ok": False,
                    "obs": f"Excepción: {str(e)}",
                    "data": {}
                }
                print(f"❌ {result['obs']}")
                execution_trace.append(f"Paso {i+1} [Excepción]: {step.tool_name} -> {result['obs']}")
                break  # Abortar

        print("--- 🏁 Ejecución Completa ---")
        return execution_trace

    def run(self, task_description: str) -> Dict[str, Any]:
        """Implementación del método 'run' para PlanThenAct."""
        start_time = time.time()
        
        # Crear callback handler para capturar métricas
        metrics_callback = MetricsCallbackHandler()
        
        try:
            # 1. Planear (con callback para medir LLM)
            plan = self._generate_plan(task_description, metrics_callback)
            
            # 2. Actuar
            execution_trace = self._execute_plan(plan)
            
            # Convertir el plan a formato serializable para JSON
            plan_dict = [
                {
                    "tool_name": step.tool_name,
                    "arguments": step.arguments
                }
                for step in plan.steps
            ]
            
            # 3. Determinar éxito: todos los pasos ejecutados sin fallos
            success = (
                len(execution_trace) == len(plan.steps) and 
                all("[✓]" in step for step in execution_trace)
            )
            
            # Obtener métricas del callback
            metrics = metrics_callback.get_summary()
            
            print(f"\n📊 Métricas: {metrics['llm_calls_count']} llamadas LLM, {metrics['total_tokens']} tokens")

            return {
                "success": success,
                "steps": len(execution_trace),
                "plan": plan_dict,  # Plan generado antes de ejecutar
                "trace": execution_trace,
                "execution_time": time.time() - start_time,
                "architecture": "PlanThenAct",
                "metrics": metrics
            }
        
        except Exception as e:
            print(f"❌ Error fatal en PlanThenAct: {e}")
            
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
            
            return {
                "success": False,
                "steps": 0,
                "plan": [],  # No se pudo generar plan
                "trace": [f"Error fatal durante la planificación: {e}"],
                "execution_time": time.time() - start_time,
                "architecture": "PlanThenAct",
                "metrics": metrics
            }