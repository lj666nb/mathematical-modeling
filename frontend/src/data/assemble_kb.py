#!/usr/bin/env python3
"""
Assemble knowledgeBase.js from individual category JSON files.
Reads frontend/src/data/categories/*.json
Writes frontend/src/data/knowledgeBase.js
"""
import json, os, glob

def esc(s):
    """Escape string for JS single-quoted string literal."""
    return s.replace('\\', '\\\\').replace("'", "\\'")

def gen_algo(a):
    """Generate JS object literal for one algorithm."""
    lines = ['      {']
    lines.append(f"        name: '{esc(a['name'])}',")
    lines.append(f"        brief: '{esc(a['brief'])}',")
    lines.append(f"        description: '{esc(a['description'])}',")
    # formulas
    lines.append('        formulas: [')
    fms = a.get('formulas', [])
    for j, f in enumerate(fms):
        c = ',' if j < len(fms)-1 else ''
        lines.append(f"          {{ name: '{esc(f['name'])}', latex: '{esc(f['latex'])}', explanation: '{esc(f['explanation'])}' }}{c}")
    lines.append('        ],')
    # code (as template literal for multiline support)
    lines.append(f"        code: `{a.get('code', '')}`,")
    # steps
    lines.append('        steps: [')
    for j, s in enumerate(a.get('steps', [])):
        c = ',' if j < len(a.get('steps', []))-1 else ''
        lines.append(f"          '{esc(s)}'{c}")
    lines.append('        ],')
    # useCases
    lines.append('        useCases: [')
    for j, u in enumerate(a.get('useCases', [])):
        c = ',' if j < len(a.get('useCases', []))-1 else ''
        lines.append(f"          '{esc(u)}'{c}")
    lines.append('        ],')
    lines.append(f"        tips: '{esc(a.get('tips', ''))}'")
    lines.append('      }')
    return '\n'.join(lines)

def gen_cat(c):
    """Generate JS object literal for one category."""
    lines = []
    lines.append(f'  "{c["id"]}": {{')
    lines.append(f"    id: '{c['id']}',")
    lines.append(f"    name: '{esc(c['name'])}',")
    lines.append(f"    color: '{c['color']}',")
    lines.append(f"    description: '{esc(c['description'])}',")
    lines.append(f"    definition: '{esc(c['definition'])}',")
    lines.append('    algorithms: [')
    for i, a in enumerate(c['algorithms']):
        comma = ',' if i < len(c['algorithms'])-1 else ''
        lines.append(gen_algo(a) + comma)
    lines.append('    ]')
    lines.append('  }')
    return '\n'.join(lines)

# Read all category JSON files
cat_dir = os.path.join(os.path.dirname(__file__), 'categories')
if not os.path.isdir(cat_dir):
    print(f"ERROR: categories directory not found: {cat_dir}")
    exit(1)

json_files = sorted(glob.glob(os.path.join(cat_dir, '*.json')))
if not json_files:
    print(f"ERROR: no JSON files found in {cat_dir}")
    exit(1)

categories = []
for jf in json_files:
    with open(jf, 'r', encoding='utf-8') as f:
        categories.append(json.load(f))
    print(f"  Loaded: {os.path.basename(jf)} -> {categories[-1]['name']} ({len(categories[-1]['algorithms'])} algorithms)")

# Generate JS
header = """/**
 * ============================================================
 * 数学建模知识库 - 前端硬编码数据
 * 每个算法独立笔记，包含原理、公式、代码、使用场景
 * 共 8 大分类的详细算法笔记
 * ============================================================
 */

export const ALGORITHM_NOTES = {
"""

footer = """
}

/**
 * 获取某个分类下的某个算法笔记
 */
export function getAlgorithmNote(categoryId, algorithmIndex) {
  const cat = ALGORITHM_NOTES[categoryId]
  if (!cat || !cat.algorithms[algorithmIndex]) return null
  return cat.algorithms[algorithmIndex]
}

/**
 * 获取所有分类摘要（用于树导航）
 */
export function getCategoriesSummary() {
  return Object.entries(ALGORITHM_NOTES).map(([id, cat]) => ({
    id: cat.id,
    name: cat.name,
    color: cat.color,
    description: cat.description,
    algorithmCount: cat.algorithms.length,
    algorithmNames: cat.algorithms.map(a => a.name)
  }))
}
"""

cat_blocks = [gen_cat(c) for c in categories]

out_path = os.path.join(os.path.dirname(__file__), 'knowledgeBase.js')
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(header)
    f.write(',\n'.join(cat_blocks))
    f.write(footer)

total = sum(len(c['algorithms']) for c in categories)
print(f"\nGenerated knowledgeBase.js: {len(categories)} categories, {total} algorithms")
print(f"Output: {out_path}")
