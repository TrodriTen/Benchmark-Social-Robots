"""
Script de benchmark completo para evaluar arquitecturas de agentes.

Este script integra:
1. Tareas simples y complejas con contextos variables
2. Sistema de métricas avanzado (tokens, latencia, replanificaciones)
3. Análisis comparativo automático
4. Generación de reportes detallados
"""

import json
import argparse
import sys
import os
from typing import Dict, Any, List, Optional
from pathlib import Path

# Añadir src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from benchmark_agent.llm_factory import get_chat_model
from benchmark_agent.architectures.base_agent import BaseAgent
from benchmark_agent.architectures.plan_then_act import PlanThenActAgent
from benchmark_agent.architectures.react import ReactAgent
from benchmark_agent.architectures.reflexion import ReflexionAgent
from benchmark_agent.architectures.reference import ReferenceAgent
from benchmark_agent.tools.dummy_tools import _sim_env
from benchmark_agent.world_state_generator import WorldStateGenerator, get_world_state_summary
from benchmark_agent.task_utils import suggest_context_requirements, detect_environment_type
from benchmark_agent.metrics import classify_result, generate_metrics_report
from benchmark_agent.perturbations import (
    PerturbationType,
    apply_perturbation,
    get_available_perturbations
)
from scenarios.simple_task import SCENARIO_LIST as SIMPLE_TASKS


def load_complex_tasks():
    """Carga tareas complejas si existen."""
    try:
        from scenarios.complex_tasks import COMPLEX_TASK_LIST
        return COMPLEX_TASK_LIST
    except ImportError:
        return []


def print_header(title: str, char: str = "="):
    """Imprime encabezado formateado."""
    print("\n" + char*80)
    print(title)
    print(char*80)


def print_task_header(task_id: str, description: str, category: str = None):
    """Imprime encabezado de tarea con formato."""
    print("\n" + "="*80)
    print(f"📝 TAREA: {task_id}")
    if category:
        print(f"📂 Categoría: {category}")
    print("="*80)
    print(f"Descripción: {description}")
    print("-"*80)


def print_task_result(result: Dict[str, Any], verbose: bool = False):
    """Imprime resultado de una tarea con formato."""
    success_icon = "✅" if result.get('success', False) else "❌"
    status_text = "ÉXITO" if result.get('success', False) else "FALLO"
    
    print(f"\n{success_icon} {status_text}")
    print(f"⏱️  Tiempo: {result.get('execution_time', 0):.2f}s")
    print(f"📊 Pasos ejecutados: {result.get('steps', 0)}")
    
    # Mostrar métricas si están disponibles
    if 'metrics' in result:
        metrics = result['metrics']
        if 'total_tokens' in metrics and metrics['total_tokens'] > 0:
            print(f"🔢 Tokens usados: {metrics['total_tokens']}")
        if 'llm_calls' in metrics and metrics['llm_calls'] > 0:
            print(f"🤖 Llamadas LLM: {metrics['llm_calls']}")
    
    if verbose and result.get('trace'):
        print("\n📝 Trace de ejecución:")
        for i, step in enumerate(result['trace'], 1):
            print(f"  {i}. {step[:100]}...")  # Limitar a 100 chars
        
    elif result.get('trace'):
        print(f"\n📝 Trace: {len(result['trace'])} pasos (usa --verbose para ver detalles)")
    
    print("="*80)


def print_summary(results: List[Dict[str, Any]], architecture_name: str):
    """Imprime resumen general del benchmark."""
    print_header(f"📊 RESUMEN GENERAL - {architecture_name}")
    
    total_tasks = len(results)
    successful_tasks = sum(1 for r in results if r.get('success', False))
    failed_tasks = total_tasks - successful_tasks
    success_rate = (successful_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    total_time = sum(r.get('execution_time', 0) for r in results)
    avg_time = total_time / total_tasks if total_tasks > 0 else 0
    total_steps = sum(r.get('steps', 0) for r in results)
    avg_steps = total_steps / total_tasks if total_tasks > 0 else 0
    
    print(f"\n🎯 Tareas Totales: {total_tasks}")
    print(f"✅ Éxitos: {successful_tasks}")
    print(f"❌ Fallos: {failed_tasks}")
    print(f"📈 Tasa de Éxito: {success_rate:.1f}%")
    print(f"\n⏱️  Tiempo Total: {total_time:.2f}s")
    print(f"⏱️  Tiempo Promedio: {avg_time:.2f}s")
    print(f"📊 Pasos Totales: {total_steps}")
    print(f"📊 Pasos Promedio: {avg_steps:.1f}")
    
    # Métricas agregadas si están disponibles
    total_tokens = sum(r.get('metrics', {}).get('total_tokens', 0) for r in results)
    total_llm_calls = sum(r.get('metrics', {}).get('llm_calls', 0) for r in results)
    
    if total_tokens > 0:
        print(f"\n🔢 Tokens Totales: {total_tokens:,}")
        print(f"🔢 Tokens Promedio: {total_tokens / total_tasks:.0f}")
    if total_llm_calls > 0:
        print(f"🤖 Llamadas LLM Totales: {total_llm_calls}")
        print(f"🤖 Llamadas LLM Promedio: {total_llm_calls / total_tasks:.1f}")
    
    print("\n📋 Detalle por Tarea:")
    print("-"*80)
    for result in results:
        status = "✅" if result.get('success', False) else "❌"
        task_id = result.get('task_id', 'unknown')
        exec_time = result.get('execution_time', 0)
        steps = result.get('steps', 0)
        print(f"{status} {task_id}: {exec_time:.2f}s, {steps} pasos")
    
    print("="*80)


def classify_step_result(step_trace: str) -> str:
    """
    Clasifica el resultado de un paso en:
    - 'success': ✓ Acción exitosa (movimiento, habla, etc)
    - 'info': ℹ️  Observación neutra (describe, ask, count)
    - 'fail': ✗ Fallo real (no se pudo realizar acción)
    
    Args:
        step_trace: String del trace del paso
        
    Returns:
        Tipo de paso: 'success', 'info', o 'fail'
    """
    # Extraer la observación del paso
    if " -> " not in step_trace:
        return 'info'
    
    obs_part = step_trace.split(" -> ", 1)[1]
    
    # Detectar herramientas de observación (no son fallos)
    observational_tools = [
        'describe_environment',
        'ask_person_location', 
        'count_objects',
        'recall_from_memory',
        'get_person_desc',
        'look_for_object',
        'get_current_location'
    ]
    
    is_observational = any(tool in step_trace for tool in observational_tools)
    
    # Si es herramienta observacional Y retorna ok:True, es info
    if is_observational and "'ok': True" in obs_part:
        return 'info'
    
    # Detectar éxito explícito
    success_indicators = [
        "Éxito:",
        "'ok': True, 'obs': 'Éxito:",
        "approved': 'approved'",
        "Se encontró a"  # find_person exitoso
    ]
    
    if any(indicator in obs_part for indicator in success_indicators):
        return 'success'
    
    # Detectar fallo explícito
    fail_indicators = [
        "Fallo:",
        "'ok': False",
        "approved': 'failed'",
        "No se encontró",
        "No se pudo",
        "Error fatal"
    ]
    
    if any(indicator in obs_part for indicator in fail_indicators):
        return 'fail'
    
    # Por defecto, si no es claro, es info
    return 'info'


def format_trace_with_symbols(trace: List[str]) -> List[str]:
    """
    Formatea trace con símbolos correctos:
    ✓ success, ℹ️ info, ✗ fail
    
    Args:
        trace: Lista de strings con los pasos del trace
        
    Returns:
        Lista de strings formateados con símbolos apropiados
    """
    formatted = []
    for i, step in enumerate(trace, 1):
        # Si ya tiene el formato "Paso X [símbolo]:", extraer la parte de acción
        if step.startswith("Paso ") and "]:" in step:
            # Extraer todo después de "]: "
            parts = step.split("]: ", 1)
            if len(parts) == 2:
                action_obs = parts[1]
                step_type = classify_step_result(step)
                
                symbol = {
                    'success': '✓',
                    'info': 'ℹ️',
                    'fail': '✗'
                }[step_type]
                
                formatted.append(f"Paso {i} [{symbol}]: {action_obs}")
            else:
                formatted.append(step)
        # Si es error fatal, mantenerlo como está
        elif "Error fatal" in step:
            formatted.append(step)
        else:
            # Si no tiene formato de paso, intentar clasificarlo de todos modos
            step_type = classify_step_result(step)
            symbol = {
                'success': '✓',
                'info': 'ℹ️',
                'fail': '✗'
            }[step_type]
            formatted.append(f"Paso {i} [{symbol}]: {step}")
    
    return formatted


def run_task_with_context(
    agent: BaseAgent,
    task: Dict[str, Any],
    world_state = None,
    apply_perturbations: bool = False,
    perturbation_types: List[str] = None
) -> Dict[str, Any]:
    """
    Ejecuta una tarea con contexto opcional, perturbaciones y recolección automática de métricas.
    
    Args:
        agent: Agente a usar
        task: Diccionario de tarea
        world_state: Estado del mundo opcional
        apply_perturbations: Si aplicar perturbaciones a la tarea
        perturbation_types: Lista de tipos de perturbaciones a aplicar
        
    Returns:
        Diccionario con resultados (incluye metrics desde el agente)
    """
    # Aplicar world state si se proporciona
    if world_state:
        _sim_env.apply_world_state(world_state)
    else:
        _sim_env.reset_to_initial()
    
    # Si se usan herramientas reales, resetear solo el mundo y la ubicación del robot
    if hasattr(agent, 'use_real_tools') and agent.use_real_tools:
        import subprocess
        import time
        
        try:
            # Resetear mundo de Gazebo
            subprocess.run(
                "rosservice call /gazebo/reset_world",
                shell=True,
                stderr=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL
            )
            time.sleep(1)
            
            # Resetear ubicación del robot
            from src.benchmark_agent.tools.ros_langgraph_tools import tm
            tm.set_current_place("init")
            
        except Exception as e:
            print(f"⚠️  Error al resetear: {e}")
    
    # Obtener descripción de tarea
    task_description = task.get('task', task.get('description', ''))
    
    # Aplicar perturbaciones si está habilitado
    perturbed_task = task_description
    perturbations_applied = []
    
    if apply_perturbations and perturbation_types:
        for pert_type in perturbation_types:
            try:
                perturbed_task = apply_perturbation(perturbed_task, pert_type)
                perturbations_applied.append(pert_type)
            except Exception as e:
                print(f"⚠️  No se pudo aplicar perturbación {pert_type}: {e}")
    
    # Ejecutar tarea (con o sin perturbaciones)
    result = agent.run(perturbed_task)
    
    # Formatear trace con símbolos correctos
    if 'trace' in result and result['trace']:
        result['trace'] = format_trace_with_symbols(result['trace'])
    
    # Añadir metadata de la tarea
    result["task_id"] = task.get('id', 'unknown')
    result["task_description"] = task_description  # Original
    result["task_description_perturbed"] = perturbed_task if apply_perturbations else None
    result["perturbations_applied"] = perturbations_applied if apply_perturbations else []
    
    if 'category' in task:
        result["task_category"] = task['category']
    if 'difficulty' in task:
        result["task_difficulty"] = task['difficulty']
    
    # Clasificar resultado (simplificado - usar solo success flag)
    if result.get('success', False):
        result["result_category"] = "success"
    else:
        result["result_category"] = "fail"
    
    # Las métricas ya vienen en result["metrics"] desde el agente
    # No necesitamos hacer nada adicional
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark completo de arquitecturas de agentes con métricas avanzadas.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  # Tareas simples con métricas
  python run_benchmark.py -a react -p azure -m gpt-4o-mini
  
  # Tareas complejas con contextos variables
  python run_benchmark.py -a react --task-suite complex --num-contexts 3
  
  # Benchmark completo con análisis
  python run_benchmark.py -a reference --task-suite all --analyze
  
  # Con más iteraciones para tareas complejas
  python run_benchmark.py -a reflexion --task-suite complex --max-iterations 20
        """
    )
    
    # Arquitectura y modelo
    parser.add_argument(
        "-a", "--architecture",
        required=True,
        choices=["plan-then-act", "react", "reflexion", "reference"],
        help="Arquitectura de agente a evaluar."
    )
    parser.add_argument(
        "-p", "--provider",
        default=None,
        choices=["openai", "ollama", "azure"],
        help="Proveedor de LLM (autodetecta si no se especifica)."
    )
    parser.add_argument(
        "-m", "--model",
        default=None,
        help="Modelo específico (ej: gpt-4o-mini, qwen2.5:7b-instruct)."
    )
    
    # Suite de tareas
    parser.add_argument(
        "--task-suite",
        default="simple",
        choices=["simple", "complex", "all"],
        help="Suite de tareas a ejecutar (default: simple)."
    )
    parser.add_argument(
        "--num-contexts",
        type=int,
        default=1,
        help="Número de contextos variables para tareas complejas (default: 1)."
    )
    parser.add_argument(
        "--context-seed",
        type=int,
        default=None,
        help="Semilla para generación de contextos (para reproducibilidad)."
    )
    
    # Parámetros de agente
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=15,
        help="Máximo de iteraciones para arquitecturas ReAct (default: 15, aumentado para tareas complejas)."
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=3,
        help="Máximo de intentos para Reflexion (default: 3)."
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Temperatura del LLM (default: 0.0)."
    )
    parser.add_argument(
        "--use-memory",
        action="store_true",
        default=True,
        help="Usar memoria vectorial en Reference (default: True)."
    )
    
    # Herramientas
    parser.add_argument(
        "--use-real-tools",
        action="store_true",
        help="Usar herramientas reales de ROS en lugar de adapters dummy."
    )
    
    # Perturbaciones
    parser.add_argument(
        "--perturbations",
        action="store_true",
        help="Aplicar perturbaciones a las tareas para evaluar robustez."
    )
    parser.add_argument(
        "--perturbation-types",
        nargs="+",
        default=None,
        choices=["distractors", "noise", "ambiguity", "incomplete", "all"],
        help="Tipos de perturbaciones a aplicar (default: todas si --perturbations está activo)."
    )
    
    # Análisis y output
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Generar análisis comparativo automático después del benchmark."
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Archivo de salida personalizado (default: auto-generado)."
    )
    parser.add_argument(
        "--output-dir",
        default="./benchmark_results",
        help="Directorio para guardar resultados (default: ./benchmark_results)."
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Modo verbose con detalles completos."
    )
    
    args = parser.parse_args()

    # Preparar perturbaciones
    perturbation_types_to_use = []
    if args.perturbations:
        if args.perturbation_types and "all" not in args.perturbation_types:
            perturbation_types_to_use = [PerturbationType(pt) for pt in args.perturbation_types]
        else:
            perturbation_types_to_use = get_available_perturbations()
    
    # Header
    print_header("🚀 BENCHMARK COMPLETO DE ARQUITECTURAS DE AGENTES")
    print(f"Arquitectura: {args.architecture}")
    print(f"Provider: {args.provider or 'auto-detect'}")
    print(f"Model: {args.model or 'default'}")
    print(f"Task Suite: {args.task_suite}")
    print(f"Temperature: {args.temperature}")
    print(f"Herramientas: {'REALES (ROS)' if args.use_real_tools else 'DUMMY (Simuladas)'}")
    if args.architecture == "reflexion":
        print(f"Max Attempts: {args.max_attempts}")
    elif args.architecture in ["react", "reference"]:
        print(f"Max Iterations: {args.max_iterations}")
    if args.architecture == "reference":
        print(f"Use Memory: {args.use_memory}")
    if args.task_suite in ["complex", "all"]:
        print(f"Contextos Variables: {args.num_contexts}")
        print(f"Context Seed: {args.context_seed or 'random'}")
    if args.perturbations:
        print(f"🔀 Perturbaciones: ACTIVAS ({len(perturbation_types_to_use)} tipos)")
        print(f"   Tipos: {', '.join([str(pt.value) for pt in perturbation_types_to_use])}")
    print("="*80)

    # 1. Cargar LLM
    print("\n⚙️  Cargando LLM...")
    try:
        agent_type = "react" if args.architecture in ["react", "reflexion", "reference"] else "plan_then_act"
        
        llm = get_chat_model(
            provider=args.provider,
            model=args.model,
            agent_type=agent_type,
            temperature=args.temperature
        )
        
        model_name = getattr(llm, 'model', 'unknown')
        print(f"✅ LLM cargado: {model_name}")
    
    except Exception as e:
        print(f"❌ Error al cargar LLM: {e}")
        print("\nVerifica:")
        print("  - Ollama está corriendo (si usas Ollama)")
        print("  - Variables de entorno están configuradas (OPENAI_API_KEY, AZURE_*)")
        print("  - El modelo especificado está disponible")
        return 1
    
    # 3. Instanciar arquitectura
    print("⚙️  Instanciando arquitectura...")
    agent_to_test: BaseAgent = None
    
    try:
        if args.architecture == "plan-then-act":
            agent_to_test = PlanThenActAgent(
                llm=llm,
                use_real_tools=args.use_real_tools
            )
        
        elif args.architecture == "react":
            agent_to_test = ReactAgent(
                llm=llm,
                max_iterations=args.max_iterations,
                use_real_tools=args.use_real_tools
            )
        
        elif args.architecture == "reflexion":
            agent_to_test = ReflexionAgent(
                llm=llm,
                tools=None,
                max_attempts=args.max_attempts,
                max_iterations_per_attempt=args.max_iterations,
                use_real_tools=args.use_real_tools
            )
        
        elif args.architecture == "reference":
            agent_to_test = ReferenceAgent(
                llm=llm,
                tools=None,
                max_iterations=args.max_iterations,
                use_memory=args.use_memory,
                use_real_tools=args.use_real_tools
            )
        
        print(f"✅ Arquitectura instanciada: {agent_to_test.__class__.__name__}")
        
        if args.use_real_tools:
            if hasattr(agent_to_test, 'tools'):
                print(f"   Herramientas reales disponibles: {len(agent_to_test.tools)}")
        else:
            if hasattr(agent_to_test, 'adapters'):
                print(f"   Adapters disponibles: {len(agent_to_test.adapters)}")
    
    except Exception as e:
        print(f"❌ Error al instanciar arquitectura: {e}")
        import traceback
        if args.verbose:
            traceback.print_exc()
        return 1

    # 3. Cargar tareas según suite
    print(f"\n📚 Cargando suite de tareas: {args.task_suite}...")
    
    tasks_to_run = []
    
    if args.task_suite in ["simple", "all"]:
        tasks_to_run.extend(SIMPLE_TASKS)
        print(f"   ✓ {len(SIMPLE_TASKS)} tareas simples cargadas")
    
    if args.task_suite in ["complex", "all"]:
        complex_tasks = load_complex_tasks()
        if complex_tasks:
            tasks_to_run.extend(complex_tasks)
            print(f"   ✓ {len(complex_tasks)} tareas complejas cargadas")
        else:
            print("   ⚠️  No se encontraron tareas complejas")
    
    if not tasks_to_run:
        print("❌ No hay tareas para ejecutar")
        return 1
    
    print(f"   📊 Total de tareas: {len(tasks_to_run)}")

    # 4. Generar contextos si es necesario
    world_states = []
    if args.task_suite in ["complex", "all"]:
        print(f"\n🌍 Generando {args.num_contexts} contextos variables adaptados a las tareas...")
        generator = WorldStateGenerator(seed=args.context_seed)
        
        # Analizar tipos de entorno requeridos por las tareas
        env_types_needed = set()
        for task in tasks_to_run:
            env_type = task.get('environment_type', detect_environment_type(task.get('task', '')))
            env_types_needed.add(env_type)
        
        print(f"   Tipos de entorno detectados: {', '.join(env_types_needed)}")
        
        # Generar contextos diversos
        for i in range(args.num_contexts):
            # Alternar entre tipos de entorno
            if "office" in env_types_needed and "house" in env_types_needed:
                # Si se necesitan ambos, alternar
                env_type = "office" if i % 2 == 0 else "house"
            elif "office" in env_types_needed:
                env_type = "office"
            elif "house" in env_types_needed:
                env_type = "house"
            else:
                env_type = "mixed"
            
            # Variar estilo de distribución
            if i % 3 == 0:
                ws = generator.generate_random_state(
                    environment_type=env_type, 
                    num_people=6,
                    num_objects=5
                )
            elif i % 3 == 1:
                ws = generator.generate_clustered_state(
                    environment_type=env_type, 
                    num_people=5,
                    num_objects=4
                )
            else:
                ws = generator.generate_sparse_state(
                    environment_type=env_type, 
                    num_people=4,
                    num_objects=3
                )
            
            world_states.append(ws)
            if args.verbose:
                print(f"\n   Contexto {i+1} ({env_type}):")
                summary_lines = get_world_state_summary(ws).split('\n')
                for line in summary_lines[:6]:  # Mostrar solo primeras líneas
                    print(f"   {line}")
        
        print(f"✅ Contextos generados")
    else:
        # Para tareas simples, usar contexto por defecto
        world_states = [None] * len(tasks_to_run)

    # 5. Inicializar métricas collector (crear uno nuevo por tarea)
    # No se usa collector global porque cada tarea debe tener métricas independientes

    # 6. Ejecutar tareas
    print(f"\n🏃 Ejecutando {len(tasks_to_run)} tareas...")
    print("-"*80)
    
    results = []
    
    for idx, task in enumerate(tasks_to_run, 1):
        # Seleccionar contexto (rotar si hay múltiples)
        world_state = None
        if world_states:
            world_state = world_states[idx % len(world_states)] if world_states[idx % len(world_states)] else None
        
        # Header de tarea
        category = task.get('category', None)
        print_task_header(task.get('id', f'task_{idx}'), 
                         task.get('task', task.get('description', '')),
                         category)
        
        if world_state and args.verbose:
            print("\n🌍 Contexto:")
            print(get_world_state_summary(world_state))
            print()
        
        try:
            # Ejecutar tarea con contexto
            result = run_task_with_context(
                agent=agent_to_test,
                task=task,
                world_state=world_state,
                apply_perturbations=args.perturbations,
                perturbation_types=perturbation_types_to_use
            )
            
            # Añadir metadata
            result["architecture"] = args.architecture
            result["model"] = model_name
            result["task_suite"] = args.task_suite
            
            results.append(result)
            
            # Mostrar resultado
            print_task_result(result, verbose=args.verbose)
        
        except Exception as e:
            print(f"\n❌ EXCEPCIÓN durante la ejecución: {e}")
            
            if args.verbose:
                import traceback
                traceback.print_exc()
            
            # Guardar resultado de error
            error_result = {
                "task_id": task.get('id', f'task_{idx}'),
                "task_description": task.get('task', task.get('description', '')),
                "architecture": args.architecture,
                "model": model_name,
                "task_suite": args.task_suite,
                "success": False,
                "steps": 0,
                "trace": [f"Error fatal: {str(e)}"],
                "execution_time": 0.0,
                "error": str(e),
                "result_category": "fail"
            }
            results.append(error_result)
            print("="*80)

    # 7. Mostrar resumen
    print_summary(results, agent_to_test.__class__.__name__)

    # 8. Guardar resultados
    # Crear directorio si no existe
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    if args.output:
        output_file = Path(args.output)
    else:
        # Generar nombre automático
        model_safe = model_name.replace(':', '_').replace('/', '_').replace('.', '_')
        suite_suffix = f"_{args.task_suite}" if args.task_suite != "simple" else ""
        output_file = output_dir / f"benchmark_{args.architecture}_{model_safe}{suite_suffix}.json"
    
    print(f"\n💾 Guardando resultados en: {output_file}")
    
    try:
        # Añadir metadata del benchmark
        benchmark_data = {
            "metadata": {
                "architecture": args.architecture,
                "model": model_name,
                "provider": args.provider or "auto",
                "task_suite": args.task_suite,
                "num_tasks": len(results),
                "num_contexts": args.num_contexts if args.task_suite in ["complex", "all"] else 1,
                "max_iterations": args.max_iterations,
                "temperature": args.temperature
            },
            "results": results
        }
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(benchmark_data, f, indent=2, ensure_ascii=False)
        print("✅ Resultados guardados exitosamente")
    except Exception as e:
        print(f"❌ Error al guardar resultados: {e}")
        return 1

    # 9. Generar análisis si se solicita
    if args.analyze:
        print("\n📊 Generando análisis comparativo...")
        try:
            from analyze_results import generate_full_report
            
            report_file = output_dir / f"analysis_{args.architecture}_{model_safe}.md"
            generate_full_report(
                results_dir=str(output_dir),
                output_file=str(report_file)
            )
            print(f"✅ Análisis guardado en: {report_file}")
        except Exception as e:
            print(f"⚠️  No se pudo generar análisis: {e}")

    # 10. Mensaje final
    print_header("🎉 BENCHMARK COMPLETADO")
    
    # Mostrar resumen final de métricas
    if results:
        success_rate = sum(1 for r in results if r.get('success', False)) / len(results) * 100
        print(f"\n📈 Tasa de Éxito Final: {success_rate:.1f}%")
        print(f"📁 Resultados guardados en: {output_file}")
        if args.analyze:
            print(f"📊 Análisis disponible en: {report_file}")
    
    print("="*80)
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
