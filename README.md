## Ejecuacion

SE LE DEBEN DAR PERMISOS SUDO al archivo scaneo\_v2.py.

Se selecciona la interfaz a la cual se le hara el escaneo activo para las siguientes fases despues del scaneo del kismet si esta seleccionado.

El tiempo es para las herramientas de kismet y netDiscover, se implementa en segundos y esta en el apartado "Duracion".

Todos los archivos generados incluido el exel, se almacenan en la carpeta historial. Por cada escaneo se generan subcarpetas que se llamaran por la fecha y hora del escaneo.

Las casillas vienen con preseleccion para hacer un repote completo, pero se pueden desactivar para solo hacer escaneos especificos al ap o solo el escaneo pasivo de kismet.

Si el equipo lo permite, cuando se esta haciendo el escaneo de kismet, al mostrar el mensaje "Iniciando kismet por x segundos..." se puede iniciar un localhost en el navegador que permite la visualizacion de los datos en tiempo real. http://localhost:2501/ - Este pedira registrar una contra y un usuario para continuar.

## dependencia python

- pandas

- openpyxl

- pytohn3-tk

## dependicias del .sh

En caso de usar kali linux estas herramientas ya vienen por defecto.

- kismet

- NetDiscover

Estas herraminetas faltan en el repertorio de kali, los .deb para su instalacion esta en la carpeta herramientas.

- ipcalc

- iw

- mtr

- wavevmon

## Posibles incovenientes

- En caso de parar el escaneo de kismet, antes de que empiece como tal es decir que muestre el mensaje de "kismet finalizado", entonces se debera reiniciar el equipo pues el proceso en el que pone en modo escaneo el equipo es especial para kismet por lo que restaurar la interfaz a la normalidad es complicado.

- existe un punto en el que se pedira esperar a que se restaure la conexion pues el escaneo pasivo de kismet inhabilita la interfaz como se menciono antes. Es importante pues el resto de herramientas son para diagnosticar la conexion con el AP.

