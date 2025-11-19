# 📊 REPORTE FINAL DE EVALUACIÓN - TESIS

**Fecha de generación**: 2025-11-18 17:36:56  
**Directorio de resultados**: tesis_results_20251118_030308

---

## 📋 Configuración de la Evaluación

- **Arquitecturas evaluadas**: react plan-then-act reference reflexion
- **Proveedor LLM**: azure
- **Modelo**: gpt-4o-mini
- **Suite de tareas**: complex
- **Contextos por arquitectura**: 5
- **Máximo de iteraciones**: 15

---

## 🎯 Estructura de Resultados

```
tesis_results_20251118_030308/
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
```

---

## 📊 Archivos Clave para la Tesis

### 1. Datos Completos (para gráficos)
**Archivo**: `reports/datos_completos.csv`

Contiene todas las métricas individuales de cada contexto. Usar para:
- Gráficos de barras (tasa de éxito por arquitectura)
- Gráficos de dispersión (tiempo vs éxito)
- Box plots (distribución de métricas)

**Columnas**:
- `architecture`: Nombre de la arquitectura
- `condition`: "Baseline" o "Perturbado"
- `context`: Número de contexto (1-5)
- `success_rate`: Tasa de éxito (%)
- `avg_time`: Tiempo promedio (segundos)
- `avg_steps`: Pasos promedio
- `avg_tokens`: Tokens promedio

### 2. Tabla Resumen (para tablas en LaTeX)
**Archivo**: `reports/tabla_resumen.csv`

Contiene estadísticas agregadas (media ± desv. estándar). Usar para:
- Tabla comparativa principal de la tesis
- Análisis de robustez (desviación estándar)

**Columnas**:
- `architecture`: Nombre de la arquitectura
- `condition`: "Baseline" o "Perturbado"
- `success_mean`: Media de tasa de éxito
- `success_std`: Desviación estándar de tasa de éxito
- `time_mean`: Media de tiempo
- `time_std`: Desviación estándar de tiempo
- `steps_mean`: Media de pasos
- `steps_std`: Desviación estándar de pasos
- `tokens_mean`: Media de tokens
- `tokens_std`: Desviación estándar de tokens

### 3. Reportes de Robustez (interpretación)
**Archivos**: `reports/robustez_*_baseline.txt` y `reports/robustez_*_perturbed.txt`

Contienen análisis detallado de robustez con:
- Coeficiente de variación (CV)
- Interpretación de consistencia
- Rating de robustez

---

## 📈 Cómo Usar los Datos en la Tesis

### Para Gráficos (Python/Matplotlib o R)

```python
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
```

### Para Tablas LaTeX

```python
import pandas as pd

# Cargar resumen
df = pd.read_csv('reports/tabla_resumen.csv')

# Filtrar baseline
baseline = df[df['condition'] == 'Baseline']

# Generar LaTeX
print(baseline[['architecture', 'success_mean', 'success_std', 
                'time_mean', 'time_std']].to_latex(index=False))
```

O manualmente:

```latex
\begin{table}[h]
\centering
\caption{Comparación de Arquitecturas Agentivas}
\begin{tabular}{lcccc}
\toprule
Arquitectura & Éxito (\%) & Tiempo (s) & Pasos & Tokens \\
\midrule
ReAct        & 95.0 ± 5.2 & 10.2 ± 1.5 & 3.2 ± 0.8 & 14748 ± 2341 \\
Plan-Then-Act& 92.0 ± 8.1 & 12.5 ± 2.3 & 4.1 ± 1.2 & 16523 ± 3102 \\
Reference    & 97.0 ± 3.2 & 11.8 ± 1.2 & 3.8 ± 0.6 & 15987 ± 1876 \\
Reflexion    & 90.0 ± 12.5 & 15.3 ± 4.1 & 5.2 ± 2.1 & 18234 ± 4567 \\
\bottomrule
\end{tabular}
\end{table}
```

---

## 🔍 Análisis de Robustez

Ver reportes individuales en:
- `reports/robustez_react_baseline.txt`
- `reports/robustez_react_perturbed.txt`
- `reports/robustez_plan-then-act_baseline.txt`
- `reports/robustez_plan-then-act_perturbed.txt`
- `reports/robustez_reference_baseline.txt`
- `reports/robustez_reference_perturbed.txt`
- `reports/robustez_reflexion_baseline.txt`
- `reports/robustez_reflexion_perturbed.txt`

---

## ✅ Checklist para la Tesis

### Sección de Resultados
- [ ] Tabla comparativa principal (usar `tabla_resumen.csv`)
- [ ] Gráfico de tasa de éxito (usar `datos_completos.csv`)
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
```bash
# Regenerar CSVs
python reports/generate_csv_data.py baseline/ perturbed/ reports/

# Regenerar análisis de robustez
python analyze_robustness.py baseline/react_*.json > reports/robustez_react_nuevo.txt
```

---

**Generado automáticamente por el sistema de evaluación**
