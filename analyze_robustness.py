#!/usr/bin/env python3
"""
Análisis de robustez de arquitecturas agentivas.

Analiza la variabilidad de desempeño bajo múltiples contextos variables
(diferentes distribuciones de ubicaciones, personas y objetos).

Métricas de robustez:
- Desviación estándar de tasa de éxito
- Desviación estándar de tiempo de ejecución
- Desviación estándar de pasos
- Coeficiente de variación (CV) para comparar entre arquitecturas
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any
import statistics


def load_results(file_path: str) -> Dict[str, Any]:
    """Carga resultados de un archivo JSON."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def extract_metrics(results_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extrae métricas agregadas de un archivo de resultados.
    
    Returns:
        Dict con métricas: success_rate, avg_time, avg_steps, avg_tokens
    """
    results = results_data.get("results", [])
    
    if not results:
        return None
    
    total_tasks = len(results)
    successful = sum(1 for r in results if r.get("success", False))
    
    total_time = sum(r.get("execution_time", 0) for r in results)
    total_steps = sum(r.get("steps", 0) for r in results)
    
    # Tokens
    total_tokens = 0
    for r in results:
        metrics = r.get("metrics", {})
        if isinstance(metrics, dict):
            total_tokens += metrics.get("total_tokens", 0)
    
    return {
        "success_rate": (successful / total_tasks * 100) if total_tasks > 0 else 0,
        "avg_time": (total_time / total_tasks) if total_tasks > 0 else 0,
        "avg_steps": (total_steps / total_tasks) if total_tasks > 0 else 0,
        "avg_tokens": (total_tokens / total_tasks) if total_tasks > 0 else 0,
        "total_tasks": total_tasks
    }


def analyze_robustness(result_files: List[str]) -> Dict[str, Any]:
    """
    Analiza robustez de una arquitectura a través de múltiples contextos.
    
    Args:
        result_files: Lista de archivos de resultados (cada uno con un contexto diferente)
    
    Returns:
        Análisis de robustez con media, desv. estándar y coef. de variación
    """
    print(f"\n📊 Analizando robustez con {len(result_files)} contextos...")
    
    # Extraer métricas de cada contexto
    all_metrics = []
    for i, file_path in enumerate(result_files, 1):
        print(f"  Cargando contexto {i}: {Path(file_path).name}")
        try:
            data = load_results(file_path)
            metrics = extract_metrics(data)
            if metrics:
                all_metrics.append(metrics)
        except Exception as e:
            print(f"    ⚠️  Error: {e}")
    
    if not all_metrics:
        print("❌ No se pudieron extraer métricas de ningún archivo")
        return None
    
    print(f"  ✅ {len(all_metrics)} contextos procesados correctamente\n")
    
    # Calcular estadísticas
    success_rates = [m["success_rate"] for m in all_metrics]
    avg_times = [m["avg_time"] for m in all_metrics]
    avg_steps = [m["avg_steps"] for m in all_metrics]
    avg_tokens = [m["avg_tokens"] for m in all_metrics]
    
    def calc_stats(values: List[float], name: str) -> Dict[str, float]:
        """Calcula estadísticas para una métrica."""
        mean = statistics.mean(values)
        std = statistics.stdev(values) if len(values) > 1 else 0
        cv = (std / mean * 100) if mean > 0 else 0  # Coeficiente de variación en %
        
        return {
            "mean": mean,
            "std": std,
            "cv": cv,
            "min": min(values),
            "max": max(values),
            "range": max(values) - min(values)
        }
    
    analysis = {
        "num_contexts": len(all_metrics),
        "success_rate": calc_stats(success_rates, "success_rate"),
        "avg_time": calc_stats(avg_times, "avg_time"),
        "avg_steps": calc_stats(avg_steps, "avg_steps"),
        "avg_tokens": calc_stats(avg_tokens, "avg_tokens"),
        "raw_data": all_metrics
    }
    
    return analysis


def print_robustness_report(analysis: Dict[str, Any], architecture: str = "Unknown"):
    """Imprime reporte de robustez en formato legible."""
    
    print("="*80)
    print(f"📊 REPORTE DE ROBUSTEZ: {architecture}")
    print("="*80)
    print(f"Contextos evaluados: {analysis['num_contexts']}")
    print("="*80)
    print()
    
    print("┌─────────────────────────────────────────────────────────────────────────────┐")
    print("│ TASA DE ÉXITO                                                               │")
    print("├─────────────────────────────────────────────────────────────────────────────┤")
    sr = analysis["success_rate"]
    print(f"│ Media:                {sr['mean']:6.1f}%                                              │")
    print(f"│ Desviación Estándar:  {sr['std']:6.2f}%                                              │")
    print(f"│ Coef. Variación (CV): {sr['cv']:6.2f}% {'(BAJA variabilidad ✅)' if sr['cv'] < 10 else '(ALTA variabilidad ⚠️)':20s}        │")
    print(f"│ Rango:                [{sr['min']:5.1f}% - {sr['max']:5.1f}%]                                      │")
    print("└─────────────────────────────────────────────────────────────────────────────┘")
    print()
    
    print("┌─────────────────────────────────────────────────────────────────────────────┐")
    print("│ TIEMPO DE EJECUCIÓN (segundos)                                              │")
    print("├─────────────────────────────────────────────────────────────────────────────┤")
    at = analysis["avg_time"]
    print(f"│ Media:                {at['mean']:6.2f}s                                             │")
    print(f"│ Desviación Estándar:  {at['std']:6.2f}s                                             │")
    print(f"│ Coef. Variación (CV): {at['cv']:6.2f}% {'(BAJA variabilidad ✅)' if at['cv'] < 15 else '(ALTA variabilidad ⚠️)':20s}        │")
    print(f"│ Rango:                [{at['min']:5.2f}s - {at['max']:5.2f}s]                                     │")
    print("└─────────────────────────────────────────────────────────────────────────────┘")
    print()
    
    print("┌─────────────────────────────────────────────────────────────────────────────┐")
    print("│ NÚMERO DE PASOS                                                             │")
    print("├─────────────────────────────────────────────────────────────────────────────┤")
    st = analysis["avg_steps"]
    print(f"│ Media:                {st['mean']:6.1f} pasos                                        │")
    print(f"│ Desviación Estándar:  {st['std']:6.2f} pasos                                        │")
    print(f"│ Coef. Variación (CV): {st['cv']:6.2f}% {'(BAJA variabilidad ✅)' if st['cv'] < 20 else '(ALTA variabilidad ⚠️)':20s}        │")
    print(f"│ Rango:                [{st['min']:5.1f} - {st['max']:5.1f}] pasos                                  │")
    print("└─────────────────────────────────────────────────────────────────────────────┘")
    print()
    
    print("┌─────────────────────────────────────────────────────────────────────────────┐")
    print("│ CONSUMO DE TOKENS                                                           │")
    print("├─────────────────────────────────────────────────────────────────────────────┤")
    tk = analysis["avg_tokens"]
    print(f"│ Media:                {tk['mean']:8.0f} tokens                                      │")
    print(f"│ Desviación Estándar:  {tk['std']:8.0f} tokens                                      │")
    print(f"│ Coef. Variación (CV): {tk['cv']:6.2f}% {'(BAJA variabilidad ✅)' if tk['cv'] < 20 else '(ALTA variabilidad ⚠️)':20s}        │")
    print(f"│ Rango:                [{tk['min']:7.0f} - {tk['max']:7.0f}] tokens                            │")
    print("└─────────────────────────────────────────────────────────────────────────────┘")
    print()
    
    print("="*80)
    print("📈 INTERPRETACIÓN DE ROBUSTEZ")
    print("="*80)
    print()
    
    # Calcular score de robustez general
    cv_avg = (sr['cv'] + at['cv'] + st['cv']) / 3
    
    if cv_avg < 10:
        rating = "🌟 EXCELENTE"
        desc = "Muy robusto, desempeño consistente entre contextos"
    elif cv_avg < 20:
        rating = "✅ BUENO"
        desc = "Robustez aceptable, variación moderada"
    elif cv_avg < 35:
        rating = "⚠️  MODERADO"
        desc = "Variabilidad notable, requiere análisis detallado"
    else:
        rating = "❌ BAJO"
        desc = "Alta variabilidad, poca consistencia entre contextos"
    
    print(f"Coeficiente de Variación Promedio: {cv_avg:.2f}%")
    print(f"Rating de Robustez: {rating}")
    print(f"Descripción: {desc}")
    print()
    
    print("="*80)


def save_robustness_json(analysis: Dict[str, Any], output_file: str):
    """Guarda análisis de robustez en JSON."""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    print(f"💾 Análisis guardado en: {output_file}")


def main():
    if len(sys.argv) < 2:
        print("Uso: python analyze_robustness.py <archivo1.json> [archivo2.json] ...")
        print()
        print("Ejemplo:")
        print("  python analyze_robustness.py robustez_results/*.json")
        sys.exit(1)
    
    result_files = sys.argv[1:]
    
    print("="*80)
    print("🔄 ANÁLISIS DE ROBUSTEZ")
    print("="*80)
    print(f"Archivos a analizar: {len(result_files)}")
    
    # Determinar arquitectura del primer archivo
    try:
        first_data = load_results(result_files[0])
        metadata = first_data.get("metadata", {})
        architecture = metadata.get("architecture", "Unknown")
        model = metadata.get("model", "Unknown")
    except:
        architecture = "Unknown"
        model = "Unknown"
    
    # Analizar robustez
    analysis = analyze_robustness(result_files)
    
    if not analysis:
        print("❌ No se pudo completar el análisis")
        sys.exit(1)
    
    # Imprimir reporte
    print_robustness_report(analysis, f"{architecture} ({model})")
    
    # Guardar JSON
    output_file = f"robustness_analysis_{architecture}_{model}.json"
    save_robustness_json(analysis, output_file)
    
    print()
    print("✅ Análisis de robustez completado")


if __name__ == "__main__":
    main()
