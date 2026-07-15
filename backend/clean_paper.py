"""
论文 Markdown 全面清理脚本
解决：$符号、\{ \}、\dots、d_{ij}、c_k^0 等未渲染乱码
输出：干净的论文 Markdown + DOCX
"""
import re
import sys
from pathlib import Path

# ============================================================
# Unicode 下标/上标映射
# ============================================================
SUBSCRIPT_DIGITS = str.maketrans('0123456789', '₀₁₂₃₄₅₆₇₈₉')
SUPERSCRIPT_DIGITS = str.maketrans('0123456789', '⁰¹²³⁴⁵⁶⁷⁸⁹')

# Unicode 下标字母（仅支持部分常用字母）
SUBSCRIPT_CHARS = {
    'a': 'ₐ', 'e': 'ₑ', 'h': 'ₕ', 'i': 'ᵢ', 'j': 'ⱼ', 'k': 'ₖ',
    'l': 'ₗ', 'm': 'ₘ', 'n': 'ₙ', 'o': 'ₒ', 'p': 'ₚ', 'r': 'ᵣ',
    's': 'ₛ', 't': 'ₜ', 'u': 'ᵤ', 'v': 'ᵥ', 'x': 'ₓ',
    # 大写
    'A': 'ₐ', 'E': 'ₑ', 'H': 'ₕ', 'I': 'ᵢ', 'J': 'ⱼ', 'K': 'ₖ',
    'L': 'ₗ', 'M': 'ₘ', 'N': 'ₙ', 'O': 'ₒ', 'P': 'ₚ', 'R': 'ᵣ',
    'S': 'ₛ', 'T': 'ₜ', 'U': 'ᵤ', 'V': 'ᵥ', 'X': 'ₓ',
}

# Unicode 上标字母
SUPERSCRIPT_CHARS = {
    'a': 'ᵃ', 'b': 'ᵇ', 'c': 'ᶜ', 'd': 'ᵈ', 'e': 'ᵉ', 'f': 'ᶠ',
    'g': 'ᵍ', 'h': 'ʰ', 'i': 'ⁱ', 'j': 'ʲ', 'k': 'ᵏ', 'l': 'ˡ',
    'm': 'ᵐ', 'n': 'ⁿ', 'o': 'ᵒ', 'p': 'ᵖ', 'r': 'ʳ', 's': 'ˢ',
    't': 'ᵗ', 'u': 'ᵘ', 'v': 'ᵛ', 'w': 'ʷ', 'x': 'ˣ', 'y': 'ʸ', 'z': 'ᶻ',
    # 大写
    'A': 'ᴬ', 'B': 'ᴮ', 'D': 'ᴰ', 'E': 'ᴱ', 'G': 'ᴳ', 'H': 'ᴴ',
    'I': 'ᴵ', 'J': 'ᴶ', 'K': 'ᴷ', 'L': 'ᴸ', 'M': 'ᴹ', 'N': 'ᴺ',
    'O': 'ᴼ', 'P': 'ᴾ', 'R': 'ᴿ', 'T': 'ᵀ', 'U': 'ᵁ', 'V': 'ⱽ', 'W': 'ᵂ',
    '+': '⁺', '-': '⁻', '=': '⁼', '(': '⁽', ')': '⁾',
}

# LaTeX 命令 → 可读文本
LATEX_COMMANDS = {
    r'\dots': '…',
    r'\ldots': '…',
    r'\cdots': '⋯',
    r'\cdot': '·',
    r'\times': '×',
    r'\pm': '±',
    r'\mp': '∓',
    r'\div': '÷',
    r'\leq': '≤',
    r'\le': '≤',
    r'\geq': '≥',
    r'\ge': '≥',
    r'\neq': '≠',
    r'\approx': '≈',
    r'\equiv': '≡',
    r'\in': '∈',
    r'\notin': '∉',
    r'\forall': '∀',
    r'\exists': '∃',
    r'\infty': '∞',
    r'\to': '→',
    r'\rightarrow': '→',
    r'\Rightarrow': '⇒',
    r'\leftarrow': '←',
    r'\Leftarrow': '⇐',
    r'\mapsto': '↦',
    r'\cup': '∪',
    r'\cap': '∩',
    r'\subseteq': '⊆',
    r'\supseteq': '⊇',
    r'\subset': '⊂',
    r'\supset': '⊃',
    r'\emptyset': '∅',
    r'\partial': '∂',
    r'\nabla': '∇',
    r'\sum': '∑',
    r'\prod': '∏',
    r'\int': '∫',
    r'\alpha': 'α',
    r'\beta': 'β',
    r'\gamma': 'γ',
    r'\delta': 'δ',
    r'\epsilon': 'ε',
    r'\varepsilon': 'ε',
    r'\zeta': 'ζ',
    r'\eta': 'η',
    r'\theta': 'θ',
    r'\vartheta': 'ϑ',
    r'\iota': 'ι',
    r'\kappa': 'κ',
    r'\lambda': 'λ',
    r'\mu': 'μ',
    r'\nu': 'ν',
    r'\xi': 'ξ',
    r'\pi': 'π',
    r'\rho': 'ρ',
    r'\varrho': 'ϱ',
    r'\sigma': 'σ',
    r'\tau': 'τ',
    r'\upsilon': 'υ',
    r'\phi': 'φ',
    r'\varphi': 'ϕ',
    r'\chi': 'χ',
    r'\psi': 'ψ',
    r'\omega': 'ω',
    r'\Gamma': 'Γ',
    r'\Delta': 'Δ',
    r'\Theta': 'Θ',
    r'\Lambda': 'Λ',
    r'\Pi': 'Π',
    r'\Sigma': 'Σ',
    r'\Omega': 'Ω',
    r'\Phi': 'Φ',
    # 定界符
    r'\{': '{',
    r'\}': '}',
    r'\lfloor': '⌊',
    r'\rfloor': '⌋',
    r'\lceil': '⌈',
    r'\rceil': '⌉',
    r'\langle': '⟨',
    r'\rangle': '⟩',
    # 空格
    r'\quad': '  ',
    r'\qquad': '    ',
    r'\,': ' ',
    r'\ ': ' ',
    # 函数名
    r'\max': 'max',
    r'\min': 'min',
    r'\arg\max': 'arg max',
    r'\arg\min': 'arg min',
    r'\log': 'log',
    r'\ln': 'ln',
    r'\exp': 'exp',
    r'\sin': 'sin',
    r'\cos': 'cos',
    r'\tan': 'tan',
    r'\gcd': 'gcd',
    r'\det': 'det',
    r'\lim': 'lim',
    r'\sup': 'sup',
    r'\inf': 'inf',
    # 文字
    r'\text': '',  # \text{...} handled specially
}


def _to_unicode_subscript(text: str) -> str:
    """将文本转为 Unicode 下标"""
    result = []
    for ch in text:
        if ch.isdigit():
            result.append(ch.translate(SUBSCRIPT_DIGITS))
        elif ch in SUBSCRIPT_CHARS:
            result.append(SUBSCRIPT_CHARS[ch])
        elif ch == ',':
            result.append('ꏜ')  # fallback comma
        elif ch == "'":
            result.append("'")
        else:
            result.append(ch)  # keep as-is
    return ''.join(result)


def _to_unicode_superscript(text: str) -> str:
    """将文本转为 Unicode 上标"""
    result = []
    for ch in text:
        if ch.isdigit():
            result.append(ch.translate(SUPERSCRIPT_DIGITS))
        elif ch in SUPERSCRIPT_CHARS:
            result.append(SUPERSCRIPT_CHARS[ch])
        elif ch == "'":
            result.append("'")
        else:
            result.append(ch)
    return ''.join(result)


def _convert_subscript(match):
    """处理 _{...} LaTeX 下标 → Unicode 下标（仅限≤2字符）或去花括号"""
    inner = match.group(1)
    # 只有 ≤2 个字母/数字才转 Unicode 下标，避免 "fuel"→"fᵤₑₗ"
    if (len(inner) <= 2 and re.match(r'^[a-zA-Z0-9]+$', inner)) or re.match(r'^[0-9]+$', inner):
        converted = _to_unicode_subscript(inner)
        # 如果所有字符都能转（转换后与原串不同），使用 Unicode；否则保留 _text
        if converted != inner or inner.isdigit():
            return converted
    # 单词或无法转换：去花括号，保留下划线
    return '_' + inner


def _convert_superscript(match):
    """处理 ^{...} LaTeX 上标 → Unicode 上标（仅限≤2字符）或去花括号"""
    inner = match.group(1)
    if (len(inner) <= 2 and re.match(r'^[a-zA-Z0-9]+$', inner)) or re.match(r'^[0-9]+$', inner):
        converted = _to_unicode_superscript(inner)
        if converted != inner or inner.isdigit():
            return converted
    return '^' + inner


def _convert_frac(match):
    """处理 \frac{a}{b}"""
    num = match.group(1)
    den = match.group(2)
    return f'({num})/({den})'


def _convert_text_command(match):
    """处理 \text{...}"""
    return match.group(1)


def clean_paper_markdown(md_text: str) -> str:
    """
    全面清理论文 Markdown，移除所有 LaTeX 标记

    Args:
        md_text: 原始 Markdown 论文文本

    Returns:
        清理后的 Markdown 文本
    """
    # ============================================================
    # Step 1: 保护代码块（```...```）不被修改
    # ============================================================
    code_blocks = []

    def _protect_code(match):
        code_blocks.append(match.group(0))
        return f'\x00CODE{len(code_blocks) - 1}\x00'

    md_text = re.sub(r'```[\s\S]*?```', _protect_code, md_text)

    # ============================================================
    # Step 2: 保护图片标记 ![alt](path)
    # ============================================================
    images = []

    def _protect_img(match):
        images.append(match.group(0))
        return f'\x00IMG{len(images) - 1}\x00'

    md_text = re.sub(r'!\[.*?\]\(.*?\)', _protect_img, md_text)

    # ============================================================
    # Step 3: 保护 Markdown 链接 [text](url)
    # ============================================================
    links = []

    def _protect_link(match):
        links.append(match.group(0))
        return f'\x00LINK{len(links) - 1}\x00'

    md_text = re.sub(r'\[([^\]]+)\]\([^)]+\)', _protect_link, md_text)

    # ============================================================
    # Step 4: 删除所有 $ 包裹符（行内和块级）
    # ============================================================
    # $$...$$ 块
    md_text = re.sub(r'\$\$\s*(.+?)\s*\$\$', r'\1', md_text, flags=re.DOTALL)
    # $...$ 行内
    md_text = re.sub(r'\$([^$]+?)\$', r'\1', md_text)

    # ============================================================
    # Step 5: LaTeX 命令 → 可读文本
    # ============================================================
    # \text{...} 特殊处理（先做）
    md_text = re.sub(r'\\text\{([^{}]+)\}', _convert_text_command, md_text)
    # \frac{a}{b} 特殊处理
    for _ in range(10):
        new_text = re.sub(
            r'\\frac\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}',
            _convert_frac, md_text
        )
        if new_text == md_text:
            break
        md_text = new_text
    # 其他 LaTeX 命令
    for cmd, repl in LATEX_COMMANDS.items():
        md_text = md_text.replace(cmd, repl)
    # \left, \right, \big, \Big 等 — 直接删除
    md_text = re.sub(r'\\left[(\[{]?', '', md_text)
    md_text = re.sub(r'\\right[)\]}]?', '', md_text)
    md_text = re.sub(r'\\[Bb]ig[lr]?', '', md_text)

    # ============================================================
    # Step 6: 下标/上标 → Unicode
    # ============================================================
    # _{...} → Unicode 下标或 _text
    md_text = re.sub(r'_\{([^{}]+)\}', _convert_subscript, md_text)
    # ^{...} → Unicode 上标或 ^text
    md_text = re.sub(r'\^\{([^{}]+)\}', _convert_superscript, md_text)
    # 🆕 裸单字母下标：变量名后面跟 _x → Unicode 下标（仅当x有对应下标字符）
    def _safe_sub_letter(m):
        ch = m.group(2)
        result = _to_unicode_subscript(ch)
        # 如果转换后和原字符不同（说明有 Unicode 下标形式），才去掉下划线
        if result != ch:
            return m.group(1) + result
        # 否则保留 _x 原样
        return m.group(0)
    md_text = re.sub(r'([a-zA-Z0-9])_([a-zA-Z])(?![a-zA-Z{])', _safe_sub_letter, md_text)
    # 🆕 裸单字符上标：变量名后面跟 ^x → Unicode 上标
    def _safe_sup_letter(m):
        ch = m.group(2)
        result = _to_unicode_superscript(ch)
        if result != ch:
            return m.group(1) + result
        return m.group(0)
    md_text = re.sub(r'([a-zA-Z0-9])\^([a-zA-Z0-9])(?![a-zA-Z{])', _safe_sup_letter, md_text)

    # ============================================================
    # Step 7: 清理标题 #### → ###
    # ============================================================
    md_text = re.sub(r'^#{4,6}\s+', '### ', md_text, flags=re.MULTILINE)

    # ============================================================
    # Step 7.5: 省略号统一 ... → …
    # ============================================================
    md_text = re.sub(r'(?<!\\)\.\.\.(?!\.)', '…', md_text)

    # ============================================================
    # Step 8: 恢复代码块、图片、链接
    # ============================================================
    for idx, block in enumerate(code_blocks):
        md_text = md_text.replace(f'\x00CODE{idx}\x00', block)
    for idx, img in enumerate(images):
        md_text = md_text.replace(f'\x00IMG{idx}\x00', img)
    for idx, link in enumerate(links):
        md_text = md_text.replace(f'\x00LINK{idx}\x00', link)

    # ============================================================
    # Step 9: 添加目录
    # ============================================================
    md_text = _add_toc(md_text)

    return md_text


def _add_toc(md_text: str) -> str:
    """在摘要之后添加目录"""
    # 在 "## 摘要" 段落后插入目录
    toc_lines = ['## 目录', '']
    # 扫描所有 ## 和 ### 标题
    for line in md_text.split('\n'):
        stripped = line.strip()
        if stripped.startswith('## ') and '目录' not in stripped:
            title = stripped[3:].strip()
            toc_lines.append(f'- {title}')
        elif stripped.startswith('### '):
            title = stripped[4:].strip()
            toc_lines.append(f'  - {title}')
    toc_text = '\n'.join(toc_lines)

    # 在摘要段落后插入目录（找到第一个 ## 后面的空行之后）
    # 查找 "## 摘要" 并在其之后的两个空行后插入
    abstract_match = re.search(r'##\s+摘要.*?\n\n', md_text, re.DOTALL)
    if abstract_match:
        insert_pos = abstract_match.end()
        md_text = md_text[:insert_pos] + toc_text + '\n\n' + md_text[insert_pos:]
    else:
        # 在第一个 ## 标题之前插入
        first_h2 = re.search(r'\n##\s', md_text)
        if first_h2:
            md_text = md_text[:first_h2.start() + 1] + toc_text + '\n\n' + md_text[first_h2.start() + 1:]

    return md_text


# ============================================================
# 主入口
# ============================================================
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python clean_paper.py <draft_paper.md>")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"File not found: {input_path}")
        sys.exit(1)

    md_text = input_path.read_text(encoding='utf-8')
    cleaned = clean_paper_markdown(md_text)

    output_path = input_path.parent / 'draft_paper_cleaned.md'
    output_path.write_text(cleaned, encoding='utf-8')
    print(f"Cleaned paper saved to: {output_path}")

    # Stats
    original_size = len(md_text)
    cleaned_size = len(cleaned)
    dollar_count_before = md_text.count('$')
    dollar_count_after = cleaned.count('$')
    backslash_count_before = md_text.count('\\')
    backslash_count_after = cleaned.count('\\')
    hash4_count_before = len(re.findall(r'^#{4,6}\s', md_text, re.MULTILINE))
    hash4_count_after = len(re.findall(r'^#{4,6}\s', cleaned, re.MULTILINE))

    print(f"\n清理统计:")
    print(f"  $ 符号: {dollar_count_before} → {dollar_count_after}")
    print(f"  \\ 反斜杠: {backslash_count_before} → {backslash_count_after}")
    print(f"  #### 标题: {hash4_count_before} → {hash4_count_after}")
    print(f"  文件大小: {original_size} → {cleaned_size} 字符")
