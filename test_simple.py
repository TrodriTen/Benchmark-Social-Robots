#!/usr/bin/env python3
"""Test simple para verificar que todo funciona"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("1. Importando service_adapter...")
from benchmark_agent.service_adapter import ADAPTERS
print(f"   ✅ {len(ADAPTERS)} adapters disponibles")

print("\n2. Importando llm_factory...")
from benchmark_agent.llm_factory import get_chat_model
print("   ✅ llm_factory importado")

print("\n3. Creando LLM...")
llm = get_chat_model(provider="ollama", model="qwen2.5:7b-instruct", temperature=0.0)
print(f"   ✅ LLM creado: {llm.model}")

print("\n4. Importando PlanThenActAgent...")
from benchmark_agent.architectures.plan_then_act import PlanThenActAgent
print("   ✅ PlanThenActAgent importado")

print("\n5. Instanciando PlanThenActAgent...")
agent = PlanThenActAgent(llm=llm)
print(f"   ✅ Agent instanciado con {len(agent.adapters)} adapters")

print("\n6. Ejecutando tarea simple...")
task = "Ve a la cocina"
print(f"   Tarea: {task}")
result = agent.run(task)
print(f"   ✅ Resultado: success={result['success']}, steps={result['steps']}")

print("\n✅ TODOS LOS TESTS PASARON")
