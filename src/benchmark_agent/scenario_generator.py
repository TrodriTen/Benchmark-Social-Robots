"""
Generador de escenarios de prueba con control de semillas y perturbaciones.

Permite generar:
1. Escenarios base (baseline) sin perturbaciones
2. Variantes con perturbaciones controladas
3. Semillas de mundo (posiciones de personas, objetos, estado inicial)
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import random


@dataclass
class WorldState:
    """
    Estado del mundo simulado (semilla).
    """
    robot_location: str = "sala"
    people_locations: Dict[str, str] = field(default_factory=lambda: {
        "Alice": "cocina",
        "Tomas": "sala",
        "David": "puerta",
        "Maria": "cocina"
    })
    objects_locations: Dict[str, str] = field(default_factory=lambda: {
        "taza": "cocina",
        "libro": "sala",
        "llave": "puerta"
    })
    available_locations: List[str] = field(default_factory=lambda: ["cocina", "sala", "puerta"])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el estado a diccionario."""
        return {
            "robot_location": self.robot_location,
            "people_locations": self.people_locations,
            "objects_locations": self.objects_locations,
            "available_locations": self.available_locations
        }


@dataclass
class TaskScenario:
    """
    Escenario de tarea con criterios de éxito.
    """
    id: str
    description: str
    category: str
    world_state: WorldState
    success_criteria: Dict[str, Any]
    expected_steps_range: tuple = (1, 10)  # Rango esperado de pasos
    difficulty: str = "medium"  # easy, medium, hard
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el escenario a diccionario."""
        return {
            "id": self.id,
            "description": self.description,
            "category": self.category,
            "world_state": self.world_state.to_dict(),
            "success_criteria": self.success_criteria,
            "expected_steps_range": self.expected_steps_range,
            "difficulty": self.difficulty
        }


class ScenarioGenerator:
    """
    Generador de escenarios de prueba.
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        Args:
            seed: Semilla para reproducibilidad
        """
        self.seed = seed
        if seed is not None:
            random.seed(seed)
    
    def generate_baseline_scenarios(self) -> List[TaskScenario]:
        """
        Genera conjunto de escenarios baseline (sin perturbaciones).
        
        Returns:
            Lista de escenarios de prueba
        """
        world = WorldState()
        
        scenarios = [
            # Navegación simple
            TaskScenario(
                id="nav_001",
                description="Ve a la cocina.",
                category="navigation_simple",
                world_state=world,
                success_criteria={
                    "must_visit": ["cocina"],
                    "must_use_tools": ["go_to_place"],
                    "min_steps": 1,
                    "max_steps": 3
                },
                expected_steps_range=(1, 2),
                difficulty="easy"
            ),
            
            # Búsqueda + interacción
            TaskScenario(
                id="search_001",
                description="Busca a Tomas y dile 'hola'.",
                category="search_interaction",
                world_state=world,
                success_criteria={
                    "must_find_person": "Tomas",
                    "must_use_tools": ["find_person", "talk"],
                    "must_say_message": "hola",
                    "min_steps": 2,
                    "max_steps": 5
                },
                expected_steps_range=(2, 4),
                difficulty="easy"
            ),
            
            # Multi-hop reasoning
            TaskScenario(
                id="multihop_001",
                description="Ve a la cocina, busca a Tomas y dile 'la comida está lista'.",
                category="multi_hop_reasoning",
                world_state=world,
                success_criteria={
                    "must_visit": ["cocina"],  # Aunque Tomas no esté ahí
                    "must_find_person": "Tomas",
                    "must_use_tools": ["go_to_place", "find_person", "talk"],
                    "must_say_message": "comida está lista",
                    "min_steps": 3,
                    "max_steps": 8
                },
                expected_steps_range=(3, 6),
                difficulty="medium"
            ),
            
            TaskScenario(
                id="multihop_002",
                description="Busca a Tomas y luego tú ve a la puerta.",
                category="multi_hop_reasoning",
                world_state=world,
                success_criteria={
                    "must_find_person": "Tomas",
                    "must_visit": ["puerta"],
                    "must_use_tools": ["find_person", "go_to_place"],
                    "min_steps": 2,
                    "max_steps": 6
                },
                expected_steps_range=(2, 4),
                difficulty="medium"
            ),
            
            # Manejo de incertidumbre - lugar desconocido
            TaskScenario(
                id="uncertainty_001",
                description="Ve al baño.",
                category="uncertainty_handling",
                world_state=world,
                success_criteria={
                    "must_recognize_unknown_location": True,
                    "must_communicate_limitation": True,
                    "expected_result": "lack_of_capabilities_or_success",  # Ambos válidos
                    "min_steps": 1,
                    "max_steps": 3
                },
                expected_steps_range=(1, 2),
                difficulty="easy"
            ),
            
            # Búsqueda en múltiples ubicaciones
            TaskScenario(
                id="search_002",
                description="Busca a David.",
                category="search_interaction",
                world_state=world,
                success_criteria={
                    "must_find_person": "David",
                    "must_use_tools": ["find_person"],
                    "may_need_navigation": True,  # Si no está en ubicación actual
                    "min_steps": 1,
                    "max_steps": 6
                },
                expected_steps_range=(1, 4),
                difficulty="medium"
            ),
            
            # Navegación + búsqueda con información
            TaskScenario(
                id="multihop_003",
                description="Pregunta dónde está Alice y luego ve a buscarla.",
                category="multi_hop_reasoning",
                world_state=world,
                success_criteria={
                    "must_use_tools": ["ask_person_location", "go_to_place", "find_person"],
                    "must_find_person": "Alice",
                    "min_steps": 3,
                    "max_steps": 6
                },
                expected_steps_range=(3, 5),
                difficulty="medium"
            ),
            
            # Interacción con múltiples personas
            TaskScenario(
                id="multihop_004",
                description="Busca a Tomas, dile 'hola', luego busca a David y dile 'adiós'.",
                category="multi_hop_reasoning",
                world_state=world,
                success_criteria={
                    "must_find_persons": ["Tomas", "David"],
                    "must_say_messages": ["hola", "adiós"],
                    "must_use_tools": ["find_person", "talk", "go_to_place"],
                    "min_steps": 4,
                    "max_steps": 10
                },
                expected_steps_range=(4, 8),
                difficulty="hard"
            )
        ]
        
        return scenarios
    
    def generate_with_world_variation(
        self, 
        base_scenario: TaskScenario,
        variation_type: str = "people_shuffle"
    ) -> TaskScenario:
        """
        Genera variante de escenario con estado de mundo modificado.
        
        Args:
            base_scenario: Escenario base
            variation_type: Tipo de variación (people_shuffle, robot_location, etc.)
            
        Returns:
            Nuevo escenario con mundo modificado
        """
        new_world = WorldState(
            robot_location=base_scenario.world_state.robot_location,
            people_locations=base_scenario.world_state.people_locations.copy(),
            objects_locations=base_scenario.world_state.objects_locations.copy(),
            available_locations=base_scenario.world_state.available_locations.copy()
        )
        
        if variation_type == "people_shuffle":
            # Redistribuir personas en ubicaciones
            people = list(new_world.people_locations.keys())
            locations = new_world.available_locations
            for person in people:
                new_world.people_locations[person] = random.choice(locations)
        
        elif variation_type == "robot_location":
            # Cambiar ubicación inicial del robot
            new_world.robot_location = random.choice(new_world.available_locations)
        
        elif variation_type == "add_distractor":
            # Agregar persona distractora
            new_world.people_locations["Carlos"] = random.choice(new_world.available_locations)
        
        new_scenario = TaskScenario(
            id=f"{base_scenario.id}_var_{variation_type}",
            description=base_scenario.description,
            category=base_scenario.category,
            world_state=new_world,
            success_criteria=base_scenario.success_criteria.copy(),
            expected_steps_range=base_scenario.expected_steps_range,
            difficulty=base_scenario.difficulty
        )
        
        return new_scenario
    
    def generate_difficulty_variants(
        self,
        base_description: str,
        category: str
    ) -> List[TaskScenario]:
        """
        Genera variantes de dificultad creciente de una tarea base.
        
        Args:
            base_description: Descripción base de la tarea
            category: Categoría de tarea
            
        Returns:
            Lista de escenarios con dificultad creciente
        """
        world = WorldState()
        
        variants = []
        
        # Easy: Tarea directa, persona en ubicación actual
        world_easy = WorldState(
            robot_location="sala",
            people_locations={"Tomas": "sala", "David": "puerta", "Alice": "cocina"}
        )
        
        variants.append(TaskScenario(
            id=f"{category}_easy",
            description=base_description,
            category=category,
            world_state=world_easy,
            success_criteria={"min_steps": 1, "max_steps": 3},
            expected_steps_range=(1, 2),
            difficulty="easy"
        ))
        
        # Medium: Persona en otra ubicación
        world_medium = WorldState(
            robot_location="sala",
            people_locations={"Tomas": "cocina", "David": "puerta", "Alice": "sala"}
        )
        
        variants.append(TaskScenario(
            id=f"{category}_medium",
            description=base_description,
            category=category,
            world_state=world_medium,
            success_criteria={"min_steps": 3, "max_steps": 6},
            expected_steps_range=(3, 5),
            difficulty="medium"
        ))
        
        # Hard: Múltiples personas, exploración necesaria
        world_hard = WorldState(
            robot_location="puerta",
            people_locations={
                "Tomas": "cocina",
                "David": "sala",
                "Alice": "puerta",
                "Maria": "cocina",
                "Carlos": "sala"
            }
        )
        
        variants.append(TaskScenario(
            id=f"{category}_hard",
            description=base_description.replace("Tomas", "Carlos"),  # Persona menos común
            category=category,
            world_state=world_hard,
            success_criteria={"min_steps": 4, "max_steps": 10},
            expected_steps_range=(4, 8),
            difficulty="hard"
        ))
        
        return variants


# Instancia global del generador
_default_generator = ScenarioGenerator(seed=42)


def get_baseline_scenarios() -> List[TaskScenario]:
    """
    Obtiene escenarios baseline estándar.
    
    Returns:
        Lista de escenarios baseline
    """
    return _default_generator.generate_baseline_scenarios()


def generate_scenario_suite(
    include_baseline: bool = True,
    include_variations: bool = False,
    include_difficulty_levels: bool = False
) -> List[TaskScenario]:
    """
    Genera suite completa de escenarios para evaluación.
    
    Args:
        include_baseline: Incluir escenarios baseline
        include_variations: Incluir variaciones de mundo
        include_difficulty_levels: Incluir variantes de dificultad
        
    Returns:
        Lista completa de escenarios
    """
    scenarios = []
    
    if include_baseline:
        scenarios.extend(get_baseline_scenarios())
    
    if include_variations:
        base_scenarios = get_baseline_scenarios()
        for base in base_scenarios[:3]:  # Solo primeros 3 para variaciones
            scenarios.append(_default_generator.generate_with_world_variation(base, "people_shuffle"))
            scenarios.append(_default_generator.generate_with_world_variation(base, "robot_location"))
    
    if include_difficulty_levels:
        variants = _default_generator.generate_difficulty_variants(
            "Busca a Tomas y dile 'hola'",
            "search_interaction"
        )
        scenarios.extend(variants)
    
    return scenarios
