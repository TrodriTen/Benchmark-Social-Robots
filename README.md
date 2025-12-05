# Benchmark Social Robot

Este repositorio contiene los scripts y herramientas para la ejecución del benchmark de robots sociales.

## Requisitos del Sistema

Para el correcto funcionamiento de este benchmark y sus componentes asociados, se requiere:

*   **Sistema Operativo:** Ubuntu 20.04 LTS
*   **ROS:** Noetic Ninjemys
*   **Python:** 3.11

## Dependencias y Workspaces

Este benchmark interactúa con varios sistemas ROS que deben estar instalados y configurados previamente. Se recomienda organizar el código en tres workspaces independientes para evitar conflictos de dependencias.

### 1. Simulation Workspace (`simulation_ws`)
Encargado del entorno de simulación en Gazebo.

```bash
mkdir -p ~/simulation_ws/src
cd ~/simulation_ws/src
git clone https://github.com/ros-naoqi/pepper_virtual.git
# Instalar dependencias
cd ~/simulation_ws
rosdep install --from-paths src --ignore-src -r -y
catkin_make
source devel/setup.bash
```

### 2. Navigation Workspace (`navigation_ws`)
Contiene el stack de navegación `ednav` y herramientas de conversión de sensores.

```bash
mkdir -p ~/navigation_ws/src
cd ~/navigation_ws/src
git clone https://github.com/SinfonIAUniandes/pepper_2dnav.git
git clone https://github.com/SinfonIAUniandes/depthimage_to_laserscan.git
# Instalar dependencias
cd ~/navigation_ws
rosdep install --from-paths src --ignore-src -r -y
catkin_make
source devel/setup.bash
```

### 3. Sinfonia Workspace (`sinfonia_ws`)
Proporciona utilidades de alto nivel para percepción y navegación.

```bash
mkdir -p ~/sinfonia_ws/src
cd ~/sinfonia_ws/src
git clone https://github.com/SinfonIAUniandes/navigation_utilities.git
git clone https://github.com/SinfonIAUniandes/perception_utilities.git
# Instalar dependencias
cd ~/sinfonia_ws
rosdep install --from-paths src --ignore-src -r -y
catkin_make
source devel/setup.bash
```

## Instalación del Benchmark

1.  Clone este repositorio.
2.  Instale las dependencias de Python requeridas (se recomienda usar un entorno virtual con Python 3.11):

```bash
pip install -r requirements.txt
```

## Guía de Ejecución

Para ejecutar el benchmark, es necesario levantar los componentes en un orden específico. Se recomienda utilizar terminales separadas para cada proceso.

### Paso 1: Simulación
Inicie el entorno de simulación. Puede elegir diferentes entornos, por ejemplo, la oficina:

```bash
# Desde su simulation_ws
source devel/setup.bash
roslaunch pepper_gazebo_plugin pepper_gazebo_plugin_in_office.launch
```

### Paso 2: Navegación (EdNav)
Inicie el sistema de navegación `ednav`. Es **obligatorio** especificar el archivo del mapa correspondiente al entorno cargado en la simulación.

```bash
# Desde su navigation_ws
source devel/setup.bash
roslaunch pepper_2dnav pepper_2dnav.launch map_file:=map_office.yaml
```
*(Asegúrese de que el archivo del mapa exista en `pepper_2dnav/maps/` o proporcione la ruta completa)*

### Paso 3: Nav Utilities
Inicie las utilidades de navegación.

```bash
# Desde su sinfonia_ws
source devel/setup.bash
rosrun navigation_utilities NavigationUtilities.py
```

### Paso 4: Perception Utilities
Inicie las utilidades de percepción.

```bash
# Desde su sinfonia_ws
source devel/setup.bash
rosrun perception_utilities PerceptionUtilities.py
```

### Paso 5: Ejecutar Benchmark
Una vez que todos los sistemas ROS estén operativos, ejecute el script principal del benchmark utilizando Python 3.11.

#### Ejemplos de uso:

**Ejecutar arquitectura React con herramientas reales:**
```bash
python3.11 run_benchmark.py -a react --use-real-tools
```

**Ejecutar arquitectura Plan-Then-Act:**
```bash
python3.11 run_benchmark.py -a plan-then-act --use-real-tools
```

**Ver todas las opciones disponibles:**
```bash
python3.11 run_benchmark.py --help
```

## Solución de Problemas

*   **Versión de Python:** Asegúrese de estar ejecutando el script con `python3.11`. Versiones anteriores pueden causar conflictos con las librerías modernas utilizadas.
*   **Variables de Entorno:** Verifique que ha hecho `source devel/setup.bash` en cada uno de los workspaces de ROS antes de lanzar los nodos.
*   **Launch vs Run:** Note que las utilidades de Sinfonia (`navigation_utilities` y `perception_utilities`) se ejecutan con `rosrun`, no con `roslaunch`.
