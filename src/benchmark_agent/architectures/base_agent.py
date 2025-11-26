from abc import ABC, abstractmethod
from typing import List, Any, Dict, Callable, Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool

class BaseAgent(ABC):
    """
    Interfaz abstracta (clase base) para todas las arquitecturas de agente.
    Esto garantiza que todas las implementaciones (ReAct, PlanThenAct, etc.) 
    tengan el mismo método de entrada 'run'.
    """
    
    def __init__(self, llm: BaseChatModel, tools: List[BaseTool] = None, use_real_tools: bool = False):
        """
        Inicializa el agente con un modelo de lenguaje y herramientas.
        
        Args:
            llm: Modelo de lenguaje
            tools: Lista de herramientas (puede ser None para usar adapters o real_tools)
            use_real_tools: Si True, usa herramientas reales de ros_langgraph_tools.
                           Si False, usa los adapters dummy por defecto.
        """
        self.llm = llm
        self.use_real_tools = use_real_tools
        
        # Determinar qué herramientas usar
        if use_real_tools:
            # Usar herramientas reales de ROS
            from ..real_tools_adapter import get_real_tools, REAL_TOOLS_METADATA
            self.tools = get_real_tools()
            self.adapters = None  # No usamos adapters con herramientas reales
            self.adapter_specs = REAL_TOOLS_METADATA
        else:
            # Usar adapters dummy (comportamiento por defecto)
            self.tools = tools or []
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