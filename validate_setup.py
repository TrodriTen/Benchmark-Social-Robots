#!/usr/bin/env python3
"""
Script de Validación Pre-Ejecución
====================================

Verifica que todo esté listo para ejecutar la evaluación completa de la tesis.

Uso:
    python validate_setup.py
"""

import sys
import subprocess
from pathlib import Path

# Colores
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'

def check_item(name, check_func):
    """Verifica un item y muestra resultado."""
    try:
        result = check_func()
        if result:
            print(f"{GREEN}✅ {name}{NC}")
            return True
        else:
            print(f"{RED}❌ {name}{NC}")
            return False
    except Exception as e:
        print(f"{RED}❌ {name} - Error: {e}{NC}")
        return False

def check_file_exists(file_path):
    """Verifica que un archivo exista."""
    return lambda: Path(file_path).exists()

def check_module(module_name):
    """Verifica que un módulo de Python esté instalado."""
    def check():
        try:
            __import__(module_name)
            return True
        except ImportError:
            return False
    return check

def check_executable(file_path):
    """Verifica que un archivo sea ejecutable."""
    def check():
        path = Path(file_path)
        return path.exists() and path.stat().st_mode & 0o111
    return check

def check_env_var(var_name):
    """Verifica que una variable de entorno esté configurada."""
    def check():
        import os
        return os.getenv(var_name) is not None
    return check

def main():
    print(f"{BLUE}{'='*80}{NC}")
    print(f"{BLUE}VALIDACIÓN DE CONFIGURACIÓN PARA TESIS{NC}")
    print(f"{BLUE}{'='*80}{NC}\n")

    all_checks = []

    # Sección 1: Archivos del Sistema
    print(f"{YELLOW}📁 Archivos del Sistema{NC}")
    all_checks.append(check_item("run_benchmark.py", check_file_exists("run_benchmark.py")))
    all_checks.append(check_item("run_complete_evaluation.sh", check_file_exists("run_complete_evaluation.sh")))
    all_checks.append(check_item("generate_thesis_plots.py", check_file_exists("generate_thesis_plots.py")))
    all_checks.append(check_item("analyze_robustness.py", check_file_exists("analyze_robustness.py")))
    all_checks.append(check_item("analyze_results.py", check_file_exists("analyze_results.py")))
    print()

    # Sección 2: Arquitecturas
    print(f"{YELLOW}🏗️  Arquitecturas Agentivas{NC}")
    all_checks.append(check_item("ReAct", check_file_exists("src/benchmark_agent/architectures/react.py")))
    all_checks.append(check_item("Plan-Then-Act", check_file_exists("src/benchmark_agent/architectures/plan_then_act.py")))
    all_checks.append(check_item("Reference", check_file_exists("src/benchmark_agent/architectures/reference.py")))
    all_checks.append(check_item("Reflexion", check_file_exists("src/benchmark_agent/architectures/reflexion.py")))
    print()

    # Sección 3: Scripts Ejecutables
    print(f"{YELLOW}⚙️  Permisos de Ejecución{NC}")
    all_checks.append(check_item("run_complete_evaluation.sh es ejecutable", 
                                 check_executable("run_complete_evaluation.sh")))
    all_checks.append(check_item("generate_thesis_plots.py es ejecutable", 
                                 check_executable("generate_thesis_plots.py")))
    print()

    # Sección 4: Dependencias Python
    print(f"{YELLOW}🐍 Dependencias Python{NC}")
    all_checks.append(check_item("langchain", check_module("langchain")))
    all_checks.append(check_item("openai", check_module("openai")))
    all_checks.append(check_item("pandas", check_module("pandas")))
    all_checks.append(check_item("matplotlib", check_module("matplotlib")))
    all_checks.append(check_item("seaborn", check_module("seaborn")))
    all_checks.append(check_item("numpy", check_module("numpy")))
    print()

    # Sección 5: Variables de Entorno (Opcional)
    print(f"{YELLOW}🔑 Variables de Entorno (Opcional){NC}")
    has_azure_key = check_item("AZURE_OPENAI_API_KEY", check_env_var("AZURE_OPENAI_API_KEY"))
    has_azure_endpoint = check_item("AZURE_OPENAI_ENDPOINT", check_env_var("AZURE_OPENAI_ENDPOINT"))
    
    if not has_azure_key or not has_azure_endpoint:
        print(f"{YELLOW}   ⚠️  Las credenciales de Azure se pueden configurar en run_benchmark.py{NC}")
    print()

    # Sección 6: Directorios
    print(f"{YELLOW}📂 Estructura de Directorios{NC}")
    all_checks.append(check_item("src/benchmark_agent/", check_file_exists("src/benchmark_agent/")))
    all_checks.append(check_item("scenarios/", check_file_exists("scenarios/")))
    
    # Crear directorio de resultados si no existe
    benchmark_results_existed = Path("benchmark_results").exists()
    Path("benchmark_results").mkdir(exist_ok=True)
    all_checks.append(check_item("benchmark_results/", check_file_exists("benchmark_results/")))
    
    if not benchmark_results_existed:
        print(f"   {YELLOW}⚠️  Directorio benchmark_results/ creado automáticamente{NC}")
    print()

    # Resumen final
    print(f"{BLUE}{'='*80}{NC}")
    passed = sum(all_checks)
    total = len(all_checks)
    
    if passed == total:
        print(f"{GREEN}✅ VALIDACIÓN EXITOSA: {passed}/{total} checks pasaron{NC}")
        print(f"\n{GREEN}🎉 ¡Todo listo para ejecutar la evaluación completa!{NC}")
        print(f"\n{BLUE}Próximo paso:{NC}")
        print(f"   ./run_complete_evaluation.sh")
        return 0
    else:
        print(f"{RED}❌ VALIDACIÓN FALLIDA: {passed}/{total} checks pasaron{NC}")
        print(f"\n{YELLOW}Correcciones necesarias:{NC}")
        
        # Sugerencias de corrección
        if not check_module("matplotlib")():
            print(f"   • Instalar dependencias de gráficos:")
            print(f"     pip install matplotlib pandas seaborn numpy")
        
        if not check_executable("run_complete_evaluation.sh")():
            print(f"   • Hacer scripts ejecutables:")
            print(f"     chmod +x run_complete_evaluation.sh generate_thesis_plots.py")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())
