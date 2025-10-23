import time
from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool

from .base_agent import BaseAgent
from ..service_adapter import get_tools_description

# --- 1. Definición de la Estructura del Plan ---

class ToolCall(BaseModel):
    """Define una única llamada a herramienta."""
    tool_name: str = Field(description="Nombre EXACTO de la herramienta (ej: 'talk', 'go_to_place', 'find_person')")
    arguments: dict = Field(description="Argumentos con NOMBRES EXACTOS de campos (ej: {'message': 'hola'}, {'location': 'cocina'})")

class Plan(BaseModel):
    """Define el plan completo como una lista de llamadas a herramientas."""
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
             "RESTRICCIONES IMPORTANTES:\n"
             "- Solo puedes usar las herramientas disponibles listadas abajo\n"
             "- Debes usar los nombres EXACTOS de herramientas y argumentos\n"
             "- NO inventes herramientas ni argumentos\n"
             "- Ubicaciones conocidas: cocina, sala, puerta\n"
             "- Personas conocidas: Tomas\n\n"
             "{tools_description}\n\n"
             "FORMATO DE RESPUESTA:\n"
             "Debes responder con un JSON con campo 'steps' (lista de llamadas).\n"
             "Cada paso debe tener:\n"
             "  - tool_name: Nombre EXACTO (ej: 'go_to_place', 'talk', 'find_person')\n"
             "  - arguments: Diccionario con CLAVES EXACTAS (ej: {{'location': 'cocina'}}, {{'message': 'hola'}})\n\n"
             "EJEMPLOS VÁLIDOS:\n"
             "{{\n"
             "  \"steps\": [\n"
             "    {{\"tool_name\": \"go_to_place\", \"arguments\": {{\"location\": \"cocina\"}}}},\n"
             "    {{\"tool_name\": \"find_person\", \"arguments\": {{\"name\": \"Tomas\"}}}},\n"
             "    {{\"tool_name\": \"talk\", \"arguments\": {{\"message\": \"hola, la comida está lista\"}}}}\n"
             "  ]\n"
             "}}\n\n"
             "EJEMPLOS INVÁLIDOS (NO HAGAS ESTO):\n"
             "- {{\"tool_name\": \"move\", ...}}  ❌ (no existe 'move', usa 'go_to_place' o 'move_to')\n"
             "- {{\"arguments\": {{\"place\": \"cocina\"}}}}  ❌ (usa 'location', no 'place')\n"
             "- {{\"arguments\": {{\"text\": \"hola\"}}}}  ❌ (usa 'message', no 'text')\n"
             "- {{\"tool_name\": \"ir_a\", ...}}  ❌ (nombres en inglés)"),
            ("human", "Tarea: {task}")
        ])
        
        llm_with_planner = self.llm.with_structured_output(Plan)
        
        return prompt_template | llm_with_planner

    def _generate_plan(self, task_description: str) -> Plan:
        """Paso 1: Generar el plan."""
        print("--- 🧠 Generando Plan ---")
        
        plan = self.planner_chain.invoke({
            "task": task_description,
            "tools_description": get_tools_description()
        })
        
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
                
                # Si falló, abortar
                if not result["ok"]:
                    print("❌ Paso fallido, abortando plan.")
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
        
        try:
            # 1. Planear
            plan = self._generate_plan(task_description)
            
            # 2. Actuar
            execution_trace = self._execute_plan(plan)
            
            # 3. Determinar éxito: todos los pasos ejecutados sin fallos
            success = (
                len(execution_trace) == len(plan.steps) and 
                all("[✓]" in step for step in execution_trace)
            )

            return {
                "success": success,
                "steps": len(execution_trace),
                "trace": execution_trace,
                "execution_time": time.time() - start_time,
                "architecture": "PlanThenAct"
            }
        
        except Exception as e:
            print(f"❌ Error fatal en PlanThenAct: {e}")
            return {
                "success": False,
                "steps": 0,
                "trace": [f"Error fatal durante la planificación: {e}"],
                "execution_time": time.time() - start_time,
                "architecture": "PlanThenAct"
            }