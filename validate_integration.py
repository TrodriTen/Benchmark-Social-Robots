#!/usr/bin/env python3
"""
Script de validación para verificar la integración de herramientas reales.

Este script verifica:
1. Que las arquitecturas se puedan instanciar en modo dummy
2. Que las arquitecturas se puedan instanciar en modo real (si ROS está disponible)
3. Que el parámetro use_real_tools se pase correctamente
"""

import sys
import os

# Añadir src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from benchmark_agent.llm_factory import get_chat_model
from benchmark_agent.architectures.react import ReactAgent
from benchmark_agent.architectures.plan_then_act import PlanThenActAgent
from benchmark_agent.architectures.reflexion import ReflexionAgent
from benchmark_agent.architectures.reference import ReferenceAgent


def test_architecture_instantiation(arch_name, arch_class, use_real_tools=False):
    """Prueba instanciar una arquitectura."""
    mode = "REAL" if use_real_tools else "DUMMY"
    print(f"\n{'='*60}")
    print(f"Probando {arch_name} en modo {mode}")
    print('='*60)
    
    try:
        # Crear LLM dummy
        from langchain_ollama import ChatOllama
        llm = ChatOllama(model="qwen2.5:0.5b", temperature=0.0)
        
        # Instanciar arquitectura
        if arch_name == "ReAct":
            agent = arch_class(llm=llm, use_real_tools=use_real_tools)
        elif arch_name == "Plan-then-Act":
            agent = arch_class(llm=llm, use_real_tools=use_real_tools)
        elif arch_name == "Reflexion":
            agent = arch_class(llm=llm, tools=[], use_real_tools=use_real_tools)
        elif arch_name == "Reference":
            agent = arch_class(llm=llm, tools=[], use_real_tools=use_real_tools)
        
        # Verificar atributos
        assert hasattr(agent, 'use_real_tools'), "Falta atributo use_real_tools"
        assert agent.use_real_tools == use_real_tools, f"use_real_tools={agent.use_real_tools}, esperado={use_real_tools}"
        
        if use_real_tools:
            assert hasattr(agent, 'tools'), "Falta atributo tools en modo real"
            assert agent.tools is not None, "tools no debe ser None en modo real"
            print(f"✅ {arch_name} instanciado correctamente en modo {mode}")
            print(f"   Herramientas disponibles: {len(agent.tools)}")
        else:
            assert hasattr(agent, 'adapters'), "Falta atributo adapters en modo dummy"
            assert agent.adapters is not None, "adapters no debe ser None en modo dummy"
            print(f"✅ {arch_name} instanciado correctamente en modo {mode}")
            print(f"   Adapters disponibles: {len(agent.adapters)}")
        
        return True
    
    except ImportError as e:
        if use_real_tools and "ros_langgraph_tools" in str(e):
            print(f"⚠️  {arch_name} en modo {mode}: ROS no disponible (esperado)")
            print(f"   Error: {str(e)[:100]}...")
            return None  # No es un error, simplemente ROS no está disponible
        else:
            print(f"❌ {arch_name} en modo {mode}: Error de importación")
            print(f"   {str(e)}")
            return False
    
    except Exception as e:
        print(f"❌ {arch_name} en modo {mode}: Error inesperado")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("="*60)
    print("VALIDACIÓN DE INTEGRACIÓN DE HERRAMIENTAS REALES")
    print("="*60)
    
    architectures = [
        ("ReAct", ReactAgent),
        ("Plan-then-Act", PlanThenActAgent),
        ("Reflexion", ReflexionAgent),
        ("Reference", ReferenceAgent)
    ]
    
    results_dummy = {}
    results_real = {}
    
    # Probar modo DUMMY
    print("\n" + "="*60)
    print("FASE 1: Modo DUMMY (sin ROS)")
    print("="*60)
    
    for arch_name, arch_class in architectures:
        results_dummy[arch_name] = test_architecture_instantiation(
            arch_name, arch_class, use_real_tools=False
        )
    
    # Probar modo REAL
    print("\n" + "="*60)
    print("FASE 2: Modo REAL (con ROS)")
    print("="*60)
    
    for arch_name, arch_class in architectures:
        results_real[arch_name] = test_architecture_instantiation(
            arch_name, arch_class, use_real_tools=True
        )
    
    # Resumen
    print("\n" + "="*60)
    print("RESUMEN DE VALIDACIÓN")
    print("="*60)
    
    print("\nModo DUMMY:")
    for arch_name in results_dummy:
        status = "✅ OK" if results_dummy[arch_name] else "❌ FALLO"
        print(f"  {arch_name:20s}: {status}")
    
    print("\nModo REAL:")
    for arch_name in results_real:
        result = results_real[arch_name]
        if result is True:
            status = "✅ OK"
        elif result is False:
            status = "❌ FALLO"
        else:  # None = ROS no disponible
            status = "⚠️  ROS no disponible"
        print(f"  {arch_name:20s}: {status}")
    
    # Conclusión
    print("\n" + "="*60)
    all_dummy_ok = all(r is True for r in results_dummy.values())
    
    if all_dummy_ok:
        print("✅ VALIDACIÓN EXITOSA")
        print("   Todas las arquitecturas funcionan en modo DUMMY")
        
        any_real_ok = any(r is True for r in results_real.values())
        if any_real_ok:
            print("   Algunas arquitecturas funcionan en modo REAL")
        else:
            print("   Modo REAL requiere ROS iniciado (esperado)")
    else:
        print("❌ VALIDACIÓN FALLIDA")
        print("   Algunas arquitecturas no funcionan en modo DUMMY")
        return 1
    
    print("="*60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
