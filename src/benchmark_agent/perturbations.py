"""
Módulo de perturbaciones controladas para pruebas de robustez.

Implementa:
1. Ruido ASR (simulación de errores de reconocimiento de voz)
2. Latencia artificial de inferencia
3. Distractores en observaciones
4. Mismatch de entorno (información incorrecta)
"""

from typing import Dict, Any, List, Callable
import time
import random
from dataclasses import dataclass


@dataclass
class PerturbationConfig:
    """
    Configuración de perturbaciones a aplicar.
    """
    asr_wer: float = 0.0           # Word Error Rate (0.0 = sin errores, 0.3 = 30% palabras incorrectas)
    latency_ms: int = 0            # Latencia artificial adicional en milisegundos
    distractor_prob: float = 0.0    # Probabilidad de agregar distractores (0.0-1.0)
    mismatch_prob: float = 0.0      # Probabilidad de información incorrecta (0.0-1.0)
    enabled: bool = False          # Si las perturbaciones están activas
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte configuración a diccionario."""
        return {
            "asr_wer": self.asr_wer,
            "latency_ms": self.latency_ms,
            "distractor_prob": self.distractor_prob,
            "mismatch_prob": self.mismatch_prob,
            "enabled": self.enabled
        }


class ASRNoiseSimulator:
    """
    Simula errores de reconocimiento de voz (ASR) con WER controlado.
    """
    
    # Sustituciones comunes de errores ASR en español
    COMMON_SUBSTITUTIONS = {
        "tomas": ["thomas", "tomás", "tomas"],
        "david": ["dávid", "dabid", "david"],
        "alice": ["alicia", "alise", "alice"],
        "maria": ["maría", "mari", "maria"],
        "cocina": ["cosina", "cozina", "cocina"],
        "sala": ["salla", "sala", "sala"],
        "puerta": ["puerto", "puerta", "puerta"],
        "hola": ["ola", "jola", "hola"],
        "adiós": ["adios", "adió", "adiós"],
        "comida": ["comeda", "comida", "comida"],
        "lista": ["lesta", "lista", "lista"]
    }
    
    def __init__(self, wer: float = 0.0):
        """
        Args:
            wer: Word Error Rate (0.0 - 1.0)
        """
        self.wer = max(0.0, min(1.0, wer))
    
    def apply_noise(self, text: str) -> str:
        """
        Aplica ruido ASR a un texto.
        
        Args:
            text: Texto original
            
        Returns:
            Texto con errores simulados
        """
        if self.wer <= 0.0:
            return text
        
        words = text.split()
        noisy_words = []
        
        for word in words:
            # Decidir si corromper esta palabra
            if random.random() < self.wer:
                word_lower = word.lower()
                
                # Si está en sustituciones comunes, usar una
                if word_lower in self.COMMON_SUBSTITUTIONS:
                    substitutions = self.COMMON_SUBSTITUTIONS[word_lower]
                    noisy_word = random.choice(substitutions)
                else:
                    # Corrupción genérica: insertar/eliminar/sustituir caracteres
                    corruption_type = random.choice(["substitute", "delete", "insert"])
                    
                    if corruption_type == "substitute" and len(word) > 2:
                        # Sustituir un carácter aleatorio
                        idx = random.randint(1, len(word) - 2)
                        chars = list(word)
                        chars[idx] = random.choice("aeiou")
                        noisy_word = "".join(chars)
                    
                    elif corruption_type == "delete" and len(word) > 3:
                        # Eliminar un carácter
                        idx = random.randint(1, len(word) - 2)
                        noisy_word = word[:idx] + word[idx+1:]
                    
                    elif corruption_type == "insert":
                        # Insertar un carácter
                        idx = random.randint(0, len(word))
                        noisy_word = word[:idx] + random.choice("aeiou") + word[idx:]
                    
                    else:
                        noisy_word = word
                
                noisy_words.append(noisy_word)
            else:
                noisy_words.append(word)
        
        return " ".join(noisy_words)


class LatencyInjector:
    """
    Inyecta latencia artificial en llamadas LLM.
    """
    
    def __init__(self, latency_ms: int = 0, variation_percent: float = 0.2):
        """
        Args:
            latency_ms: Latencia base en milisegundos
            variation_percent: Variación aleatoria (0.2 = ±20%)
        """
        self.latency_ms = max(0, latency_ms)
        self.variation_percent = variation_percent
    
    def inject_latency(self):
        """
        Inyecta latencia con variación aleatoria.
        """
        if self.latency_ms <= 0:
            return
        
        # Calcular latencia con variación
        variation = self.latency_ms * self.variation_percent
        actual_latency = self.latency_ms + random.uniform(-variation, variation)
        actual_latency = max(0, actual_latency)
        
        # Sleep
        time.sleep(actual_latency / 1000.0)


class DistractorInjector:
    """
    Inyecta distractores en observaciones de sensores.
    """
    
    DISTRACTOR_TEMPLATES = [
        "Ruido ambiental detectado.",
        "Movimiento en el campo visual.",
        "Sensor de proximidad activado brevemente.",
        "Sonido no identificado capturado.",
        "Cambio de iluminación detectado.",
        "Objeto no reconocido en el fondo.",
        "Interferencia temporal en cámara."
    ]
    
    def __init__(self, prob: float = 0.0):
        """
        Args:
            prob: Probabilidad de agregar distractor (0.0-1.0)
        """
        self.prob = max(0.0, min(1.0, prob))
    
    def maybe_add_distractor(self, observation: str) -> str:
        """
        Agrega distractor a una observación con probabilidad configurada.
        
        Args:
            observation: Observación original
            
        Returns:
            Observación posiblemente con distractor
        """
        if random.random() < self.prob:
            distractor = random.choice(self.DISTRACTOR_TEMPLATES)
            # Agregar distractor antes o después
            if random.random() < 0.5:
                return f"{distractor} {observation}"
            else:
                return f"{observation} {distractor}"
        return observation


class EnvironmentMismatchInjector:
    """
    Inyecta información incorrecta sobre el entorno (mismatch).
    """
    
    def __init__(self, prob: float = 0.0):
        """
        Args:
            prob: Probabilidad de información incorrecta (0.0-1.0)
        """
        self.prob = max(0.0, min(1.0, prob))
    
    def maybe_inject_mismatch(
        self, 
        observation: Dict[str, Any],
        mismatch_type: str = "person_location"
    ) -> Dict[str, Any]:
        """
        Inyecta mismatch en la observación.
        
        Args:
            observation: Observación original
            mismatch_type: Tipo de mismatch a inyectar
            
        Returns:
            Observación posiblemente con mismatch
        """
        if random.random() >= self.prob:
            return observation
        
        obs_copy = observation.copy()
        
        if mismatch_type == "person_location":
            # Reportar persona en ubicación incorrecta
            if "obs" in obs_copy and "no está aquí" in obs_copy["obs"]:
                # Cambiar la ubicación reportada
                wrong_locations = ["cocina", "sala", "puerta", "pasillo"]
                wrong_loc = random.choice(wrong_locations)
                obs_copy["obs"] = obs_copy["obs"].replace("está en ", f"está en {wrong_loc} [INCORRECTO] ")
        
        elif mismatch_type == "navigation_success":
            # Reportar éxito cuando hubo fallo (o viceversa)
            if "ok" in obs_copy:
                obs_copy["ok"] = not obs_copy["ok"]
                if obs_copy["ok"]:
                    obs_copy["obs"] = "Éxito: " + obs_copy.get("obs", "")
                else:
                    obs_copy["obs"] = "Fallo: " + obs_copy.get("obs", "")
        
        return obs_copy


class PerturbationManager:
    """
    Gestor centralizado de perturbaciones.
    """
    
    def __init__(self, config: PerturbationConfig):
        """
        Args:
            config: Configuración de perturbaciones
        """
        self.config = config
        self.asr_noise = ASRNoiseSimulator(config.asr_wer)
        self.latency = LatencyInjector(config.latency_ms)
        self.distractor = DistractorInjector(config.distractor_prob)
        self.mismatch = EnvironmentMismatchInjector(config.mismatch_prob)
        self.perturbations_applied = 0
    
    def apply_to_task_input(self, task_description: str) -> str:
        """
        Aplica perturbaciones al input de tarea (ASR noise).
        
        Args:
            task_description: Descripción original de tarea
            
        Returns:
            Descripción posiblemente con ruido ASR
        """
        if not self.config.enabled:
            return task_description
        
        perturbed = self.asr_noise.apply_noise(task_description)
        if perturbed != task_description:
            self.perturbations_applied += 1
        return perturbed
    
    def apply_before_llm_call(self):
        """
        Aplica perturbaciones antes de llamada LLM (latencia).
        """
        if not self.config.enabled:
            return
        
        self.latency.inject_latency()
    
    def apply_to_observation(
        self, 
        observation: Dict[str, Any],
        obs_type: str = "sensor"
    ) -> Dict[str, Any]:
        """
        Aplica perturbaciones a una observación.
        
        Args:
            observation: Observación original
            obs_type: Tipo de observación (sensor, navigation, etc.)
            
        Returns:
            Observación con perturbaciones aplicadas
        """
        if not self.config.enabled:
            return observation
        
        obs_copy = observation.copy()
        
        # Agregar distractores a la observación de texto
        if "obs" in obs_copy and isinstance(obs_copy["obs"], str):
            original_obs = obs_copy["obs"]
            obs_copy["obs"] = self.distractor.maybe_add_distractor(obs_copy["obs"])
            if obs_copy["obs"] != original_obs:
                self.perturbations_applied += 1
        
        # Inyectar mismatch según tipo
        if obs_type == "person_search":
            obs_copy = self.mismatch.maybe_inject_mismatch(obs_copy, "person_location")
        elif obs_type == "navigation":
            obs_copy = self.mismatch.maybe_inject_mismatch(obs_copy, "navigation_success")
        
        return obs_copy
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de perturbaciones aplicadas.
        
        Returns:
            Diccionario con estadísticas
        """
        return {
            "config": self.config.to_dict(),
            "perturbations_applied": self.perturbations_applied
        }


def create_perturbation_levels() -> Dict[str, PerturbationConfig]:
    """
    Crea configuraciones predefinidas de perturbación.
    
    Returns:
        Diccionario de niveles de perturbación
    """
    return {
        "baseline": PerturbationConfig(
            asr_wer=0.0,
            latency_ms=0,
            distractor_prob=0.0,
            mismatch_prob=0.0,
            enabled=False
        ),
        
        "mild": PerturbationConfig(
            asr_wer=0.1,          # 10% WER
            latency_ms=100,        # +100ms latencia
            distractor_prob=0.1,   # 10% distractores
            mismatch_prob=0.05,    # 5% mismatch
            enabled=True
        ),
        
        "moderate": PerturbationConfig(
            asr_wer=0.2,          # 20% WER
            latency_ms=300,        # +300ms latencia
            distractor_prob=0.2,   # 20% distractores
            mismatch_prob=0.1,     # 10% mismatch
            enabled=True
        ),
        
        "severe": PerturbationConfig(
            asr_wer=0.3,          # 30% WER
            latency_ms=500,        # +500ms latencia
            distractor_prob=0.3,   # 30% distractores
            mismatch_prob=0.2,     # 20% mismatch
            enabled=True
        )
    }


# =============================================================================
# API simplificada para compatibilidad con run_benchmark.py
# =============================================================================

from enum import Enum

class PerturbationType(Enum):
    """Tipos de perturbación disponibles."""
    DISTRACTORS = "distractors"
    NOISE = "noise"
    AMBIGUITY = "ambiguity"
    INCOMPLETE = "incomplete"


def get_available_perturbations() -> List[str]:
    """
    Retorna lista de tipos de perturbación disponibles.
    
    Returns:
        Lista de strings con nombres de perturbaciones
    """
    return [p.value for p in PerturbationType]


def apply_perturbation(task_description: str, perturbation_types: List[PerturbationType]) -> str:
    """
    Aplica perturbaciones a una descripción de tarea.
    
    Args:
        task_description: Descripción original de la tarea
        perturbation_types: Lista de tipos de perturbación a aplicar
        
    Returns:
        Descripción de tarea perturbada
    """
    perturbed = task_description
    
    for p_type in perturbation_types:
        if p_type == PerturbationType.DISTRACTORS:
            # Agregar información irrelevante
            distractors = [
                " (Note: The weather is sunny today.)",
                " (By the way, it's Tuesday.)",
                " (Remember that your battery is at 85%.)",
                " (The temperature is 22°C.)"
            ]
            perturbed += random.choice(distractors)
            
        elif p_type == PerturbationType.NOISE:
            # Agregar ruido ASR simulado
            simulator = ASRNoiseSimulator(wer=0.15)
            perturbed = simulator.apply_noise(perturbed)
            
        elif p_type == PerturbationType.AMBIGUITY:
            # Hacer la tarea más ambigua
            ambiguity_phrases = [
                " Maybe check the nearby area first.",
                " It might be there or somewhere close.",
                " You could try looking around.",
                " Perhaps start somewhere."
            ]
            perturbed += random.choice(ambiguity_phrases)
            
        elif p_type == PerturbationType.INCOMPLETE:
            # Remover información al azar
            words = perturbed.split()
            if len(words) > 5:
                # Remover 1-2 palabras aleatorias
                num_to_remove = random.randint(1, min(2, len(words) // 3))
                indices_to_remove = random.sample(range(1, len(words) - 1), num_to_remove)
                perturbed = " ".join([w for i, w in enumerate(words) if i not in indices_to_remove])
                perturbed += " [...]"
    
    return perturbed
