#!/usr/bin/env python3
"""
Generador Automático de Gráficos para Tesis
=============================================

Este script genera todos los gráficos necesarios para la sección de resultados
de la tesis, listos para incluir en LaTeX.

Uso:
    python generate_thesis_plots.py <results_dir>

Ejemplo:
    python generate_thesis_plots.py tesis_results_20250118_120000

Gráficos generados:
    1. success_rate_comparison.png - Comparación de tasa de éxito
    2. execution_time_comparison.png - Comparación de tiempo de ejecución
    3. token_consumption.png - Consumo de tokens por arquitectura
    4. robustness_analysis.png - Coeficiente de variación
    5. perturbation_impact.png - Impacto de perturbaciones
    6. comprehensive_comparison.png - Panel con todas las métricas

Requisitos:
    pip install matplotlib pandas seaborn numpy
"""

import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path

# Configuración de estilo
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# Colores consistentes por arquitectura
ARCH_COLORS = {
    'react': '#FF6B6B',
    'plan-then-act': '#4ECDC4',
    'reference': '#45B7D1',
    'reflexion': '#FFA07A'
}

def load_data(results_dir):
    """Carga los datos desde el directorio de resultados."""
    reports_dir = Path(results_dir) / "reports"
    
    datos_completos = pd.read_csv(reports_dir / "datos_completos.csv")
    tabla_resumen = pd.read_csv(reports_dir / "tabla_resumen.csv")
    
    return datos_completos, tabla_resumen

def plot_success_rate_comparison(df, output_dir):
    """Gráfico 1: Comparación de tasa de éxito."""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Separar por condición
    baseline = df[df['condition'] == 'Baseline'].groupby('architecture')['success_rate'].mean()
    perturbed = df[df['condition'] == 'Perturbado'].groupby('architecture')['success_rate'].mean()
    
    x = np.arange(len(baseline))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, baseline, width, label='Sin Perturbaciones', 
                   alpha=0.8, edgecolor='black')
    bars2 = ax.bar(x + width/2, perturbed, width, label='Con Perturbaciones',
                   alpha=0.8, edgecolor='black')
    
    ax.set_xlabel('Arquitectura', fontsize=12, fontweight='bold')
    ax.set_ylabel('Tasa de Éxito (%)', fontsize=12, fontweight='bold')
    ax.set_title('Comparación de Tasa de Éxito por Arquitectura', 
                 fontsize=14, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels([arch.upper() for arch in baseline.index], rotation=15, ha='right')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3, axis='y')
    ax.set_ylim([0, 105])
    
    # Añadir valores sobre las barras
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}%',
                   ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'success_rate_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Generado: success_rate_comparison.png")

def plot_execution_time_comparison(df, output_dir):
    """Gráfico 2: Comparación de tiempo de ejecución."""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    baseline = df[df['condition'] == 'Baseline'].groupby('architecture')['avg_time'].mean()
    perturbed = df[df['condition'] == 'Perturbado'].groupby('architecture')['avg_time'].mean()
    
    x = np.arange(len(baseline))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, baseline, width, label='Sin Perturbaciones',
                   alpha=0.8, edgecolor='black')
    bars2 = ax.bar(x + width/2, perturbed, width, label='Con Perturbaciones',
                   alpha=0.8, edgecolor='black')
    
    ax.set_xlabel('Arquitectura', fontsize=12, fontweight='bold')
    ax.set_ylabel('Tiempo Promedio (segundos)', fontsize=12, fontweight='bold')
    ax.set_title('Comparación de Tiempo de Ejecución por Arquitectura',
                 fontsize=14, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels([arch.upper() for arch in baseline.index], rotation=15, ha='right')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3, axis='y')
    
    # Añadir valores sobre las barras
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}s',
                   ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'execution_time_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Generado: execution_time_comparison.png")

def plot_token_consumption(df, output_dir):
    """Gráfico 3: Consumo de tokens."""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Boxplot para mostrar distribución
    baseline = df[df['condition'] == 'Baseline']
    
    positions = []
    data_to_plot = []
    labels = []
    
    for i, arch in enumerate(baseline['architecture'].unique()):
        arch_data = baseline[baseline['architecture'] == arch]['avg_tokens']
        data_to_plot.append(arch_data)
        positions.append(i)
        labels.append(arch.upper())
    
    bp = ax.boxplot(data_to_plot, positions=positions, widths=0.6,
                    patch_artist=True, showmeans=True,
                    boxprops=dict(facecolor='lightblue', alpha=0.7),
                    medianprops=dict(color='red', linewidth=2),
                    meanprops=dict(marker='D', markerfacecolor='green', markersize=8))
    
    ax.set_xlabel('Arquitectura', fontsize=12, fontweight='bold')
    ax.set_ylabel('Tokens Promedio', fontsize=12, fontweight='bold')
    ax.set_title('Distribución de Consumo de Tokens por Arquitectura',
                 fontsize=14, fontweight='bold', pad=20)
    ax.set_xticks(positions)
    ax.set_xticklabels(labels, rotation=15, ha='right')
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'token_consumption.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Generado: token_consumption.png")

def plot_robustness_analysis(df_summary, output_dir):
    """Gráfico 4: Análisis de robustez (Coeficiente de Variación)."""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    baseline = df_summary[df_summary['condition'] == 'Baseline']
    
    # Calcular CV (Coefficient of Variation) = (std / mean) * 100
    architectures = baseline['architecture'].values
    cv_success = (baseline['success_std'] / baseline['success_mean'] * 100).values
    cv_time = (baseline['time_std'] / baseline['time_mean'] * 100).values
    
    x = np.arange(len(architectures))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, cv_success, width, label='CV Tasa de Éxito',
                   alpha=0.8, edgecolor='black')
    bars2 = ax.bar(x + width/2, cv_time, width, label='CV Tiempo',
                   alpha=0.8, edgecolor='black')
    
    # Líneas de referencia para interpretación
    ax.axhline(y=10, color='green', linestyle='--', alpha=0.5, label='Excelente (CV < 10%)')
    ax.axhline(y=20, color='orange', linestyle='--', alpha=0.5, label='Bueno (CV < 20%)')
    ax.axhline(y=35, color='red', linestyle='--', alpha=0.5, label='Moderado (CV < 35%)')
    
    ax.set_xlabel('Arquitectura', fontsize=12, fontweight='bold')
    ax.set_ylabel('Coeficiente de Variación (%)', fontsize=12, fontweight='bold')
    ax.set_title('Análisis de Robustez: Coeficiente de Variación',
                 fontsize=14, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels([arch.upper() for arch in architectures], rotation=15, ha='right')
    ax.legend(fontsize=9, loc='upper right')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Añadir valores sobre las barras
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}%',
                   ha='center', va='bottom', fontsize=8)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'robustness_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Generado: robustness_analysis.png")

def plot_perturbation_impact(df, output_dir):
    """Gráfico 5: Impacto de perturbaciones."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    architectures = df['architecture'].unique()
    
    # Calcular degradación
    degradation_success = []
    degradation_time = []
    
    for arch in architectures:
        baseline_success = df[(df['architecture'] == arch) & 
                             (df['condition'] == 'Baseline')]['success_rate'].mean()
        perturbed_success = df[(df['architecture'] == arch) & 
                              (df['condition'] == 'Perturbado')]['success_rate'].mean()
        
        baseline_time = df[(df['architecture'] == arch) & 
                          (df['condition'] == 'Baseline')]['avg_time'].mean()
        perturbed_time = df[(df['architecture'] == arch) & 
                           (df['condition'] == 'Perturbado')]['avg_time'].mean()
        
        degradation_success.append(baseline_success - perturbed_success)
        degradation_time.append(perturbed_time - baseline_time)
    
    # Gráfico 1: Degradación de tasa de éxito
    bars1 = ax1.bar(range(len(architectures)), degradation_success, 
                    color=['red' if x > 0 else 'green' for x in degradation_success],
                    alpha=0.7, edgecolor='black')
    ax1.set_xlabel('Arquitectura', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Degradación de Tasa de Éxito (puntos %)', fontsize=12, fontweight='bold')
    ax1.set_title('Impacto en Tasa de Éxito', fontsize=13, fontweight='bold')
    ax1.set_xticks(range(len(architectures)))
    ax1.set_xticklabels([arch.upper() for arch in architectures], rotation=15, ha='right')
    ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
    ax1.grid(True, alpha=0.3, axis='y')
    
    for i, bar in enumerate(bars1):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}',
                ha='center', va='bottom' if height > 0 else 'top', fontsize=9)
    
    # Gráfico 2: Incremento de tiempo
    bars2 = ax2.bar(range(len(architectures)), degradation_time,
                    color=['red' if x > 0 else 'green' for x in degradation_time],
                    alpha=0.7, edgecolor='black')
    ax2.set_xlabel('Arquitectura', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Incremento de Tiempo (segundos)', fontsize=12, fontweight='bold')
    ax2.set_title('Impacto en Tiempo de Ejecución', fontsize=13, fontweight='bold')
    ax2.set_xticks(range(len(architectures)))
    ax2.set_xticklabels([arch.upper() for arch in architectures], rotation=15, ha='right')
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
    ax2.grid(True, alpha=0.3, axis='y')
    
    for i, bar in enumerate(bars2):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}s',
                ha='center', va='bottom' if height > 0 else 'top', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'perturbation_impact.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Generado: perturbation_impact.png")

def plot_comprehensive_comparison(df, df_summary, output_dir):
    """Gráfico 6: Panel comprensivo con todas las métricas."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    baseline = df[df['condition'] == 'Baseline']
    architectures = sorted(baseline['architecture'].unique())
    
    # Subplot 1: Tasa de éxito
    ax = axes[0, 0]
    success_data = [baseline[baseline['architecture'] == arch]['success_rate'].values 
                    for arch in architectures]
    bp1 = ax.boxplot(success_data, labels=[a.upper() for a in architectures],
                     patch_artist=True, showmeans=True)
    for patch, color in zip(bp1['boxes'], [ARCH_COLORS.get(a, 'gray') for a in architectures]):
        patch.set_facecolor(color)
        patch.set_alpha(0.6)
    ax.set_title('Tasa de Éxito', fontsize=13, fontweight='bold')
    ax.set_ylabel('Éxito (%)', fontsize=11)
    ax.grid(True, alpha=0.3, axis='y')
    ax.tick_params(axis='x', rotation=15)
    
    # Subplot 2: Tiempo de ejecución
    ax = axes[0, 1]
    time_data = [baseline[baseline['architecture'] == arch]['avg_time'].values 
                 for arch in architectures]
    bp2 = ax.boxplot(time_data, labels=[a.upper() for a in architectures],
                     patch_artist=True, showmeans=True)
    for patch, color in zip(bp2['boxes'], [ARCH_COLORS.get(a, 'gray') for a in architectures]):
        patch.set_facecolor(color)
        patch.set_alpha(0.6)
    ax.set_title('Tiempo de Ejecución', fontsize=13, fontweight='bold')
    ax.set_ylabel('Tiempo (s)', fontsize=11)
    ax.grid(True, alpha=0.3, axis='y')
    ax.tick_params(axis='x', rotation=15)
    
    # Subplot 3: Pasos promedio
    ax = axes[1, 0]
    steps_data = [baseline[baseline['architecture'] == arch]['avg_steps'].values 
                  for arch in architectures]
    bp3 = ax.boxplot(steps_data, labels=[a.upper() for a in architectures],
                     patch_artist=True, showmeans=True)
    for patch, color in zip(bp3['boxes'], [ARCH_COLORS.get(a, 'gray') for a in architectures]):
        patch.set_facecolor(color)
        patch.set_alpha(0.6)
    ax.set_title('Pasos Promedio', fontsize=13, fontweight='bold')
    ax.set_ylabel('Pasos', fontsize=11)
    ax.grid(True, alpha=0.3, axis='y')
    ax.tick_params(axis='x', rotation=15)
    
    # Subplot 4: Tokens promedio
    ax = axes[1, 1]
    tokens_data = [baseline[baseline['architecture'] == arch]['avg_tokens'].values 
                   for arch in architectures]
    bp4 = ax.boxplot(tokens_data, labels=[a.upper() for a in architectures],
                     patch_artist=True, showmeans=True)
    for patch, color in zip(bp4['boxes'], [ARCH_COLORS.get(a, 'gray') for a in architectures]):
        patch.set_facecolor(color)
        patch.set_alpha(0.6)
    ax.set_title('Consumo de Tokens', fontsize=13, fontweight='bold')
    ax.set_ylabel('Tokens', fontsize=11)
    ax.grid(True, alpha=0.3, axis='y')
    ax.tick_params(axis='x', rotation=15)
    
    fig.suptitle('Comparación Comprensiva de Arquitecturas Agentivas',
                 fontsize=16, fontweight='bold', y=0.995)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'comprehensive_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✅ Generado: comprehensive_comparison.png")

def generate_latex_table(df_summary, output_dir):
    """Genera código LaTeX para tabla de resultados."""
    baseline = df_summary[df_summary['condition'] == 'Baseline'].sort_values('architecture')
    
    latex_code = r"""\begin{table}[h]
\centering
\caption{Comparación de Arquitecturas Agentivas en Escenarios Baseline}
\label{tab:results_comparison}
\begin{tabular}{lcccc}
\toprule
\textbf{Arquitectura} & \textbf{Éxito (\%)} & \textbf{Tiempo (s)} & \textbf{Pasos} & \textbf{Tokens} \\
\midrule
"""
    
    for _, row in baseline.iterrows():
        arch_name = row['architecture'].replace('-', '-').title()
        latex_code += f"{arch_name} & "
        latex_code += f"{row['success_mean']:.1f} $\\pm$ {row['success_std']:.1f} & "
        latex_code += f"{row['time_mean']:.1f} $\\pm$ {row['time_std']:.1f} & "
        latex_code += f"{row['steps_mean']:.1f} $\\pm$ {row['steps_std']:.1f} & "
        latex_code += f"{row['tokens_mean']:.0f} $\\pm$ {row['tokens_std']:.0f} \\\\\n"
    
    latex_code += r"""\bottomrule
\end{tabular}
\end{table}
"""
    
    with open(output_dir / 'tabla_latex.tex', 'w') as f:
        f.write(latex_code)
    
    print("✅ Generado: tabla_latex.tex")

def main():
    if len(sys.argv) < 2:
        print("❌ Error: Directorio de resultados no especificado")
        print(f"\nUso: python {sys.argv[0]} <results_dir>")
        print(f"Ejemplo: python {sys.argv[0]} tesis_results_20250118_120000")
        sys.exit(1)
    
    results_dir = Path(sys.argv[1])
    
    if not results_dir.exists():
        print(f"❌ Error: El directorio {results_dir} no existe")
        sys.exit(1)
    
    reports_dir = results_dir / "reports"
    plots_dir = reports_dir / "plots"
    plots_dir.mkdir(exist_ok=True)
    
    print("📊 Generando gráficos para la tesis...")
    print(f"   Directorio de entrada: {results_dir}")
    print(f"   Directorio de salida: {plots_dir}")
    print()
    
    # Cargar datos
    try:
        df, df_summary = load_data(results_dir)
        print(f"✅ Datos cargados: {len(df)} registros, {len(df_summary)} resúmenes")
        print()
    except Exception as e:
        print(f"❌ Error al cargar datos: {e}")
        sys.exit(1)
    
    # Generar gráficos
    print("🎨 Generando gráficos...")
    try:
        plot_success_rate_comparison(df, plots_dir)
        plot_execution_time_comparison(df, plots_dir)
        plot_token_consumption(df, plots_dir)
        plot_robustness_analysis(df_summary, plots_dir)
        plot_perturbation_impact(df, plots_dir)
        plot_comprehensive_comparison(df, df_summary, plots_dir)
        generate_latex_table(df_summary, plots_dir)
    except Exception as e:
        print(f"❌ Error al generar gráficos: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print()
    print("✅ Todos los gráficos generados exitosamente")
    print()
    print("📁 Archivos generados:")
    for file in sorted(plots_dir.glob("*")):
        print(f"   • {file.name}")
    print()
    print("💡 Próximos pasos:")
    print("   1. Revisar los gráficos en el directorio plots/")
    print("   2. Incluir en tu tesis LaTeX con:")
    print("      \\includegraphics[width=\\textwidth]{plots/success_rate_comparison.png}")
    print("   3. Copiar tabla_latex.tex directamente a tu documento")
    print()

if __name__ == "__main__":
    main()
