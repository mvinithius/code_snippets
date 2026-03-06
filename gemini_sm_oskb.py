import requests
import zlib
import base64
import urllib.parse
from bs4 import BeautifulSoup
import re

# --- CONFIGURAÇÕES DO CONFLUENCE ---
CONFLUENCE_URL = "https://seu-dominio.atlassian.net/wiki" # Mude para sua URL do Data Center
PAGE_ID = "12345678"
BEARER_TOKEN = "SEU_TOKEN_AQUI"

HEADERS = {
    "Authorization": f"Bearer {BEARER_TOKEN}",
    "Content-Type": "application/json"
}

def get_oskb_data():
    """
    ESPAÇO RESERVADO: Implemente aqui a conexão com seu outro sistema.
    O retorno deve ser uma lista de tuplas de strings.
    Exemplo: [("Item1", "Valor1"), ("Item2", "Valor2")]
    """
    # Exemplo de mock para teste:
    # return [("Server", "Production"), ("Database", "Main")]
    return []

def extract_drawio_xml(page_id):
    """Baixa o conteúdo da página e extrai o XML da macro Draw.io."""
    url = f"{CONFLUENCE_URL}/rest/api/content/{page_id}?expand=body.storage"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    
    storage_view = response.json()['body']['storage']['value']
    soup = BeautifulSoup(storage_view, 'html.parser')
    
    # Procura pela macro do drawio
    drawio_macro = soup.find('ac:structured-macro', attrs={'ac:name': 'drawio'})
    if not drawio_macro:
        print("Macro Draw.io não encontrada na página.")
        return None

    # O conteúdo do diagrama costuma estar em um parâmetro chamado 'diagramData' ou anexo
    # Em muitas versões, o texto está codificado dentro da tag
    data_param = drawio_macro.find('ac:plain-text-parameter', attrs={'ac:name': 'diagramData'})
    if data_param:
        return data_param.text
    return None

def parse_drawio_text(xml_data):
    """Descomprime o XML do Draw.io e extrai os textos das células."""
    # O Draw.io geralmente usa compressão zlib + base64 + URL encode
    try:
        decoded = base64.b64decode(xml_data)
        decompressed = zlib.decompress(decoded, -15)
        xml_content = urllib.parse.unquote(decompressed.decode('utf-8'))
    except:
        xml_content = xml_data # Caso já venha como XML puro

    soup = BeautifulSoup(xml_content, 'xml')
    # Células de texto no Draw.io ficam em atributos 'value' de tags mxCell
    cells = soup.find_all('mxCell')
    
    extracted_strings = []
    for cell in cells:
        val = cell.get('value')
        if val:
            # Limpa tags HTML que o Draw.io insere (como <div>, <b>)
            clean_text = re.sub('<[^<]+?>', '', val).strip()
            if clean_text:
                # Lógica de split por =, virgula ou espaços conforme solicitado
                # Transforma em tupla se houver separadores
                if any(sep in clean_text for sep in ['=', ',']):
                    parts = re.split(r'[=,]', clean_text)
                    extracted_strings.append(tuple(p.strip() for p in parts if p.strip()))
                else:
                    extracted_strings.append(clean_text)
    
    return extracted_strings

def compare_lists(list_a, list_b):
    set_a = set(list_a)
    set_b = set(list_b)
    
    only_in_a = set_a - set_b
    only_in_b = set_b - set_a
    intersection = set_a & set_b
    
    return {
        "all_match": set_a == set_b,
        "only_in_system_metaphor": list(only_in_a),
        "only_in_oskb": list(only_in_b),
        "count_a": len(list_a),
        "count_b": len(list_b)
    }

def save_to_markdown(results, filename="comparison_result.md"):
    with open(filename, "w", encoding="utf-8") as f:
        f.write("# Relatório de Comparação de Dados\n\n")
        f.write(f"**Status de Sincronização:** {'✅ Totalmente Alinhado' if results['all_match'] else '❌ Divergências Encontradas'}\n\n")
        
        f.write("### Resumo de Quantidades\n")
        f.write(f"- **System Metaphor (Draw.io):** {results['count_a']} itens\n")
        f.write(f"- **OSKB (Sistema Externo):** {results['count_b']} itens\n\n")
        
        f.write("--- \n\n")
        
        f.write("### 🚩 Itens exclusivos: System Metaphor\n")
        if results['only_in_system_metaphor']:
            for item in results['only_in_system_metaphor']: f.write(f"- {item}\n")
        else: f.write("_Nenhum item exclusivo._\n")
            
        f.write("\n### 🚩 Itens exclusivos: OSKB\n")
        if results['only_in_oskb']:
            for item in results['only_in_oskb']: f.write(f"- {item}\n")
        else: f.write("_Nenhum item exclusivo._\n")

if __name__ == "__main__":
    print("Iniciando extração...")
    
    # 1. Coleta do Confluence (System Metaphor)
    raw_xml = extract_drawio_xml(PAGE_ID)
    if raw_xml:
        system_metaphor = parse_drawio_text(raw_xml)
        
        # 2. Coleta do Sistema Externo (OSKB)
        oskb = get_oskb_data()
        
        # 3. Comparação
        comparison = compare_lists(system_metaphor, oskb)
        
        # 4. Salvar Resultado
        save_to_markdown(comparison)
        print("Processo concluído. Resultado salvo em comparison_result.md")
    else:
        print("Falha ao obter dados do Confluence.")
