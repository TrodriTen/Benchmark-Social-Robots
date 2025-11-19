#!/usr/bin/env python3
"""
Script de prueba para validar el sistema con tareas complejas.
Ejecuta un subset de tareas con contextos variables.
"""

import sys
import json
from pathlib import Path

# Agregar directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from src.benchmark_agent.llm_factory import get_chat_model
from src.benchmark_agent.service_adapter import ADAPTERS
from src.benchmark_agent.tools.dummy_tools import _sim_env
from src.benchmark_agent.world_state_generator import WorldStateGenerator, get_world_state_summary
from src.benchmark_agent.architectures.react import ReactAgent
from scenarios.complex_tasks import get_tasks_by_category


def test_complex_task(task: dict, architecture_class, llm, world_state=None):
    """
    Prueba una tarea compleja con una arquitectura específica.
    
    Args:
        task: Diccionario de tarea
        architecture_class: Clase de arquitectura a usar
        llm: Modelo LLM
        world_state: Estado del mundo (opcional)
    
    Returns:
        Diccionario con resultados
    """
    print(f"\n{'='*80}")
    print(f"TASK: {task['task']}")
    print(f"Category: {task['category']}")
    print(f"Difficulty: {task['difficulty']}")
    print(f"Expected tools: {', '.join(task.get('expected_tools', []))}")
    print(f"{'='*80}\n")
    
    # Aplicar world state si se proporciona
    if world_state:
        _sim_env.apply_world_state(world_state)
        print("=== World State ===")
        print(get_world_state_summary(world_state))
        print()
    else:
        _sim_env.reset_to_initial()
    
    # Crear agente (sin pasar tools, las obtiene del service_adapter)
    agent = architecture_class(llm=llm)
    
    # Ejecutar tarea
    try:
        result = agent.run(task['task'])
        
        print(f"\n{'='*80}")
        print("RESULT:")
        print(f"Success: {result.get('success', False)}")
        print(f"Output: {result.get('output', 'N/A')}")
        print(f"Steps: {len(result.get('trace', []))}")
        print(f"Duration: {result.get('duration_seconds', 0):.2f}s")
        print(f"{'='*80}\n")
        
        return {
            "task_id": task['id'],
            "task_description": task['task'],
            "success": result.get('success', False),
            "output": result.get('output', ''),
            "steps": len(result.get('trace', [])),
            "duration": result.get('duration_seconds', 0),
            "trace": result.get('trace', [])
        }
    
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "task_id": task['id'],
            "task_description": task['task'],
            "success": False,
            "error": str(e),
            "steps": 0,
            "duration": 0
        }


def main():
    """Función principal de prueba."""
    print("="*80)
    print("COMPLEX TASKS VALIDATION TEST")
    print("="*80)
    
    # Configurar LLM (Azure OpenAI)
    print("\n[1/5] Configurando LLM...")
    llm = get_chat_model(provider="azure", model="gpt-4o-mini", agent_type="react")
    print("✓ LLM configurado: Azure OpenAI gpt-4o-mini")
    
    # Crear generador de world states
    print("\n[2/5] Creando generador de contextos...")
    world_generator = WorldStateGenerator(seed=42)
    print("✓ Generador creado con seed=42")
    
    # Seleccionar subset de tareas para probar
    print("\n[3/5] Seleccionando tareas de prueba...")
    
    # Tomar 1 tarea de cada categoría
    test_tasks = []
    
    # Navigation simple
    nav_tasks = get_tasks_by_category("navigation_simple")
    if nav_tasks:
        test_tasks.append(nav_tasks[0])  # "Go to the kitchen"
    
    # Memory reasoning (la más importante para validar)
    memory_tasks = get_tasks_by_category("memory_reasoning")
    if memory_tasks:
        # Tomar la tarea de "Find out who likes strawberries"
        for task in memory_tasks:
            if "strawberries" in task['task'].lower():
                test_tasks.append(task)
                break
    
    # Perception
    perception_tasks = get_tasks_by_category("perception")
    if perception_tasks:
        # Tomar tarea de conteo
        for task in perception_tasks:
            if "count" in task['task'].lower():
                test_tasks.append(task)
                break
    
    # Search verify
    search_tasks = get_tasks_by_category("search_verify")
    if search_tasks:
        test_tasks.append(search_tasks[0])
    
    print(f"✓ Seleccionadas {len(test_tasks)} tareas para validar")
    for i, task in enumerate(test_tasks, 1):
        print(f"  {i}. [{task['category']}] {task['task'][:60]}...")
    
    # Generar world states variables
    print("\n[4/5] Generando contextos variables...")
    world_states = [
        world_generator.generate_random_state(environment_type="mixed", num_people=6),
        world_generator.generate_clustered_state(environment_type="office", num_people=5),
        world_generator.generate_sparse_state(environment_type="house", num_people=3),
        None  # Usar estado por defecto para última tarea
    ]
    print(f"✓ Generados {len(world_states)} contextos diferentes")
    
    # Ejecutar pruebas
    print("\n[5/5] Ejecutando tareas...")
    print("="*80)
    
    results = []
    for i, (task, world_state) in enumerate(zip(test_tasks, world_states), 1):
        print(f"\n>>> TEST {i}/{len(test_tasks)} <<<")
        
        result = test_complex_task(
            task=task,
            architecture_class=ReactAgent,  # Usar React como baseline
            llm=llm,
            world_state=world_state
        )
        
        results.append(result)
        
        # Pequeña pausa entre tareas
        import time
        time.sleep(1)
    
    # Resumen de resultados
    print("\n" + "="*80)
    print("RESUMEN DE RESULTADOS")
    print("="*80)
    
    successful = sum(1 for r in results if r.get('success', False))
    total = len(results)
    success_rate = (successful / total * 100) if total > 0 else 0
    
    print(f"\nTareas exitosas: {successful}/{total} ({success_rate:.1f}%)")
    print(f"Promedio de pasos: {sum(r.get('steps', 0) for r in results) / total:.1f}")
    print(f"Tiempo total: {sum(r.get('duration', 0) for r in results):.2f}s")
    
    print("\nDetalle por tarea:")
    for i, result in enumerate(results, 1):
        status = "✓" if result.get('success', False) else "✗"
        task_desc = result['task_description'][:50]
        steps = result.get('steps', 0)
        duration = result.get('duration', 0)
        print(f"  {status} Task {i}: {task_desc}... ({steps} steps, {duration:.1f}s)")
    
    # Guardar resultados
    output_file = "test_complex_tasks_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "summary": {
                "total_tasks": total,
                "successful": successful,
                "success_rate": success_rate,
                "avg_steps": sum(r.get('steps', 0) for r in results) / total,
                "total_duration": sum(r.get('duration', 0) for r in results)
            },
            "results": results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Resultados guardados en: {output_file}")
    print("\n" + "="*80)
    
    # Retornar código de salida basado en éxito
    return 0 if success_rate >= 75 else 1


if __name__ == "__main__":
    exit(main())
