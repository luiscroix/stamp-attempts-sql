#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para generar archivos SQL con comandos de consola de Symfony
basados en archivos CSV e XML de timbrados duplicados.

El formato de salida es:
bin/console doctrine:query:sql "UPDATE invoice_invoice_attempts SET ..."

Las comillas están correctamente escapadas para ejecutarse en la consola.
"""

import os
import csv
import xml.etree.ElementTree as ET
from pathlib import Path
import re


def escape_sql_string(value):
    """Escapa comillas simples en strings SQL."""
    if value is None:
        return "null"
    return "'" + str(value).replace("'", "''") + "'"


def escape_for_shell_double_quotes(value):
    r"""Escapa un string para que funcione dentro de comillas dobles en la shell.
    
    Dentro de comillas dobles en shell, necesitamos escapar:
    - Comillas dobles con \"
    - Backslashes con \\
    - Variables $ con \$
    - Backticks con \`
    """
    if value is None:
        return ""
    # Escapar backslashes primero (importante: hacerlo primero)
    value = str(value).replace("\\", "\\\\")
    # Escapar comillas dobles
    value = value.replace('"', '\\"')
    # Escapar variables $ (por si acaso hay variables en el contenido)
    value = value.replace("$", "\\$")
    # Escapar backticks
    value = value.replace("`", "\\`")
    return value


def extract_tfd_element(xml_content):
    """Extrae el elemento completo TimbreFiscalDigital del XML."""
    # Buscar el elemento TimbreFiscalDigital usando regex
    # Puede ser auto-cerrado (<tfd:TimbreFiscalDigital ... />) o con etiquetas separadas
    # Primero intentar elemento auto-cerrado
    pattern = r'<tfd:TimbreFiscalDigital[^>]*/>'
    match = re.search(pattern, xml_content, re.DOTALL)
    if match:
        return match.group(0)
    
    # Intentar con etiquetas separadas
    pattern = r'<tfd:TimbreFiscalDigital[^>]*>.*?</tfd:TimbreFiscalDigital>'
    match = re.search(pattern, xml_content, re.DOTALL)
    if match:
        return match.group(0)
    
    # Intentar con namespace alternativo (auto-cerrado)
    pattern = r'<[^:]*:TimbreFiscalDigital[^>]*/>'
    match = re.search(pattern, xml_content, re.DOTALL)
    if match:
        return match.group(0)
    
    # Intentar con namespace alternativo (etiquetas separadas)
    pattern = r'<[^:]*:TimbreFiscalDigital[^>]*>.*?</[^:]*:TimbreFiscalDigital>'
    match = re.search(pattern, xml_content, re.DOTALL)
    if match:
        return match.group(0)
    
    return None


def get_receptor_rfc(xml_content):
    """Extrae el RFC del receptor del XML."""
    try:
        root = ET.fromstring(xml_content)
        
        # Intentar con namespace cfdi
        receptor = root.find('.//{http://www.sat.gob.mx/cfd/4}Receptor')
        if receptor is not None and 'Rfc' in receptor.attrib:
            return receptor.get('Rfc')
        
        # Buscar en todo el árbol cualquier elemento que contenga "Receptor" en el tag
        for elem in root.iter():
            if 'Receptor' in elem.tag and 'Rfc' in elem.attrib:
                return elem.get('Rfc')
        
        # Como último recurso, buscar con regex
        pattern = r'<[^:]*:Receptor[^>]*Rfc="([^"]+)"'
        match = re.search(pattern, xml_content)
        if match:
            return match.group(1)
                
    except ET.ParseError as e:
        print(f"Error al parsear XML: {e}")
    except Exception as e:
        print(f"Error al extraer RFC: {e}")
    
    return None


def get_uuid_from_xml(xml_content):
    """Extrae el UUID del XML."""
    try:
        root = ET.fromstring(xml_content)
        # Buscar el elemento TimbreFiscalDigital
        tfd = root.find('.//{http://www.sat.gob.mx/TimbreFiscalDigital}TimbreFiscalDigital')
        if tfd is not None and 'UUID' in tfd.attrib:
            return tfd.get('UUID')
        
        # Intentar sin namespace
        for elem in root.iter():
            if 'TimbreFiscalDigital' in elem.tag and 'UUID' in elem.attrib:
                return elem.get('UUID')
        
        # Como último recurso, buscar con regex
        pattern = r'<[^:]*:TimbreFiscalDigital[^>]*UUID="([^"]+)"'
        match = re.search(pattern, xml_content)
        if match:
            return match.group(1)
                
    except ET.ParseError as e:
        print(f"Error al parsear XML: {e}")
    except Exception as e:
        print(f"Error al extraer UUID: {e}")
    
    return None


def process_company_folder(company_path):
    """Procesa una carpeta de compañía y genera el archivo queries.sql."""
    company_path = Path(company_path)
    csv_file = company_path / "informations.csv"
    
    # Intentar también con "information.csv" si no existe "informations.csv"
    if not csv_file.exists():
        csv_file = company_path / "information.csv"
    
    if not csv_file.exists():
        print(f"Advertencia: No se encontró archivo CSV en {company_path}")
        return
    
    xmls_folder = company_path / "XMLS"
    if not xmls_folder.exists():
        print(f"Advertencia: No se encontró carpeta XMLS en {company_path}")
        return
    
    # Leer el CSV
    records = []
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2:
                    record_id = row[0].strip()
                    rfc = row[1].strip()
                    records.append((record_id, rfc))
    except Exception as e:
        print(f"Error al leer CSV {csv_file}: {e}")
        return
    
    # Cargar todos los XMLs en memoria
    xml_files = {}
    for xml_file in xmls_folder.glob("*.xml"):
        try:
            with open(xml_file, 'r', encoding='utf-8') as f:
                xml_content = f.read()
                receptor_rfc = get_receptor_rfc(xml_content)
                if receptor_rfc:
                    xml_files[receptor_rfc.upper()] = {
                        'path': xml_file,
                        'content': xml_content
                    }
        except Exception as e:
            print(f"Error al leer XML {xml_file}: {e}")
    
    # Generar queries SQL
    queries = []
    for record_id, rfc in records:
        rfc_upper = rfc.upper()
        if rfc_upper in xml_files:
            xml_data = xml_files[rfc_upper]
            xml_content = xml_data['content']
            xml_filename = xml_data['path'].name
            
            # Extraer información del XML
            uuid = get_uuid_from_xml(xml_content)
            tfd_element = extract_tfd_element(xml_content)
            
            if uuid and tfd_element:
                # Escapar el contenido del XML y TFD para SQL (comillas simples escapadas con '')
                xml_escaped_sql = escape_sql_string(xml_content)
                tfd_escaped_sql = escape_sql_string(tfd_element)
                uuid_escaped_sql = escape_sql_string(uuid)
                
                # Construir la query SQL
                sql_query = f"UPDATE invoice_invoice_attempts SET xml = {xml_escaped_sql}, tfd = {tfd_escaped_sql}, raw_response = null, uuid = {uuid_escaped_sql} WHERE id = {record_id}"
                
                # Escapar la query SQL completa para que funcione dentro de comillas dobles en la shell
                sql_query_escaped = escape_for_shell_double_quotes(sql_query)
                
                # Generar el comando completo de Symfony
                command = f'bin/console doctrine:query:sql "{sql_query_escaped}"'
                queries.append(command)
            else:
                print(f"Advertencia: No se pudo extraer UUID o TFD para RFC {rfc} (ID: {record_id})")
        else:
            print(f"Advertencia: No se encontró XML para RFC {rfc} (ID: {record_id})")
    
    # Escribir el archivo queries.sql
    output_file = company_path / "queries.sql"
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for query in queries:
                f.write(query + '\n')
        print(f"✓ Generado {output_file} con {len(queries)} queries")
    except Exception as e:
        print(f"Error al escribir {output_file}: {e}")


def main():
    """Función principal."""
    # Obtener el directorio actual del script
    script_dir = Path(__file__).parent
    
    # Buscar todas las carpetas de compañías (carpetas que no sean el directorio raíz ni contengan instructions.md)
    company_folders = []
    for item in script_dir.iterdir():
        if item.is_dir() and item.name != "XMLS" and not item.name.startswith('.'):
            # Verificar que tenga una carpeta XMLS o un archivo CSV
            if (item / "XMLS").exists() or (item / "informations.csv").exists() or (item / "information.csv").exists():
                company_folders.append(item)
    
    if not company_folders:
        print("No se encontraron carpetas de compañías para procesar.")
        return
    
    print(f"Procesando {len(company_folders)} carpeta(s) de compañía(s)...\n")
    
    for company_folder in company_folders:
        print(f"Procesando: {company_folder.name}")
        process_company_folder(company_folder)
        print()
    
    print("Proceso completado.")


if __name__ == "__main__":
    main()

