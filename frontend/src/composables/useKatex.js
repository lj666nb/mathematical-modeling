/**
 * useKatex — LaTeX 渲染工具
 * 处理文本中 $$...$$ 块级公式和 $...$ 行内公式
 */
import katex from 'katex'

/**
 * 渲染文本中的 LaTeX 公式为 HTML
 * 支持 $$...$$ / \[...\] 块级公式 和 $...$ / \(...\) 行内公式
 * @param {string} text — 包含 LaTeX 分隔符的原始文本
 * @returns {string} — 渲染后的 HTML 字符串
 */
export function renderAllMath(text) {
  if (!text) return ''

  // Step 1: 替换 $$...$$ 块级公式（支持跨行）
  let html = text.replace(/\$\$([\s\S]*?)\$\$/g, (_, formula) => {
    try {
      return katex.renderToString(formula.trim(), {
        displayMode: true,
        throwOnError: false,
        trust: true,
      })
    } catch {
      return `<code>${escapeHtml(formula.trim())}</code>`
    }
  })

  // Step 2: 替换 \[...\] 块级公式（LaTeX 标准语法）
  html = html.replace(/\\\[([\s\S]*?)\\\]/g, (_, formula) => {
    try {
      return katex.renderToString(formula.trim(), {
        displayMode: true,
        throwOnError: false,
        trust: true,
      })
    } catch {
      return `<code>${escapeHtml(formula.trim())}</code>`
    }
  })

  // Step 2.5: 替换 [ \begin{...} ... \end{...} ] 非标准格式（部分 AI 模型使用）
  html = html.replace(/\[\s*(\\begin\{[^}]+\}[\s\S]*?\\end\{[^}]+\})\s*\]/g, (_, formula) => {
    try {
      return katex.renderToString(formula.trim(), {
        displayMode: true,
        throwOnError: false,
        trust: true,
      })
    } catch {
      return `<code>${escapeHtml(formula.trim())}</code>`
    }
  })

  // Step 3: 替换 $...$ 行内公式
  html = html.replace(/(?<!\$)\$([^$\n]+?)\$(?!\$)/g, (_, formula) => {
    try {
      return katex.renderToString(formula.trim(), {
        displayMode: false,
        throwOnError: false,
        trust: true,
      })
    } catch {
      return `<code>${escapeHtml(formula.trim())}</code>`
    }
  })

  // Step 4: 替换 \(...\) 行内公式（LaTeX 标准语法）
  html = html.replace(/\\\(([\s\S]*?)\\\)/g, (_, formula) => {
    try {
      return katex.renderToString(formula.trim(), {
        displayMode: false,
        throwOnError: false,
        trust: true,
      })
    } catch {
      return `<code>${escapeHtml(formula.trim())}</code>`
    }
  })

  return html
}

/**
 * 渲染单个 LaTeX 公式为 HTML
 * @param {string} latex — LaTeX 源码（不含 $$ 分隔符）
 * @param {boolean} displayMode — 是否块级展示
 * @returns {{ html: string|null, error: string|null }}
 */
export function renderFormula(latex, displayMode = true) {
  try {
    const html = katex.renderToString(latex, {
      displayMode,
      throwOnError: false,
      trust: true,
    })
    return { html, error: null }
  } catch (e) {
    return { html: null, error: e.message }
  }
}

function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}
