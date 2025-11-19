# src/benchmark_agent/task_utils.py

"""
Utilidades para análisis y procesamiento de tareas.
"""

from typing import Dict, Any, List
import re


# Palabras clave que indican tipo de entorno
OFFICE_KEYWORDS = {
    "office", "reception", "elevator", "cafeteria", "library", "conference", 
    "meeting room", "lobby", "archive", "copy room", "main entrance", 
    "parking lot", "technical department", "HR department", "sales department",
    "finance department", "break room"
}

HOUSE_KEYWORDS = {
    "living room", "kitchen", "bedroom", "bathroom", "gym", "entrance hall", "garden"
}


def detect_environment_type(task_description: str) -> str:
    """
    Detecta el tipo de entorno requerido basándose en la descripción de la tarea.
    
    Args:
        task_description: Descripción de la tarea
        
    Returns:
        "office", "house", o "mixed"
    """
    task_lower = task_description.lower()
    
    # Contar coincidencias
    office_count = sum(1 for keyword in OFFICE_KEYWORDS if keyword in task_lower)
    house_count = sum(1 for keyword in HOUSE_KEYWORDS if keyword in task_lower)
    
    if office_count > 0 and house_count > 0:
        return "mixed"
    elif office_count > 0:
        return "office"
    elif house_count > 0:
        return "house"
    else:
        # Default: mixed para tareas genéricas
        return "mixed"


def extract_mentioned_people(task_description: str, available_people: List[str]) -> List[str]:
    """
    Extrae nombres de personas mencionadas en la descripción de la tarea.
    
    Args:
        task_description: Descripción de la tarea
        available_people: Lista de personas disponibles
        
    Returns:
        Lista de nombres encontrados
    """
    mentioned = []
    task_lower = task_description.lower()
    
    for person in available_people:
        # Buscar el nombre exacto (case-insensitive)
        pattern = r'\b' + re.escape(person.lower()) + r'\b'
        if re.search(pattern, task_lower):
            mentioned.append(person)
    
    return mentioned


def extract_mentioned_locations(task_description: str) -> List[str]:
    """
    Extrae ubicaciones mencionadas en la descripción de la tarea.
    
    Args:
        task_description: Descripción de la tarea
        
    Returns:
        Lista de ubicaciones encontradas
    """
    all_locations = list(OFFICE_KEYWORDS | HOUSE_KEYWORDS)
    mentioned = []
    task_lower = task_description.lower()
    
    for location in all_locations:
        if location in task_lower:
            mentioned.append(location)
    
    return mentioned


def suggest_context_requirements(task: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sugiere requisitos de contexto basándose en la tarea.
    
    Args:
        task: Diccionario de tarea
        
    Returns:
        Diccionario con requisitos sugeridos:
        {
            "environment_type": str,
            "required_locations": List[str],
            "mentioned_people": List[str],
            "min_people": int,
            "min_objects": int
        }
    """
    from .world_state_generator import ALL_PEOPLE
    
    task_desc = task.get("task", "")
    
    # Detectar tipo de entorno
    env_type = task.get("environment_type")
    if not env_type:
        env_type = detect_environment_type(task_desc)
    
    # Extraer ubicaciones y personas mencionadas
    required_locations = extract_mentioned_locations(task_desc)
    mentioned_people = extract_mentioned_people(task_desc, ALL_PEOPLE)
    
    # Estimar requisitos mínimos
    min_people = max(len(mentioned_people), 3)  # Al menos 3 personas
    min_objects = 3  # Al menos 3 objetos
    
    # Aumentar si la tarea es compleja
    if task.get("category") in ["multi_person", "memory_reasoning", "complex_multi_step"]:
        min_people = max(min_people, 6)
        min_objects = max(min_objects, 5)
    
    return {
        "environment_type": env_type,
        "required_locations": required_locations,
        "mentioned_people": mentioned_people,
        "min_people": min_people,
        "min_objects": min_objects
    }


def validate_context_for_task(task: Dict[str, Any], world_state) -> Dict[str, Any]:
    """
    Valida que un WorldState sea adecuado para una tarea.
    
    Args:
        task: Diccionario de tarea
        world_state: Instancia de WorldState
        
    Returns:
        Diccionario con:
        {
            "valid": bool,
            "missing_locations": List[str],
            "missing_people": List[str],
            "warnings": List[str]
        }
    """
    requirements = suggest_context_requirements(task)
    
    missing_locations = []
    missing_people = []
    warnings = []
    
    # Verificar ubicaciones requeridas
    for loc in requirements["required_locations"]:
        if loc not in world_state.available_locations:
            missing_locations.append(loc)
    
    # Verificar personas mencionadas
    for person in requirements["mentioned_people"]:
        if person not in world_state.people_locations:
            missing_people.append(person)
    
    # Verificar cantidad mínima de personas
    if len(world_state.people_locations) < requirements["min_people"]:
        warnings.append(
            f"Se recomiendan al menos {requirements['min_people']} personas, "
            f"pero solo hay {len(world_state.people_locations)}"
        )
    
    # Verificar tipo de entorno
    env_type = requirements["environment_type"]
    if env_type == "office":
        office_locs = [loc for loc in world_state.available_locations 
                      if loc in OFFICE_KEYWORDS]
        if len(office_locs) < 3:
            warnings.append(
                f"Tarea requiere entorno de oficina pero solo hay {len(office_locs)} "
                f"ubicaciones de oficina disponibles"
            )
    
    valid = len(missing_locations) == 0 and len(missing_people) == 0
    
    return {
        "valid": valid,
        "missing_locations": missing_locations,
        "missing_people": missing_people,
        "warnings": warnings
    }
