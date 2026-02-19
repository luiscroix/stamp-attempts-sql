##  Project Structure

- [Company folder]
    - archivos.xml
- instructions.md

## Project description

Este proyecto tiene la finalidad de obtener las peticiones SQL para ingresar la información faltante en la base de datos de los timbrados duplicados.

Cada carpeta es una empresa, dentro de la carpeta de la empresa hay una carpeta llamada XMLS en la cual encontraras archivos .xml de las cuales extraeremos la información.

## Instructions

Generar un script en python en el cual recorras por las carpetas de las compañias, leeras los archivos XML en de cada carpeta.

Identificaras el xml como resultado necesito un archivo querys.sql dentro de la carpeta de la compañia.

El SQL debe tener el siguiente formato:

Update invoice_invoice_attempts set xml = "[XML file]", tfd = "[Elemento :TimbreFiscalDigital del XML]", raw_response = null, uuid = [uuid property from xml], status = 1 where invoice_id = [registro Folio del xml '/cfdi:Comprobante/@Folio')] and type = 2

Se debe considerar ahora que el sql sera ejecutado via consola en un proyecto symfony, por lo que el resultado debe ser :

bin/console doctrine:query:sql "SQL"

Muy importante que las comillas esten bien escapadas, ya que el query esta dentro de comillas dobles para ejecutarlo en la consola.


Agrega tambien un search.sql donde generes esta consulta:

Select parent_id from invoice_invoices where id in (numero_folio, numero_folio)
