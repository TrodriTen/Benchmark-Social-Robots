#!/bin/bash
# CHECKLIST INTERACTIVO PARA TESIS
# Ejecutar: bash CHECKLIST_TESIS.sh

clear

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${MAGENTA}"
cat << "EOF"
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                      CHECKLIST COMPLETO PARA TESIS                           ║
║                   Evaluación de Arquitecturas Agentivas                      ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}\n"

# Función para verificar estado
check_status() {
    if [ -f "$1" ] || [ -d "$1" ]; then
        echo -e "${GREEN}✅${NC}"
        return 0
    else
        echo -e "${RED}❌${NC}"
        return 1
    fi
}

# Función para verificar dependencia Python
check_python_module() {
    python -c "import $1" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅${NC}"
        return 0
    else
        echo -e "${RED}❌${NC}"
        return 1
    fi
}

echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}FASE 1: PREPARACIÓN DEL ENTORNO${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════════${NC}\n"

echo -e "$(check_status "run_complete_evaluation.sh") Script maestro (run_complete_evaluation.sh)"
echo -e "$(check_status "generate_thesis_plots.py") Generador de gráficos (generate_thesis_plots.py)"
echo -e "$(check_status "analyze_robustness.py") Analizador de robustez (analyze_robustness.py)"
echo -e "$(check_status "validate_setup.py") Validador de setup (validate_setup.py)"

echo ""
echo -e "Dependencias Python:"
echo -e "$(check_python_module "langchain") langchain"
echo -e "$(check_python_module "openai") openai"
echo -e "$(check_python_module "pandas") pandas ${YELLOW}(necesario para gráficos)${NC}"
echo -e "$(check_python_module "matplotlib") matplotlib ${YELLOW}(necesario para gráficos)${NC}"
echo -e "$(check_python_module "seaborn") seaborn ${YELLOW}(necesario para gráficos)${NC}"
echo -e "$(check_python_module "numpy") numpy"

echo ""
if [ ! -f ~/.pip_deps_installed ]; then
    echo -e "${YELLOW}⚠️  Para instalar dependencias faltantes:${NC}"
    echo -e "   ${BLUE}pip install matplotlib pandas seaborn numpy${NC}"
    echo ""
fi

echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}FASE 2: EJECUCIÓN DE EVALUACIÓN${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════════${NC}\n"

# Buscar directorio de resultados más reciente
LATEST_RESULTS=$(find . -maxdepth 1 -type d -name "tesis_results_*" 2>/dev/null | sort -r | head -1)

if [ -n "$LATEST_RESULTS" ]; then
    echo -e "${GREEN}✅${NC} Resultados encontrados: ${GREEN}$LATEST_RESULTS${NC}"
    
    # Verificar archivos baseline
    BASELINE_COUNT=$(find "$LATEST_RESULTS/baseline" -name "*.json" 2>/dev/null | wc -l)
    PERTURBED_COUNT=$(find "$LATEST_RESULTS/perturbed" -name "*.json" 2>/dev/null | wc -l)
    
    echo -e "   • Baseline: $BASELINE_COUNT archivos JSON"
    echo -e "   • Perturbado: $PERTURBED_COUNT archivos JSON"
    
    if [ $BASELINE_COUNT -ge 20 ] && [ $PERTURBED_COUNT -ge 20 ]; then
        echo -e "   ${GREEN}✅ Evaluación completa (40 archivos esperados)${NC}"
    else
        echo -e "   ${YELLOW}⚠️  Evaluación incompleta (esperado: 40 archivos)${NC}"
    fi
else
    echo -e "${RED}❌${NC} No se encontraron resultados"
    echo -e "   ${YELLOW}→ Ejecutar:${NC} ${BLUE}./run_complete_evaluation.sh${NC}"
fi

echo ""
echo -e "Checklist de Ejecución:"
echo -e "[ ] 1. Ejecutar: ${BLUE}./run_complete_evaluation.sh${NC}"
echo -e "[ ] 2. Esperar ~30-60 minutos"
echo -e "[ ] 3. Verificar que se generaron 40 archivos JSON"

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}FASE 3: GENERACIÓN DE GRÁFICOS Y REPORTES${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════════${NC}\n"

if [ -n "$LATEST_RESULTS" ]; then
    PLOTS_DIR="$LATEST_RESULTS/reports/plots"
    
    if [ -d "$PLOTS_DIR" ]; then
        echo -e "${GREEN}✅${NC} Directorio de gráficos: ${GREEN}$PLOTS_DIR${NC}"
        
        # Verificar gráficos generados
        declare -a EXPECTED_PLOTS=(
            "success_rate_comparison.png"
            "execution_time_comparison.png"
            "token_consumption.png"
            "robustness_analysis.png"
            "perturbation_impact.png"
            "comprehensive_comparison.png"
            "tabla_latex.tex"
        )
        
        PLOTS_FOUND=0
        for plot in "${EXPECTED_PLOTS[@]}"; do
            if [ -f "$PLOTS_DIR/$plot" ]; then
                echo -e "   ${GREEN}✅${NC} $plot"
                ((PLOTS_FOUND++))
            else
                echo -e "   ${RED}❌${NC} $plot"
            fi
        done
        
        if [ $PLOTS_FOUND -eq ${#EXPECTED_PLOTS[@]} ]; then
            echo -e "\n   ${GREEN}✅ Todos los gráficos generados (7/7)${NC}"
        else
            echo -e "\n   ${YELLOW}⚠️  Gráficos incompletos ($PLOTS_FOUND/${#EXPECTED_PLOTS[@]})${NC}"
            echo -e "   ${YELLOW}→ Ejecutar:${NC} ${BLUE}python generate_thesis_plots.py $LATEST_RESULTS${NC}"
        fi
    else
        echo -e "${RED}❌${NC} Gráficos no generados"
        echo -e "   ${YELLOW}→ Ejecutar:${NC} ${BLUE}python generate_thesis_plots.py $LATEST_RESULTS${NC}"
    fi
    
    # Verificar CSVs
    echo ""
    echo "Archivos CSV:"
    check_status "$LATEST_RESULTS/reports/datos_completos.csv" && echo -e "${GREEN}✅${NC} datos_completos.csv" || echo -e "${RED}❌${NC} datos_completos.csv"
    check_status "$LATEST_RESULTS/reports/tabla_resumen.csv" && echo -e "${GREEN}✅${NC} tabla_resumen.csv" || echo -e "${RED}❌${NC} tabla_resumen.csv"
    
    # Verificar reportes de robustez
    echo ""
    echo "Reportes de Robustez:"
    ROBUSTEZ_COUNT=$(find "$LATEST_RESULTS/reports" -name "robustez_*.txt" 2>/dev/null | wc -l)
    echo -e "   • Encontrados: $ROBUSTEZ_COUNT reportes"
    if [ $ROBUSTEZ_COUNT -eq 8 ]; then
        echo -e "   ${GREEN}✅ Completo (8 reportes esperados)${NC}"
    else
        echo -e "   ${YELLOW}⚠️  Incompleto (esperado: 8 reportes)${NC}"
    fi
fi

echo ""
echo -e "Checklist de Gráficos:"
echo -e "[ ] 1. Instalar: ${BLUE}pip install matplotlib pandas seaborn${NC}"
echo -e "[ ] 2. Ejecutar: ${BLUE}python generate_thesis_plots.py tesis_results_*${NC}"
echo -e "[ ] 3. Verificar 7 archivos en plots/"

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}FASE 4: INTEGRACIÓN EN TESIS${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════════${NC}\n"

echo -e "Checklist de Escritura:"
echo -e "[ ] 1. Copiar gráficos PNG a carpeta figures/ de LaTeX"
echo -e "[ ] 2. Copiar tabla_latex.tex a documento"
echo -e "[ ] 3. Escribir Sección de Metodología"
echo -e "[ ] 4. Escribir Sección de Resultados (con tabla y gráficos)"
echo -e "[ ] 5. Escribir Sección de Discusión (trade-offs, robustez)"
echo -e "[ ] 6. Escribir Sección de Conclusiones"

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}RESUMEN DE ESTADO${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════════${NC}\n"

# Calcular progreso general
TOTAL_STEPS=4
COMPLETED_STEPS=0

# Fase 1: Preparación
if [ -f "run_complete_evaluation.sh" ] && [ -f "generate_thesis_plots.py" ]; then
    ((COMPLETED_STEPS++))
fi

# Fase 2: Ejecución
if [ -n "$LATEST_RESULTS" ] && [ $BASELINE_COUNT -ge 20 ] && [ $PERTURBED_COUNT -ge 20 ]; then
    ((COMPLETED_STEPS++))
fi

# Fase 3: Gráficos
if [ -d "$PLOTS_DIR" ] && [ $PLOTS_FOUND -eq 7 ]; then
    ((COMPLETED_STEPS++))
fi

# Calcular porcentaje
PERCENTAGE=$((COMPLETED_STEPS * 100 / TOTAL_STEPS))

echo -e "Progreso General: ${GREEN}$COMPLETED_STEPS/$TOTAL_STEPS fases completadas${NC} (${PERCENTAGE}%)"
echo ""

if [ $COMPLETED_STEPS -eq 0 ]; then
    echo -e "${YELLOW}📍 ESTADO: Listo para comenzar${NC}"
    echo -e "${BLUE}Siguiente paso: ./run_complete_evaluation.sh${NC}"
elif [ $COMPLETED_STEPS -eq 1 ]; then
    echo -e "${YELLOW}📍 ESTADO: Evaluación en progreso${NC}"
    echo -e "${BLUE}Siguiente paso: Esperar a que termine o verificar logs${NC}"
elif [ $COMPLETED_STEPS -eq 2 ]; then
    echo -e "${YELLOW}📍 ESTADO: Evaluación completa, generar gráficos${NC}"
    echo -e "${BLUE}Siguiente paso: python generate_thesis_plots.py $LATEST_RESULTS${NC}"
elif [ $COMPLETED_STEPS -eq 3 ]; then
    echo -e "${GREEN}📍 ESTADO: Gráficos listos, comenzar a escribir${NC}"
    echo -e "${BLUE}Siguiente paso: Integrar en tesis LaTeX${NC}"
else
    echo -e "${GREEN}🎉 ESTADO: ¡Todo listo para defensa!${NC}"
fi

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}COMANDOS ÚTILES${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════════${NC}\n"

echo -e "${YELLOW}Validar configuración:${NC}"
echo -e "   ${BLUE}python validate_setup.py${NC}"
echo ""

echo -e "${YELLOW}Ejecutar evaluación completa:${NC}"
echo -e "   ${BLUE}./run_complete_evaluation.sh${NC}"
echo ""

echo -e "${YELLOW}Generar gráficos:${NC}"
echo -e "   ${BLUE}python generate_thesis_plots.py tesis_results_YYYYMMDD_HHMMSS${NC}"
echo ""

echo -e "${YELLOW}Ver último reporte:${NC}"
if [ -n "$LATEST_RESULTS" ]; then
    echo -e "   ${BLUE}cat $LATEST_RESULTS/reports/REPORTE_FINAL_TESIS.md${NC}"
else
    echo -e "   ${BLUE}cat tesis_results_*/reports/REPORTE_FINAL_TESIS.md${NC}"
fi
echo ""

echo -e "${YELLOW}Ver gráficos generados:${NC}"
if [ -n "$PLOTS_DIR" ]; then
    echo -e "   ${BLUE}ls -lh $PLOTS_DIR/${NC}"
else
    echo -e "   ${BLUE}ls -lh tesis_results_*/reports/plots/${NC}"
fi

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════════════${NC}\n"
echo -e "${GREEN}Para más información, consultar:${NC}"
echo -e "   • ${BLUE}GUIA_EVALUACION_COMPLETA.md${NC} - Guía completa"
echo -e "   • ${BLUE}RESUMEN_SISTEMA_COMPLETO.md${NC} - Resumen del sistema"
echo -e "   • ${BLUE}GUIA_ROBUSTEZ.md${NC} - Guía de robustez"
echo ""
