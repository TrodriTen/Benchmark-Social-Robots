from dataclasses import dataclass
from typing import Any, List, Dict, Optional
import time


# ============================================================================
# SIMULACIÓN DE ENTORNO - Estado simulado del robot y entorno
# ============================================================================

class SimulatedEnvironment:
    """Simula el estado del entorno para respuestas consistentes"""
    
    def __init__(self):
        # Ubicación inicial del robot
        self.current_location = "living room"
        self.initial_location = "living room"
        
        # Ubicaciones disponibles (ampliado para tareas complejas)
        self.available_locations = [
            # Casa
            "living room", "kitchen", "bedroom", "bathroom", "gym", 
            "dinner table", "sofa", "entrance", "corridor",
            # Oficina
            "office", "library", "garden", "cafeteria", "conference room",
            "reception", "lobby", "break room", "archive room", "copy room",
            "main entrance", "parking lot", "elevator",
            "meeting room A", "meeting room B", "meeting room C",
            "marketing department", "sales department", "development department"
        ]
        
        # Personas disponibles en el entorno simulado
        self.available_people = [
            "Alice", "Tomas", "David", "Maria", "Carlos", "Ana", "Jorge",
            "Richard", "Laura", "Sophia", "Alex", "Elena", "Miguel", "Pablo",
            "Julia", "Peter"
        ]
        
        # Ubicaciones por defecto de personas (puede ser modificado)
        self.people_locations = {
            # Personas casa
            "Alice": "kitchen",
            "Tomas": "living room",
            "David": "entrance",
            "Maria": "kitchen",
            "Peter": "gym",
            # Personas oficina
            "Carlos": "kitchen",
            "Ana": "library",
            "Jorge": "garden",
            "Richard": "office",
            "Laura": "library",
            "Sophia": "break room",
            "Alex": "cafeteria",
            "Elena": "conference room",
            "Miguel": "cafeteria",
            "Pablo": "office",
            "Julia": "reception"
        }
        
        # Objetos en el entorno
        self.objects_locations = {
            # Casa
            "chair": "garden",
            "exercise ball": "gym",
            "table": "cafeteria",
            "sofa": "living room",
            # Oficina
            "folder": "archive room",
            "first aid kit": "corridor",
            "package": "main entrance",
            "printer": "copy room",
            "keys": "office",
            "book": "library",
            "coffee machine": "cafeteria"
        }
        
        # Memoria del robot (para tareas complejas)
        self.memory = {}
        
    def find_person_at_location(self, target_person: str = None):
        """Busca una persona en la ubicación actual del robot"""
        people_here = [person for person, location in self.people_locations.items() 
                      if location == self.current_location]
        
        if not people_here:
            return None, f"No hay nadie en {self.current_location}"
            
        if target_person and target_person in people_here:
            return target_person, f"Se encontró a {target_person} en {self.current_location}"
        elif target_person and target_person not in people_here:
            actual_location = self.people_locations.get(target_person, "desconocida")
            if actual_location == "desconocida":
                return None, f"No se conoce la ubicación de {target_person}"
            return None, f"{target_person} no está aquí. {target_person} está en {actual_location}"
        else:
            # Si no especifica persona, devolver la primera disponible
            found_person = people_here[0]
            return found_person, f"Se encontró a {found_person} en {self.current_location}"
    
    def move_to_location(self, location: str):
        """Simula movimiento del robot"""
        # Normalizar nombre (espacios, minúsculas)
        location_normalized = location.lower().strip()
        
        # Buscar coincidencia flexible
        for available_loc in self.available_locations:
            if location_normalized in available_loc.lower() or available_loc.lower() in location_normalized:
                self.current_location = available_loc
                return True, f"Robot se movió a {available_loc}"
        
        # No encontrado
        return False, f"Ubicación '{location}' no conocida. No puedo ir a lugares que no conozco."
    
    def find_object(self, object_name: str):
        """Busca un objeto en la ubicación actual"""
        objects_here = [obj for obj, location in self.objects_locations.items() 
                       if location == self.current_location]
        
        if not objects_here:
            return None, f"No se encontraron objetos en {self.current_location}"
        
        # Búsqueda flexible
        object_normalized = object_name.lower().strip()
        for obj in objects_here:
            if object_normalized in obj.lower() or obj.lower() in object_normalized:
                return obj, f"Se encontró {obj} en {self.current_location}"
        
        return None, f"No se encontró '{object_name}' en {self.current_location}"
    
    def store_memory(self, key: str, value: Any):
        """Almacena información en memoria"""
        self.memory[key] = value
        return f"Información almacenada: {key}"
    
    def recall_memory(self, key: str = None):
        """Recupera información de memoria"""
        if key:
            return self.memory.get(key, f"No hay información almacenada con clave '{key}'")
        else:
            # Retornar toda la memoria
            if not self.memory:
                return "La memoria está vacía"
            return str(self.memory)
    
    def describe_location(self):
        """Describe la ubicación actual con personas y objetos"""
        people_here = [person for person, loc in self.people_locations.items() if loc == self.current_location]
        objects_here = [obj for obj, loc in self.objects_locations.items() if loc == self.current_location]
        
        description = f"Estoy en {self.current_location}. "
        
        if people_here:
            description += f"Veo a: {', '.join(people_here)}. "
        else:
            description += "No hay personas aquí. "
        
        if objects_here:
            description += f"Objetos visibles: {', '.join(objects_here)}."
        else:
            description += "No veo objetos notables."
        
        return description
    
    def reset_to_initial(self):
        """Resetea el robot a ubicación inicial"""
        self.current_location = self.initial_location
        self.memory.clear()
        return f"Robot regresó a {self.initial_location}"
    
    def apply_world_state(self, world_state):
        """
        Aplica un WorldState al entorno simulado.
        
        Args:
            world_state: Instancia de WorldState del world_state_generator
        """
        self.current_location = world_state.robot_location
        self.initial_location = world_state.robot_location
        self.available_locations = world_state.available_locations.copy()
        self.people_locations = world_state.people_locations.copy()
        self.objects_locations = world_state.objects_locations.copy()
        self.memory.clear()
    
    def get_current_state_dict(self) -> Dict:
        """Retorna el estado actual como diccionario."""
        return {
            "current_location": self.current_location,
            "initial_location": self.initial_location,
            "people_locations": self.people_locations.copy(),
            "objects_locations": self.objects_locations.copy(),
            "memory": self.memory.copy()
        }

# Instancia global del entorno simulado
_sim_env = SimulatedEnvironment()

# ============================================================================
# RESPONSE TYPES - Objetos ligeros para simular respuestas de servicios
# ============================================================================

@dataclass
class ApprovedResponse:
    """Respuesta genérica con campo approved (bool)"""
    approved: bool = True

@dataclass
class StringResponse:
    """Respuesta con string aprobación"""
    result: str = "approved"
    
    def __eq__(self, other):
        if isinstance(other, str):
            return self.result == other
        return super().__eq__(other)
    
    def __str__(self):
        return self.result

@dataclass
class FaceRecognitionResponse:
    """Respuesta de reconocimiento facial"""
    approved: bool = True
    person: str = "Alice"

@dataclass
class DepthResponse:
    """Respuesta con profundidad"""
    depth: float = 1.23

@dataclass
class TextResponse:
    """Respuesta con texto"""
    text: str = "DUMMY_TEXT"

@dataclass
class AnswerResponse:
    """Respuesta con campo answer"""
    answer: str = "This is a simulated answer"

@dataclass
class MessageResponse:
    """Respuesta con campo message"""
    message: str = "Simulated message"
    approved: bool = True

@dataclass
class LabelsResponse:
    """Respuesta con labels y approved"""
    approved: bool = True
    labels: str = "person,cup,bottle"

@dataclass
class PersonDescriptionResponse:
    """Respuesta de descripción de persona"""
    gender: str = "Man"
    age: int = 30
    status: str = "happy"
    race: str = "caucasian"

@dataclass
class ClothesColorResponse:
    """Respuesta de color de ropa"""
    approved: bool = True
    color: str = "blue"

@dataclass
class NavigationResponse:
    """Respuesta de navegación"""
    approved: str = "approved"
    
    def __eq__(self, other):
        if isinstance(other, str):
            return self.approved == other
        return super().__eq__(other)

@dataclass
class ImgDescriptionResponse:
    """Respuesta de descripción de imagen con GPT Vision"""
    approved: bool = True
    message: str = "A person standing in a room with furniture"


# ============================================================================
# MESSAGE TYPES - Stubs para tipos de mensaje
# ============================================================================

@dataclass
class Twist:
    """Geometría - Mensaje de movimiento"""
    linear: Any = None
    angular: Any = None
    
    def __post_init__(self):
        if self.linear is None:
            self.linear = type('obj', (object,), {'x': 0.0, 'y': 0.0, 'z': 0.0})()
        if self.angular is None:
            self.angular = type('obj', (object,), {'x': 0.0, 'y': 0.0, 'z': 0.0})()

@dataclass
class TouchMsg:
    """Mensaje de toque de sensores"""
    name: str = ""
    state: bool = False

@dataclass
class GetLabelsMsg:
    """Mensaje de etiquetas detectadas"""
    labels: List[str] = None
    x_coordinates: List[float] = None
    y_coordinates: List[float] = None
    widths: List[float] = None
    heights: List[float] = None
    ids: List[int] = None
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = ["person", "cup", "bottle"]
        if self.x_coordinates is None:
            self.x_coordinates = [100.0, 200.0, 300.0]
        if self.y_coordinates is None:
            self.y_coordinates = [150.0, 180.0, 220.0]
        if self.widths is None:
            self.widths = [80.0, 60.0, 50.0]
        if self.heights is None:
            self.heights = [120.0, 100.0, 90.0]
        if self.ids is None:
            self.ids = [1, 2, 3]

@dataclass
class GetClothesColorMsg:
    """Mensaje de colores de ropa"""
    colors: List[str] = None
    
    def __post_init__(self):
        if self.colors is None:
            self.colors = ["blue", "red"]

@dataclass
class SpeechRecognitionStatusMsg:
    """Mensaje de estado de reconocimiento de voz"""
    status: str = "completed"

@dataclass
class SetAnglesMsg:
    """Mensaje para configurar ángulos"""
    angles: List[float] = None
    
    def __post_init__(self):
        if self.angles is None:
            self.angles = [0.0]

@dataclass
class AnimationMsg:
    """Mensaje de animación"""
    family: str = ""
    animation_name: str = ""

@dataclass
class LedsParametersMsg:
    """Mensaje de parámetros de LEDs"""
    name: str = ""
    red: int = 0
    green: int = 0
    blue: int = 0
    time: float = 0.0

@dataclass
class SimpleFeedbackMsg:
    """Mensaje de retroalimentación de navegación"""
    navigation_status: int = 0


# ============================================================================
# REQUEST TYPES - Stubs para tipos de request
# ============================================================================

@dataclass
class SetAngleSrvRequest:
    """Request para configurar ángulos"""
    name: List[str] = None
    angle: List[float] = None
    speed: float = 0.0
    
    def __post_init__(self):
        if self.name is None:
            self.name = []
        if self.angle is None:
            self.angle = []

@dataclass
class SetOpenCloseHandSrvRequest:
    """Request para abrir/cerrar mano"""
    hand: str = ""
    state: str = ""

@dataclass
class TalkSrvRequest:
    """Request para hablar"""
    text: str = ""
    language: str = "English"
    wait: bool = True
    animated: bool = False
    speed: str = "100"

@dataclass
class Speech2TextSrvRequest:
    """Request para speech to text"""
    seconds: int = 0
    lang: str = "eng"

@dataclass
class TabletServiceSrvRequest:
    """Request para servicio de tablet"""
    data: str = ""

@dataclass
class LookForObjectSrvRequest:
    """Request para buscar objeto"""
    object_name: str = ""
    ignore_already_seen: bool = False

@dataclass
class SaveFaceSrvRequest:
    """Request para guardar cara"""
    name: str = ""
    num_pics: int = 5

@dataclass
class RecognizeFaceSrvRequest:
    """Request para reconocer cara"""
    num_pics: int = 3

@dataclass
class SaveImageSrvRequest:
    """Request para guardar imagen"""
    path: str = ""

@dataclass
class SetModelRecognitionSrvRequest:
    """Request para configurar modelo de reconocimiento"""
    model_name: str = ""

@dataclass
class ReadQrSrvRequest:
    """Request para leer QR"""
    timeout: float = 0.0

@dataclass
class FilteredImageSrvRequest:
    """Request para imagen filtrada"""
    filter_name: str = ""

@dataclass
class TurnCameraSrvRequest:
    """Request para controlar cámara"""
    camera_name: str = ""
    command: str = ""
    resolution: int = 1
    fps: int = 15

@dataclass
class StartRecognitionSrvRequest:
    """Request para iniciar reconocimiento"""
    camera_name: str = ""

@dataclass
class FilterLabelsByDistanceSrvRequest:
    """Request para filtrar etiquetas por distancia"""
    activate: bool = False
    distance: float = 0.0
    labels: List[str] = None
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = []

@dataclass
class AddRecognitionModelSrvRequest:
    """Request para agregar modelo de reconocimiento"""
    camera_name: str = ""
    model_name: str = ""

@dataclass
class RemoveRecognitionModelSrvRequest:
    """Request para remover modelo de reconocimiento"""
    camera_name: str = ""
    model_name: str = ""

@dataclass
class SetCurrentPlaceSrvRequest:
    """Request para establecer lugar actual"""
    place_name: str = ""

@dataclass
class GoToRelativePointSrvRequest:
    """Request para ir a punto relativo"""
    x: float = 0.0
    y: float = 0.0
    theta: float = 0.0

@dataclass
class GoToPlaceSrvRequest:
    """Request para ir a lugar"""
    place_name: str = ""
    graph: int = 1

@dataclass
class NavigateToSrvRequest:
    """Request para navegar a"""
    x: float = 0.0
    y: float = 0.0

@dataclass
class FollowYouSrvRequest:
    """Request para seguir"""
    command: bool = False
    speed: float = 0.1

@dataclass
class SpinSrvRequest:
    """Request para girar"""
    degrees: float = 0.0

@dataclass
class AddPlaceSrvRequest:
    """Request para agregar lugar"""
    name: str = ""
    edges: List[str] = None
    persist: int = 0
    
    def __post_init__(self):
        if self.edges is None:
            self.edges = []

@dataclass
class AddPlaceWithCoordinatesSrvRequest:
    """Request para agregar lugar con coordenadas"""
    name: str = ""
    x: float = 0.0
    y: float = 0.0
    theta: float = 0.0
    persist: int = 0


# ============================================================================
# DUMMY SERVICE IMPLEMENTATIONS
# ============================================================================

def turn_camera_srv(camera_name: str, command: str = "custom", resolution: int = 1, fps: int = 15):
    """Simula turn_camera - retorna 'approved' como string"""
    print(f"[DUMMY] turn_camera: camera={camera_name}, cmd={command}, res={resolution}, fps={fps}")
    return "approved"

def filtered_image_srv(filter_name: str):
    """Simula filtered_image - retorna objeto con .approved"""
    print(f"[DUMMY] filtered_image: filter={filter_name}")
    return ApprovedResponse(approved=True)

def start_recognition_srv(camera_name: str):
    """Simula start_recognition - retorna 'approved' como string"""
    print(f"[DUMMY] start_recognition: camera={camera_name}")
    return "approved"

def get_labels_srv(start: bool):
    """Simula get_labels - retorna objeto con .approved y .labels"""
    print(f"[DUMMY] get_labels: start={start}")
    return LabelsResponse(approved=True, labels="person,cup,bottle,chair")

def calculate_depth_of_label_srv(x: float, y: float, w: float, h: float):
    """Simula calculate_depth_of_label - retorna objeto con .depth"""
    print(f"[DUMMY] calculate_depth_of_label: x={x}, y={y}, w={w}, h={h}")
    return DepthResponse(depth=1.5)

def look_for_object_srv(object_name: str, ignore_already_seen: bool = False):
    """Simula look_for_object - retorna 'approved' como string"""
    print(f"[DUMMY] look_for_object: object={object_name}, ignore={ignore_already_seen}")
    return "approved"

def save_face_srv(name: str, num_pics: int = 5):
    """Simula save_face - retorna objeto con .approved"""
    print(f"[DUMMY] save_face: name={name}, pics={num_pics}")
    return ApprovedResponse(approved=True)

def recognize_face_srv(num_pics: int = 3):
    """Simula recognize_face - retorna objeto con .approved y .person basado en ubicación"""
    print(f"[DUMMY] recognize_face: pics={num_pics}")
    found_person, message = _sim_env.find_person_at_location()
    
    if found_person:
        print(f"[DUMMY] -> {message}")
        return FaceRecognitionResponse(approved=True, person=found_person)
    else:
        print(f"[DUMMY] -> {message}")
        return FaceRecognitionResponse(approved=False, person="")

def remove_faces_data_srv():
    """Simula remove_faces_data - retorna objeto con .approved"""
    print("[DUMMY] remove_faces_data")
    return ApprovedResponse(approved=True)

def get_person_description_srv():
    """Simula get_person_description - retorna dict-like con atributos"""
    print("[DUMMY] get_person_description")
    return PersonDescriptionResponse(gender="Man", age=30, status="happy", race="caucasian")

def get_clothes_color_srv():
    """Simula get_clothes_color - retorna objeto con .approved"""
    print("[DUMMY] get_clothes_color")
    return ApprovedResponse(approved=True)

def get_first_clothes_color_srv():
    """Simula get_first_clothes_color - retorna objeto con .approved"""
    print("[DUMMY] get_first_clothes_color")
    return ApprovedResponse(approved=True)

def img_description_srv(prompt: str, camera_name: str = "front_camera", distance: float = 0.0):
    """Simula img_description_with_gpt_vision - retorna objeto con .message y .approved"""
    print(f"[DUMMY] img_description: prompt='{prompt}', camera={camera_name}, dist={distance}")
    return ImgDescriptionResponse(approved=True, message="A person is waving at the camera")

def read_qr_srv(timeout: float):
    """Simula read_qr - retorna objeto con .text"""
    print(f"[DUMMY] read_qr: timeout={timeout}")
    return TextResponse(text="DUMMY_QR_CODE")

def pose_srv(camera_name: str, start: bool):
    """Simula start_pose_recognition - retorna objeto con .approved"""
    print(f"[DUMMY] pose_srv: camera={camera_name}, start={start}")
    return ApprovedResponse(approved=True)

def set_model_recognition_srv(model_name: str):
    """Simula set_model_recognition - retorna objeto con .approved"""
    print(f"[DUMMY] set_model_recognition: model={model_name}")
    return ApprovedResponse(approved=True)

def add_recognition_model_srv(camera_name: str, model_name: str):
    """Simula add_recognition_model - retorna objeto con .approved"""
    print(f"[DUMMY] add_recognition_model: camera={camera_name}, model={model_name}")
    return ApprovedResponse(approved=True)

def remove_recognition_model_srv(camera_name: str, model_name: str):
    """Simula remove_recognition_model - retorna objeto con .approved"""
    print(f"[DUMMY] remove_recognition_model: camera={camera_name}, model={model_name}")
    return ApprovedResponse(approved=True)

def filter_labels_by_distance_srv(activate: bool, distance: float, labels: List[str]):
    """Simula filter_labels_by_distance - retorna objeto con .approved"""
    print(f"[DUMMY] filter_labels_by_distance: activate={activate}, dist={distance}, labels={labels}")
    return ApprovedResponse(approved=True)

# SPEECH SERVICES

def talk_srv(text: str, language: str = "English", wait: bool = True, animated: bool = False, speed: str = "100"):
    """Simula talk - retorna True"""
    print(f"[DUMMY] talk: '{text}' [{language}] wait={wait} animated={animated} speed={speed}")
    return True

def speech2text_srv(seconds: int = 0, lang: str = "eng"):
    """Simula speech2text - retorna respuestas predefinidas según contexto"""
    print(f"[DUMMY] speech2text: seconds={seconds}, lang={lang}")
    
    # Respuestas simuladas realistas para benchmarking
    simulated_responses = [
        "Sí, estoy aquí",
        "Hola robot", 
        "Gracias",
        "Está bien",
        "No necesito nada más"
    ]
    
    # Usar la ubicación actual para dar respuestas contextualmente apropiadas
    current_location = _sim_env.current_location
    people_here = [person for person, location in _sim_env.people_locations.items() 
                   if location == current_location]
    
    if people_here:
        return f"Hola, soy {people_here[0]}. ¿En qué puedo ayudarte?"
    else:
        return "No escucho a nadie cerca"

def q_a_srv(tag: str):
    """Simula q_a - retorna string"""
    print(f"[DUMMY] q_a: tag={tag}")
    responses = {
        "age": "I am 5 years old",
        "name": "My name is Pepper",
        "drink": "I prefer water"
    }
    return responses.get(tag, "I don't know")

def answer_srv(question: str, temperature: float = 0.5, save_conversation: bool = True, fill_time: bool = True):
    """Simula answer - retorna objeto con .answer"""
    print(f"[DUMMY] answer: question='{question}', temp={temperature}")
    return AnswerResponse(answer="This is a simulated answer to your question")

def hot_word_srv(words: List[str], noise: bool = False, eyes: bool = False, thresholds: List[float] = None):
    """Simula hot_word - retorna True"""
    print(f"[DUMMY] hot_word: words={words}, noise={noise}, eyes={eyes}, thresh={thresholds}")
    return True

# NAVIGATION SERVICES

def set_current_place_srv(place_name: str):
    """Simula set_current_place - retorna True"""
    print(f"[DUMMY] set_current_place: place={place_name}")
    return True

def go_to_relative_point_srv(x: float, y: float, theta: float):
    """Simula go_to_relative_point - retorna True"""
    print(f"[DUMMY] go_to_relative_point: x={x}, y={y}, theta={theta}")
    return True

def go_to_place_srv(place_name: str, graph: int = 1):
    """Simula go_to_place - retorna 'approved' y actualiza ubicación del robot"""
    print(f"[DUMMY] go_to_place: place={place_name}, graph={graph}")
    
    success, message = _sim_env.move_to_location(place_name)
    if success:
        print(f"[DUMMY] -> {message}")
        return NavigationResponse(approved="approved")
    else:
        print(f"[DUMMY] -> {message}")  
        return NavigationResponse(approved="failed")

def start_random_navigation_srv():
    """Simula start_random_navigation - retorna True"""
    print("[DUMMY] start_random_navigation")
    return True

def add_place_srv(name: str, edges: List[str] = None, persist: int = 0):
    """Simula add_place - retorna True"""
    print(f"[DUMMY] add_place: name={name}, edges={edges}, persist={persist}")
    return True

def add_place_with_coordinates_srv(name: str, x: float, y: float, theta: float, persist: int = 0):
    """Simula add_place_with_coordinates - retorna True"""
    print(f"[DUMMY] add_place_with_coordinates: name={name}, x={x}, y={y}, theta={theta}, persist={persist}")
    return True

def follow_you_srv(command: bool, speed: float = 0.1):
    """Simula follow_you - retorna True"""
    print(f"[DUMMY] follow_you: command={command}, speed={speed}")
    return True

def robot_stop_srv():
    """Simula robot_stop - retorna True"""
    print("[DUMMY] robot_stop")
    return True

def spin_srv(degrees: float):
    """Simula spin - retorna True"""
    print(f"[DUMMY] spin: degrees={degrees}")
    return True

def go_to_defined_angle_srv(degrees: float):
    """Simula go_to_defined_angle - retorna True"""
    print(f"[DUMMY] go_to_defined_angle: degrees={degrees}")
    return True

def get_route_guidance_srv(place_name: str):
    """Simula get_route_guidance - retorna string"""
    print(f"[DUMMY] get_route_guidance: place={place_name}")
    return "Turn left, then go straight for 5 meters"

def constant_spin_srv(velocity: float):
    """Simula constant_spin - retorna True"""
    print(f"[DUMMY] constant_spin: velocity={velocity}")
    return True

def get_absolute_position_srv():
    """Simula get_absolute_position - retorna objeto con coordenadas"""
    print("[DUMMY] get_absolute_position")
    pos = type('obj', (object,), {'x': 1.0, 'y': 2.0, 'theta': 0.5})()
    return pos

def correct_position_srv():
    """Simula correct_position - retorna True"""
    print("[DUMMY] correct_position")
    return True

# MANIPULATION SERVICES

def go_to_pose(pose: str, velocity: float = 0.05):
    """Simula go_to_pose (manipulation) - retorna True"""
    print(f"[DUMMY] go_to_pose: pose={pose}, velocity={velocity}")
    return True

def move_head(head_position: str = "default"):
    """Simula move_head (manipulation) - retorna True"""
    print(f"[DUMMY] move_head: position={head_position}")
    return True

# PYTOOLKIT SERVICES

def set_stiffnesses_srv(joints: List[str], stiffness: float):
    """Simula set_stiffnesses - retorna True"""
    print(f"[DUMMY] set_stiffnesses: joints={joints}, stiff={stiffness}")
    return True

def set_arms_security_srv(state: bool):
    """Simula set_arms_security - retorna True"""
    print(f"[DUMMY] set_arms_security: state={state}")
    return True

def set_output_volume_srv(volume: int):
    """Simula set_output_volume - retorna 'approved'"""
    print(f"[DUMMY] set_output_volume: volume={volume}")
    return "approved"

def show_web_view_srv(url: str):
    """Simula show_web_view - retorna objeto con .approved"""
    print(f"[DUMMY] show_web_view: url={url}")
    return ApprovedResponse(approved=True)

def show_image_srv(image_path: str):
    """Simula show_image - retorna objeto con .approved"""
    print(f"[DUMMY] show_image: path={image_path}")
    return ApprovedResponse(approved=True)

def hide_srv():
    """Simula hide (tablet) - retorna True"""
    print("[DUMMY] hide")
    return True

def show_video_srv(video_url: str):
    """Simula show_video - retorna objeto con .approved"""
    print(f"[DUMMY] show_video: url={video_url}")
    return ApprovedResponse(approved=True)

def show_topic_srv(topic: str):
    """Simula show_topic - retorna objeto con .approved"""
    print(f"[DUMMY] show_topic: topic={topic}")
    return ApprovedResponse(approved=True)

def show_words_srv():
    """Simula show_words - retorna True"""
    print("[DUMMY] show_words")
    return True

def show_picture_srv():
    """Simula show_picture - retorna True"""
    print("[DUMMY] show_picture")
    return True

def set_hot_word_language_srv(language: str):
    """Simula set_hot_word_language - retorna True"""
    print(f"[DUMMY] set_hot_word_language: lang={language}")
    return True

def move_head_srv(position: str):
    """Simula move_head (pytoolkit) - retorna True"""
    print(f"[DUMMY] move_head_srv: position={position}")
    return True

def toggle_get_angle_srv(request):
    """Simula toggle_get_angle - retorna True"""
    print(f"[DUMMY] toggle_get_angle: {request}")
    return True

def set_angle_srv(joints: List[str], angles: List[float], speed: float):
    """Simula set_angle - retorna True"""
    print(f"[DUMMY] set_angle: joints={joints}, angles={angles}, speed={speed}")
    return True

def navigate_to_srv(x: float, y: float):
    """Simula navigate_to (pytoolkit) - retorna True"""
    print(f"[DUMMY] navigate_to: x={x}, y={y}")
    return True

def enable_security_srv():
    """Simula enable_security - retorna True"""
    print("[DUMMY] enable_security")
    return True

def set_security_distance_srv(distance: float):
    """Simula set_security_distance - retorna 'approved'"""
    print(f"[DUMMY] set_security_distance: distance={distance}")
    return "approved"

def go_to_posture_srv(posture: str):
    """Simula go_to_posture - retorna 'approved'"""
    print(f"[DUMMY] go_to_posture: posture={posture}")
    return "approved"

def set_move_arms_enabled_srv(state: bool):
    """Simula set_move_arms_enabled - retorna True"""
    print(f"[DUMMY] set_move_arms_enabled: state={state}")
    return True

def set_awareness_srv(state: bool):
    """Simula set_awareness (BasicAwareness) - retorna True"""
    print(f"[DUMMY] set_awareness: state={state}")
    return True

def set_orthogonal_security_distance_srv(distance: float):
    """Simula set_orthogonal_security_distance - retorna 'approved'"""
    print(f"[DUMMY] set_orthogonal_security_distance: distance={distance}")
    return "approved"

def set_tangential_security_distance_srv(distance: float):
    """Simula set_tangential_security_distance - retorna 'approved'"""
    print(f"[DUMMY] set_tangential_security_distance: distance={distance}")
    return "approved"

def set_state_srv(state: bool):
    """Simula set_state (AutonomousLife) - retorna True"""
    print(f"[DUMMY] set_state (autonomous_life): state={state}")
    return True

def stop_tracker_srv():
    """Simula stop_tracker - retorna True"""
    print("[DUMMY] stop_tracker")
    return True

def start_tracker_srv():
    """Simula start_tracker - retorna True"""
    print("[DUMMY] start_tracker")
    return True

def start_follow_face_srv():
    """Simula start_follow_face - retorna True"""
    print("[DUMMY] start_follow_face")
    return True

def toggle_breathing_srv(request):
    """Simula toggle_breathing - retorna True"""
    print(f"[DUMMY] toggle_breathing: {request}")
    return True

def motion_tools_srv(request):
    """Simula motion_tools - retorna True"""
    print(f"[DUMMY] motion_tools: {request}")
    return True

def battery_service_srv():
    """Simula battery_service - retorna objeto genérico"""
    print("[DUMMY] battery_service")
    return type('obj', (object,), {'level': 95})()

def set_speechrecognition_srv(subscribe: bool, noise: bool, eyes: bool):
    """Simula set_speechrecognition - retorna objeto con .approved"""
    print(f"[DUMMY] set_speechrecognition: sub={subscribe}, noise={noise}, eyes={eyes}")
    return ApprovedResponse(approved=True)

def speech_recognition_srv():
    """Simula speech_recognition - retorna string"""
    print("[DUMMY] speech_recognition")
    return "recognized speech"

def tablet_service_srv(data: str):
    """Simula tablet_service genérico - retorna objeto con .approved"""
    print(f"[DUMMY] tablet_service: data={data}")
    return ApprovedResponse(approved=True)

def misc_tools_srv(request):
    """Simula misc_tools - retorna True"""
    print(f"[DUMMY] misc_tools: {request}")
    return True

def set_open_close_hand_srv(hand: str, state: str):
    """Simula set_open_close_hand - retorna 'approved'"""
    print(f"[DUMMY] set_open_close_hand: hand={hand}, state={state}")
    return "approved"

def save_image_srv(path: str):
    """Simula save_image - retorna objeto con .approved"""
    print(f"[DUMMY] save_image: path={path}")
    return ApprovedResponse(approved=True)


# ============================================================================
# SERVICE REGISTRY - Mapeo de nombres lógicos a funciones dummy
# ============================================================================

SERVICES = {
    # Perception
    "/perception_utilities/turn_camera_srv": turn_camera_srv,
    "/perception_utilities/filtered_image_srv": filtered_image_srv,
    "/perception_utilities/filtered_image": filtered_image_srv,
    "/perception_utilities/start_recognition_srv": start_recognition_srv,
    "/perception_utilities/get_labels_srv": get_labels_srv,
    "/perception_utilities/calculate_depth_of_label_srv": calculate_depth_of_label_srv,
    "/perception_utilities/look_for_object_srv": look_for_object_srv,
    "/perception_utilities/save_face_srv": save_face_srv,
    "/perception_utilities/recognize_face_srv": recognize_face_srv,
    "/perception_utilities/remove_faces_data_srv": remove_faces_data_srv,
    "/perception_utilities/get_person_description_srv": get_person_description_srv,
    "/perception_utilities/get_clothes_color_srv": get_clothes_color_srv,
    "/perception_utilities/get_first_clothes_color_srv": get_first_clothes_color_srv,
    "perception_utilities/img_description_with_gpt_vision_srv": img_description_srv,
    "/perception_utilities/read_qr_srv": read_qr_srv,
    "perception_utilities/read_qr_srv": read_qr_srv,
    "/perception_utilities/pose_srv": pose_srv,
    "perception_utilities/set_model_recognition_srv": set_model_recognition_srv,
    "/perception_utilities/add_recognition_model_srv": add_recognition_model_srv,
    "/perception_utilities/remove_recognition_model_srv": remove_recognition_model_srv,
    "/perception_utilities/filter_labels_by_distance_srv": filter_labels_by_distance_srv,
    
    # Speech
    "/speech_utilities/talk_srv": talk_srv,
    "speech_utilities/speech2text_srv": speech2text_srv,
    "/speech_utilities/q_a_srv": q_a_srv,
    "/speech_utilities/answers_srv": answer_srv,
    "/speech_utilities/hot_word_srv": hot_word_srv,
    
    # Navigation
    "/navigation_utilities/set_current_place_srv": set_current_place_srv,
    "navigation_utilities/get_absolute_position_srv": get_absolute_position_srv,
    "navigation_utilities/go_to_relative_point_srv": go_to_relative_point_srv,
    "/navigation_utilities/go_to_relative_point_srv": go_to_relative_point_srv,
    "navigation_utilities/go_to_place_srv": go_to_place_srv,
    "/navigation_utilities/go_to_place_srv": go_to_place_srv,
    "navigation_utilities/start_random_navigation_srv": start_random_navigation_srv,
    "/navigation_utilities/start_random_navigation_srv": start_random_navigation_srv,
    "navigation_utilities/add_place_srv": add_place_srv,
    "/navigation_utilities/add_place_srv": add_place_srv,
    "navigation_utilities/add_place_with_coordinates_srv": add_place_with_coordinates_srv,
    "/navigation_utilities/add_place_with_coordinates_srv": add_place_with_coordinates_srv,
    "/navigation_utilities/follow_you_srv": follow_you_srv,
    "navigation_utilities/robot_stop_srv": robot_stop_srv,
    "/navigation_utilities/robot_stop_srv": robot_stop_srv,
    "navigation_utilities/spin_srv": spin_srv,
    "/navigation_utilities/spin_srv": spin_srv,
    "/navigation_utilities/go_to_defined_angle_srv": go_to_defined_angle_srv,
    "navigation_utilities/get_route_guidance_srv": get_route_guidance_srv,
    "/navigation_utilities/get_route_guidance_srv": get_route_guidance_srv,
    "/navigation_utilities/constant_spin_srv": constant_spin_srv,
    
    # Manipulation
    "manipulation_utilities/go_to_pose": go_to_pose,
    "manipulation_utilities/move_head": move_head,
    
    # PyToolkit
    "pytoolkit/ALMotion/set_stiffnesses_srv": set_stiffnesses_srv,
    "pytoolkit/ALMotion/set_arms_security_srv": set_arms_security_srv,
    "/pytoolkit/ALAudioDevice/set_output_volume_srv": set_output_volume_srv,
    "/pytoolkit/ALTabletService/show_web_view_srv": show_web_view_srv,
    "/pytoolkit/ALTabletService/show_image_srv": show_image_srv,
    "/pytoolkit/ALTabletService/hide_srv": hide_srv,
    "/pytoolkit/ALTabletService/play_video_srv": show_video_srv,
    "/pytoolkit/ALTabletService/show_topic_srv": show_topic_srv,
    "/pytoolkit/ALTabletService/show_words_srv": show_words_srv,
    "pytoolkit/ALTabletService/show_picture_srv": show_picture_srv,
    "/pytoolkit/ALSpeechRecognition/set_hot_word_language_srv": set_hot_word_language_srv,
    "/pytoolkit/ALMotion/move_head_srv": move_head_srv,
    "/pytoolkit/ALMotion/toggle_get_angle_srv": toggle_get_angle_srv,
    "/pytoolkit/ALMotion/set_angle_srv": set_angle_srv,
    "/pytoolkit/ALNavigation/navigate_to_srv": navigate_to_srv,
    "/pytoolkit/ALMotion/enable_security_srv": enable_security_srv,
    "/pytoolkit/ALMotion/set_security_distance_srv": set_security_distance_srv,
    "/pytoolkit/ALRobotPosture/go_to_posture_srv": go_to_posture_srv,
    "pytoolkit/ALMotion/set_move_arms_enabled_srv": set_move_arms_enabled_srv,
    "/pytoolkit/ALBasicAwareness/set_awareness_srv": set_awareness_srv,
    "/pytoolkit/ALMotion/set_orthogonal_security_distance_srv": set_orthogonal_security_distance_srv,
    "/pytoolkit/ALMotion/set_tangential_security_distance_srv": set_tangential_security_distance_srv,
    "/pytoolkit/ALAutonomousLife/set_state_srv": set_state_srv,
    "/pytoolkit/ALTracker/stop_tracker_srv": stop_tracker_srv,
    "/pytoolkit/ALTracker/start_tracker_srv": start_tracker_srv,
    "/pytoolkit/ALTracker/start_follow_face": start_follow_face_srv,
    "/pytoolkit/ALMotion/toggle_breathing_srv": toggle_breathing_srv,
    "/robot_toolkit/motion_tools_srv": motion_tools_srv,
    "/pytoolkit/ALBattery/battery_srv": battery_service_srv,
    "/pytoolkit/ALSpeechRecognition/set_speechrecognition_srv": set_speechrecognition_srv,
    "/pytoolkit/ALSpeechRecognition/speech_recognition_srv": speech_recognition_srv,
    "/pytoolkit/ALTabletService/tablet_service_srv": tablet_service_srv,
    "/pytoolkit/ALMisc/misc_tools_srv": misc_tools_srv,
    "/pytoolkit/ALMotion/set_open_close_hand_srv": set_open_close_hand_srv,
    "/perception_utilities/save_image_srv": save_image_srv,
}


# ============================================================================
# DUMMY SERVICE PROXY - Emula rospy.ServiceProxy
# ============================================================================

class DummyServiceProxy:
    """
    Emula rospy.ServiceProxy sin dependencias ROS.
    Delega las llamadas a las funciones dummy registradas en SERVICES.
    """
    
    def __init__(self, service_name: str, srv_type=None):
        """
        Args:
            service_name: Nombre del servicio ROS
            srv_type: Tipo de servicio (ignorado en dummy)
        """
        self.service_name = service_name
        self.srv_type = srv_type
        self._func = SERVICES.get(service_name)
        
        if self._func is None:
            print(f"[WARNING] Servicio no implementado: {service_name}")
            # Crear función dummy genérica
            self._func = lambda *args, **kwargs: ApprovedResponse(approved=True)
    
    def __call__(self, *args, **kwargs):
        """Llama a la función dummy correspondiente"""
        return self._func(*args, **kwargs)
    
    def call(self, *args, **kwargs):
        """Alias para compatibilidad"""
        return self(*args, **kwargs)


# ============================================================================
# DUMMY PUBLISHERS/SUBSCRIBERS - Stubs inocuos
# ============================================================================

class DummyPublisher:
    """Stub para rospy.Publisher - no hace nada real"""
    
    def __init__(self, topic: str, msg_type, queue_size: int = 10):
        self.topic = topic
        self.msg_type = msg_type
        self.queue_size = queue_size
    
    def publish(self, msg):
        """Simula publicación sin hacer nada"""
        print(f"[DUMMY_PUB] {self.topic}: {msg}")


class DummySubscriber:
    """Stub para rospy.Subscriber - no se suscribe realmente"""
    
    def __init__(self, topic: str, msg_type, callback):
        self.topic = topic
        self.msg_type = msg_type
        self.callback = callback
        print(f"[DUMMY_SUB] Suscrito a {topic}")


# ============================================================================
# DUMMY ROSPY FUNCTIONS
# ============================================================================

class DummyTime:
    """Simula rospy.Time"""
    
    @staticmethod
    def now():
        return type('obj', (object,), {
            'secs': int(time.time()),
            'nsecs': int((time.time() % 1) * 1e9)
        })()


class DummyRate:
    """Simula rospy.Rate"""
    
    def __init__(self, hz: float):
        self.hz = hz
        self.sleep_duration = 1.0 / hz
    
    def sleep(self):
        time.sleep(self.sleep_duration)


class DummyDuration:
    """Simula rospy.Duration"""
    
    def __init__(self, secs: float):
        self.secs = secs


class DummyTimer:
    """Simula rospy.Timer"""
    
    def __init__(self, duration, callback, oneshot=False):
        self.duration = duration
        self.callback = callback
        self.oneshot = oneshot
        print(f"[DUMMY_TIMER] Creado timer: duration={duration}, oneshot={oneshot}")


def dummy_init_node(name: str, **kwargs):
    """Simula rospy.init_node"""
    print(f"[DUMMY] init_node: {name}")


def dummy_wait_for_service(service_name: str, timeout: float = None):
    """Simula rospy.wait_for_service - no espera nada"""
    print(f"[DUMMY] wait_for_service: {service_name}")


def dummy_get_param(param_name: str, default=None):
    """Simula rospy.get_param"""
    print(f"[DUMMY] get_param: {param_name}")
    # Retornar valores plausibles según el parámetro
    if "robot_name" in param_name:
        return "nova"
    return default


def dummy_sleep(duration: float):
    """Simula rospy.sleep sin dormir realmente (para tests rápidos)"""
    # Para tests, no dormimos realmente
    pass


def dummy_get_time():
    """Simula rospy.get_time()"""
    return time.time()


class DummyServiceException(Exception):
    """Simula rospy.ServiceException"""
    pass


# ============================================================================
# MÓDULO ROSPY DUMMY COMPLETO
# ============================================================================

class DummyRospy:
    """Módulo completo que simula rospy"""
    
    ServiceProxy = DummyServiceProxy
    Publisher = DummyPublisher
    Subscriber = DummySubscriber
    Time = DummyTime
    Rate = DummyRate
    Duration = DummyDuration
    Timer = DummyTimer
    ServiceException = DummyServiceException
    
    @staticmethod
    def init_node(name: str, **kwargs):
        dummy_init_node(name, **kwargs)
    
    @staticmethod
    def wait_for_service(service_name: str, timeout: float = None):
        dummy_wait_for_service(service_name, timeout)
    
    @staticmethod
    def get_param(param_name: str, default=None):
        return dummy_get_param(param_name, default)
    
    @staticmethod
    def sleep(duration: float):
        dummy_sleep(duration)
    
    @staticmethod
    def get_time():
        return dummy_get_time()


# Instancia global para importar
rospy = DummyRospy()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def ok():
    """Helper para crear respuesta genérica OK"""
    return ApprovedResponse(approved=True)

def approved():
    """Helper para crear respuesta 'approved' como string"""
    return "approved"

def msg(**kwargs):
    """Helper para crear mensaje genérico con atributos arbitrarios"""
    return type('GenericMsg', (object,), kwargs)()


# ============================================================================
# CLI - Inventario de servicios simulados
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("DUMMY TOOLS - Simulador de servicios ROS para task_module.py")
    print("="*80)
    print(f"\nTotal de servicios simulados: {len(SERVICES)}\n")
    
    print("PERCEPTION SERVICES:")
    for svc in sorted([s for s in SERVICES.keys() if 'perception' in s]):
        print(f"  - {svc}")
    
    print("\nSPEECH SERVICES:")
    for svc in sorted([s for s in SERVICES.keys() if 'speech' in s]):
        print(f"  - {svc}")
    
    print("\nNAVIGATION SERVICES:")
    for svc in sorted([s for s in SERVICES.keys() if 'navigation' in s]):
        print(f"  - {svc}")
    
    print("\nMANIPULATION SERVICES:")
    for svc in sorted([s for s in SERVICES.keys() if 'manipulation' in s]):
        print(f"  - {svc}")
    
    print("\nPYTOOLKIT SERVICES:")
    for svc in sorted([s for s in SERVICES.keys() if 'pytoolkit' in s or 'robot_toolkit' in s]):
        print(f"  - {svc}")
    
    print("\n" + "="*80)
    print("Ejemplo de uso:")
    print("="*80)
    print("""
from dummy_tools import DummyServiceProxy, rospy

# Simular servicio de percepción
turn_camera = DummyServiceProxy('/perception_utilities/turn_camera_srv', None)
result = turn_camera('front_camera', 'enable', 1, 15)
print(f"Resultado: {result}")  # "approved"

# Simular reconocimiento facial
recognize = DummyServiceProxy('/perception_utilities/recognize_face_srv', None)
response = recognize(3)
print(f"Persona: {response.person}, Aprobado: {response.approved}")

# Simular navegación
go_to = DummyServiceProxy('/navigation_utilities/go_to_place_srv', None)
result = go_to('living_room', 1)
print(f"Navegación: {result}")  # NavigationResponse(approved='approved')
    """)
    print("="*80 + "\n")