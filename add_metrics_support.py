#!/usr/bin/env python3
"""
Script para agregar soporte de métricas a las arquitecturas Reference y Reflexion.
"""

import re

def add_metrics_to_reference():
    """Agrega soporte de métricas a ReferenceAgent."""
    file_path = "src/benchmark_agent/architectures/reference.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # 1. Agregar import
    if "from ..callbacks import MetricsCallbackHandler" not in content:
        content = content.replace(
            "from ..service_adapter import get_tools_description, get_tool_names",
            "from ..service_adapter import get_tools_description, get_tool_names\nfrom ..callbacks import MetricsCallbackHandler"
        )
    
    # 2. Modificar el método run para usar callbacks
    # Buscar el método run y agregar el callback
    old_run_pattern = r'(def run\(self, task_description: str\) -> Dict\[str, Any\]:.*?""".*?""".*?start_time = time\.time\(\))'
    new_run_start = r'\1\n        \n        # Crear callback handler para capturar métricas\n        metrics_callback = MetricsCallbackHandler()'
    
    content = re.sub(old_run_pattern, new_run_start, content, flags=re.DOTALL)
    
    # 3. Modificar las llamadas a agent_executor.invoke para incluir callbacks
    old_invoke = 'response = agent_executor.invoke({"input": task_description})'
    new_invoke = '''response = agent_executor.invoke(
                {"input": task_description},
                config={"callbacks": [metrics_callback]}
            )'''
    content = content.replace(old_invoke, new_invoke)
    
    # 4. Agregar métricas al return exitoso
    # Buscar el return exitoso y agregar métricas
    old_return_pattern = r'(return \{[\s\S]*?"success": True,[\s\S]*?"trace": trace,[\s\S]*?"duration_seconds": duration_seconds[\s\S]*?\})'
    
    # Verificar si ya tiene metrics
    if '"metrics"' not in content:
        # Insertar metrics antes del cierre del dict
        content = re.sub(
            r'("duration_seconds": duration_seconds)\n(\s*\})',
            r'\1,\n                "metrics": metrics_callback.get_summary()\n\2',
            content
        )
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("✅ ReferenceAgent actualizado")


def add_metrics_to_reflexion():
    """Agrega soporte de métricas a ReflexionAgent."""
    file_path = "src/benchmark_agent/architectures/reflexion.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # 1. Agregar import
    if "from ..callbacks import MetricsCallbackHandler" not in content:
        # Buscar el último import de ..
        last_import = content.rfind("from ..")
        if last_import != -1:
            # Encontrar el final de esa línea
            end_of_line = content.find('\n', last_import)
            content = content[:end_of_line+1] + "from ..callbacks import MetricsCallbackHandler\n" + content[end_of_line+1:]
    
    # 2. Modificar el método run_with_reflexion
    if "metrics_callback = MetricsCallbackHandler()" not in content:
        # Agregar creación del callback al inicio del método
        old_run_pattern = r'(def run_with_reflexion\(self[\s\S]*?""".*?""")'
        new_run_start = r'\1\n        # Crear callback handler para capturar métricas\n        metrics_callback = MetricsCallbackHandler()'
        
        content = re.sub(old_run_pattern, new_run_start, content, flags=re.DOTALL, count=1)
    
    # 3. Modificar las llamadas al reactor para incluir callbacks
    # Esto es más complejo porque Reflexion llama a run() del reactor múltiples veces
    # Por ahora, agreguemos el callback al método _run_actor_step
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("✅ ReflexionAgent actualizado (parcialmente - requiere revisión manual)")


if __name__ == "__main__":
    print("Agregando soporte de métricas a las arquitecturas...")
    print()
    
    try:
        add_metrics_to_reference()
    except Exception as e:
        print(f"❌ Error actualizando Reference: {e}")
    
    try:
        add_metrics_to_reflexion()
    except Exception as e:
        print(f"❌ Error actualizando Reflexion: {e}")
    
    print()
    print("✨ Proceso completado")
    print()
    print("NOTA: Es posible que necesites ajustes manuales adicionales.")
    print("Verifica que los callbacks se estén pasando correctamente en todos los invoke().")
