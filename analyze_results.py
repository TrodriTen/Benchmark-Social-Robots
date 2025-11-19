"""
Módulo de análisis comparativo de resultados de benchmark.

Genera:
1. Tablas comparativas (Arquitectura × LLM)
2. Análisis de degradación con perturbaciones
3. Guías de selección arquitectónica
4. Visualizaciones (requiere matplotlib)
"""

import json
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys


def load_results(results_file: str) -> List[Dict[str, Any]]:
    """
    Carga resultados de benchmark desde archivo JSON.
    
    Args:
        results_file: Ruta al archivo de resultados
        
    Returns:
        Lista de resultados
    """
    with open(results_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def aggregate_by_architecture(results_files: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Agrega resultados por arquitectura.
    
    Args:
        results_files: Lista de archivos de resultados
        
    Returns:
        Diccionario de agregaciones por arquitectura
    """
    aggregated = {}
    
    for file in results_files:
        try:
            results = load_results(file)
            if not results:
                continue
            
            arch = results[0].get("architecture", "unknown")
            model = results[0].get("model", "unknown")
            
            key = f"{arch}_{model}"
            
            # Calcular métricas agregadas
            total_tasks = len(results)
            successful = sum(1 for r in results if r.get("success", False))
            
            total_time = sum(r.get("execution_time", 0) for r in results)
            total_steps = sum(r.get("steps", 0) for r in results)
            total_tokens = sum(r.get("metrics", {}).get("total_tokens", 0) for r in results)
            
            aggregated[key] = {
                "architecture": arch,
                "model": model,
                "total_tasks": total_tasks,
                "successful_tasks": successful,
                "success_rate": round(successful / total_tasks * 100, 1) if total_tasks > 0 else 0,
                "avg_time": round(total_time / total_tasks, 2) if total_tasks > 0 else 0,
                "avg_steps": round(total_steps / total_tasks, 1) if total_tasks > 0 else 0,
                "avg_tokens": round(total_tokens / total_tasks, 1) if total_tasks > 0 else 0,
                "total_tokens": total_tokens,
                "total_time": round(total_time, 2)
            }
        
        except Exception as e:
            print(f"Error procesando {file}: {e}", file=sys.stderr)
    
    return aggregated


def generate_comparison_table(aggregated: Dict[str, Dict[str, Any]]) -> str:
    """
    Genera tabla comparativa en formato markdown.
    
    Args:
        aggregated: Resultados agregados por arquitectura
        
    Returns:
        Tabla en formato markdown
    """
    table = "# Tabla Comparativa: Arquitectura × LLM\n\n"
    table += "| Arquitectura | Modelo | Tareas | Éxito (%) | Tiempo Avg (s) | Pasos Avg | Tokens Avg |\n"
    table += "|-------------|--------|--------|-----------|----------------|-----------|------------|\n"
    
    # Ordenar por tasa de éxito descendente
    sorted_items = sorted(
        aggregated.items(),
        key=lambda x: (x[1]["success_rate"], -x[1]["avg_time"]),
        reverse=True
    )
    
    for key, data in sorted_items:
        table += f"| {data['architecture']} | {data['model']} | {data['total_tasks']} | "
        table += f"{data['success_rate']:.1f}% | {data['avg_time']:.2f} | "
        table += f"{data['avg_steps']:.1f} | {data['avg_tokens']:.1f} |\n"
    
    return table


def analyze_degradation(
    baseline_results: List[Dict[str, Any]],
    perturbed_results: List[Dict[str, Any]],
    perturbation_level: str = "unknown"
) -> Dict[str, Any]:
    """
    Analiza degradación relativa con respecto a baseline.
    
    Args:
        baseline_results: Resultados sin perturbaciones
        perturbed_results: Resultados con perturbaciones
        perturbation_level: Nivel de perturbación aplicado
        
    Returns:
        Análisis de degradación
    """
    # Calcular métricas baseline
    baseline_success = sum(1 for r in baseline_results if r.get("success", False))
    baseline_success_rate = baseline_success / len(baseline_results) if baseline_results else 0
    
    baseline_avg_time = sum(r.get("execution_time", 0) for r in baseline_results) / len(baseline_results) if baseline_results else 0
    baseline_avg_steps = sum(r.get("steps", 0) for r in baseline_results) / len(baseline_results) if baseline_results else 0
    
    # Calcular métricas con perturbaciones
    perturbed_success = sum(1 for r in perturbed_results if r.get("success", False))
    perturbed_success_rate = perturbed_success / len(perturbed_results) if perturbed_results else 0
    
    perturbed_avg_time = sum(r.get("execution_time", 0) for r in perturbed_results) / len(perturbed_results) if perturbed_results else 0
    perturbed_avg_steps = sum(r.get("steps", 0) for r in perturbed_results) / len(perturbed_results) if perturbed_results else 0
    
    # Calcular degradación relativa
    degradation_success = baseline_success_rate - perturbed_success_rate
    degradation_time = ((perturbed_avg_time - baseline_avg_time) / baseline_avg_time * 100) if baseline_avg_time > 0 else 0
    degradation_steps = ((perturbed_avg_steps - baseline_avg_steps) / baseline_avg_steps * 100) if baseline_avg_steps > 0 else 0
    
    return {
        "perturbation_level": perturbation_level,
        "baseline": {
            "success_rate": round(baseline_success_rate * 100, 1),
            "avg_time": round(baseline_avg_time, 2),
            "avg_steps": round(baseline_avg_steps, 1)
        },
        "perturbed": {
            "success_rate": round(perturbed_success_rate * 100, 1),
            "avg_time": round(perturbed_avg_time, 2),
            "avg_steps": round(perturbed_avg_steps, 1)
        },
        "degradation": {
            "success_rate_drop": round(degradation_success * 100, 1),
            "time_increase_pct": round(degradation_time, 1),
            "steps_increase_pct": round(degradation_steps, 1)
        }
    }


def generate_selection_guide(aggregated: Dict[str, Dict[str, Any]]) -> str:
    """
    Genera guía de selección arquitectónica basada en restricciones.
    
    Args:
        aggregated: Resultados agregados por arquitectura
        
    Returns:
        Guía de selección en markdown
    """
    guide = "# Guía de Selección Arquitectónica\n\n"
    
    # Ordenar por diferentes criterios
    by_success = sorted(aggregated.items(), key=lambda x: x[1]["success_rate"], reverse=True)
    by_speed = sorted(aggregated.items(), key=lambda x: x[1]["avg_time"])
    by_efficiency = sorted(aggregated.items(), key=lambda x: x[1]["avg_tokens"])
    
    guide += "## Recomendaciones por Restricción\n\n"
    
    guide += "### Máxima Fiabilidad (Success Rate)\n"
    guide += "Para aplicaciones críticas donde el éxito es prioritario:\n\n"
    for i, (key, data) in enumerate(by_success[:3], 1):
        guide += f"{i}. **{data['architecture']}** con {data['model']}: "
        guide += f"{data['success_rate']:.1f}% éxito, "
        guide += f"{data['avg_time']:.2f}s promedio\n"
    
    guide += "\n### Mínima Latencia (Speed)\n"
    guide += "Para aplicaciones con restricciones temporales estrictas:\n\n"
    for i, (key, data) in enumerate(by_speed[:3], 1):
        guide += f"{i}. **{data['architecture']}** con {data['model']}: "
        guide += f"{data['avg_time']:.2f}s promedio, "
        guide += f"{data['success_rate']:.1f}% éxito\n"
    
    guide += "\n### Mínimo Costo (Token Efficiency)\n"
    guide += "Para aplicaciones con restricciones de presupuesto:\n\n"
    for i, (key, data) in enumerate(by_efficiency[:3], 1):
        guide += f"{i}. **{data['architecture']}** con {data['model']}: "
        guide += f"{data['avg_tokens']:.0f} tokens promedio, "
        guide += f"{data['success_rate']:.1f}% éxito\n"
    
    guide += "\n## Análisis Trade-offs\n\n"
    
    # Identificar arquitecturas balanceadas
    guide += "### Arquitecturas Balanceadas\n"
    guide += "Compromiso entre éxito, velocidad y costo:\n\n"
    
    # Calcular score balanceado (normalizado)
    scores = []
    for key, data in aggregated.items():
        # Normalizar métricas (invertir tiempo y tokens para que mayor = mejor)
        max_success = max(d["success_rate"] for d in aggregated.values())
        min_time = min(d["avg_time"] for d in aggregated.values()) or 1
        min_tokens = min(d["avg_tokens"] for d in aggregated.values()) or 1
        
        score = (
            (data["success_rate"] / max_success if max_success > 0 else 0) * 0.5 +
            (min_time / data["avg_time"] if data["avg_time"] > 0 else 0) * 0.3 +
            (min_tokens / data["avg_tokens"] if data["avg_tokens"] > 0 else 0) * 0.2
        )
        scores.append((key, data, score))
    
    scores.sort(key=lambda x: x[2], reverse=True)
    
    for i, (key, data, score) in enumerate(scores[:3], 1):
        guide += f"{i}. **{data['architecture']}** con {data['model']} (score: {score:.2f})\n"
        guide += f"   - Éxito: {data['success_rate']:.1f}%\n"
        guide += f"   - Tiempo: {data['avg_time']:.2f}s\n"
        guide += f"   - Tokens: {data['avg_tokens']:.0f}\n\n"
    
    return guide


def generate_full_report(
    results_files: List[str],
    output_file: str = "analysis_report.md"
):
    """
    Genera reporte completo de análisis.
    
    Args:
        results_files: Lista de archivos de resultados
        output_file: Archivo de salida para el reporte
    """
    print(f"📊 Analizando {len(results_files)} archivos de resultados...")
    
    # Agregar resultados
    aggregated = aggregate_by_architecture(results_files)
    
    if not aggregated:
        print("❌ No se encontraron resultados válidos")
        return
    
    print(f"✅ {len(aggregated)} configuraciones analizadas")
    
    # Generar reporte
    report = "# Reporte de Análisis Comparativo\n\n"
    report += f"**Fecha**: {Path().resolve()}\n\n"
    report += f"**Configuraciones Analizadas**: {len(aggregated)}\n\n"
    
    # Tabla comparativa
    report += generate_comparison_table(aggregated)
    report += "\n\n"
    
    # Guía de selección
    report += generate_selection_guide(aggregated)
    
    # Guardar reporte
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ Reporte guardado en: {output_file}")
    
    # Mostrar resumen en consola
    print("\n" + "="*80)
    print("📊 RESUMEN DE ANÁLISIS")
    print("="*80)
    print(generate_comparison_table(aggregated))


if __name__ == "__main__":
    import glob
    
    # Buscar todos los archivos de resultados
    results_files = glob.glob("benchmark_results_*.json")
    
    if not results_files:
        print("❌ No se encontraron archivos de resultados (benchmark_results_*.json)")
        sys.exit(1)
    
    print(f"Encontrados {len(results_files)} archivos de resultados:")
    for f in results_files:
        print(f"  - {f}")
    print()
    
    generate_full_report(results_files)
