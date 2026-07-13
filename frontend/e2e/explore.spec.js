/**
 * Playwright DOM 探索测试 — 逐页深入查看 DOM 树和交互元素
 * 运行: npx playwright test e2e/explore.spec.js --headed
 */
import { test } from '@playwright/test';

const ACCOUNT = { username: 'guoketg', password: '123456' };

test.describe('前端 DOM 探索', () => {

  test('🔍 全页面 DOM 结构探索', async ({ page }) => {
    test.setTimeout(120000);

    // ========== 登录 ==========
    console.log('\n🔐 登录...');
    await page.goto('http://localhost/login');
    await page.waitForLoadState('networkidle');
    await page.fill('input[type="text"]', ACCOUNT.username);
    await page.fill('input[type="password"]', ACCOUNT.password);
    await page.click('button:has-text("登录")');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);
    console.log('✅ 登录成功 →', page.url());

    // ========== 遍历所有页面 ==========
    const pages = [
      '/dashboard',
      '/llm-config',
      '/experiments',
      '/code-editor',
      '/agent-chat',
      '/teacher-stats',
    ];

    for (const path of pages) {
      console.log(`\n${'='.repeat(50)}`);
      console.log(`📄 ${path}`);
      console.log('='.repeat(50));

      await page.goto(`http://localhost${path}`);
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(300);

      // 截图
      await page.screenshot({ path: `playwright-report/dom-${path.replace(/\//g, '-')}.png`, fullPage: true });

      // -------- 提取 DOM --------
      const dom = await page.evaluate(() => {
        const data = {};

        // 1. 页面标题
        data.title = document.title;

        // 2. 所有标题
        data.headings = [...document.querySelectorAll('h1,h2,h3,h4')].map(h => ({
          tag: h.tagName,
          text: h.textContent.trim().slice(0, 80),
        }));

        // 3. 侧边栏
        data.sidebar = [...document.querySelectorAll('.el-menu-item, [class*="sidebar"] a, [class*="Sidebar"] a, nav a, .el-aside a')].map(a => ({
          text: a.textContent.trim().slice(0, 40),
          href: a.getAttribute('href') || '',
        }));

        // 4. 按钮
        data.buttons = [...document.querySelectorAll('button, .el-button')].filter(b => b.offsetParent !== null).map(b => ({
          text: b.textContent.trim().slice(0, 50),
          class: b.className.slice(0, 60),
        }));

        // 5. 输入框
        data.inputs = [...document.querySelectorAll('input, textarea, select')].filter(i => i.offsetParent !== null).map(i => ({
          type: i.type || i.tagName,
          placeholder: i.placeholder || '',
          name: i.name || i.getAttribute('aria-label') || '',
        }));

        // 6. 表格
        data.tables = [...document.querySelectorAll('table, .el-table')].map(t => {
          const headers = [...t.querySelectorAll('th, .el-table__header th')].map(h => h.textContent.trim().slice(0, 30));
          const rowCount = t.querySelectorAll('tr, .el-table__row').length;
          return { headers, rowCount };
        });

        // 7. 卡片/面板
        data.cards = [...document.querySelectorAll('.el-card, [class*="card"], [class*="panel"]')].map(c => ({
          header: (c.querySelector('.el-card__header, [class*="header"], h3')?.textContent || '').trim().slice(0, 50),
          class: c.className.slice(0, 80),
        }));

        // 8. 弹窗/对话框
        data.dialogs = [...document.querySelectorAll('.el-dialog, .el-drawer, [role="dialog"]')].map(d => ({
          title: (d.querySelector('.el-dialog__title, [class*="title"]')?.textContent || '').trim().slice(0, 50),
          visible: d.offsetParent !== null,
        }));

        // 9. 元素统计
        data.stats = {
          divs: document.querySelectorAll('div').length,
          spans: document.querySelectorAll('span').length,
          images: document.querySelectorAll('img').length,
          links: document.querySelectorAll('a').length,
          paragraphs: document.querySelectorAll('p').length,
        };

        return data;
      });

      // -------- 打印结果 --------
      console.log(`  🏷  标题: ${dom.title}`);
      console.log(`  📐 标题结构: ${dom.headings.map(h => `${h.tag}→${h.text}`).join(' | ')}`);
      console.log(`  📋 侧边栏: ${dom.sidebar.map(s => s.text).join(' | ')}`);
      console.log(`  🔘 按钮(${dom.buttons.length}): ${dom.buttons.map(b => b.text).join(', ')}`);
      console.log(`  ✏️  输入框(${dom.inputs.length}): ${dom.inputs.map(i => `${i.type}:"${i.placeholder}"`).join(', ')}`);
      if (dom.tables.length) {
        dom.tables.forEach((t, i) => console.log(`  📊 表格${i + 1}: ${t.rowCount}行, headers=[${t.headers.join(', ')}]`));
      }
      if (dom.cards.length) console.log(`  🃏 卡片(${dom.cards.length}): ${dom.cards.map(c => c.header || c.class).join(' | ')}`);
      if (dom.dialogs.filter(d => d.visible).length) console.log(`  💬 弹窗: ${dom.dialogs.filter(d => d.visible).map(d => d.title).join(', ')}`);
      console.log(`  📊 统计: ${dom.stats.divs}div ${dom.stats.images}img ${dom.stats.links}a ${dom.stats.paragraphs}p`);
      console.log(`  📸 截图: playwright-report/dom-${path.replace(/\//g, '-')}.png`);
    }

    console.log('\n' + '='.repeat(50));
    console.log('✅ 全页面 DOM 探索完成');
  });
});
