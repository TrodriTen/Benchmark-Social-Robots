"""
Callback handler personalizado para capturar métricas del LLM en LangChain.
"""

from typing import Any, Dict, List, Optional
from langchain.callbacks.base import BaseCallbackHandler
from langchain_core.outputs import LLMResult
import time


class MetricsCallbackHandler(BaseCallbackHandler):
    """
    Callback handler que captura métricas de llamadas al LLM durante la ejecución.
    
    Registra:
    - Número de llamadas al LLM
    - Tokens de entrada y salida
    - Latencia de cada llamada
    - Tipo de llamada (generation, tool_call, etc.)
    """
    
    def __init__(self):
        self.llm_calls: List[Dict[str, Any]] = []
        self.total_tokens_input: int = 0
        self.total_tokens_output: int = 0
        self.total_latency: float = 0.0
        self._last_start_time: Optional[float] = None
        self._last_prompt_tokens: int = 0  # Tokens estimados del último prompt
        
    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        **kwargs: Any
    ) -> None:
        """Callback cuando inicia una llamada al LLM."""
        # Registrar tiempo de inicio (simplemente el último, asumiendo ejecución secuencial)
        self._last_start_time = time.time()
        
        # Estimar tokens de entrada basado en longitud del prompt
        # Aproximación: 1 token ≈ 4 caracteres
        total_prompt_chars = sum(len(p) for p in prompts)
        self._last_prompt_tokens = max(1, total_prompt_chars // 4)
    
    def on_llm_end(
        self,
        response: LLMResult,
        **kwargs: Any
    ) -> None:
        """Callback cuando termina una llamada al LLM."""
        # Calcular latencia
        if self._last_start_time is not None:
            latency = time.time() - self._last_start_time
            self._last_start_time = None
        else:
            latency = 0.0
        
        # Extraer información de tokens
        tokens_input = 0
        tokens_output = 0
        model_name = "unknown"
        
        # DEBUG: Verificar qué hay en llm_output
        # print(f"DEBUG: llm_output = {response.llm_output if hasattr(response, 'llm_output') else 'NO ATTRIBUTE'}")
        
        # Intentar extraer tokens de llm_output
        if hasattr(response, 'llm_output') and response.llm_output:
            llm_output = response.llm_output
            
            # OpenAI/Azure format
            if 'token_usage' in llm_output:
                token_usage = llm_output['token_usage']
                tokens_input = token_usage.get('prompt_tokens', 0)
                tokens_output = token_usage.get('completion_tokens', 0)
            
            # Ollama format
            elif 'prompt_eval_count' in llm_output:
                tokens_input = llm_output.get('prompt_eval_count', 0)
                tokens_output = llm_output.get('eval_count', 0)
        
        # Intentar extraer de generations (alternativa para algunos providers)
        if tokens_input == 0 and tokens_output == 0 and hasattr(response, 'generations'):
            for generation_list in response.generations:
                for generation in generation_list:
                    if hasattr(generation, 'generation_info') and generation.generation_info:
                        gen_info = generation.generation_info
                        # Azure OpenAI puede poner tokens aquí
                        if 'token_usage' in gen_info:
                            token_usage = gen_info['token_usage']
                            tokens_input = token_usage.get('prompt_tokens', 0)
                            tokens_output = token_usage.get('completion_tokens', 0)
                            break
                    
                    # Si no hay token_usage, estimar por longitud de texto
                    # Aproximación: 1 token ≈ 4 caracteres para inglés/español
                    if tokens_output == 0 and hasattr(generation, 'text'):
                        tokens_output = max(1, len(generation.text) // 4)
                
                if tokens_input > 0 or tokens_output > 0:
                    break
        
        # Último recurso: Si aún no tenemos tokens de salida, estimarlos del texto
        if tokens_output == 0 and hasattr(response, 'generations') and response.generations:
            total_text_len = sum(
                len(gen.text) for gen_list in response.generations 
                for gen in gen_list if hasattr(gen, 'text')
            )
            if total_text_len > 0:
                tokens_output = max(1, total_text_len // 4)
        
        # Si no tenemos tokens_input del response, usar la estimación del prompt
        if tokens_input == 0 and self._last_prompt_tokens > 0:
            tokens_input = self._last_prompt_tokens
            self._last_prompt_tokens = 0  # Resetear
        
        # Extraer model name
        if hasattr(response, 'llm_output') and response.llm_output:
            llm_output = response.llm_output
            if 'model_name' in llm_output:
                model_name = llm_output['model_name']
            elif 'model' in llm_output:
                model_name = llm_output['model']
        
        # Registrar llamada
        call_info = {
            "tokens_input": tokens_input,
            "tokens_output": tokens_output,
            "tokens_total": tokens_input + tokens_output,
            "latency": latency,
            "model": model_name,
            "timestamp": time.time()
        }
        
        self.llm_calls.append(call_info)
        self.total_tokens_input += tokens_input
        self.total_tokens_output += tokens_output
        self.total_latency += latency
    
    def on_llm_error(
        self,
        error: Exception,
        **kwargs: Any
    ) -> None:
        """Callback cuando hay un error en la llamada al LLM."""
        # Registrar error pero no lo propagamos
        pass
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Retorna resumen de métricas capturadas.
        
        Returns:
            Diccionario con todas las métricas
        """
        total_tokens = self.total_tokens_input + self.total_tokens_output
        num_calls = len(self.llm_calls)
        
        return {
            "llm_calls_count": num_calls,
            "total_tokens": total_tokens,
            # Nombres alternativos para compatibilidad
            "prompt_tokens": self.total_tokens_input,
            "completion_tokens": self.total_tokens_output,
            "input_tokens": self.total_tokens_input,
            "output_tokens": self.total_tokens_output,
            # Totales explícitos
            "total_tokens_input": self.total_tokens_input,
            "total_tokens_output": self.total_tokens_output,
            # Latencia
            "total_latency_seconds": self.total_latency,
            "total_latency": self.total_latency,
            # Promedios
            "avg_tokens_per_call": total_tokens / num_calls if num_calls > 0 else 0,
            "avg_latency_per_call": self.total_latency / num_calls if num_calls > 0 else 0,
            # Detalle y compatibilidad
            "llm_calls_detail": self.llm_calls,
            "execution_time": self.total_latency,  # Para compatibilidad
            "replannings": 0  # No aplicable en este callback
        }
    
    def reset(self):
        """Resetea las métricas para una nueva ejecución."""
        self.llm_calls = []
        self.total_tokens_input = 0
        self.total_tokens_output = 0
        self.total_latency = 0.0
        self._last_start_time = None
        self._last_prompt_tokens = 0
