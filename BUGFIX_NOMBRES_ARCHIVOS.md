# 🐛 PROBLEMA RESUELTO: Nombres de Archivos de Resultados

## ❌ Problema Identificado

El script `run_complete_evaluation.sh` no estaba encontrando los archivos de resultados generados por `run_benchmark.py`.

### Causa Raíz

**Discrepancia en nombres de archivo**:

- **Script esperaba**: `benchmark_{architecture}_{MODEL}.json`
  - Ejemplo: `benchmark_react_gpt-4o-mini.json`

- **Script generaba**: `benchmark_{architecture}_{MODEL_SAFE}_{TASK_SUITE}.json`
  - Ejemplo: `benchmark_react_gpt-4o-mini_complex.json`

**Problema adicional**: El directorio `benchmark_results/` no existía.

---

## ✅ Solución Aplicada

### 1. Crear directorio de resultados
```bash
mkdir -p benchmark_results
```

### 2. Actualizar script para usar nombre correcto

**Antes**:
```bash
if [ -f "benchmark_results/benchmark_${arch}_${MODEL}.json" ]; then
    mv "benchmark_results/benchmark_${arch}_${MODEL}.json" "$OUTPUT_FILE"
```

**Después**:
```bash
MODEL_SAFE=$(echo "$MODEL" | sed 's/:/_/g; s/\//_/g; s/\./_/g')
RESULT_FILE="benchmark_results/benchmark_${arch}_${MODEL_SAFE}_${TASK_SUITE}.json"

if [ -f "$RESULT_FILE" ]; then
    mv "$RESULT_FILE" "$OUTPUT_FILE"
```

---

## 🔍 Cómo Detectar el Problema

### Síntoma
```
❌     ✗ No se generó resultado
```

### Verificación Manual

1. **Verificar si se genera archivo**:
```bash
ls -la benchmark_results/
```

2. **Ver logs de ejecución**:
```bash
cat tesis_results_*/baseline/*.log | tail -50
```

3. **Ver qué archivo se creó realmente**:
```bash
find benchmark_results/ -name "benchmark_*.json" -mmin -10
```

---

## 📝 Aprendizajes

### Por Qué Pasó

El archivo `run_benchmark.py` genera nombres con formato:
```python
output_file = output_dir / f"benchmark_{args.architecture}_{model_safe}{suite_suffix}.json"
```

Donde `suite_suffix` es:
- `""` (vacío) si `task_suite == "simple"`
- `"_complex"` si `task_suite == "complex"`
- `"_all"` si `task_suite == "all"`

### Lección

Siempre verificar:
1. Que el directorio de salida existe antes de ejecutar
2. Que los nombres de archivo coincidan exactamente entre generación y búsqueda
3. Usar variables para nombres de archivo en lugar de hardcodear

---

## ✅ Estado Actual

**Problemas resueltos**:
- ✅ Directorio `benchmark_results/` creado
- ✅ Script actualizado para usar nombre correcto con `_complex`
- ✅ Aplicado tanto a baseline como a perturbed
- ✅ Procesos anteriores detenidos
- ✅ Resultados parciales limpiados

**Listo para**:
```bash
./run_complete_evaluation.sh
```

---

## 🚀 Verificación Post-Ejecución

Después de ejecutar, verificar que los archivos se mueven correctamente:

```bash
# Ver estructura de directorios
tree tesis_results_*/

# Contar archivos generados
find tesis_results_*/baseline -name "*.json" | wc -l   # Debe ser 20
find tesis_results_*/perturbed -name "*.json" | wc -l  # Debe ser 20

# Ver logs si hay problemas
tail -f tesis_results_*/baseline/*.log
```

---

## 📋 Checklist de Validación

Antes de cada ejecución completa:

- [ ] `benchmark_results/` existe: `mkdir -p benchmark_results`
- [ ] Variables de entorno configuradas (Azure API key)
- [ ] Entorno virtual activado: `source ~/venvs/llm311/bin/activate`
- [ ] Sin procesos previos corriendo: `ps aux | grep run_benchmark`
- [ ] Espacio suficiente en disco: `df -h .`

---

**Problema resuelto**: 18 Nov 2025, 02:14  
**Solución aplicada**: Actualización de `run_complete_evaluation.sh` líneas 145-152 y 193-200
