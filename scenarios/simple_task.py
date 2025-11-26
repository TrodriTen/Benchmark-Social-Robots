# scenarios/simple_tasks.py

# Lista de tareas para el benchmark adaptadas a los lugares REALES del mapa de navegación ROS
# Lugares disponibles en el mapa: ["init", "kitchen", "bedroom", "gym", "sofa", "dinner_table"]
# Herramientas disponibles: Navigation (go_to_location) y Perception (find_object, count_objects, view_description, etc)
# NO usar: speak, listen (speech), ask_for_object, give_object (manipulation)

SCENARIO_LIST = [
    {
        "id": "task_001",
        "description": "Ve a kitchen."
    },
    {
        "id": "task_002",
        "description": "Ve a bedroom."
    },
    {
        "id": "task_003",
        "description": "Ve a init.", 
    },
    {
        "id": "task_004",
        "description": "Ve a sofa.",
    },
    {
        "id": "task_005",
        "description": "Ve a kitchen y luego ve a bedroom.",
    },
    {
        "id": "task_006",
        "description": "Ve a init, luego a kitchen.",
    },
    {
        "id": "task_007",
        "description": "Busca un objeto chair.",
    },
    {
        "id": "task_008",
        "description": "Ve a kitchen y busca dinner_table.",
    },
    {
        "id": "task_009",
        "description": "Cuenta cuántos objetos de tipo person hay.",
    },
    {
        "id": "task_010",
        "description": "Ve a bedroom, luego regresa a init.",
    }
]