# Práctica 2 - Puente de Ambite
## Programación Paralela - Año 2022/2023
##Facultad de CC.Matemáticas UCM

El pueblo de Ambite (https://es.wikipedia.org/wiki/Ambite) tiene un puente que atraviesa el río Tajuña. Es un puente compartido por peatones y vehículos. La anchura del
puente no permite el paso de vehículos en ambos sentidos (Observa la figura 1.). Por motivos de seguridad los peatones y los vehículos no pueden compartir el puente. En el caso de los peatones, sí que que pueden pasar peatones en sentido contrario.

Desarrolla en papel el monitor (o monitores) necesarios. Parte de una solución sencilla que cumpla la seguridad y a partir de ella intenta buscar soluciones a los problema de inanición.
### Escribe el invariante del monitor.
### Demuestra que el puente es seguro (no hay coches y peatones a la vez en el puente,
no hay coches en sentidos opuestos)
### Demuestra la ausencia de deadlocks
### Demuestra la ausencia de inanición.

Implementa una solución en python con la biblioteca multiprocessing.
