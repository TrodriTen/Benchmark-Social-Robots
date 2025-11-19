import json
import csv
import sys
from pathlib import Path
import statistics

def load_json(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def extract_metrics(results_data):
    """Extrae métricas de un archivo de resultados."""
    results = results_data.get("results", [])
    metadata = results_data.get("metadata", {})
    
    if not results:
        return None
    
    total = len(results)
    success = sum(1 for r in results if r.get("success", False))
    
    times = [r.get("execution_time", 0) for r in results]
    steps = [r.get("steps", 0) for r in results]
    tokens = [r.get("metrics", {}).get("total_tokens", 0) for r in results]
    
    return {
        "architecture": metadata.get("architecture", "unknown"),
        "success_rate": (success / total * 100) if total > 0 else 0,
        "avg_time": sum(times) / total if total > 0 else 0,
        "avg_steps": sum(steps) / total if total > 0 else 0,
        "avg_tokens": sum(tokens) / total if total > 0 else 0
    }

def generate_comparison_csv(baseline_dir, perturbed_dir, output_file):
    """Genera CSV con comparación de todas las arquitecturas."""
    
    # Recopilar datos
    data = []
    
    for condition, directory in [("Baseline", baseline_dir), ("Perturbado", perturbed_dir)]:
        for json_file in Path(directory).glob("*.json"):
            metrics = extract_metrics(load_json(json_file))
            if metrics:
                metrics["condition"] = condition
                metrics["context"] = json_file.stem.split("_")[-1]
                data.append(metrics)
    
    # Escribir CSV
    if data:
        fieldnames = ["architecture", "condition", "context", "success_rate", 
                     "avg_time", "avg_steps", "avg_tokens"]
        
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        
        print(f"✅ CSV generado: {output_file}")
    else:
        print("❌ No se encontraron datos")

def generate_summary_table(baseline_dir, perturbed_dir, output_file):
    """Genera tabla resumen con estadísticas agregadas."""
    
    summary = {}
    
    for condition, directory in [("Baseline", baseline_dir), ("Perturbado", perturbed_dir)]:
        for arch in ["react", "plan-then-act", "reference", "reflexion"]:
            files = list(Path(directory).glob(f"{arch}_context*.json"))
            
            if not files:
                continue
            
            all_metrics = [extract_metrics(load_json(f)) for f in files]
            all_metrics = [m for m in all_metrics if m]
            
            if not all_metrics:
                continue
            
            key = f"{arch}_{condition}"
            
            success_rates = [m["success_rate"] for m in all_metrics]
            times = [m["avg_time"] for m in all_metrics]
            steps = [m["avg_steps"] for m in all_metrics]
            tokens = [m["avg_tokens"] for m in all_metrics]
            
            summary[key] = {
                "architecture": arch,
                "condition": condition,
                "success_mean": statistics.mean(success_rates),
                "success_std": statistics.stdev(success_rates) if len(success_rates) > 1 else 0,
                "time_mean": statistics.mean(times),
                "time_std": statistics.stdev(times) if len(times) > 1 else 0,
                "steps_mean": statistics.mean(steps),
                "steps_std": statistics.stdev(steps) if len(steps) > 1 else 0,
                "tokens_mean": statistics.mean(tokens),
                "tokens_std": statistics.stdev(tokens) if len(tokens) > 1 else 0
            }
    
    # Escribir CSV
    if summary:
        fieldnames = ["architecture", "condition", "success_mean", "success_std",
                     "time_mean", "time_std", "steps_mean", "steps_std",
                     "tokens_mean", "tokens_std"]
        
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(summary.values())
        
        print(f"✅ Tabla resumen generada: {output_file}")
    else:
        print("❌ No se encontraron datos para resumen")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Uso: python generate_csv_data.py <baseline_dir> <perturbed_dir> <output_dir>")
        sys.exit(1)
    
    baseline_dir = sys.argv[1]
    perturbed_dir = sys.argv[2]
    output_dir = sys.argv[3]
    
    # Generar CSVs
    generate_comparison_csv(
        baseline_dir, 
        perturbed_dir,
        f"{output_dir}/datos_completos.csv"
    )
    
    generate_summary_table(
        baseline_dir,
        perturbed_dir,
        f"{output_dir}/tabla_resumen.csv"
    )
    
    print("\n✅ Todos los CSVs generados correctamente")
