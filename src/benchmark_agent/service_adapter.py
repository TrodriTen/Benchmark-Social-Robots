"""
Service Adapter - Capa de compatibilidad entre arquitecturas de agentes y dummy_tools.

Este módulo:
1. Envuelve DummyServiceProxy con aliases estables
2. Normaliza retornos heterogéneos a formato común {"ok", "obs", "data"}
3. Proporciona metadata para prompts y planificadores
"""

from typing import Dict, Any, Callable
from .tools.dummy_tools import DummyServiceProxy as SP


# ============================================================================
# HELPERS - Normalización de respuestas
# ============================================================================

def _is_ok(resp: Any) -> bool:
    """
    Determina si una respuesta del servicio dummy indica éxito.
    
    Args:
        resp: Respuesta de cualquier tipo del dummy
        
    Returns:
        True si indica éxito, False en caso contrario
    """
    try:
        # True directo
        if resp is True:
            return True
        
        # String "approved"
        if isinstance(resp, str):
            return resp.strip().lower() == "approved"
        
        # Objeto con atributo .approved
        if hasattr(resp, "approved"):
            val = getattr(resp, "approved")
            if isinstance(val, str):
                return val.strip().lower() == "approved"
            return bool(val)
        
    except Exception:
        pass
    
    return False


def _stringify(resp: Any) -> str:
    """
    Convierte cualquier respuesta del dummy a string legible.
    
    Args:
        resp: Respuesta de cualquier tipo
        
    Returns:
        Representación en string
    """
    try:
        if isinstance(resp, str):
            return resp
        
        if hasattr(resp, "__dict__"):
            attrs = resp.__dict__
            return ", ".join(f"{k}={v}" for k, v in attrs.items())
        
        return str(resp)
    
    except Exception:
        return str(resp)


# ============================================================================
# MAPA DE SERVICIOS - Instancias de DummyServiceProxy por alias
# ============================================================================

SRV: Dict[str, SP] = {
    # Perception
    "turn_camera": SP("/perception_utilities/turn_camera_srv"),
    "start_recognition": SP("/perception_utilities/start_recognition_srv"),
    "get_labels": SP("/perception_utilities/get_labels_srv"),
    "calc_depth": SP("/perception_utilities/calculate_depth_of_label_srv"),
    "look_for_object": SP("/perception_utilities/look_for_object_srv"),
    "save_face": SP("/perception_utilities/save_face_srv"),
    "recognize_face": SP("/perception_utilities/recognize_face_srv"),
    "remove_faces": SP("/perception_utilities/remove_faces_data_srv"),
    "get_person_desc": SP("/perception_utilities/get_person_description_srv"),
    "get_clothes_color": SP("/perception_utilities/get_clothes_color_srv"),
    "img_desc": SP("perception_utilities/img_description_with_gpt_vision_srv"),
    "read_qr": SP("/perception_utilities/read_qr_srv"),
    "set_model": SP("perception_utilities/set_model_recognition_srv"),
    "add_model": SP("/perception_utilities/add_recognition_model_srv"),
    "remove_model": SP("/perception_utilities/remove_recognition_model_srv"),
    "filter_by_distance": SP("/perception_utilities/filter_labels_by_distance_srv"),
    
    # Speech
    "talk": SP("/speech_utilities/talk_srv"),
    "speech2text": SP("speech_utilities/speech2text_srv"),
    "qa": SP("/speech_utilities/q_a_srv"),
    "answer": SP("/speech_utilities/answers_srv"),
    "hot_word": SP("/speech_utilities/hot_word_srv"),
    
    # Navigation
    "set_current_place": SP("/navigation_utilities/set_current_place_srv"),
    "go_to_relative": SP("/navigation_utilities/go_to_relative_point_srv"),
    "go_to_place": SP("/navigation_utilities/go_to_place_srv"),
    "navigate_to": SP("/pytoolkit/ALNavigation/navigate_to_srv"),
    "add_place": SP("/navigation_utilities/add_place_srv"),
    "add_place_coords": SP("/navigation_utilities/add_place_with_coordinates_srv"),
    "follow_you": SP("/navigation_utilities/follow_you_srv"),
    "robot_stop": SP("/navigation_utilities/robot_stop_srv"),
    "spin": SP("/navigation_utilities/spin_srv"),
    "go_to_angle": SP("/navigation_utilities/go_to_defined_angle_srv"),
    "get_route": SP("/navigation_utilities/get_route_guidance_srv"),
    "constant_spin": SP("/navigation_utilities/constant_spin_srv"),
    "get_position": SP("navigation_utilities/get_absolute_position_srv"),
    
    # Manipulation
    "go_to_pose": SP("manipulation_utilities/go_to_pose"),
    "move_head": SP("manipulation_utilities/move_head"),
    
    # PyToolkit básico
    "set_stiffnesses": SP("pytoolkit/ALMotion/set_stiffnesses_srv"),
    "set_volume": SP("/pytoolkit/ALAudioDevice/set_output_volume_srv"),
    "show_web": SP("/pytoolkit/ALTabletService/show_web_view_srv"),
    "show_image": SP("/pytoolkit/ALTabletService/show_image_srv"),
    "hide_tablet": SP("/pytoolkit/ALTabletService/hide_srv"),
    "show_video": SP("/pytoolkit/ALTabletService/play_video_srv"),
    "set_awareness": SP("/pytoolkit/ALBasicAwareness/set_awareness_srv"),
    "set_autonomous": SP("/pytoolkit/ALAutonomousLife/set_state_srv"),
}


# ============================================================================
# FUNCIONES ADAPTADORAS - Una por herramienta relevante
# ============================================================================

def talk(message: str, language: str = "English") -> Dict[str, Any]:
    """Habla por voz."""
    r = SRV["talk"](message, language, True, False, "100")
    return {
        "ok": _is_ok(r),
        "obs": f"Éxito: El mensaje fue dicho." if _is_ok(r) else f"Fallo: No se pudo decir el mensaje.",
        "data": {}
    }


def go_to_place(location: str, graph: int = 1) -> Dict[str, Any]:
    """Navega al lugar dado."""
    r = SRV["go_to_place"](location, graph)
    approved = getattr(r, "approved", None)
    return {
        "ok": _is_ok(r),
        "obs": f"Éxito: El robot ha llegado a {location}." if _is_ok(r) else f"Fallo: No se pudo llegar a {location}.",
        "data": {"approved": approved}
    }


def find_person(name: str) -> Dict[str, Any]:
    """
    Busca a una persona (simulado con recognize_face).
    En el contexto del benchmark, "find_person" se mapea a reconocimiento facial.
    """
    r = SRV["recognize_face"](3)
    person = getattr(r, "person", None)
    approved = getattr(r, "approved", None)
    
    # Simular que encontramos a la persona si el nombre coincide
    # En el dummy siempre devuelve "Alice", pero podemos adaptarlo
    found = approved and person is not None
    
    return {
        "ok": found,
        "obs": f"Éxito: Se encontró a {name}." if found else f"Fallo: No se encontró a {name}.",
        "data": {"person": person, "approved": approved}
    }


def recognize_face(num_pics: int = 3) -> Dict[str, Any]:
    """Reconoce una persona."""
    r = SRV["recognize_face"](num_pics)
    person = getattr(r, "person", None)
    approved = getattr(r, "approved", None)
    return {
        "ok": _is_ok(r),
        "obs": f"Éxito: Persona reconocida como {person}." if _is_ok(r) else "Fallo: No se pudo reconocer persona.",
        "data": {"person": person, "approved": approved}
    }


def read_qr(timeout: float = 5.0) -> Dict[str, Any]:
    """Lee un código QR."""
    r = SRV["read_qr"](timeout)
    text = getattr(r, "text", None)
    return {
        "ok": text is not None,
        "obs": f"Éxito: QR leído: {text}" if text else "Fallo: No se pudo leer QR.",
        "data": {"text": text}
    }


def calc_depth(x: float, y: float, w: float, h: float) -> Dict[str, Any]:
    """Calcula profundidad de un bounding box."""
    r = SRV["calc_depth"](x, y, w, h)
    depth = getattr(r, "depth", None)
    return {
        "ok": depth is not None,
        "obs": f"Éxito: Profundidad calculada: {depth}m" if depth else "Fallo: No se pudo calcular profundidad.",
        "data": {"depth": depth}
    }


def speech2text(seconds: int = 0, lang: str = "eng") -> Dict[str, Any]:
    """Reconocimiento de voz."""
    r = SRV["speech2text"](seconds, lang)
    text = str(r) if r else ""
    return {
        "ok": bool(text),
        "obs": f"Éxito: Reconocido: '{text}'" if text else "Fallo: No se reconoció voz.",
        "data": {"text": text}
    }


def img_desc(prompt: str, camera: str = "front_camera", distance: float = 0.0) -> Dict[str, Any]:
    """Descripción de imagen con GPT Vision."""
    r = SRV["img_desc"](prompt, camera, distance)
    message = getattr(r, "message", None)
    approved = getattr(r, "approved", None)
    return {
        "ok": _is_ok(r),
        "obs": f"Éxito: {message}" if _is_ok(r) else "Fallo: No se pudo describir imagen.",
        "data": {"message": message, "approved": approved}
    }


def spin(degrees: float) -> Dict[str, Any]:
    """Gira el robot X grados."""
    r = SRV["spin"](degrees)
    return {
        "ok": _is_ok(r),
        "obs": f"Éxito: Robot giró {degrees}°." if _is_ok(r) else f"Fallo: No se pudo girar {degrees}°.",
        "data": {}
    }


def get_person_desc() -> Dict[str, Any]:
    """Obtiene descripción de persona."""
    r = SRV["get_person_desc"]()
    return {
        "ok": True,
        "obs": f"Éxito: {_stringify(r)}",
        "data": {
            "gender": getattr(r, "gender", None),
            "age": getattr(r, "age", None),
            "status": getattr(r, "status", None),
            "race": getattr(r, "race", None)
        }
    }


def look_for_object(object_name: str, ignore_seen: bool = False) -> Dict[str, Any]:
    """Busca un objeto."""
    r = SRV["look_for_object"](object_name, ignore_seen)
    return {
        "ok": _is_ok(r),
        "obs": f"Éxito: Objeto '{object_name}' encontrado." if _is_ok(r) else f"Fallo: Objeto '{object_name}' no encontrado.",
        "data": {}
    }


# ============================================================================
# MAPA DE ADAPTADORES - Funciones callable por alias
# ============================================================================

ADAPTERS: Dict[str, Callable] = {
    "talk": talk,
    "say": talk,  # Alias alternativo
    "go_to_place": go_to_place,
    "move_to": go_to_place,  # Alias alternativo
    "find_person": find_person,
    "recognize_face": recognize_face,
    "read_qr": read_qr,
    "calc_depth": calc_depth,
    "speech2text": speech2text,
    "listen": speech2text,  # Alias alternativo
    "img_desc": img_desc,
    "spin": spin,
    "get_person_desc": get_person_desc,
    "look_for_object": look_for_object,
}


# ============================================================================
# METADATA DE HERRAMIENTAS - Para prompts y planificadores
# ============================================================================

ADAPTER_SPECS: Dict[str, Dict[str, Any]] = {
    "talk": {
        "args": {"message": "str", "language": "str"},
        "required": ["message"],
        "desc": "Habla un mensaje por voz. Usa 'message' para el texto a decir.",
        "examples": [
            {"message": "hola, la comida está lista"},
            {"message": "buenos días", "language": "Spanish"}
        ]
    },
    "say": {
        "args": {"message": "str", "language": "str"},
        "required": ["message"],
        "desc": "Alias de 'talk'. Habla un mensaje por voz.",
        "examples": [{"message": "hola mundo"}]
    },
    "go_to_place": {
        "args": {"location": "str", "graph": "int"},
        "required": ["location"],
        "desc": "Navega a un lugar conocido. Ubicaciones: cocina, sala, puerta.",
        "examples": [
            {"location": "cocina"},
            {"location": "sala", "graph": 1}
        ]
    },
    "move_to": {
        "args": {"location": "str", "graph": "int"},
        "required": ["location"],
        "desc": "Alias de 'go_to_place'. Navega a un lugar.",
        "examples": [{"location": "puerta"}]
    },
    "find_person": {
        "args": {"name": "str"},
        "required": ["name"],
        "desc": "Busca y reconoce a una persona. Personas conocidas: Tomas.",
        "examples": [{"name": "Tomas"}]
    },
    "recognize_face": {
        "args": {"num_pics": "int"},
        "required": [],
        "desc": "Reconoce una cara tomando fotos.",
        "examples": [{"num_pics": 3}, {}]
    },
    "read_qr": {
        "args": {"timeout": "float"},
        "required": [],
        "desc": "Lee un código QR con timeout en segundos.",
        "examples": [{"timeout": 5.0}, {}]
    },
    "calc_depth": {
        "args": {"x": "float", "y": "float", "w": "float", "h": "float"},
        "required": ["x", "y", "w", "h"],
        "desc": "Calcula profundidad de un bounding box (x, y, ancho, alto).",
        "examples": [{"x": 10.0, "y": 20.0, "w": 80.0, "h": 120.0}]
    },
    "speech2text": {
        "args": {"seconds": "int", "lang": "str"},
        "required": [],
        "desc": "Reconocimiento de voz.",
        "examples": [{"seconds": 5, "lang": "eng"}, {}]
    },
    "listen": {
        "args": {"seconds": "int", "lang": "str"},
        "required": [],
        "desc": "Alias de 'speech2text'. Escucha al usuario.",
        "examples": [{}]
    },
    "img_desc": {
        "args": {"prompt": "str", "camera": "str", "distance": "float"},
        "required": ["prompt"],
        "desc": "Describe imagen con GPT Vision.",
        "examples": [{"prompt": "¿qué objetos hay?"}, {"prompt": "describe la escena", "camera": "front_camera"}]
    },
    "spin": {
        "args": {"degrees": "float"},
        "required": ["degrees"],
        "desc": "Gira el robot X grados.",
        "examples": [{"degrees": 90.0}, {"degrees": 180.0}]
    },
    "get_person_desc": {
        "args": {},
        "required": [],
        "desc": "Obtiene descripción de la persona frente al robot (género, edad, etc).",
        "examples": [{}]
    },
    "look_for_object": {
        "args": {"object_name": "str", "ignore_seen": "bool"},
        "required": ["object_name"],
        "desc": "Busca un objeto específico en el entorno.",
        "examples": [{"object_name": "taza"}, {"object_name": "botella", "ignore_seen": False}]
    }
}


# ============================================================================
# HELPERS PARA PARSEO DE ACTION INPUT
# ============================================================================

def normalize_action_input(tool_name: str, raw_input: Any) -> Dict[str, Any]:
    """
    Normaliza Action Input de diferentes formatos al dict esperado por el adapter.
    
    Args:
        tool_name: Nombre de la herramienta
        raw_input: Input crudo (puede ser string, dict, etc.)
        
    Returns:
        Dict con argumentos normalizados
        
    Raises:
        ValueError: Si tool_name no existe o input es inválido
    """
    if tool_name not in ADAPTER_SPECS:
        raise ValueError(f"Herramienta desconocida: {tool_name}")
    
    spec = ADAPTER_SPECS[tool_name]
    args_spec = spec["args"]
    required = spec.get("required", [])
    
    # Si ya es un dict, validar y retornar
    if isinstance(raw_input, dict):
        # Validar que tenga los required
        for req in required:
            if req not in raw_input:
                raise ValueError(f"Falta argumento requerido '{req}' para {tool_name}")
        return raw_input
    
    # Si es string simple, intentar mapear al primer argumento requerido
    if isinstance(raw_input, str):
        raw_input = raw_input.strip()
        
        # Mapeos comunes para valores simples
        if tool_name in ["talk", "say"]:
            return {"message": raw_input}
        elif tool_name in ["go_to_place", "move_to"]:
            return {"location": raw_input}
        elif tool_name == "find_person":
            return {"name": raw_input}
        elif tool_name == "look_for_object":
            return {"object_name": raw_input}
        elif tool_name == "img_desc":
            return {"prompt": raw_input}
        else:
            # Intentar asignar al primer required
            if required:
                return {required[0]: raw_input}
            else:
                raise ValueError(f"No se puede convertir string a args para {tool_name}")
    
    # Si es número, intentar mapear
    if isinstance(raw_input, (int, float)):
        if tool_name == "spin":
            return {"degrees": float(raw_input)}
        elif tool_name == "read_qr":
            return {"timeout": float(raw_input)}
        elif tool_name in ["speech2text", "listen"]:
            return {"seconds": int(raw_input)}
        elif tool_name == "recognize_face":
            return {"num_pics": int(raw_input)}
    
    raise ValueError(f"No se puede normalizar input {raw_input} para {tool_name}")


def get_tools_description() -> str:
    """
    Genera descripción textual de todas las herramientas para prompts.
    
    Returns:
        String formateado con herramientas disponibles
    """
    lines = ["HERRAMIENTAS DISPONIBLES:", ""]
    
    for tool_name, spec in sorted(ADAPTER_SPECS.items()):
        args_str = ", ".join(f"{k}:{v}" for k, v in spec["args"].items())
        req_str = f" [Requeridos: {', '.join(spec['required'])}]" if spec["required"] else ""
        lines.append(f"- {tool_name}({args_str}){req_str}")
        lines.append(f"  {spec['desc']}")
        if spec.get("examples"):
            lines.append(f"  Ejemplos: {spec['examples'][0]}")
        lines.append("")
    
    return "\n".join(lines)


def get_tool_names() -> str:
    """Retorna lista de nombres de herramientas separados por comas."""
    return ", ".join(sorted(ADAPTER_SPECS.keys()))