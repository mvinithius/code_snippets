## “””
confluence_drawio_comparator.py

Script para:

1. Baixar o conteúdo da macro Draw.io do Confluence Data Center via Bearer Token
1. Extrair texto do diagrama e transformar em lista de strings/tuplas
1. Coletar dados do sistema OSKB (função a ser implementada)
1. Comparar as duas listas (System Metaphor vs OSKB)
1. Salvar resultado em arquivo Markdown formatado

Dependências:
pip install requests lxml
“””

import re
import sys
import json
import zlib
import base64
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import unquote, quote
from typing import Union

# =============================================================================

# CONFIGURAÇÕES — preencha antes de executar

# =============================================================================

CONFLUENCE_BASE_URL = “https://seu-confluence.empresa.com”   # Ex: https://confluence.empresa.com
BEARER_TOKEN        = “SEU_BEARER_TOKEN_AQUI”
PAGE_ID             = “123456789”                             # ID da página Confluence que contém o Draw.io
OUTPUT_FILE         = “comparacao_system_metaphor_vs_oskb.md”

# =============================================================================

# SEÇÃO 1 — Download e extração do Draw.io

# =============================================================================

def get_confluence_page_content(page_id: str) -> dict:
“””
Busca o conteúdo storage-format de uma página Confluence via REST API v1.
Retorna o JSON completo da resposta.
“””
url = f”{CONFLUENCE_BASE_URL}/rest/api/content/{page_id}?expand=body.storage”
headers = {
“Authorization”: f”Bearer {BEARER_TOKEN}”,
“Accept”: “application/json”,
}
response = requests.get(url, headers=headers, timeout=30)
response.raise_for_status()
return response.json()

def extract_drawio_xml_from_page(page_json: dict) -> str:
“””
Localiza a macro Draw.io dentro do storage-format HTML da página
e retorna o conteúdo XML/JSON bruto do diagrama.
“””
storage_body = page_json[“body”][“storage”][“value”]

```
# A macro Draw.io armazena o diagrama dentro de:
# <ac:structured-macro ac:name="drawio">
#   <ac:parameter ac:name="diagramXml">...</ac:parameter>
# </ac:structured-macro>
# OU via attachment referenciada. Aqui tratamos o caso inline (diagramXml).

# Precisamos de um wrapper para parsing XML válido
wrapped = f"<root>{storage_body}</root>"
# Remove namespaces problemáticos para simplificar o parsing
wrapped = re.sub(r' xmlns[^"]*"[^"]*"', '', wrapped)

try:
    root = ET.fromstring(wrapped)
except ET.ParseError as e:
    raise ValueError(f"Erro ao parsear o storage-format da página: {e}")

# Procura pela macro drawio
for macro in root.iter("structured-macro"):
    name_attr = macro.get("name", "")
    if name_attr.lower() in ("drawio", "draw.io"):
        for param in macro.iter("parameter"):
            if param.get("name", "").lower() == "diagramxml":
                return param.text or ""
        # Caso o diagrama esteja como attachment, retorna aviso
        raise ValueError(
            "Macro Draw.io encontrada, mas usa attachment. "
            "Implemente get_drawio_from_attachment() para esse caso."
        )

raise ValueError("Nenhuma macro Draw.io encontrada na página informada.")
```

def decode_drawio_xml(raw: str) -> str:
“””
O Draw.io pode armazenar o XML como:
- XML puro
- Base64(Deflate(encodeURIComponent(XML)))  ← formato compactado padrão
Detecta automaticamente e retorna o XML descomprimido.
“””
raw = raw.strip()

```
# Se começa com '<', já é XML puro
if raw.startswith("<"):
    return raw

# Tenta decodificar Base64 + Deflate + URL-decode
try:
    b64_decoded = base64.b64decode(raw)
    deflated    = zlib.decompress(b64_decoded, wbits=-15)   # raw deflate
    url_decoded = unquote(deflated.decode("utf-8"))
    return url_decoded
except Exception:
    pass

# Tenta só Base64 sem deflate
try:
    b64_decoded = base64.b64decode(raw)
    return b64_decoded.decode("utf-8")
except Exception:
    pass

# Devolve como está e deixa o parser tentar
return raw
```

def extract_text_from_drawio_xml(xml_string: str) -> list[Union[str, tuple]]:
“””
Percorre todos os elementos <mxCell> do XML do Draw.io,
coleta o atributo ‘value’ (texto visível no diagrama) e
retorna uma lista de strings ou tuplas de strings.

```
Regras de divisão:
  - Remove tags HTML internas (Draw.io usa <br>, <b>, etc.)
  - Divide pelo sinal '=' → tupla ("chave", "valor")
  - Divide por ',' → tupla de múltiplos valores
  - Strings simples ficam como str
"""
try:
    root = ET.fromstring(xml_string)
except ET.ParseError as e:
    raise ValueError(f"Erro ao parsear o XML do Draw.io: {e}")

result: list[Union[str, tuple]] = []
seen: set = set()

# Suporte tanto a <mxGraphModel> plano quanto a <root> aninhado
cells = root.iter("mxCell")

for cell in cells:
    value = cell.get("value", "").strip()
    if not value:
        continue

    # Remove tags HTML internas
    value = re.sub(r"<[^>]+>", " ", value).strip()
    value = re.sub(r"\s+", " ", value)

    if not value or value in seen:
        continue
    seen.add(value)

    parsed = _parse_cell_value(value)
    result.append(parsed)

return result
```

def _parse_cell_value(value: str) -> Union[str, tuple]:
“””
Divide uma string de célula Draw.io em tupla, se aplicável.
Prioridade: ‘=’ > ‘,’
“””
# Divisão por ‘=’
if “=” in value:
parts = [p.strip() for p in value.split(”=”, 1)]
if all(parts):
return tuple(parts)

```
# Divisão por ','
if "," in value:
    parts = [p.strip() for p in value.split(",")]
    parts = [p for p in parts if p]
    if len(parts) > 1:
        return tuple(parts)

return value
```

# =============================================================================

# SEÇÃO 2 — Coleta do sistema OSKB  ← IMPLEMENTE AQUI

# =============================================================================

def get_oskb_data() -> list[Union[str, tuple]]:
“””
TODO: Implemente esta função para coletar os dados do sistema OSKB.

```
Diretrizes:
  - Retorne uma lista de strings ou tuplas de strings, no mesmo formato
    que extract_text_from_drawio_xml() retorna para o Draw.io.
  - Exemplos de retorno esperado:
        ["ITEM_A", "ITEM_B", ("chave", "valor"), ("a", "b", "c")]
  - Substitua o `raise NotImplementedError` abaixo pela sua implementação.

Exemplo de esqueleto para uma API REST:
    url = "https://oskb.empresa.com/api/items"
    headers = {"Authorization": "Bearer SEU_TOKEN_OSKB"}
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    data = response.json()
    # ... transforme data em lista de strings/tuplas e retorne

Exemplo de esqueleto para banco de dados:
    import psycopg2
    conn = psycopg2.connect("host=... dbname=... user=... password=...")
    cur  = conn.cursor()
    cur.execute("SELECT campo1, campo2 FROM tabela_oskb")
    rows = cur.fetchall()
    return [tuple(str(c) for c in row) if len(row) > 1 else str(row[0])
            for row in rows]
"""
raise NotImplementedError(
    "A função get_oskb_data() ainda não foi implementada. "
    "Preencha-a na SEÇÃO 2 deste script."
)
```

# =============================================================================

# SEÇÃO 3 — Normalização e comparação

# =============================================================================

def normalize_item(item: Union[str, tuple]) -> str:
“””
Converte qualquer item (str ou tuple) em uma string normalizada
para comparação case-insensitive sem espaços extras.
“””
if isinstance(item, tuple):
return “ | “.join(str(p).strip().lower() for p in item)
return str(item).strip().lower()

def item_to_display(item: Union[str, tuple]) -> str:
“”“Representação legível de um item para o relatório.”””
if isinstance(item, tuple):
return “ | “.join(str(p).strip() for p in item)
return str(item).strip()

def compare_lists(
list_a: list,
list_b: list,
name_a: str = “System Metaphor”,
name_b: str = “OSKB”,
) -> dict:
“””
Compara duas listas e retorna um dicionário com:
- total em cada lista
- itens presentes em ambas
- itens apenas em A
- itens apenas em B
- flag de igualdade total
“””
norm_a = {normalize_item(i): item_to_display(i) for i in list_a}
norm_b = {normalize_item(i): item_to_display(i) for i in list_b}

```
keys_a = set(norm_a.keys())
keys_b = set(norm_b.keys())

in_both     = keys_a & keys_b
only_in_a   = keys_a - keys_b
only_in_b   = keys_b - keys_a

return {
    "name_a": name_a,
    "name_b": name_b,
    "total_a": len(list_a),
    "total_b": len(list_b),
    "in_both":   sorted(norm_a[k] for k in in_both),
    "only_in_a": sorted(norm_a[k] for k in only_in_a),
    "only_in_b": sorted(norm_b[k] for k in only_in_b),
    "all_match": len(only_in_a) == 0 and len(only_in_b) == 0,
}
```

# =============================================================================

# SEÇÃO 4 — Geração do relatório Markdown

# =============================================================================

def build_markdown_report(result: dict, list_a: list, list_b: list) -> str:
“”“Gera o conteúdo do arquivo Markdown com o resultado da comparação.”””
now    = datetime.now().strftime(”%d/%m/%Y %H:%M:%S”)
name_a = result[“name_a”]
name_b = result[“name_b”]

```
lines = []

# Cabeçalho
lines += [
    f"# Comparação: {name_a} vs {name_b}",
    "",
    f"> Gerado em: {now}",
    "",
    "---",
    "",
]

# Resumo executivo
status_emoji = "✅" if result["all_match"] else "⚠️"
status_text  = (
    "**Todas as strings estão presentes em ambas as listas.**"
    if result["all_match"]
    else "**Nem todas as strings estão presentes em ambas as listas.**"
)

lines += [
    "## Resumo Executivo",
    "",
    f"{status_emoji} {status_text}",
    "",
    "| Métrica | Valor |",
    "|---------|-------|",
    f"| Total de itens em **{name_a}** | {result['total_a']} |",
    f"| Total de itens em **{name_b}** | {result['total_b']} |",
    f"| Itens em **ambas** as listas | {len(result['in_both'])} |",
    f"| Itens **apenas** em {name_a} | {len(result['only_in_a'])} |",
    f"| Itens **apenas** em {name_b} | {len(result['only_in_b'])} |",
    "",
    "---",
    "",
]

# Itens em comum
lines += [
    f"## ✅ Itens presentes em ambas as listas ({len(result['in_both'])})",
    "",
]
if result["in_both"]:
    for item in result["in_both"]:
        lines.append(f"- {item}")
else:
    lines.append("_Nenhum item em comum._")
lines.append("")
lines.append("---")
lines.append("")

# Apenas em A
lines += [
    f"## 🔴 Itens presentes **apenas** em {name_a} ({len(result['only_in_a'])})",
    "",
    f"> Estes itens existem no **{name_a}** mas **não** foram encontrados no **{name_b}**.",
    "",
]
if result["only_in_a"]:
    for item in result["only_in_a"]:
        lines.append(f"- {item}")
else:
    lines.append(f"_Todos os itens de {name_a} estão presentes em {name_b}._")
lines.append("")
lines.append("---")
lines.append("")

# Apenas em B
lines += [
    f"## 🔵 Itens presentes **apenas** em {name_b} ({len(result['only_in_b'])})",
    "",
    f"> Estes itens existem no **{name_b}** mas **não** foram encontrados no **{name_a}**.",
    "",
]
if result["only_in_b"]:
    for item in result["only_in_b"]:
        lines.append(f"- {item}")
else:
    lines.append(f"_Todos os itens de {name_b} estão presentes em {name_a}._")
lines.append("")
lines.append("---")
lines.append("")

# Listas completas
lines += [
    "## 📋 Listas completas",
    "",
    f"### {name_a} ({result['total_a']} itens)",
    "",
]
for item in list_a:
    lines.append(f"- {item_to_display(item)}")
lines.append("")

lines += [
    f"### {name_b} ({result['total_b']} itens)",
    "",
]
for item in list_b:
    lines.append(f"- {item_to_display(item)}")
lines.append("")

return "\n".join(lines)
```

def save_markdown(content: str, filepath: str) -> None:
with open(filepath, “w”, encoding=“utf-8”) as f:
f.write(content)
print(f”[✓] Relatório salvo em: {filepath}”)

# =============================================================================

# SEÇÃO 5 — Orquestração principal

# =============================================================================

def main():
print(”=” * 60)
print(”  Confluence Draw.io → OSKB Comparator”)
print(”=” * 60)

```
# --- 1. Baixa página do Confluence ---
print(f"\n[1/5] Buscando página {PAGE_ID} no Confluence...")
try:
    page_json = get_confluence_page_content(PAGE_ID)
    print(f"      Página: {page_json.get('title', 'sem título')}")
except requests.HTTPError as e:
    print(f"[ERRO] Falha ao acessar o Confluence: {e}")
    sys.exit(1)

# --- 2. Extrai XML do Draw.io ---
print("[2/5] Extraindo macro Draw.io...")
try:
    raw_drawio   = extract_drawio_xml_from_page(page_json)
    drawio_xml   = decode_drawio_xml(raw_drawio)
except ValueError as e:
    print(f"[ERRO] {e}")
    sys.exit(1)

# --- 3. Extrai texto do diagrama → System Metaphor ---
print("[3/5] Extraindo texto do diagrama...")
system_metaphor: list = extract_text_from_drawio_xml(drawio_xml)
print(f"      {len(system_metaphor)} itens encontrados no System Metaphor.")

# --- 4. Coleta dados do OSKB ---
print("[4/5] Coletando dados do OSKB...")
try:
    oskb: list = get_oskb_data()
    print(f"      {len(oskb)} itens encontrados no OSKB.")
except NotImplementedError as e:
    print(f"[AVISO] {e}")
    print("        Usando lista OSKB vazia para demonstração.")
    oskb = []

# --- 5. Compara e gera relatório ---
print("[5/5] Comparando listas e gerando relatório Markdown...")
result   = compare_lists(system_metaphor, oskb, "System Metaphor", "OSKB")
markdown = build_markdown_report(result, system_metaphor, oskb)
save_markdown(markdown, OUTPUT_FILE)

# Resumo no terminal
print()
print("─" * 40)
if result["all_match"]:
    print("✅  Todas as strings estão em ambas as listas!")
else:
    print("⚠️   As listas diferem:")
    print(f"    • Apenas em System Metaphor : {len(result['only_in_a'])} item(s)")
    print(f"    • Apenas em OSKB            : {len(result['only_in_b'])} item(s)")
    print(f"    • Em comum                  : {len(result['in_both'])} item(s)")
print("─" * 40)
```

if **name** == “**main**”:
main()