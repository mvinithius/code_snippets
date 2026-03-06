import requests
import xml.etree.ElementTree as ET
import base64
import re
from typing import List, Tuple
from pathlib import Path


# ===============================
# CONFIGURAÇÃO
# ===============================

CONFLUENCE_BASE_URL = "https://seu-confluence.com"
PAGE_ID = "PAGE_ID_AQUI"
BEARER_TOKEN = "SEU_TOKEN_AQUI"

OUTPUT_MD = "comparison_report.md"


# ===============================
# CONFLUENCE
# ===============================

def get_confluence_page_content():
    url = f"{CONFLUENCE_BASE_URL}/rest/api/content/{PAGE_ID}?expand=body.storage"

    headers = {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.json()["body"]["storage"]["value"]


# ===============================
# EXTRAIR XML DO DRAW.IO
# ===============================

def extract_drawio_xml(page_html: str) -> str:
    """
    Procura pela macro draw.io no HTML da página
    """

    pattern = r'<ac:structured-macro ac:name="drawio".*?</ac:structured-macro>'
    match = re.search(pattern, page_html, re.DOTALL)

    if not match:
        raise Exception("Macro draw.io não encontrada")

    macro = match.group(0)

    # procura conteúdo base64
    data_pattern = r"<ac:plain-text-body><!\[CDATA\[(.*?)\]\]></ac:plain-text-body>"
    data_match = re.search(data_pattern, macro, re.DOTALL)

    if not data_match:
        raise Exception("Conteúdo do draw.io não encontrado")

    encoded = data_match.group(1)

    decoded = base64.b64decode(encoded)

    return decoded.decode("utf-8")


# ===============================
# EXTRAIR TEXTO DO DIAGRAMA
# ===============================

def extract_text_from_drawio(xml_content: str) -> List[str]:

    root = ET.fromstring(xml_content)

    texts = []

    for elem in root.iter():
        value = elem.attrib.get("value")

        if value:
            clean = re.sub("<.*?>", "", value)
            texts.append(clean.strip())

    return texts


# ===============================
# NORMALIZAÇÃO DOS TEXTOS
# ===============================

def normalize_texts(texts: List[str]) -> List[Tuple[str, ...]]:
    """
    Divide textos usando
    =
    ,
    espaço
    """

    normalized = []

    for text in texts:

        parts = re.split(r"[=,\s]+", text)

        parts = [p.strip() for p in parts if p.strip()]

        if parts:
            normalized.append(tuple(parts))

    return normalized


# ===============================
# COLETA OSKB (IMPLEMENTAR)
# ===============================

def get_oskb_data() -> List[Tuple[str, ...]]:
    """
    IMPLEMENTAR AQUI

    Esta função deve retornar algo como:

    [
        ("service", "user"),
        ("api", "gateway"),
        ...
    ]
    """

    raise NotImplementedError("Implementar coleta do OSKB aqui")


# ===============================
# COMPARAÇÃO
# ===============================

def compare_lists(list_a, list_b):

    set_a = set(list_a)
    set_b = set(list_b)

    only_a = set_a - set_b
    only_b = set_b - set_a

    all_match = len(only_a) == 0 and len(only_b) == 0

    return {
        "count_a": len(set_a),
        "count_b": len(set_b),
        "only_a": sorted(list(only_a)),
        "only_b": sorted(list(only_b)),
        "all_match": all_match
    }


# ===============================
# MARKDOWN REPORT
# ===============================

def generate_markdown(result, path):

    lines = []

    lines.append("# System Metaphor vs OSKB\n")

    lines.append("## Summary\n")

    lines.append(f"- System Metaphor items: **{result['count_a']}**")
    lines.append(f"- OSKB items: **{result['count_b']}**")

    if result["all_match"]:
        lines.append("\n✅ **All items match between lists**\n")
    else:
        lines.append("\n❌ **Differences found between lists**\n")

    lines.append("\n---\n")

    lines.append("## Items only in System Metaphor\n")

    if result["only_a"]:
        for item in result["only_a"]:
            lines.append(f"- {item}")
    else:
        lines.append("None")

    lines.append("\n---\n")

    lines.append("## Items only in OSKB\n")

    if result["only_b"]:
        for item in result["only_b"]:
            lines.append(f"- {item}")
    else:
        lines.append("None")

    Path(path).write_text("\n".join(lines))

    print(f"Report saved to {path}")


# ===============================
# MAIN
# ===============================

def main():

    print("Downloading Confluence page...")

    html = get_confluence_page_content()

    print("Extracting Draw.io XML...")

    xml = extract_drawio_xml(html)

    print("Extracting diagram texts...")

    texts = extract_text_from_drawio(xml)

    print("Normalizing System Metaphor list...")

    system_metaphor = normalize_texts(texts)

    print("Collecting OSKB data...")

    oskb = get_oskb_data()

    print("Comparing lists...")

    result = compare_lists(system_metaphor, oskb)

    print("Generating report...")

    generate_markdown(result, OUTPUT_MD)


if __name__ == "__main__":
    main()