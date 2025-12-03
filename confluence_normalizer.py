from bs4 import BeautifulSoup

def clean_confluence_html(raw):
    soup = BeautifulSoup(raw, "lxml-xml")

    # Remove macros que são só wrappers
    for tag in soup.find_all(["ac:structured-macro", "ac:parameter", "ac:link", "ri:attachment"]):
        tag.unwrap()

    # Agora converte tudo para HTML normal
    html = soup.get_text("\n", strip=False)
    return html

def normalize_macros(raw):
    soup = BeautifulSoup(raw, "lxml-xml")

    # Panel
    for panel in soup.find_all("ac:structured-macro", {"ac:name": "panel"}):
        title = panel.find("ac:parameter", {"ac:name": "title"})
        body = panel.find("ac:rich-text-body")
        text = f"\n=== PANEL: {title.text if title else ''} ===\n{body.get_text()}\n"
        panel.replace_with(text)

    # Expand
    for exp in soup.find_all("ac:structured-macro", {"ac:name": "expand"}):
        title = exp.find("ac:parameter", {"ac:name": "title"})
        body = exp.find("ac:rich-text-body")
        text = f"\n> EXPAND SECTION: {title.text}\n{body.get_text()}\n"
        exp.replace_with(text)

    # Status
    for st in soup.find_all("ac:structured-macro", {"ac:name": "status"}):
        color = st.get("ac:parameter", "colour") if st else ""
        txt = st.text.strip()
        st.replace_with(f"[STATUS: {txt} - {color}]")

    return str(soup)

def convert_tables_to_markdown(html):
    soup = BeautifulSoup(html, "html.parser")

    for table in soup.find_all("table"):
        md = []
        rows = table.find_all("tr")

        for i, tr in enumerate(rows):
            cols = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
            md.append("| " + " | ".join(cols) + " |")

            if i == 0:
                md.append("| " + " | ".join(["---"] * len(cols)) + " |")

        table.replace_with("\n".join(md))

    return str(soup)
