"""
Script de benchmark para evaluar arquitecturas de agentes con el nuevo service_adapter.

Este script:
1. Carga el LLM configurado (Ollama, OpenAI, Azure)
2. Instancia la arquitectura seleccionada con adapters en lugar de tools legacy
3. Ejecuta escenarios de prueba definidos en scenarios/simple_task.py
4. Guarda resultados en formato JSON
"""

import json
import argparse
import sys
import os
from typing import Dict, Any, List

# Añadir src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from benchmark_agent.llm_factory import get_chat_model
from benchmark_agent.architectures.base_agent import BaseAgent
from benchmark_agent.architectures.plan_then_act import PlanThenActAgent
from benchmark_agent.architectures.react import ReactAgent
from benchmark_agent.architectures.reflexion import ReflexionAgent
from benchmark_agent.architectures.reference import ReferenceAgent
from scenarios.simple_task import SCENARIO_LIST


def print_task_header(task_id: str, description: str):
    """Imprime encabezado de tarea con formato."""
    print("\n" + "="*80)
    print(f"📝 TAREA: {task_id}")
    print("="*80)
    print(f"Descripción: {description}")
    print("-"*80)


def print_task_result(result: Dict[str, Any]):
    """Imprime resultado de una tarea con formato."""
    success_icon = "✅" if result['success'] else "❌"
    status_text = "ÉXITO" if result['success'] else "FALLO"
    
    print(f"\n{success_icon} {status_text}")
    print(f"⏱️  Tiempo: {result['execution_time']:.2f}s")
    print(f"📊 Pasos ejecutados: {result['steps']}")
    
    if result.get('trace'):
        print("\n📝 Trace de ejecución:")
        for i, step in enumerate(result['trace'][:5], 1):  # Mostrar primeros 5 pasos
            print(f"  {i}. {step}")
        if len(result['trace']) > 5:
            print(f"  ... (+{len(result['trace']) - 5} pasos más)")
    
    print("="*80)


def print_summary(results: List[Dict[str, Any]], architecture_name: str):
    """Imprime resumen general del benchmark."""
    print("\n" + "="*80)
    print(f"📊 RESUMEN GENERAL - {architecture_name}")
    print("="*80)
    
    total_tasks = len(results)
    successful_tasks = sum(1 for r in results if r['success'])
    failed_tasks = total_tasks - successful_tasks
    success_rate = (successful_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    total_time = sum(r['execution_time'] for r in results)
    avg_time = total_time / total_tasks if total_tasks > 0 else 0
    total_steps = sum(r['steps'] for r in results)
    avg_steps = total_steps / total_tasks if total_tasks > 0 else 0
    
    print(f"\n🎯 Tareas Totales: {total_tasks}")
    print(f"✅ Éxitos: {successful_tasks}")
    print(f"❌ Fallos: {failed_tasks}")
    print(f"📈 Tasa de Éxito: {success_rate:.1f}%")
    print(f"\n⏱️  Tiempo Total: {total_time:.2f}s")
    print(f"⏱️  Tiempo Promedio: {avg_time:.2f}s")
    print(f"📊 Pasos Totales: {total_steps}")
    print(f"📊 Pasos Promedio: {avg_steps:.1f}")
    
    print("\n📋 Detalle por Tarea:")
    print("-"*80)
    for result in results:
        status = "✅" if result['success'] else "❌"
        print(f"{status} {result['task_id']}: {result['execution_time']:.2f}s, {result['steps']} pasos")
    
    print("="*80)


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark de arquitecturas de agentes con service_adapter.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python run_benchmark.py -a plan-then-act
  python run_benchmark.py -a react -p ollama -m qwen2.5:7b-instruct
  python run_benchmark.py -a reflexion -p azure -m gpt-4o-mini
  python run_benchmark.py -a reference --max-attempts 3
        """
    )
    
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
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=10,
        help="Máximo de iteraciones para arquitecturas ReAct (default: 10)."
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
    parser.add_argument(
        "--output",
        default=None,
        help="Archivo de salida personalizado (default: auto-generado)."
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Modo verbose con detalles completos."
    )
    
    args = parser.parse_args()

    # Header
    print("\n" + "="*80)
    print("🚀 BENCHMARK DE ARQUITECTURAS DE AGENTES")
    print("="*80)
    print(f"Arquitectura: {args.architecture}")
    print(f"Provider: {args.provider or 'auto-detect'}")
    print(f"Model: {args.model or 'default'}")
    print(f"Temperature: {args.temperature}")
    if args.architecture == "reflexion":
        print(f"Max Attempts: {args.max_attempts}")
    elif args.architecture in ["react", "reference"]:
        print(f"Max Iterations: {args.max_iterations}")
    if args.architecture == "reference":
        print(f"Use Memory: {args.use_memory}")
    print("="*80)

    # 1. Cargar LLM
    print("\n⚙️  Cargando LLM...")
    try:
        # Determinar agent_type para factory (afecta stop tokens, etc.)
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

    # 2. Instanciar arquitectura
    print("\n⚙️  Instanciando arquitectura...")
    agent_to_test: BaseAgent = None
    
    try:
        if args.architecture == "plan-then-act":
            agent_to_test = PlanThenActAgent(llm=llm)
        
        elif args.architecture == "react":
            agent_to_test = ReactAgent(
                llm=llm,
                max_iterations=args.max_iterations
            )
        
        elif args.architecture == "reflexion":
            agent_to_test = ReflexionAgent(
                llm=llm,
                tools=[],  # Ya no usa tools legacy
                max_attempts=args.max_attempts,
                max_iterations_per_attempt=args.max_iterations
            )
        
        elif args.architecture == "reference":
            agent_to_test = ReferenceAgent(
                llm=llm,
                tools=[],  # Ya no usa tools legacy
                max_iterations=args.max_iterations,
                use_memory=args.use_memory
            )
        
        print(f"✅ Arquitectura instanciada: {agent_to_test.__class__.__name__}")
        
        # Verificar que tiene adapters
        if hasattr(agent_to_test, 'adapters'):
            print(f"   Adapters disponibles: {len(agent_to_test.adapters)}")
        else:
            print("   ⚠️  Advertencia: No se encontraron adapters")
    
    except Exception as e:
        print(f"❌ Error al instanciar arquitectura: {e}")
        import traceback
        if args.verbose:
            traceback.print_exc()
        return 1

    # 3. Ejecutar escenarios
    print(f"\n🏃 Ejecutando {len(SCENARIO_LIST)} escenarios...")
    print("-"*80)
    
    results = []
    
    for idx, task in enumerate(SCENARIO_LIST, 1):
        print_task_header(task['id'], task['description'])
        
        try:
            # Ejecutar tarea
            result = agent_to_test.run(task['description'])
            
            # Añadir metadata
            result["task_id"] = task['id']
            result["task_description"] = task['description']
            result["architecture"] = args.architecture
            result["model"] = model_name
            
            results.append(result)
            
            # Mostrar resultado
            print_task_result(result)
        
        except Exception as e:
            print(f"\n❌ EXCEPCIÓN durante la ejecución: {e}")
            
            if args.verbose:
                import traceback
                traceback.print_exc()
            
            # Guardar resultado de error
            error_result = {
                "task_id": task['id'],
                "task_description": task['description'],
                "architecture": args.architecture,
                "model": model_name,
                "success": False,
                "steps": 0,
                "trace": [f"Error fatal: {str(e)}"],
                "execution_time": 0.0,
                "error": str(e)
            }
            results.append(error_result)
            print("="*80)

    # 4. Mostrar resumen
    print_summary(results, agent_to_test.__class__.__name__)

    # 5. Guardar resultados
    if args.output:
        output_file = args.output
    else:
        # Generar nombre automático
        model_safe = model_name.replace(':', '_').replace('/', '_').replace('.', '_')
        output_file = f"benchmark_results_{args.architecture}_{model_safe}.json"
    
    print(f"\n💾 Guardando resultados en: {output_file}")
    
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print("✅ Resultados guardados exitosamente")
    except Exception as e:
        print(f"❌ Error al guardar resultados: {e}")
        return 1

    # 6. Mensaje final
    print("\n" + "="*80)
    print("🎉 BENCHMARK COMPLETADO")
    print("="*80)
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)