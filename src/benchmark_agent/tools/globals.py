
# ==============================================================================
# APPLICATION CONFIGURATION
# ==============================================================================
# Initial settings and available locations
# NOTA: Los lugares deben coincidir con los del mapa de navegación ROS
# Lugares disponibles en el grafo de navegación: house_door, kitchen, living_room, bedroom, dining, etc.
global initial_location
initial_location = "init"

global config
config = {"configurable": {"langgraph_user_id": "user"}, "recursion_limit": 25}

global places
places = ["init", "kitchen", "bedroom", "gym", "sofa", "dinner_table"]
