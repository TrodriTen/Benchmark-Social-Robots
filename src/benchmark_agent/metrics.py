"""
Módulo de métricas extendidas para benchmark de arquitecturas agentivas.

Define:
1. Categorías de resultado (success/partial/fail/lack-of-capabilities)
2. Métricas de eficiencia (tokens, latencia, replannings)
3. Funciones de análisis y clasificación de resultados
"""

from typing import Dict, Any, List, Optional
from enum import Enum
import time


class ResultCategory(str, Enum):
    """
    Categorías de resultado según el protocolo de evaluación.
    """
    SUCCESS = "success"                      # Tarea completada exitosamente
    PARTIAL = "partial"                       # Tarea parcialmente completada
    FAIL = "fail"                            # Tarea fallida (error o resultado incorrecto)
    LACK_OF_CAPABILITIES = "lack_of_capabilities"  # Robot no tiene capacidades para la tarea


class TaskCategory(str, Enum):
    """
    Taxonomía de tareas para análisis estructurado.
    """
    NAVIGATION_SIMPLE = "navigation_simple"           # Ir a un lugar conocido
    SEARCH_INTERACTION = "search_interaction"         # Buscar persona + interactuar
    MULTI_HOP_REASONING = "multi_hop_reasoning"       # Razonamiento multi-paso
    UNCERTAINTY_HANDLING = "uncertainty_handling"     # Manejo de información incompleta
    OBJECT_MANIPULATION = "object_manipulation"       # Manipulación de objetos
    UNKNOWN_LOCATION = "unknown_location"             # Navegar a lugar desconocido


class MetricsCollector:
    """
    Colector de métricas detalladas durante la ejecución de tareas.
    """
    
    def __init__(self):
        self.llm_calls: List[Dict[str, Any]] = []
        self.replannings: int = 0
        self.total_tokens: int = 0
        self.total_latency: float = 0.0
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
    
    def start_execution(self):
        """Marca el inicio de la ejecución."""
        self.start_time = time.time()
    
    def end_execution(self):
        """Marca el fin de la ejecución."""
        self.end_time = time.time()
    
    def record_llm_call(
        self, 
        tokens_input: int = 0, 
        tokens_output: int = 0,
        latency: float = 0.0,
        model: str = "unknown",
        call_type: str = "generation"
    ):
        """
        Registra una llamada al LLM.
        
        Args:
            tokens_input: Tokens en el prompt
            tokens_output: Tokens generados
            latency: Tiempo de respuesta en segundos
            model: Nombre del modelo usado
            call_type: Tipo de llamada (generation, reflection, planning, etc.)
        """
        self.llm_calls.append({
            "tokens_input": tokens_input,
            "tokens_output": tokens_output,
            "tokens_total": tokens_input + tokens_output,
            "latency": latency,
            "model": model,
            "call_type": call_type
        })
        self.total_tokens += (tokens_input + tokens_output)
        self.total_latency += latency
    
    def record_replanning(self):
        """Registra un evento de replanificación."""
        self.replannings += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Retorna resumen de métricas recolectadas.
        
        Returns:
            Diccionario con todas las métricas
        """
        execution_time = 0.0
        if self.start_time and self.end_time:
            execution_time = self.end_time - self.start_time
        
        return {
            "llm_calls_count": len(self.llm_calls),
            "total_tokens": self.total_tokens,
            "total_latency": round(self.total_latency, 3),
            "execution_time": round(execution_time, 3),
            "replannings": self.replannings,
            "llm_calls_detail": self.llm_calls,
            "avg_tokens_per_call": round(self.total_tokens / len(self.llm_calls), 1) if self.llm_calls else 0,
            "avg_latency_per_call": round(self.total_latency / len(self.llm_calls), 3) if self.llm_calls else 0
        }


def classify_result(
    task_description: str,
    output: Dict[str, Any],
    intermediate_steps: List
) -> ResultCategory:
    """
    Clasifica el resultado de una tarea en una de las categorías definidas.
    
    Args:
        task_description: Descripción de la tarea solicitada
        output: Output del agente
        intermediate_steps: Pasos intermedios ejecutados
        
    Returns:
        Categoría de resultado
    """
    # Si no hay output, es fallo
    if not output or "output" not in output:
        return ResultCategory.FAIL
    
    output_text = str(output.get("output", "")).lower()
    
    # Detectar falta de capacidades
    lack_patterns = [
        "no conozco",
        "no tengo acceso",
        "no puedo",
        "no está disponible",
        "no sé cómo",
        "desconocido"
    ]
    
    if any(pattern in output_text for pattern in lack_patterns):
        # Verificar si es legítimo (ej: baño no existe) vs falta de capacidad real
        if any(word in task_description.lower() for word in ["baño", "bathroom", "jardín", "garage"]):
            # Lugar que no existe -> es éxito (reconoció limitación correctamente)
            return ResultCategory.SUCCESS
        else:
            return ResultCategory.LACK_OF_CAPABILITIES
    
    # Detectar éxito completo
    success_patterns = [
        "completé la tarea",
        "he encontrado",
        "he llegado",
        "he dicho",
        "he comunicado",
        "tarea completada"
    ]
    
    if any(pattern in output_text for pattern in success_patterns):
        # Verificar que hubo acciones exitosas
        if intermediate_steps:
            successful_steps = sum(
                1 for _, obs in intermediate_steps
                if "éxito" in str(obs).lower()
            )
            if successful_steps > 0:
                return ResultCategory.SUCCESS
    
    # Detectar éxito parcial
    # Si ejecutó algunas acciones exitosas pero no completó todo
    if intermediate_steps:
        successful_steps = sum(
            1 for _, obs in intermediate_steps
            if "éxito" in str(obs).lower()
        )
        total_steps = len(intermediate_steps)
        
        if 0 < successful_steps < total_steps:
            return ResultCategory.PARTIAL
        elif successful_steps == total_steps and total_steps > 0:
            return ResultCategory.SUCCESS
    
    # Detectar fallo
    fail_patterns = [
        "error fatal",
        "falló",
        "no se pudo",
        "imposible"
    ]
    
    if any(pattern in output_text for pattern in fail_patterns):
        return ResultCategory.FAIL
    
    # Default: si hay output pero no está claro -> parcial
    if len(output_text.strip()) > 10:
        return ResultCategory.PARTIAL
    
    return ResultCategory.FAIL


def classify_task(task_description: str) -> TaskCategory:
    """
    Clasifica una tarea en una categoría de la taxonomía.
    
    Args:
        task_description: Descripción de la tarea
        
    Returns:
        Categoría de tarea
    """
    desc_lower = task_description.lower()
    
    # Navegación simple
    if any(pattern in desc_lower for pattern in ["ve a", "go to", "navega a", "dirígete a"]):
        # Verificar si es lugar desconocido
        if any(place in desc_lower for place in ["baño", "bathroom", "jardín", "garage", "patio"]):
            return TaskCategory.UNKNOWN_LOCATION
        return TaskCategory.NAVIGATION_SIMPLE
    
    # Búsqueda + interacción
    if any(pattern in desc_lower for pattern in ["busca a", "find", "dile", "tell", "pregunta"]):
        # Si tiene múltiples pasos -> multi-hop
        if " y " in desc_lower or " luego " in desc_lower or " después " in desc_lower:
            return TaskCategory.MULTI_HOP_REASONING
        return TaskCategory.SEARCH_INTERACTION
    
    # Manipulación de objetos
    if any(pattern in desc_lower for pattern in ["toma", "agarra", "pick up", "coloca", "place"]):
        return TaskCategory.OBJECT_MANIPULATION
    
    # Manejo de incertidumbre
    if any(pattern in desc_lower for pattern in ["si no", "en caso de", "intenta", "verifica"]):
        return TaskCategory.UNCERTAINTY_HANDLING
    
    # Default: multi-hop si tiene conectores
    if " y " in desc_lower or " luego " in desc_lower:
        return TaskCategory.MULTI_HOP_REASONING
    
    return TaskCategory.NAVIGATION_SIMPLE


def calculate_cost_estimate(
    total_tokens: int,
    model: str = "gpt-4o-mini"
) -> float:
    """
    Estima el costo en USD basado en tokens consumidos.
    
    Args:
        total_tokens: Total de tokens (input + output)
        model: Nombre del modelo
        
    Returns:
        Costo estimado en USD
    """
    # Precios aproximados (USD por millón de tokens, combinado input+output promedio)
    pricing = {
        "gpt-4o-mini": 0.30,  # $0.15 input + $0.60 output (promedio ~$0.30)
        "gpt-4o": 7.50,        # $2.50 input + $10.00 output (promedio ~$7.50)
        "gpt-4-turbo": 15.0,   # $10 input + $30 output (promedio ~$15)
        "gpt-3.5-turbo": 1.0,  # ~$1 promedio
        "qwen2.5:7b": 0.0,     # Local, sin costo
        "ollama": 0.0,         # Local, sin costo
    }
    
    # Buscar precio por modelo
    cost_per_million = 0.0
    for key, price in pricing.items():
        if key in model.lower():
            cost_per_million = price
            break
    
    # Calcular costo
    cost_usd = (total_tokens / 1_000_000) * cost_per_million
    return round(cost_usd, 6)


def generate_metrics_report(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Genera un reporte completo de métricas para un conjunto de resultados.
    
    Args:
        results: Lista de resultados de benchmark
        
    Returns:
        Diccionario con reporte de métricas agregadas
    """
    if not results:
        return {}
    
    # Agregaciones
    total_tasks = len(results)
    
    # Contar por categoría de resultado
    categories_count = {}
    for r in results:
        cat = r.get("result_category", "unknown")
        categories_count[cat] = categories_count.get(cat, 0) + 1
    
    # Métricas de eficiencia
    total_tokens = sum(r.get("metrics", {}).get("total_tokens", 0) for r in results)
    total_time = sum(r.get("execution_time", 0) for r in results)
    total_steps = sum(r.get("steps", 0) for r in results)
    total_replannings = sum(r.get("metrics", {}).get("replannings", 0) for r in results)
    total_llm_calls = sum(r.get("metrics", {}).get("llm_calls_count", 0) for r in results)
    
    # Promedios
    avg_tokens = round(total_tokens / total_tasks, 1) if total_tasks > 0 else 0
    avg_time = round(total_time / total_tasks, 2) if total_tasks > 0 else 0
    avg_steps = round(total_steps / total_tasks, 1) if total_tasks > 0 else 0
    avg_replannings = round(total_replannings / total_tasks, 2) if total_tasks > 0 else 0
    
    # Costo estimado
    model = results[0].get("model", "unknown") if results else "unknown"
    total_cost = calculate_cost_estimate(total_tokens, model)
    
    return {
        "total_tasks": total_tasks,
        "result_categories": categories_count,
        "success_rate": round((categories_count.get("success", 0) / total_tasks * 100), 1) if total_tasks > 0 else 0,
        "efficiency_metrics": {
            "total_tokens": total_tokens,
            "avg_tokens_per_task": avg_tokens,
            "total_execution_time": round(total_time, 2),
            "avg_execution_time": avg_time,
            "total_steps": total_steps,
            "avg_steps_per_task": avg_steps,
            "total_replannings": total_replannings,
            "avg_replannings_per_task": avg_replannings,
            "total_llm_calls": total_llm_calls
        },
        "cost_estimate": {
            "total_usd": total_cost,
            "per_task_usd": round(total_cost / total_tasks, 6) if total_tasks > 0 else 0,
            "model": model
        }
    }
