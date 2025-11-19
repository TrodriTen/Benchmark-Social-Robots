#!/bin/bash
################################################################################
# SCRIPT MAESTRO DE EVALUACIÓN COMPLETA PARA TESIS
################################################################################
# 
# Este script ejecuta una evaluación completa de todas las arquitecturas
# agentivas con y sin perturbaciones, múltiples contextos, y genera reportes
# automáticos listos para incluir en la tesis.
#
# Autor: Benchmark Social Robot
# Fecha: 2025-01-18
################################################################################

set -e

# ============================================================================
# CONFIGURACIÓN GENERAL
# ============================================================================

# Modelos y providers
PROVIDER="azure"
MODEL="gpt-4o-mini"

# Arquitecturas a evaluar
ARCHITECTURES=("react" "plan-then-act" "reference" "reflexion")

# Suites de tareas
TASK_SUITE="complex"  # complex tiene más variedad para robustez

# Configuración de robustez
NUM_CONTEXTS=5  # Número de contextos por arquitectura (5 = rápido, 10 = riguroso)

# Configuración de ejecución
MAX_ITERATIONS=15
TIMEOUT=3600  # 30 minutos por arquitectura/contexto (48 tareas complejas)

# Directorio de resultados
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_BASE="tesis_results_${TIMESTAMP}"
mkdir -p "$RESULTS_BASE"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================

log_section() {
    echo ""
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${MAGENTA}$1${NC}"
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_progress() {
    echo -e "${CYAN}🔄 $1${NC}"
}

# ============================================================================
# BANNER INICIAL
# ============================================================================

clear
echo -e "${MAGENTA}"
cat << "EOF"
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║              EVALUACIÓN COMPLETA DE ARQUITECTURAS AGENTIVAS                  ║
║                   Benchmark para Tesis de Grado                              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

log_info "Directorio de resultados: $RESULTS_BASE"
log_info "Arquitecturas: ${ARCHITECTURES[*]}"
log_info "Contextos por arquitectura: $NUM_CONTEXTS"
log_info "Provider: $PROVIDER"
log_info "Modelo: $MODEL"
echo ""

# Confirmar antes de continuar
read -p "¿Desea continuar con la evaluación completa? (s/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[SsYy]$ ]]; then
    log_warning "Evaluación cancelada por el usuario"
    exit 0
fi

# Activar entorno virtual
log_progress "Activando entorno virtual..."
source ~/venvs/llm311/bin/activate
log_success "Entorno activado"

# ============================================================================
# FASE 1: BASELINE SIN PERTURBACIONES
# ============================================================================

log_section "FASE 1: EVALUACIÓN BASELINE (SIN PERTURBACIONES)"

BASELINE_DIR="$RESULTS_BASE/baseline"
mkdir -p "$BASELINE_DIR"

for arch in "${ARCHITECTURES[@]}"; do
    log_progress "Evaluando $arch (Baseline)..."
    
    for context in $(seq 1 $NUM_CONTEXTS); do
        log_info "  Contexto $context/$NUM_CONTEXTS"
        
        OUTPUT_FILE="${BASELINE_DIR}/${arch}_context${context}.json"
        
        timeout $TIMEOUT python run_benchmark.py \
            -a "$arch" \
            -p "$PROVIDER" \
            -m "$MODEL" \
            --task-suite "$TASK_SUITE" \
            --max-iterations "$MAX_ITERATIONS" \
            --context-seed "$context" \
            2>&1 | tee "${BASELINE_DIR}/${arch}_context${context}.log" > /dev/null
        
        # Mover resultado (buscar archivo más reciente que coincida con el patrón)
        # El modelo puede reportarse como "unknown" así que buscamos por arquitectura y task_suite
        if [ "$TASK_SUITE" = "simple" ]; then
            PATTERN="benchmark_results/benchmark_${arch}_*.json"
        else
            PATTERN="benchmark_results/benchmark_${arch}_*_${TASK_SUITE}.json"
        fi
        
        # Buscar el archivo más reciente que coincida
        RESULT_FILE=$(ls -t $PATTERN 2>/dev/null | head -1)
        
        if [ -n "$RESULT_FILE" ] && [ -f "$RESULT_FILE" ]; then
            mv "$RESULT_FILE" "$OUTPUT_FILE"
            log_success "    ✓ Guardado en $OUTPUT_FILE"
        else
            log_error "    ✗ No se generó resultado (patrón buscado: $PATTERN)"
        fi
        
        sleep 2
    done
    
    log_success "$arch baseline completado"
    echo ""
done

log_success "FASE 1 COMPLETADA"

# ============================================================================
# FASE 2: EVALUACIÓN CON PERTURBACIONES
# ============================================================================

log_section "FASE 2: EVALUACIÓN CON PERTURBACIONES"

PERTURBED_DIR="$RESULTS_BASE/perturbed"
mkdir -p "$PERTURBED_DIR"

# Tipos de perturbaciones a probar
PERTURBATION_TYPES="distractors noise"

for arch in "${ARCHITECTURES[@]}"; do
    log_progress "Evaluando $arch (Con Perturbaciones)..."
    
    for context in $(seq 1 $NUM_CONTEXTS); do
        log_info "  Contexto $context/$NUM_CONTEXTS"
        
        OUTPUT_FILE="${PERTURBED_DIR}/${arch}_context${context}.json"
        
        timeout $TIMEOUT python run_benchmark.py \
            -a "$arch" \
            -p "$PROVIDER" \
            -m "$MODEL" \
            --task-suite "$TASK_SUITE" \
            --max-iterations "$MAX_ITERATIONS" \
            --context-seed "$context" \
            --perturbations \
            --perturbation-types $PERTURBATION_TYPES \
            2>&1 | tee "${PERTURBED_DIR}/${arch}_context${context}.log" > /dev/null
        
        # Mover resultado (buscar archivo más reciente que coincida con el patrón)
        # El modelo puede reportarse como "unknown" así que buscamos por arquitectura y task_suite
        if [ "$TASK_SUITE" = "simple" ]; then
            PATTERN="benchmark_results/benchmark_${arch}_*.json"
        else
            PATTERN="benchmark_results/benchmark_${arch}_*_${TASK_SUITE}.json"
        fi
        
        # Buscar el archivo más reciente que coincida
        RESULT_FILE=$(ls -t $PATTERN 2>/dev/null | head -1)
        
        if [ -n "$RESULT_FILE" ] && [ -f "$RESULT_FILE" ]; then
            mv "$RESULT_FILE" "$OUTPUT_FILE"
            log_success "    ✓ Guardado en $OUTPUT_FILE"
        else
            log_error "    ✗ No se generó resultado (patrón buscado: $PATTERN)"
        fi
        
        sleep 2
    done
    
    log_success "$arch con perturbaciones completado"
    echo ""
done

log_success "FASE 2 COMPLETADA"

# ============================================================================
# FASE 3: ANÁLISIS Y GENERACIÓN DE REPORTES
# ============================================================================

log_section "FASE 3: GENERACIÓN DE REPORTES Y ANÁLISIS"

REPORTS_DIR="$RESULTS_BASE/reports"
mkdir -p "$REPORTS_DIR"

log_progress "Generando análisis de robustez para cada arquitectura..."

# Análisis de robustez para baseline
for arch in "${ARCHITECTURES[@]}"; do
    log_info "  Analizando robustez de $arch (Baseline)..."
    
    python analyze_robustness.py \
        "${BASELINE_DIR}/${arch}_context"*.json \
        > "${REPORTS_DIR}/robustez_${arch}_baseline.txt"
    
    log_success "    ✓ Reporte guardado"
done

# Análisis de robustez con perturbaciones
for arch in "${ARCHITECTURES[@]}"; do
    log_info "  Analizando robustez de $arch (Con Perturbaciones)..."
    
    python analyze_robustness.py \
        "${PERTURBED_DIR}/${arch}_context"*.json \
        > "${REPORTS_DIR}/robustez_${arch}_perturbed.txt"
    
    log_success "    ✓ Reporte guardado"
done

log_success "Análisis de robustez completado"
echo ""

# ============================================================================
# FASE 4: GENERACIÓN DE DATOS PARA GRÁFICOS Y TABLAS
# ============================================================================

log_section "FASE 4: GENERACIÓN DE DATOS PARA GRÁFICOS"

log_progress "Generando CSV para gráficos y tablas..."

# Crear script Python para generar CSVs
cat > "${REPORTS_DIR}/generate_csv_data.py" << 'EOFPYTHON'
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
EOFPYTHON

# Ejecutar generación de CSVs
python "${REPORTS_DIR}/generate_csv_data.py" \
    "$BASELINE_DIR" \
    "$PERTURBED_DIR" \
    "$REPORTS_DIR"

log_success "CSVs generados"

# ============================================================================
# FASE 5: REPORTE FINAL CONSOLIDADO
# ============================================================================

log_section "FASE 5: GENERACIÓN DE REPORTE CONSOLIDADO"

FINAL_REPORT="${REPORTS_DIR}/REPORTE_FINAL_TESIS.md"

log_progress "Generando reporte final consolidado..."

cat > "$FINAL_REPORT" << EOF
# 📊 REPORTE FINAL DE EVALUACIÓN - TESIS

**Fecha de generación**: $(date '+%Y-%m-%d %H:%M:%S')  
**Directorio de resultados**: $RESULTS_BASE

---

## 📋 Configuración de la Evaluación

- **Arquitecturas evaluadas**: ${ARCHITECTURES[*]}
- **Proveedor LLM**: $PROVIDER
- **Modelo**: $MODEL
- **Suite de tareas**: $TASK_SUITE
- **Contextos por arquitectura**: $NUM_CONTEXTS
- **Máximo de iteraciones**: $MAX_ITERATIONS

---

## 🎯 Estructura de Resultados

\`\`\`
$RESULTS_BASE/
├── baseline/              # Resultados sin perturbaciones
│   ├── react_context1.json
│   ├── react_context2.json
│   ├── ...
│   ├── plan-then-act_context1.json
│   ├── ...
│
├── perturbed/             # Resultados con perturbaciones
│   ├── react_context1.json
│   ├── ...
│
└── reports/               # Análisis y reportes
    ├── robustez_react_baseline.txt
    ├── robustez_react_perturbed.txt
    ├── ...
    ├── datos_completos.csv        # ← PARA GRÁFICOS
    ├── tabla_resumen.csv          # ← PARA TABLAS
    └── REPORTE_FINAL_TESIS.md     # ← ESTE ARCHIVO
\`\`\`

---

## 📊 Archivos Clave para la Tesis

### 1. Datos Completos (para gráficos)
**Archivo**: \`reports/datos_completos.csv\`

Contiene todas las métricas individuales de cada contexto. Usar para:
- Gráficos de barras (tasa de éxito por arquitectura)
- Gráficos de dispersión (tiempo vs éxito)
- Box plots (distribución de métricas)

**Columnas**:
- \`architecture\`: Nombre de la arquitectura
- \`condition\`: "Baseline" o "Perturbado"
- \`context\`: Número de contexto (1-$NUM_CONTEXTS)
- \`success_rate\`: Tasa de éxito (%)
- \`avg_time\`: Tiempo promedio (segundos)
- \`avg_steps\`: Pasos promedio
- \`avg_tokens\`: Tokens promedio

### 2. Tabla Resumen (para tablas en LaTeX)
**Archivo**: \`reports/tabla_resumen.csv\`

Contiene estadísticas agregadas (media ± desv. estándar). Usar para:
- Tabla comparativa principal de la tesis
- Análisis de robustez (desviación estándar)

**Columnas**:
- \`architecture\`: Nombre de la arquitectura
- \`condition\`: "Baseline" o "Perturbado"
- \`success_mean\`: Media de tasa de éxito
- \`success_std\`: Desviación estándar de tasa de éxito
- \`time_mean\`: Media de tiempo
- \`time_std\`: Desviación estándar de tiempo
- \`steps_mean\`: Media de pasos
- \`steps_std\`: Desviación estándar de pasos
- \`tokens_mean\`: Media de tokens
- \`tokens_std\`: Desviación estándar de tokens

### 3. Reportes de Robustez (interpretación)
**Archivos**: \`reports/robustez_*_baseline.txt\` y \`reports/robustez_*_perturbed.txt\`

Contienen análisis detallado de robustez con:
- Coeficiente de variación (CV)
- Interpretación de consistencia
- Rating de robustez

---

## 📈 Cómo Usar los Datos en la Tesis

### Para Gráficos (Python/Matplotlib o R)

\`\`\`python
import pandas as pd
import matplotlib.pyplot as plt

# Cargar datos
df = pd.read_csv('reports/datos_completos.csv')

# Gráfico de barras: Tasa de éxito por arquitectura
baseline = df[df['condition'] == 'Baseline']
plt.figure(figsize=(10, 6))
baseline.groupby('architecture')['success_rate'].mean().plot(kind='bar')
plt.title('Tasa de Éxito por Arquitectura')
plt.ylabel('Tasa de Éxito (%)')
plt.xlabel('Arquitectura')
plt.tight_layout()
plt.savefig('success_rate_comparison.png', dpi=300)
\`\`\`

### Para Tablas LaTeX

\`\`\`python
import pandas as pd

# Cargar resumen
df = pd.read_csv('reports/tabla_resumen.csv')

# Filtrar baseline
baseline = df[df['condition'] == 'Baseline']

# Generar LaTeX
print(baseline[['architecture', 'success_mean', 'success_std', 
                'time_mean', 'time_std']].to_latex(index=False))
\`\`\`

O manualmente:

\`\`\`latex
\\begin{table}[h]
\\centering
\\caption{Comparación de Arquitecturas Agentivas}
\\begin{tabular}{lcccc}
\\toprule
Arquitectura & Éxito (\\%) & Tiempo (s) & Pasos & Tokens \\\\
\\midrule
ReAct        & 95.0 ± 5.2 & 10.2 ± 1.5 & 3.2 ± 0.8 & 14748 ± 2341 \\\\
Plan-Then-Act& 92.0 ± 8.1 & 12.5 ± 2.3 & 4.1 ± 1.2 & 16523 ± 3102 \\\\
Reference    & 97.0 ± 3.2 & 11.8 ± 1.2 & 3.8 ± 0.6 & 15987 ± 1876 \\\\
Reflexion    & 90.0 ± 12.5 & 15.3 ± 4.1 & 5.2 ± 2.1 & 18234 ± 4567 \\\\
\\bottomrule
\\end{tabular}
\\end{table}
\`\`\`

---

## 🔍 Análisis de Robustez

Ver reportes individuales en:
EOF

# Agregar lista de reportes de robustez
for arch in "${ARCHITECTURES[@]}"; do
    echo "- \`reports/robustez_${arch}_baseline.txt\`" >> "$FINAL_REPORT"
    echo "- \`reports/robustez_${arch}_perturbed.txt\`" >> "$FINAL_REPORT"
done

cat >> "$FINAL_REPORT" << EOF

---

## ✅ Checklist para la Tesis

### Sección de Resultados
- [ ] Tabla comparativa principal (usar \`tabla_resumen.csv\`)
- [ ] Gráfico de tasa de éxito (usar \`datos_completos.csv\`)
- [ ] Gráfico de tiempo de ejecución
- [ ] Gráfico de consumo de tokens
- [ ] Análisis de robustez (usar reportes de robustez)

### Sección de Discusión
- [ ] Comparar con baseline (con vs sin perturbaciones)
- [ ] Interpretar coeficientes de variación
- [ ] Discutir trade-offs (éxito vs tiempo vs costo)
- [ ] Identificar arquitectura óptima por escenario

### Sección de Conclusiones
- [ ] Resumir hallazgos principales
- [ ] Recomendaciones de selección arquitectónica
- [ ] Limitaciones del estudio
- [ ] Trabajo futuro

---

## 📞 Soporte

Para regenerar gráficos o análisis adicionales:
\`\`\`bash
# Regenerar CSVs
python reports/generate_csv_data.py baseline/ perturbed/ reports/

# Regenerar análisis de robustez
python analyze_robustness.py baseline/react_*.json > reports/robustez_react_nuevo.txt
\`\`\`

---

**Generado automáticamente por el sistema de evaluación**
EOF

log_success "Reporte final generado: $FINAL_REPORT"

# ============================================================================
# RESUMEN FINAL
# ============================================================================

log_section "✅ EVALUACIÓN COMPLETA FINALIZADA"

echo -e "${GREEN}"
cat << "EOF"
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                         ✅ EVALUACIÓN COMPLETADA                             ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

log_success "Directorio de resultados: $RESULTS_BASE"
echo ""
log_info "📊 Archivos clave generados:"
echo "   • Datos completos: $REPORTS_DIR/datos_completos.csv"
echo "   • Tabla resumen: $REPORTS_DIR/tabla_resumen.csv"
echo "   • Reporte final: $FINAL_REPORT"
echo ""
log_info "📝 Próximos pasos:"
echo "   1. Revisar el reporte final: cat $FINAL_REPORT"
echo "   2. Generar gráficos usando datos_completos.csv"
echo "   3. Incluir tabla_resumen.csv en tu tesis LaTeX"
echo ""
log_success "¡Todo listo para escribir la sección de resultados! 🎉"
echo ""

# Mostrar estadísticas finales
log_info "📈 Estadísticas de ejecución:"
TOTAL_BENCHMARKS=$((${#ARCHITECTURES[@]} * $NUM_CONTEXTS * 2))
echo "   • Total de benchmarks ejecutados: $TOTAL_BENCHMARKS"
echo "   • Arquitecturas evaluadas: ${#ARCHITECTURES[@]}"
echo "   • Contextos por arquitectura: $NUM_CONTEXTS"
echo "   • Condiciones evaluadas: 2 (Baseline + Perturbaciones)"
echo ""

exit 0
