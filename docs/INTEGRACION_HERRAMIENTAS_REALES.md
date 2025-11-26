# Integración de Herramientas Reales en el Benchmark

## Resumen

Se ha completado la integración de las herramientas reales de `ros_langgraph_tools.py` en las 4 arquitecturas del benchmark (ReAct, Plan-then-Act, Reflexion, Reference). Esto permite ejecutar el benchmark con herramientas reales de ROS en lugar de los adapters dummy simulados.

## Cambios Implementados

### 1. Nuevo Módulo: `real_tools_adapter.py`

Ubicación: `src/benchmark_agent/real_tools_adapter.py`

Este módulo proporciona:
- Importación lazy de todas las herramientas de `ros_langgraph_tools.py`
- Funciones de compatibilidad (`get_real_tools()`, `get_real_tools_description()`, `get_real_tool_names()`)
- Metadata de herramientas (`REAL_TOOLS_METADATA`)
- Manejo de errores robusto para problemas de inicialización de ROS

**Herramientas disponibles:**
- **Percepción**: `find_object`, `count_objects`, `search_for_specific_person`, `find_item_with_characteristic`, `get_person_gesture`, `get_items_on_top_of_furniture`, `view_description`
- **Habla**: `speak`, `listen`, `question_and_answer`
- **Navegación**: `go_to_location`, `follow_person`
- **Manipulación**: `ask_for_object`, `give_object`

### 2. Actualización de `base_agent.py`

- Nuevo parámetro `use_real_tools` en el constructor
- Lógica para seleccionar entre:
  - Herramientas reales de ROS (`use_real_tools=True`)
  - Adapters dummy simulados (`use_real_tools=False`, por defecto)

### 3. Actualización de las 4 Arquitecturas

Todas las arquitecturas ahora soportan el parámetro `use_real_tools`:

#### **ReAct** (`react.py`)
- Constructor actualizado con `use_real_tools`
- Método `_create_langchain_tools()` adaptado para retornar herramientas reales o adapters
- Nuevo método `_get_real_tools_prompt()` con prompt específico para herramientas reales

#### **Plan-then-Act** (`plan_then_act.py`)
- Constructor actualizado con `use_real_tools`
- Método `_create_planner_chain()` usa descripción de herramientas reales cuando aplica
- Método `_execute_plan()` adaptado para ejecutar herramientas reales o adapters
- Normalización de resultados para ambos modos

#### **Reflexion** (`reflexion.py`)
- Constructor actualizado con `use_real_tools`
- Método `_create_langchain_tools()` retorna herramientas reales o convierte adapters

#### **Reference** (`reference.py`)
- Constructor actualizado con `use_real_tools`
- Método `_create_langchain_tools()` retorna herramientas reales o convierte adapters

### 4. Actualización de `run_benchmark.py`

**Nuevo parámetro CLI:** `--use-real-tools`

```bash
# Ejecutar con herramientas reales de ROS
python run_benchmark.py -a react --use-real-tools

# Ejecutar con adapters dummy (por defecto)
python run_benchmark.py -a react
```

**Cambios implementados:**
- Nuevo argumento de línea de comandos `--use-real-tools`
- Display en el header mostrando si usa herramientas REALES o DUMMY
- Instanciación de todas las arquitecturas con el parámetro `use_real_tools`
- Información de herramientas disponibles según el modo

## Uso

### Modo Dummy (Por Defecto)

Usa adapters simulados que no requieren ROS:

```bash
python run_benchmark.py -a react -p azure -m gpt-4o-mini
```

### Modo Herramientas Reales

Usa las herramientas reales de ROS (requiere ROS iniciado):

```bash
# Asegúrate de que ROS esté corriendo
roscore &

# Inicia los servicios necesarios
# (task_module debe estar inicializado)

# Ejecutar benchmark con herramientas reales
python run_benchmark.py -a react -p azure -m gpt-4o-mini --use-real-tools
```

### Ejemplos Combinados

```bash
# Plan-then-Act con herramientas reales
python run_benchmark.py -a plan-then-act --use-real-tools --task-suite simple

# Reflexion con herramientas reales y más intentos
python run_benchmark.py -a reflexion --use-real-tools --max-attempts 5

# Reference con herramientas reales y memoria
python run_benchmark.py -a reference --use-real-tools --use-memory
```

## Compatibilidad hacia atrás

- **100% compatible**: El código existente funciona sin cambios
- **Por defecto**: Usa adapters dummy (comportamiento original)
- **Opt-in**: Herramientas reales solo se usan cuando se especifica `--use-real-tools`

## Notas Técnicas

### Importación Lazy

Las herramientas reales se importan de forma lazy para evitar:
- Inicialización prematura de ROS
- Errores cuando ROS no está disponible
- Overhead innecesario en modo dummy

### Manejo de Errores

Si las herramientas reales no se pueden cargar:
```
ImportError: Error al importar herramientas de ros_langgraph_tools: ...
Asegúrate de que ROS esté iniciado y los servicios estén disponibles.
```

### Normalización de Resultados

En Plan-then-Act, los resultados de herramientas reales se normalizan al formato estándar:
```python
{
    "ok": bool,
    "obs": str,
    "data": dict
}
```

## Testing

Para probar la integración:

```bash
# 1. Modo dummy (no requiere ROS)
python run_benchmark.py -a react --task-suite simple --verbose

# 2. Modo real (requiere ROS y servicios)
# Primero: iniciar ROS y servicios
# Luego:
python run_benchmark.py -a react --use-real-tools --task-suite simple --verbose
```

## Próximos Pasos

1. **Validación completa**: Ejecutar benchmark completo con ambos modos
2. **Comparación de resultados**: Comparar métricas entre dummy y real
3. **Documentación de servicios**: Documentar qué servicios ROS deben estar corriendo
4. **Tests automatizados**: Crear tests que verifiquen ambos modos

## Archivos Modificados

```
src/benchmark_agent/
├── real_tools_adapter.py          [NUEVO]
├── architectures/
│   ├── base_agent.py              [MODIFICADO]
│   ├── react.py                   [MODIFICADO]
│   ├── plan_then_act.py           [MODIFICADO]
│   ├── reflexion.py               [MODIFICADO]
│   └── reference.py               [MODIFICADO]
run_benchmark.py                   [MODIFICADO]
```

## Conclusión

La integración está completa y lista para uso. Las 4 arquitecturas ahora pueden ejecutarse con herramientas reales de ROS mediante el flag `--use-real-tools`, manteniendo compatibilidad total con el modo dummy existente.
