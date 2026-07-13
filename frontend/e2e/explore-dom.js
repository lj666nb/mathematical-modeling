/**
 * Playwright 前端 DOM 探索脚本
 * 自动登录 → 遍历所有页面 → 截图 + 提取 DOM 结构
 */
import { chromium } from '@playwright/test';

const BASE = 'http://localhost';
const ACCOUNT = { username: 'guoketg', password: '123456' };

async function login(page) {
  console.log('\n🔐 登录中...');
  await page.goto(`${BASE}/login`);
  await page.waitForLoadState('networkidle');
  await page.fill('input[type="text"]', ACCOUNT.username);
  await page.fill('input[type="password"]', ACCOUNT.password);
  await page.click('button:has-text("登录")');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(500);
  console.log('✅ 登录成功，当前 URL:', page.url());
}

async function explorePage(page, path, name) {
  console.log(`\n📄 探索页面: ${name} (${path})`);
  await page.goto(`${BASE}${path}`);
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(300);

  // 截图
  await page.screenshot({ path: `playwright-report/${name}.png`, fullPage: true });

  // 提取 DOM 关键信息
  const domInfo = await page.evaluate(() => {
    const info = {};

    // 页面标题
    info.title = document.title;

    // 所有 h1-h3 标题文字
    info.headings = [];
    document.querySelectorAll('h1, h2, h3').forEach(h => {
      info.headings.push({ tag: h.tagName, text: h.textContent.trim().substring(0, 60) });
    });

    // 所有按钮
    info.buttons = [];
    document.querySelectorAll('button, .el-button, [role="button"]').forEach(b => {
      info.buttons.push({ text: b.textContent.trim().substring(0, 40), visible: b.offsetParent !== null });
    });

    // 所有输入框
    info.inputs = [];
    document.querySelectorAll('input, textarea, select').forEach(i => {
      info.inputs.push({
        type: i.type || i.tagName,
        placeholder: i.placeholder || '',
        name: i.name || '',
        visible: i.offsetParent !== null,
      });
    });

    // 侧边栏菜单项
    info.menuItems = [];
    document.querySelectorAll('.el-menu-item, .sidebar a, nav a, [class*="menu"]').forEach(m => {
      info.menuItems.push({ text: m.textContent.trim().substring(0, 40), href: m.getAttribute('href') || '' });
    });

    // 主要内容区域 class
    const main = document.querySelector('main, .main-content, .el-main, [class*="content"]');
    info.mainClasses = main ? main.className : 'N/A';

    // 统计关键元素数量
    info.counts = {
      divs: document.querySelectorAll('div').length,
      spans: document.querySelectorAll('span').length,
      tables: document.querySelectorAll('table, .el-table').length,
      forms: document.querySelectorAll('form, .el-form').length,
      cards: document.querySelectorAll('.el-card, [class*="card"]').length,
    };

    return info;
  });

  // 打印 DOM 结构
  console.log(`  标题: ${domInfo.title}`);
  console.log(`  页面 heading:`, domInfo.headings.map(h => `${h.tag}: ${h.text}`).join(' | ') || '(无)');
  console.log(`  按钮 (${domInfo.buttons.length}):`, domInfo.buttons.filter(b => b.visible).map(b => b.text).join(', ') || '(无)');
  console.log(`  输入框 (${domInfo.inputs.length}):`, domInfo.inputs.filter(i => i.visible).map(i => `${i.type}/${i.placeholder}`).join(', ') || '(无)');
  console.log(`  菜单项 (${domInfo.menuItems.length}):`, domInfo.menuItems.map(m => m.text).join(' | '));
  console.log(`  元素统计: ${domInfo.counts.divs} divs, ${domInfo.counts.tables} tables, ${domInfo.counts.forms} forms, ${domInfo.counts.cards} cards`);
  console.log(`  📸 截图: playwright-report/${name}.png`);

  return domInfo;
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  try {
    // 1. 登录
    await login(page);

    // 2. 遍历所有页面
    const pages = [
      { path: '/dashboard', name: '01-Dashboard' },
      { path: '/llm-config', name: '02-LlmConfig' },
      { path: '/experiments', name: '03-Experiments' },
      { path: '/code-editor', name: '04-CodeEditor' },
      { path: '/agent-chat', name: '05-AgentChat' },
      { path: '/teacher-stats', name: '06-TeacherStats' },
    ];

    for (const p of pages) {
      await explorePage(page, p.path, p.name);
    }

    console.log('\n' + '='.repeat(60));
    console.log('✅ 全部页面探索完成！');
    console.log('📸 截图保存在 playwright-report/ 目录');
    console.log('='.repeat(60));

  } catch (err) {
    console.error('❌ 错误:', err.message);
    // 出错时截图
    await page.screenshot({ path: 'playwright-report/error.png', fullPage: true });
  } finally {
    await browser.close();
  }
})();
