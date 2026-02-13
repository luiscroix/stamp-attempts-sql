##  Project Structure

- [Company folder]
    - XMLS
        - uuid.xml
    - information.csv
- instructions.md

## Project description

Este proyecto tiene la finalidad de obtener las peticiones SQL para ingresar la información faltante en la base de datos de los timbrados duplicados.

Cada carpeta es una empresa, dentro de la carpeta de la empresa hay una carpeta XMLS de las cuales extraeremos la información.

Tambien hay un archivo informations.csv la cual seria nuestra guia para identificar los registros de 

## Instructions

Generar un script en python en el cual recorras por las carpetas de las compañias, leeras el archivo information.csv y los archivos XML en la carpeta XMLS.

Identificaras el xml correspondiente al registro del csv y como resultado necesito un archivo querys.sql dentro de la carpeta de la compañia. Para esto, la segunda columna del csv es el RFC que usaras para identificar el XML.

El SQL debe tener el siguiente formato:

Update invoice_invoice_attempts set xml = "[XML file]", tfd = "[Elemento :TimbreFiscalDigital del XML]", raw_response = null, uuid = [uuid property from xml] where id = [id from instructions.csv]

Se debe considerar ahora que el sql sera ejecutado via consola en un proyecto symfony, por lo que el resultado debe ser :

bin/console doctrine:query:sql "SQL"

Muy importante que las comillas esten bien escapadas, ya que el query esta dentro de comillas dobles para ejecutarlo en la consola.