"""
Utilidades para parseo y renderizado seguro de Markdown a HTML para mensajes de chat y descripciones.
"""

import re
from markupsafe import Markup, escape


def render_markdown(text: str) -> Markup:
    """
    Convierte texto con sintaxis Markdown común a HTML limpio y seguro.
    Soporta:
    - Bloques de código (```lenguaje ... ```)
    - Código en línea (`codigo`)
    - Negritas (**texto** o __texto__)
    - Cursivas (*texto* o _texto_)
    - Encabezados (#, ##, ###)
    - Listas numeradas y no numeradas
    - Citas / Blockquotes (> texto)
    - Enlaces ([texto](url))
    - Saltos de línea
    """
    if not text:
        return Markup("")

    text_str = str(text)

    # 1. Extraer bloques de código para evitar que el formateo interno altere su contenido
    code_blocks = []

    def save_code_block(match):
        lang = match.group(1).strip() if match.group(1) else ""
        code_content = match.group(2)
        idx = len(code_blocks)
        escaped_code = str(escape(code_content.rstrip()))
        code_blocks.append((lang, escaped_code))
        return f"__CODE_BLOCK_{idx}__"

    # Regex para bloques ```lang\ncode```
    text_processed = re.sub(r"```([a-zA-Z0-9_-]*)\n?([\s\S]*?)```", save_code_block, text_str)

    # 2. Extraer código inline (`code`)
    inline_codes = []

    def save_inline_code(match):
        code_content = match.group(1)
        idx = len(inline_codes)
        inline_codes.append(str(escape(code_content)))
        return f"__INLINE_CODE_{idx}__"

    text_processed = re.sub(r"`([^`\n]+)`", save_inline_code, text_processed)

    # 3. Escapar el resto del texto HTML para evitar XSS
    text_escaped = str(escape(text_processed))

    # 4. Enlaces [texto](url seguro)
    def format_link(match):
        label = match.group(1)
        url = match.group(2).strip()
        if url.startswith(("http://", "https://", "mailto:", "/")):
            return f'<a href="{url}" target="_blank" rel="noopener noreferrer" class="chat-link">{label}</a>'
        return match.group(0)

    text_escaped = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", format_link, text_escaped)

    # 5. Encabezados (###, ##, #)
    lines = text_escaped.split("\n")
    formatted_lines = []
    in_ul = False
    in_ol = False

    for line in lines:
        stripped = line.strip()

        # Encabezados
        if stripped.startswith("### "):
            line = f'<h5 class="markdown-heading-3">{stripped[4:]}</h5>'
        elif stripped.startswith("## "):
            line = f'<h4 class="markdown-heading-2">{stripped[3:]}</h4>'
        elif stripped.startswith("# "):
            line = f'<h3 class="markdown-heading-1">{stripped[2:]}</h3>'

        # Citas (Blockquotes)
        elif stripped.startswith("&gt; ") or stripped.startswith("> "):
            quote_text = stripped[5:] if stripped.startswith("&gt; ") else stripped[2:]
            line = f'<blockquote class="markdown-quote">{quote_text}</blockquote>'

        # Listas desordenadas (- o * o •)
        elif re.match(r"^[-*•]\s+(.*)$", stripped):
            item_text = re.sub(r"^[-*•]\s+", "", stripped)
            if not in_ul:
                formatted_lines.append('<ul class="markdown-list">')
                in_ul = True
            formatted_lines.append(f"<li>{item_text}</li>")
            continue

        # Listas ordenadas (1. 2. 3.)
        elif re.match(r"^\d+\.\s+(.*)$", stripped):
            item_text = re.sub(r"^\d+\.\s+", "", stripped)
            if not in_ol:
                formatted_lines.append('<ol class="markdown-list">')
                in_ol = True
            formatted_lines.append(f"<li>{item_text}</li>")
            continue

        else:
            if in_ul:
                formatted_lines.append("</ul>")
                in_ul = False
            if in_ol:
                formatted_lines.append("</ol>")
                in_ol = False

        formatted_lines.append(line)

    if in_ul:
        formatted_lines.append("</ul>")
    if in_ol:
        formatted_lines.append("</ol>")

    res = "\n".join(formatted_lines)

    # 6. Negrita (**texto** o __texto__)
    res = re.sub(r"\*\*([^\*]+)\*\*", r"<strong>\1</strong>", res)
    res = re.sub(r"__([^_]+)__", r"<strong>\1</strong>", res)

    # 7. Cursiva (*texto* o _texto_)
    res = re.sub(r"(?<!\*)\*([^\*\n]+)\*(?!\*)", r"<em>\1</em>", res)
    res = re.sub(r"(?<!_)_([^_\n]+)_(?!_)", r"<em>\1</em>", res)

    # 8. Tachado (~~texto~~)
    res = re.sub(r"~~([^~]+)~~", r"<del>\1</del>", res)

    # 9. Restaurar código inline
    for idx, incode in enumerate(inline_codes):
        res = res.replace(f"__INLINE_CODE_{idx}__", f'<code class="inline-code">{incode}</code>')

    # 10. Restaurar bloques de código con cabecera y botón de copiar
    for idx, (lang, ccode) in enumerate(code_blocks):
        lang_label = lang if lang else "código"
        block_html = (
            f'<div class="code-block-wrapper">'
            f'<div class="code-block-header">'
            f'<span class="code-lang-tag">{lang_label}</span>'
            f'<button type="button" class="btn-copy-code" onclick="copyCodeSnippet(this)" title="Copiar código">Copiar</button>'
            f'</div>'
            f'<pre class="code-block"><code>{ccode}</code></pre>'
            f'</div>'
        )
        res = res.replace(f"__CODE_BLOCK_{idx}__", block_html)

    # 11. Línea horizontal (---)
    res = re.sub(r"^---+$", r'<hr class="markdown-hr">', res, flags=re.MULTILINE)

    # 12. Convertir saltos de línea normales fuera de listas / bloques en <br>
    # pero preservando espaciado limpio
    res = res.replace("\n", "<br>")
    # Limpiar <br> innecesarios después de elementos de bloque
    res = re.sub(r"(</div>|</pre>|</h3>|</h4>|</h5>|</blockquote>|</ul>|</ol>|<hr[^>]*>)<br>", r"\1", res)
    res = re.sub(r"<br>(<div|<h3|<h4|<h5|<blockquote|<ul|<ol|<hr)", r"\1", res)

    return Markup(res)
