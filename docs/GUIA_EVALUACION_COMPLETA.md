# 🎓 GUÍA COMPLETA DE EVALUACIÓN PARA TESIS

## 📋 Descripción General

Este sistema automatizado ejecuta una evaluación completa de las 4 arquitecturas agentivas con y sin perturbaciones, analiza la robustez, y genera todos los reportes, gráficos y tablas necesarios para tu tesis.

---

## 🚀 Inicio Rápido

### 1. Instalación de Dependencias

```bash
# Activar entorno virtual
source ~/venvs/llm311/bin/activate

# Instalar dependencias para gráficos
pip install matplotlib pandas seaborn numpy
```

### 2. Ejecutar Evaluación Completa

```bash
# Hacer scripts ejecutables (solo la primera vez)
chmod +x run_complete_evaluation.sh

# Ejecutar evaluación completa
./run_complete_evaluation.sh
```

**⏱️ Tiempo estimado**: 
- Con 5 contextos: ~20-30 minutos
- Con 10 contextos: ~40-60 minutos

### 3. Generar Gráficos

```bash
# Reemplazar con el directorio generado
python generate_thesis_plots.py tesis_results_YYYYMMDD_HHMMSS
```

---

## 📊 ¿Qué se Genera?

### Estructura de Resultados

```
tesis_results_YYYYMMDD_HHMMSS/
├── baseline/                          # Sin perturbaciones
│   ├── react_context1.json
│   ├── react_context2.json
│   ├── ...
│   ├── plan-then-act_context1.json
│   ├── reference_context1.json
│   └── reflexion_context1.json
│
├── perturbed/                         # Con perturbaciones
│   ├── react_context1.json
│   ├── ...
│
└── reports/                           # Análisis y gráficos
    ├── datos_completos.csv            # ← Para gráficos
    ├── tabla_resumen.csv              # ← Para tablas LaTeX
    ├── robustez_react_baseline.txt
    ├── robustez_react_perturbed.txt
    ├── ...
    ├── REPORTE_FINAL_TESIS.md         # ← Guía de uso
    │
    └── plots/                         # Gráficos para tesis
        ├── success_rate_comparison.png
        ├── execution_time_comparison.png
        ├── token_consumption.png
        ├── robustness_analysis.png
        ├── perturbation_impact.png
        ├── comprehensive_comparison.png
        └── tabla_latex.tex            # ← Tabla lista para copiar
```

---

## 🎨 Gráficos Generados

### 1. **success_rate_comparison.png**
- Comparación de tasa de éxito por arquitectura
- Baseline vs Perturbado
- **Uso en tesis**: Sección de Resultados - Rendimiento General

### 2. **execution_time_comparison.png**
- Comparación de tiempo de ejecución
- **Uso en tesis**: Sección de Resultados - Eficiencia Temporal

### 3. **token_consumption.png**
- Distribución de consumo de tokens (boxplot)
- **Uso en tesis**: Sección de Resultados - Costo Computacional

### 4. **robustness_analysis.png**
- Coeficiente de variación (CV) para evaluar robustez
- Líneas de referencia: Excelente, Bueno, Moderado
- **Uso en tesis**: Sección de Resultados - Análisis de Robustez

### 5. **perturbation_impact.png**
- Degradación de rendimiento con perturbaciones
- **Uso en tesis**: Sección de Discusión - Impacto de Perturbaciones

### 6. **comprehensive_comparison.png**
- Panel 2x2 con todas las métricas
- **Uso en tesis**: Apéndice o Resumen Visual

---

## 📄 Cómo Usar en LaTeX

### Incluir Gráficos

```latex
\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{plots/success_rate_comparison.png}
\caption{Comparación de tasa de éxito entre arquitecturas agentivas}
\label{fig:success_comparison}
\end{figure}
```

### Incluir Tabla

```latex
% Copiar contenido de plots/tabla_latex.tex directamente
```

El archivo `tabla_latex.tex` ya está formateado y listo para copiar.

---

## 🔧 Configuración Avanzada

### Modificar Parámetros del Benchmark

Editar `run_complete_evaluation.sh`:

```bash
# Línea 18-22
NUM_CONTEXTS=10           # Cambiar a 10 para mayor rigor
TASK_SUITE="complex"      # O "simple" para pruebas rápidas
MAX_ITERATIONS=20         # Máximo de pasos del agente
TIMEOUT=600               # Timeout en segundos (10 min)
```

### Cambiar Modelo LLM

```bash
# Línea 15-16
PROVIDER="azure"
MODEL="gpt-4o-mini"       # O "gpt-4o" para mayor precisión
```

### Tipos de Perturbaciones

```bash
# Línea 113 en run_complete_evaluation.sh
PERTURBATION_TYPES="distractors noise ambiguity"
```

Opciones disponibles:
- `distractors`: Información irrelevante en el contexto
- `noise`: Ruido simulado de ASR (reconocimiento de voz)
- `ambiguity`: Instrucciones ambiguas
- `latency`: Simulación de latencia en herramientas
- `mismatch`: Desajuste entre contexto y estado real

---

## 📈 Interpretar los Resultados

### Coeficiente de Variación (CV)

El CV mide la consistencia de una arquitectura:

- **CV < 10%**: 🌟 **Excelente** - Muy consistente
- **CV < 20%**: ✅ **Bueno** - Consistente
- **CV < 35%**: ⚠️ **Moderado** - Aceptable
- **CV > 35%**: ❌ **Bajo** - Inconsistente

**Ejemplo de interpretación**:
```
ReAct: CV = 5.2% → Excelente robustez
Reflexion: CV = 28.3% → Robustez moderada
```

### Degradación por Perturbaciones

**Fórmula**: `Degradación = Baseline - Perturbado`

- **Degradación < 5%**: Muy resistente a perturbaciones
- **Degradación 5-15%**: Moderadamente resistente
- **Degradación > 15%**: Sensible a perturbaciones

---

## 🎯 Checklist para la Tesis

### Sección de Metodología
- [ ] Describir configuración: 4 arquitecturas, 5 contextos, 2 condiciones
- [ ] Explicar métricas: tasa de éxito, tiempo, pasos, tokens
- [ ] Detallar tipos de perturbaciones aplicadas

### Sección de Resultados
- [ ] **Tabla 1**: Comparación general (usar `tabla_latex.tex`)
- [ ] **Figura 1**: Tasa de éxito (`success_rate_comparison.png`)
- [ ] **Figura 2**: Tiempo de ejecución (`execution_time_comparison.png`)
- [ ] **Figura 3**: Consumo de tokens (`token_consumption.png`)
- [ ] **Figura 4**: Análisis de robustez (`robustness_analysis.png`)
- [ ] **Figura 5**: Impacto de perturbaciones (`perturbation_impact.png`)

### Sección de Discusión
- [ ] Interpretar trade-offs: éxito vs tiempo vs costo
- [ ] Comparar robustez entre arquitecturas (CV)
- [ ] Analizar sensibilidad a perturbaciones
- [ ] Identificar mejor arquitectura por escenario

### Sección de Conclusiones
- [ ] Resumir hallazgos clave
- [ ] Recomendar arquitectura según contexto de uso
- [ ] Mencionar limitaciones (modelo usado, tipos de tareas)
- [ ] Proponer trabajo futuro (más perturbaciones, modelos)

---

## 🐛 Troubleshooting

### Error: "No se generó resultado"
**Solución**: Verificar que el entorno virtual está activado y las dependencias instaladas.

### Gráficos no se generan
**Solución**: 
```bash
pip install matplotlib pandas seaborn numpy
```

### Timeout en benchmarks
**Solución**: Aumentar `TIMEOUT` en `run_complete_evaluation.sh` (línea 22).

### CSV vacíos
**Solución**: Verificar que los archivos JSON existen en `baseline/` y `perturbed/`.

---

## 📞 Comandos Útiles

### Ver progreso durante ejecución
```bash
# En otra terminal
tail -f tesis_results_*/baseline/*.log
```

### Regenerar solo gráficos
```bash
python generate_thesis_plots.py tesis_results_YYYYMMDD_HHMMSS
```

### Regenerar solo análisis de robustez
```bash
python analyze_robustness.py baseline/react_*.json > reports/robustez_react_nuevo.txt
```

### Comparar dos ejecuciones
```bash
# Comparar resultados de diferentes fechas
python analyze_results.py \
    tesis_results_20250118_120000/baseline/react_context1.json \
    tesis_results_20250119_140000/baseline/react_context1.json
```

---

## ⏱️ Estimación de Tiempos

| Configuración | Arquitecturas | Contextos | Condiciones | Tiempo Total |
|---------------|---------------|-----------|-------------|--------------|
| Rápida        | 4             | 3         | 2           | ~15 min      |
| Estándar      | 4             | 5         | 2           | ~30 min      |
| Rigurosa      | 4             | 10        | 2           | ~60 min      |
| Tesis Final   | 4             | 10        | 2           | ~60 min + 5 min gráficos |

---

## 🎓 Ejemplo de Uso Completo

```bash
# 1. Preparación
source ~/venvs/llm311/bin/activate
pip install matplotlib pandas seaborn numpy

# 2. Ejecución completa
./run_complete_evaluation.sh
# Confirmar con 'y' cuando se solicite

# 3. Esperar a que termine (~30 min)
# Ver progreso: tail -f tesis_results_*/baseline/react_context1.log

# 4. Generar gráficos
python generate_thesis_plots.py tesis_results_20250118_120000

# 5. Revisar resultados
cat tesis_results_20250118_120000/reports/REPORTE_FINAL_TESIS.md
open tesis_results_20250118_120000/reports/plots/  # Ver gráficos

# 6. Copiar a tesis LaTeX
cp tesis_results_20250118_120000/reports/plots/* ~/tesis/figures/
cp tesis_results_20250118_120000/reports/plots/tabla_latex.tex ~/tesis/tables/
```

---

## ✅ Validación de Resultados

Después de la ejecución, verificar:

1. ✅ **40 archivos JSON** (4 arquitecturas × 5 contextos × 2 condiciones)
2. ✅ **8 reportes de robustez** (4 arquitecturas × 2 condiciones)
3. ✅ **2 CSVs** (datos_completos.csv, tabla_resumen.csv)
4. ✅ **7 gráficos** (6 PNG + 1 TEX)

```bash
# Contar archivos
find tesis_results_*/baseline -name "*.json" | wc -l   # Debe ser 20
find tesis_results_*/perturbed -name "*.json" | wc -l  # Debe ser 20
find tesis_results_*/reports/plots -type f | wc -l     # Debe ser 7
```

---

## 💡 Tips para la Tesis

1. **No ejecutes el benchmark el último día**: Reserva tiempo para análisis
2. **Usa 10 contextos mínimo**: Mayor rigor estadístico
3. **Guarda múltiples ejecuciones**: Para comparar evolución del modelo
4. **Documenta configuración**: Incluir en metodología (modelo, params)
5. **Interpreta CV cuidadosamente**: No solo el promedio importa

---

## 📚 Referencias

- `run_complete_evaluation.sh`: Script maestro de evaluación
- `generate_thesis_plots.py`: Generador de gráficos
- `analyze_robustness.py`: Análisis estadístico de robustez
- `analyze_results.py`: Comparación entre arquitecturas

---

**¿Listo para tu tesis? 🎉**

Con esta guía tienes todo lo necesario para:
- ✅ Ejecutar evaluación completa
- ✅ Generar gráficos profesionales
- ✅ Obtener tablas formateadas
- ✅ Escribir secciones de resultados y discusión

**¡Éxito con tu defensa! 🎓**
