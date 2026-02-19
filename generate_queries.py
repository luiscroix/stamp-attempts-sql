#!/usr/bin/env python3
"""
Genera archivos querys.sql en cada carpeta de compañía.

Recorre las carpetas de compañías que tengan una subcarpeta "XMLS",
lee los archivos .xml de cada XMLS y genera un archivo querys.sql
en la carpeta de la compañía con los UPDATE para invoice_invoice_attempts,
listos para ejecutar con:

  bin/console doctrine:query:sql "SQL"
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path


# Namespaces CFDI 4.0 y TimbreFiscalDigital
NS = {
    "cfdi": "http://www.sat.gob.mx/cfd/4",
    "tfd": "http://www.sat.gob.mx/TimbreFiscalDigital",
}


def extraer_tfd_como_texto(contenido_xml: str) -> str:
    """Extrae el elemento TimbreFiscalDigital completo como cadena."""
    # Buscar <tfd:TimbreFiscalDigital ... /> o </tfd:TimbreFiscalDigital>
    match = re.search(
        r"<tfd:TimbreFiscalDigital[^>]*(?:/>|>.*?</tfd:TimbreFiscalDigital>)",
        contenido_xml,
        re.DOTALL,
    )
    if match:
        return match.group(0)
    # Por si el prefijo es otro o no hay prefijo
    match = re.search(
        r"<[^:]*:?TimbreFiscalDigital[^>]*(?:/>|>.*?</[^:]*:?TimbreFiscalDigital>)",
        contenido_xml,
        re.DOTALL,
    )
    if match:
        return match.group(0)
    return ""


def extraer_folio_y_uuid(contenido_xml: str) -> tuple[str | None, str | None]:
    """Extrae Folio del Comprobante y UUID del TimbreFiscalDigital."""
    try:
        root = ET.fromstring(contenido_xml)
        folio = None
        uuid = None
        # Folio en Comprobante (puede tener prefijo cfdi:)
        for elem in [root] + list(root.iter()):
            tag = elem.tag
            if "Comprobante" in tag or tag == "{" + NS["cfdi"] + "}Comprobante":
                folio = elem.get("Folio")
            if "TimbreFiscalDigital" in tag or tag == "{" + NS["tfd"] + "}TimbreFiscalDigital":
                uuid = elem.get("UUID")
            if folio is not None and uuid is not None:
                break
        return (folio, uuid)
    except ET.ParseError:
        return (None, None)


def escapar_para_consola(s: str) -> str:
    """
    Escapa la cadena para ir dentro de comillas dobles en la consola.
    Doctrine recibe: bin/console doctrine:query:sql "SQL"
    Dentro del SQL, las comillas dobles de los literales deben ser \\"
    y las barras invertidas que introduzcamos deben escaparse si es necesario.
    """
    # Escapar backslash primero, luego comillas dobles
    return s.replace("\\", "\\\\").replace('"', '\\"')


def procesar_carpeta_compania(base: Path, carpeta_compania: Path, carpeta_xmls: Path) -> None:
    """Genera querys.sql y search.sql en la carpeta de la compañía a partir de los XML en XMLS/."""
    lineas_sql = []
    folios = []
    for archivo_xml in sorted(carpeta_xmls.glob("*.xml")):
        try:
            contenido_xml = archivo_xml.read_text(encoding="utf-8", errors="replace").strip()
        except Exception:
            continue
        if not contenido_xml:
            continue

        tfd_texto = extraer_tfd_como_texto(contenido_xml)
        folio, uuid = extraer_folio_y_uuid(contenido_xml)
        if not folio:
            continue
        if not uuid:
            uuid = ""

        # Escapar valores para meter dentro de comillas dobles en la consola
        xml_esc = escapar_para_consola(contenido_xml)
        tfd_esc = escapar_para_consola(tfd_texto)
        uuid_sql = f'"{uuid}"'
        # UPDATE ... set xml = "...", tfd = "...", raw_response = null, uuid = "...", status = 1 where invoice_id = ... and type = 2
        sql = (
            f'UPDATE invoice_invoice_attempts SET xml = "{xml_esc}", tfd = "{tfd_esc}", '
            f'raw_response = NULL, uuid = {uuid_sql}, status = 1 '
            f"WHERE invoice_id = {folio} AND type = 2"
        )
        linea_consola = f'bin/console doctrine:query:sql "{escapar_para_consola(sql)}"'
        lineas_sql.append(linea_consola)
        folios.append(folio)

    if not lineas_sql:
        return

    archivo_salida = carpeta_compania / "querys.sql"
    archivo_salida.write_text("\n".join(lineas_sql) + "\n", encoding="utf-8")
    print(f"  {archivo_salida.relative_to(base)}: {len(lineas_sql)} consulta(s)")

    # search.sql: Select parent_id from invoice_invoices where id in (numero_folio, ...)
    lista_folios = ", ".join(folios)
    search_sql = f"Select parent_id from invoice_invoices where id in ({lista_folios})"
    archivo_search = carpeta_compania / "search.sql"
    archivo_search.write_text(search_sql + "\n", encoding="utf-8")
    print(f"  {archivo_search.relative_to(base)}")


def main():
    base = Path(__file__).resolve().parent
    # Carpetas de compañía: solo las que tienen subcarpeta "XMLS" con archivos .xml
    subcarpeta_xmls = "XMLS"
    encontradas = 0
    print(f"Procesando compañías (carpetas con {subcarpeta_xmls}/)...")
    for carpeta in sorted(base.iterdir()):
        if not carpeta.is_dir() or carpeta.name.startswith("."):
            continue
        carpeta_xmls = carpeta / subcarpeta_xmls
        if not carpeta_xmls.is_dir():
            continue
        xmls = list(carpeta_xmls.glob("*.xml"))
        if not xmls:
            continue
        print(f"\n--- {carpeta.name}/{subcarpeta_xmls}/")
        procesar_carpeta_compania(base, carpeta, carpeta_xmls)
        encontradas += 1
    if encontradas == 0:
        print(f"No se encontraron carpetas de compañía con subcarpeta '{subcarpeta_xmls}' y archivos .xml.")
    print("\nProceso terminado.")


if __name__ == "__main__":
    main()
