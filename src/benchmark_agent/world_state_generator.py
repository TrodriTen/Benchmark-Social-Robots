# src/benchmark_agent/world_state_generator.py

"""
Generador de estados del mundo variables para testing.
Permite crear contextos aleatorios con diferentes ubicaciones de personas y objetos.
"""

import random
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from copy import deepcopy


# ============================================================================
# CONFIGURACIÓN DEL MUNDO
# ============================================================================

# Ubicaciones disponibles por tipo
HOUSE_LOCATIONS = [
    "living room",
    "kitchen",
    "bedroom",
    "bathroom",
    "gym",
    "entrance hall",
    "garden"
]

OFFICE_LOCATIONS = [
    "office",
    "library",
    "cafeteria",
    "conference room",
    "reception",
    "lobby",
    "break room",
    "archive room",
    "copy room",
    "main entrance",
    "parking lot",
    "elevator",
    "meeting room A",
    "meeting room B",
    "meeting room C",
    "technical department",
    "HR department",
    "sales department",
    "finance department"
]

ALL_LOCATIONS = HOUSE_LOCATIONS + OFFICE_LOCATIONS

# Personas disponibles
ALL_PEOPLE = [
    "Alice", "Tomas", "David", "Maria", "Carlos", "Ana", "Jorge", "Richard",
    "Laura", "Sophia", "Alex", "Elena", "Miguel", "Pablo", "Julia", "Peter"
]

# Objetos rastreables
ALL_OBJECTS = [
    "chair", "exercise ball", "table", "folder", "first aid kit", 
    "package", "printer", "keys", "book", "coffee machine"
]


@dataclass
class WorldState:
    """Representa el estado del mundo en un momento dado."""
    robot_location: str
    people_locations: Dict[str, str]  # persona -> ubicación
    objects_locations: Dict[str, str]  # objeto -> ubicación
    available_locations: List[str]
    
    def get_people_in_location(self, location: str) -> List[str]:
        """Retorna lista de personas en una ubicación."""
        return [person for person, loc in self.people_locations.items() if loc == location]
    
    def get_objects_in_location(self, location: str) -> List[str]:
        """Retorna lista de objetos en una ubicación."""
        return [obj for obj, loc in self.objects_locations.items() if loc == location]
    
    def get_person_location(self, person_name: str) -> Optional[str]:
        """Retorna la ubicación de una persona."""
        return self.people_locations.get(person_name)
    
    def get_object_location(self, object_name: str) -> Optional[str]:
        """Retorna la ubicación de un objeto."""
        return self.objects_locations.get(object_name)
    
    def to_dict(self) -> Dict:
        """Convierte el estado a diccionario."""
        return {
            "robot_location": self.robot_location,
            "people_locations": self.people_locations.copy(),
            "objects_locations": self.objects_locations.copy(),
            "available_locations": self.available_locations.copy()
        }
    
    def describe(self) -> str:
        """Genera descripción textual del estado."""
        lines = [
            f"Robot location: {self.robot_location}",
            f"\nAvailable locations ({len(self.available_locations)}):",
            f"  {', '.join(self.available_locations)}",
            f"\nPeople locations ({len(self.people_locations)}):"
        ]
        for person, loc in sorted(self.people_locations.items()):
            lines.append(f"  - {person}: {loc}")
        
        lines.append(f"\nObjects locations ({len(self.objects_locations)}):")
        for obj, loc in sorted(self.objects_locations.items()):
            lines.append(f"  - {obj}: {loc}")
        
        return "\n".join(lines)


class WorldStateGenerator:
    """Genera estados del mundo variables para testing."""
    
    def __init__(self, seed: Optional[int] = None):
        """
        Args:
            seed: Semilla para reproducibilidad (opcional)
        """
        self.seed = seed
        if seed is not None:
            random.seed(seed)
    
    def generate_random_state(
        self,
        environment_type: str = "mixed",  # "house", "office", "mixed"
        num_people: Optional[int] = None,
        num_objects: Optional[int] = None,
        robot_start_location: Optional[str] = None
    ) -> WorldState:
        """
        Genera un estado aleatorio del mundo.
        
        Args:
            environment_type: Tipo de entorno ("house", "office", "mixed")
            num_people: Número de personas (None = aleatorio)
            num_objects: Número de objetos (None = aleatorio)
            robot_start_location: Ubicación inicial del robot (None = aleatoria)
            
        Returns:
            WorldState generado
        """
        # Seleccionar ubicaciones según tipo de entorno
        if environment_type == "house":
            locations = HOUSE_LOCATIONS.copy()
        elif environment_type == "office":
            locations = OFFICE_LOCATIONS.copy()
        else:  # mixed
            locations = ALL_LOCATIONS.copy()
        
        # Determinar ubicación inicial del robot
        if robot_start_location and robot_start_location in locations:
            robot_loc = robot_start_location
        else:
            robot_loc = random.choice(locations)
        
        # Determinar número de personas y objetos
        if num_people is None:
            num_people = random.randint(3, min(10, len(ALL_PEOPLE)))
        if num_objects is None:
            num_objects = random.randint(3, min(8, len(ALL_OBJECTS)))
        
        # Seleccionar personas y objetos aleatorios
        selected_people = random.sample(ALL_PEOPLE, min(num_people, len(ALL_PEOPLE)))
        selected_objects = random.sample(ALL_OBJECTS, min(num_objects, len(ALL_OBJECTS)))
        
        # Distribuir personas en ubicaciones
        people_locations = {}
        for person in selected_people:
            people_locations[person] = random.choice(locations)
        
        # Distribuir objetos en ubicaciones
        objects_locations = {}
        for obj in selected_objects:
            objects_locations[obj] = random.choice(locations)
        
        return WorldState(
            robot_location=robot_loc,
            people_locations=people_locations,
            objects_locations=objects_locations,
            available_locations=locations
        )
    
    def generate_clustered_state(
        self,
        environment_type: str = "mixed",
        num_people: int = 6,
        num_objects: int = 6,
        cluster_probability: float = 0.7
    ) -> WorldState:
        """
        Genera un estado con clustering (personas/objetos tienden a agruparse).
        
        Args:
            environment_type: Tipo de entorno
            num_people: Número de personas
            num_objects: Número de objetos
            cluster_probability: Probabilidad de agruparse (0-1)
            
        Returns:
            WorldState con distribución agrupada
        """
        # Seleccionar ubicaciones
        if environment_type == "house":
            locations = HOUSE_LOCATIONS.copy()
            popular_locations = ["living room", "kitchen"]
        elif environment_type == "office":
            locations = OFFICE_LOCATIONS.copy()
            popular_locations = ["cafeteria", "conference room", "office"]
        else:
            locations = ALL_LOCATIONS.copy()
            popular_locations = ["living room", "kitchen", "cafeteria", "conference room"]
        
        robot_loc = random.choice(locations)
        
        # Seleccionar personas y objetos
        selected_people = random.sample(ALL_PEOPLE, min(num_people, len(ALL_PEOPLE)))
        selected_objects = random.sample(ALL_OBJECTS, min(num_objects, len(ALL_OBJECTS)))
        
        # Distribuir con clustering
        people_locations = {}
        for person in selected_people:
            if random.random() < cluster_probability:
                # Agrupar en ubicaciones populares
                people_locations[person] = random.choice(popular_locations)
            else:
                # Distribución uniforme
                people_locations[person] = random.choice(locations)
        
        objects_locations = {}
        for obj in selected_objects:
            if random.random() < cluster_probability:
                objects_locations[obj] = random.choice(popular_locations)
            else:
                objects_locations[obj] = random.choice(locations)
        
        return WorldState(
            robot_location=robot_loc,
            people_locations=people_locations,
            objects_locations=objects_locations,
            available_locations=locations
        )
    
    def generate_sparse_state(
        self,
        environment_type: str = "mixed",
        num_people: int = 3,
        num_objects: int = 3
    ) -> WorldState:
        """
        Genera un estado disperso (pocas personas/objetos, bien distribuidos).
        
        Args:
            environment_type: Tipo de entorno
            num_people: Número de personas
            num_objects: Número de objetos
            
        Returns:
            WorldState disperso
        """
        # Seleccionar ubicaciones
        if environment_type == "house":
            locations = HOUSE_LOCATIONS.copy()
        elif environment_type == "office":
            locations = OFFICE_LOCATIONS.copy()
        else:
            locations = ALL_LOCATIONS.copy()
        
        robot_loc = random.choice(locations)
        
        # Seleccionar personas y objetos
        selected_people = random.sample(ALL_PEOPLE, min(num_people, len(ALL_PEOPLE)))
        selected_objects = random.sample(ALL_OBJECTS, min(num_objects, len(ALL_OBJECTS)))
        
        # Distribuir de forma dispersa (una persona por ubicación si es posible)
        used_locations: Set[str] = set()
        people_locations = {}
        
        for person in selected_people:
            # Intentar asignar ubicación no usada
            available = [loc for loc in locations if loc not in used_locations]
            if available:
                loc = random.choice(available)
                used_locations.add(loc)
            else:
                loc = random.choice(locations)
            people_locations[person] = loc
        
        # Distribuir objetos de forma similar
        used_locations.clear()
        objects_locations = {}
        
        for obj in selected_objects:
            available = [loc for loc in locations if loc not in used_locations]
            if available:
                loc = random.choice(available)
                used_locations.add(loc)
            else:
                loc = random.choice(locations)
            objects_locations[obj] = loc
        
        return WorldState(
            robot_location=robot_loc,
            people_locations=people_locations,
            objects_locations=objects_locations,
            available_locations=locations
        )
    
    def generate_custom_state(
        self,
        robot_location: str,
        people_locations: Dict[str, str],
        objects_locations: Dict[str, str],
        environment_type: str = "mixed"
    ) -> WorldState:
        """
        Genera un estado personalizado con ubicaciones específicas.
        
        Args:
            robot_location: Ubicación del robot
            people_locations: Diccionario persona -> ubicación
            objects_locations: Diccionario objeto -> ubicación
            environment_type: Tipo de entorno
            
        Returns:
            WorldState personalizado
        """
        if environment_type == "house":
            locations = HOUSE_LOCATIONS.copy()
        elif environment_type == "office":
            locations = OFFICE_LOCATIONS.copy()
        else:
            locations = ALL_LOCATIONS.copy()
        
        return WorldState(
            robot_location=robot_location,
            people_locations=people_locations.copy(),
            objects_locations=objects_locations.copy(),
            available_locations=locations
        )
    
    def generate_variations(
        self,
        base_state: WorldState,
        num_variations: int = 5,
        variation_degree: float = 0.3
    ) -> List[WorldState]:
        """
        Genera variaciones de un estado base.
        
        Args:
            base_state: Estado base
            num_variations: Número de variaciones a generar
            variation_degree: Grado de variación (0=ninguno, 1=completamente diferente)
            
        Returns:
            Lista de WorldStates variados
        """
        variations = []
        
        for _ in range(num_variations):
            # Copiar estado base
            new_state = deepcopy(base_state)
            
            # Calcular cuántas personas/objetos mover
            num_people_to_move = int(len(new_state.people_locations) * variation_degree)
            num_objects_to_move = int(len(new_state.objects_locations) * variation_degree)
            
            # Mover personas aleatorias
            people_to_move = random.sample(
                list(new_state.people_locations.keys()),
                min(num_people_to_move, len(new_state.people_locations))
            )
            for person in people_to_move:
                new_state.people_locations[person] = random.choice(new_state.available_locations)
            
            # Mover objetos aleatorios
            objects_to_move = random.sample(
                list(new_state.objects_locations.keys()),
                min(num_objects_to_move, len(new_state.objects_locations))
            )
            for obj in objects_to_move:
                new_state.objects_locations[obj] = random.choice(new_state.available_locations)
            
            # Opcionalmente mover el robot
            if random.random() < variation_degree:
                new_state.robot_location = random.choice(new_state.available_locations)
            
            variations.append(new_state)
        
        return variations


# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================

def create_default_world_state() -> WorldState:
    """Crea un estado del mundo por defecto para compatibilidad."""
    return WorldState(
        robot_location="living room",
        people_locations={
            "Alice": "kitchen",
            "Tomas": "living room",
            "David": "bedroom",
            "Maria": "kitchen"
        },
        objects_locations={
            "chair": "living room",
            "table": "kitchen",
            "keys": "bedroom"
        },
        available_locations=ALL_LOCATIONS
    )


def get_world_state_summary(state: WorldState) -> str:
    """
    Genera un resumen conciso del estado para incluir en prompts.
    
    Args:
        state: Estado del mundo
        
    Returns:
        String con resumen
    """
    lines = [
        f"Robot is currently at: {state.robot_location}",
        f"Available locations: {', '.join(state.available_locations)}",
        "\nPeople in the environment:"
    ]
    
    # Agrupar personas por ubicación
    location_to_people = {}
    for person, loc in state.people_locations.items():
        if loc not in location_to_people:
            location_to_people[loc] = []
        location_to_people[loc].append(person)
    
    for loc in sorted(location_to_people.keys()):
        people = ", ".join(location_to_people[loc])
        lines.append(f"  - {loc}: {people}")
    
    return "\n".join(lines)


if __name__ == "__main__":
    # Ejemplos de uso
    generator = WorldStateGenerator(seed=42)
    
    print("=== Random State (House) ===")
    state1 = generator.generate_random_state(environment_type="house", num_people=4)
    print(state1.describe())
    
    print("\n=== Clustered State (Office) ===")
    state2 = generator.generate_clustered_state(environment_type="office", num_people=6)
    print(state2.describe())
    
    print("\n=== Sparse State (Mixed) ===")
    state3 = generator.generate_sparse_state(num_people=3, num_objects=3)
    print(state3.describe())
    
    print("\n=== Variations ===")
    variations = generator.generate_variations(state1, num_variations=2, variation_degree=0.5)
    for i, var in enumerate(variations, 1):
        print(f"\nVariation {i}:")
        print(get_world_state_summary(var))
