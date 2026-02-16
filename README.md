# Instrucciones

Para usar el script debes de tener el proyecto con esta estructura

1.- En la carpeta raiz, crea un directorio con el nombre del RFC de la empresa EMISORA

2.- Dentro de la carpeta anterior, crea una carpeta con nombre XMLS

3.- Dentro de la carpeta XMLS, coloca los archivos .xml de los timbrados.

importante que el nombre tenga este formato: [uuid].xml  ejemplo: d3d8a073-331c-4c25-a01b-176749981032.xml

4.- Dentro de la carpeta del EMISOR, crea un archivo llamado informations.csv

Ese archivo debe seguir este formato por cada linea
[id_invoice_invoice_attempts],[RFC RECEPTOR]

5.- Ejecuta el script

python3 generate_queries.py

6.- Por cada carpeta de empresa emisora se creara un archivo queries.sql como resultado
