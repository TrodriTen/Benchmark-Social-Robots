from abc import ABC, abstractmethod
from typing import List, Any, Dict, Callable
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool

class BaseAgent(ABC):
    """
    Interfaz abstracta (clase base) para todas las arquitecturas de agente.
    Esto garantiza que todas las implementaciones (ReAct, PlanThenAct, etc.) 
    tengan el mismo método de entrada 'run'.
    """
    
    def __init__(self, llm: BaseChatModel, tools: List[BaseTool] = None):
        """
        Inicializa el agente con un modelo de lenguaje y herramientas.
        
        Args:
            llm: Modelo de lenguaje
            tools: Lista de herramientas (legacy, puede ser None)
        """
        self.llm = llm
        self.tools = tools or []
        
        # NUEVO: Usar adapters en lugar de tools directamente
        from ..service_adapter import ADAPTERS, ADAPTER_SPECS
        self.adapters: Dict[str, Callable] = ADAPTERS
        self.adapter_specs: Dict[str, Dict] = ADAPTER_SPECS
    
    @abstractmethod
    def run(self, task_description: str) -> Dict[str, Any]:
        """
        El método principal que ejecuta una tarea.
        
        Args:
            task_description: La instrucción en lenguaje natural (ej: "Ve a la cocina").
        
        Returns:
            Un diccionario con los resultados y métricas del benchmark, por ejemplo:
            {
                "success": bool,
                "steps": int,
                "trace": List[str],
                "execution_time": float,
                "architecture": str
            }
        """
        pass