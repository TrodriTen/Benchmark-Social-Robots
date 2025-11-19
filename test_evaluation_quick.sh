#!/bin/bash
################################################################################
# TEST RÁPIDO DE EVALUACIÓN
################################################################################
# 
# Ejecuta un benchmark rápido de solo 1 contexto con task_suite=simple
# para validar que todo el pipeline funciona correctamente.
#
################################################################################

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}TEST RÁPIDO - Validación del Pipeline${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}\n"

# Configuración de prueba
PROVIDER="azure"
MODEL="gpt-4o-mini"
ARCHITECTURE="react"
TASK_SUITE="simple"  # Solo 10 tareas simples
CONTEXT_SEED=999

# Directorio de prueba
TEST_DIR="test_quick_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$TEST_DIR"

echo -e "${BLUE}Configuración de prueba:${NC}"
echo "  • Arquitectura: $ARCHITECTURE"
echo "  • Suite: $TASK_SUITE (10 tareas)"
echo "  • Contexto: 1"
echo "  • Directorio: $TEST_DIR"
echo ""

# Activar entorno
echo -e "${CYAN}Activando entorno virtual...${NC}"
source ~/venvs/llm311/bin/activate
echo -e "${GREEN}✓ Entorno activado${NC}\n"

# Ejecutar benchmark
echo -e "${CYAN}Ejecutando benchmark de prueba...${NC}"
timeout 600 python run_benchmark.py \
    -a "$ARCHITECTURE" \
    -p "$PROVIDER" \
    -m "$MODEL" \
    --task-suite "$TASK_SUITE" \
    --max-iterations 15 \
    --context-seed "$CONTEXT_SEED" \
    2>&1 | tee "${TEST_DIR}/test.log"

# Verificar resultado
echo ""
echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}Verificando resultado...${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}\n"

# Buscar archivo generado (el modelo puede reportarse como "unknown")
# Buscar cualquier archivo que coincida con el patrón
PATTERN="benchmark_results/benchmark_${ARCHITECTURE}_*.json"
FOUND_FILE=$(ls -t $PATTERN 2>/dev/null | head -1)

if [ -n "$FOUND_FILE" ]; then
    echo -e "${BLUE}Archivo encontrado:${NC} $FOUND_FILE"
    EXPECTED_FILE="$FOUND_FILE"
fi

if [ -f "$EXPECTED_FILE" ]; then
    echo -e "${GREEN}✓ Archivo encontrado${NC}\n"
    
    # Mover a directorio de prueba
    mv "$EXPECTED_FILE" "${TEST_DIR}/result.json"
    echo -e "${GREEN}✓ Movido a: ${TEST_DIR}/result.json${NC}\n"
    
    # Mostrar resumen
    echo -e "${BLUE}Resumen del resultado:${NC}"
    python3 << EOF
import json
with open('${TEST_DIR}/result.json', 'r') as f:
    data = json.load(f)
    
metadata = data.get('metadata', {})
results = data.get('results', [])

print(f"  • Arquitectura: {metadata.get('architecture')}")
print(f"  • Modelo: {metadata.get('model')}")
print(f"  • Tareas: {metadata.get('num_tasks')}")
print(f"  • Éxitos: {sum(1 for r in results if r.get('success', False))}")
print(f"  • Fallos: {sum(1 for r in results if not r.get('success', False))}")

if results:
    avg_time = sum(r.get('execution_time', 0) for r in results) / len(results)
    avg_tokens = sum(r.get('metrics', {}).get('total_tokens', 0) for r in results) / len(results)
    print(f"  • Tiempo promedio: {avg_time:.2f}s")
    print(f"  • Tokens promedio: {avg_tokens:.0f}")
EOF
    
    echo ""
    echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✓ TEST EXITOSO - El pipeline funciona correctamente${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${CYAN}Puedes ejecutar la evaluación completa con:${NC}"
    echo -e "  ${BLUE}./run_complete_evaluation.sh${NC}"
    echo ""
    
else
    echo -e "${RED}✗ Archivo NO encontrado${NC}\n"
    
    echo -e "${YELLOW}Archivos en benchmark_results/:${NC}"
    ls -lh benchmark_results/ 2>/dev/null || echo "  (vacío)"
    
    echo ""
    echo -e "${YELLOW}Últimas líneas del log:${NC}"
    tail -30 "${TEST_DIR}/test.log"
    
    echo ""
    echo -e "${RED}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${RED}✗ TEST FALLIDO${NC}"
    echo -e "${RED}════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${YELLOW}Revisar:${NC}"
    echo "  1. Credenciales de Azure configuradas"
    echo "  2. Log completo: ${TEST_DIR}/test.log"
    echo ""
    exit 1
fi
