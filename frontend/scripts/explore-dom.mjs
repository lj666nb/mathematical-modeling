/**
 * Playwright DOM 实时探索 — 直接输出到终端
 */
import { chromium } from 'playwright';

async function main() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  // === 登录 ===
  console.log('🔐 登录...');
  await page.goto('http://localhost/login');
  await page.waitForLoadState('networkidle');
  await page.fill('#username', 'guoketg');
  await page.fill('#password', '123456');
  await page.click('button[type=submit]');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(600);
  console.log('✅ 已登录:', page.url());

  const pages = [
    ['/dashboard', 'Dashboard'],
    ['/llm-config', 'LLM-config'],
    ['/experiments', 'Experiments'],
    ['/code-editor', 'CodeEditor'],
    ['/agent-chat', 'AgentChat'],
    ['/teacher-stats', 'TeacherStats'],
  ];

  for (const [path, name] of pages) {
    console.log('\n' + '='.repeat(60));
    console.log('📄 [' + name + '] ' + path);
    console.log('='.repeat(60));

    await page.goto('http://localhost' + path);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(400);

    const dom = await page.evaluate(() => {
      const q = (s) => [...document.querySelectorAll(s)];

      // 侧边栏菜单
      const menuSelectors = ['.el-menu-item', '.el-aside a', '.sidebar a', 'nav a'];
      let sidebar = [];
      for (const sel of menuSelectors) {
        sidebar = q(sel).filter(el => el.textContent.trim() && el.offsetParent !== null)
          .map(el => '  · ' + el.textContent.trim().replace(/\s+/g, ' '));
        if (sidebar.length) break;
      }

      const headings = q('h1,h2,h3,h4')
        .filter(h => h.offsetParent !== null)
        .map(h => '  ' + h.tagName + ' | ' + h.textContent.trim().slice(0, 80));

      const buttons = q('button, .el-button, [role=button]')
        .filter(b => b.offsetParent !== null)
        .map(b => '  [' + b.className.split(' ').slice(0, 2).join(' ') + '] ' + b.textContent.trim().slice(0, 50));

      const inputs = q('input, textarea, select')
        .filter(i => i.offsetParent !== null)
        .map(i => '  <' + (i.type || i.tagName) + '> placeholder="' + (i.placeholder || '') + '" name="' + (i.name || '') + '"');

      const tables = q('table, .el-table')
        .map(t => {
          const hdrs = [...t.querySelectorAll('th')].map(h => h.textContent.trim().slice(0, 20));
          return '  📊 ' + t.querySelectorAll('tr').length + '行 [' + hdrs.join(', ') + ']';
        });

      const cards = q('.el-card, [class*=card]')
        .filter(c => c.offsetParent !== null)
        .map(c => {
          const hdr = c.querySelector('[class*=header], h3, h4');
          return '  🃏 ' + (hdr ? hdr.textContent.trim().slice(0, 50) : c.className.split(' ')[0]);
        });

      return { sidebar, headings, buttons, inputs, tables, cards };
    });

    if (dom.sidebar.length) { console.log('📋 侧边栏:'); console.log(dom.sidebar.join('\n')); }
    if (dom.headings.length) { console.log('📐 标题:'); console.log(dom.headings.join('\n')); }
    if (dom.cards.length) { console.log('🃏 卡片/面板:'); console.log(dom.cards.join('\n')); }
    if (dom.buttons.length) { console.log('🔘 按钮(' + dom.buttons.length + '):'); console.log(dom.buttons.join('\n')); }
    if (dom.inputs.length) { console.log('✏️ 输入框(' + dom.inputs.length + '):'); console.log(dom.inputs.join('\n')); }
    if (dom.tables.length) { console.log('📊 表格(' + dom.tables.length + '):'); console.log(dom.tables.join('\n')); }

    await page.screenshot({ path: 'playwright-report/dom-' + name + '.png', fullPage: true });
    console.log('📸 playwright-report/dom-' + name + '.png');
  }

  console.log('\n' + '='.repeat(60));
  console.log('✅ 全部 6 个页面探索完成');
  await browser.close();
}

main().catch(err => { console.error('❌', err.message); process.exit(1); });
