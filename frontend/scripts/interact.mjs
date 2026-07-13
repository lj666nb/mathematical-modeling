/**
 * Playwright 交互操作 — 实际点击/输入/切换
 */
import { chromium } from 'playwright';

async function main() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  // ====== 登录 ======
  console.log('🔐 登录...');
  await page.goto('http://localhost/login');
  await page.waitForLoadState('networkidle');
  await page.fill('#username', 'guoketg');
  await page.fill('#password', '123456');
  await page.click('button[type=submit]');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(500);
  console.log('✅ 登录成功\n');

  // ====== 操作1: LLM配置页 — 点击"新建"看弹窗 ======
  console.log('━'.repeat(50));
  console.log('🖱️  操作1: LLM配置页 → 点击"新建"按钮');
  await page.goto('http://localhost/llm-config');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(300);

  const newBtn = page.locator('button:has-text("新建")');
  if (await newBtn.isVisible()) {
    await newBtn.click();
    await page.waitForTimeout(500);

    // 检查弹窗是否出现
    const dialog = page.locator('.el-dialog, .el-drawer, [role=dialog]');
    if (await dialog.isVisible()) {
      const dialogTitle = await dialog.locator('.el-dialog__title, [class*=title]').first().textContent().catch(() => '');
      console.log('  ✅ 弹窗已打开:', dialogTitle || '(无标题)');

      // 弹窗内的表单元素
      const formEls = await page.evaluate(() => {
        const dlg = document.querySelector('.el-dialog, .el-drawer, [role=dialog]');
        if (!dlg) return [];
        return [...dlg.querySelectorAll('input, select, textarea, button')]
          .filter(el => el.offsetParent !== null)
          .map(el => {
            if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.tagName === 'SELECT')
              return `  ✏️ <${el.tagName}> placeholder="${el.placeholder}" ${el.type ? 'type=' + el.type : ''}`;
            return `  🔘 ${el.textContent.trim().slice(0, 40)}`;
          });
      });
      console.log('  弹窗内容:');
      formEls.forEach(e => console.log(e));

      // 填入示例数据
      const nameInp = dialog.locator('input').first();
      if (await nameInp.isVisible()) {
        await nameInp.fill('测试配置-DeepSeek');
        console.log('  ✍️  已填入: 测试配置-DeepSeek');
      }

      // 关闭弹窗
      const cancelBtn = dialog.locator('button:has-text("取消"), button:has-text("关闭")').first();
      if (await cancelBtn.isVisible()) await cancelBtn.click();
      else await page.keyboard.press('Escape');
      await page.waitForTimeout(300);
      console.log('  ❌ 弹窗已关闭');
    }
  }

  // ====== 操作2: AI对话 — 切换Agent + 发送消息 ======
  console.log('\n' + '━'.repeat(50));
  console.log('🖱️  操作2: AI对话页 → 切换Agent');
  await page.goto('http://localhost/agent-chat');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(300);

  // 查看当前显示的Agent
  const currentAgent = page.locator('h3').first();
  console.log('  当前Agent:', await currentAgent.textContent().catch(() => '?'));

  // 点击"切换"按钮
  const switchBtn = page.locator('button:has-text("切换")');
  if (await switchBtn.isVisible()) {
    await switchBtn.click();
    await page.waitForTimeout(400);
    const newAgent = page.locator('h3').first();
    console.log('  切换后Agent:', await newAgent.textContent().catch(() => '?'));
  }

  // 在输入框打字
  const chatInput = page.locator('textarea').first();
  if (await chatInput.isVisible()) {
    await chatInput.fill('什么是层次分析法？');
    await page.waitForTimeout(300);
    const inputVal = await chatInput.inputValue();
    console.log('  ✍️  已输入:', inputVal);
  }

  // ====== 操作3: 题库 → 点击第一个"开始实验"进入代码编辑器 ======
  console.log('\n' + '━'.repeat(50));
  console.log('🖱️  操作3: 题库 → 点击"开始实验"');
  await page.goto('http://localhost/experiments');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(300);

  const startBtn = page.locator('button:has-text("开始实验")').first();
  if (await startBtn.isVisible()) {
    const expTitle = await page.locator('h3').first().textContent().catch(() => '');
    console.log('  第一个实验:', expTitle);
    await startBtn.click();
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);
    console.log('  当前URL:', page.url());

    // 检查代码编辑器中的内容
    const codeContent = await page.evaluate(() => {
      const ta = document.querySelector('textarea');
      return ta ? ta.value.slice(0, 200) : '(未找到代码编辑区)';
    });
    console.log('  编辑器内容(前200字):', codeContent);
  }

  // ====== 操作4: 侧边栏导航 ======
  console.log('\n' + '━'.repeat(50));
  console.log('🖱️  操作4: 侧边栏菜单逐个点击');
  const menuItems = await page.evaluate(() => {
    const links = document.querySelectorAll('.el-menu-item');
    return [...links].filter(l => l.offsetParent !== null).map(l => ({
      text: l.textContent.trim(),
    }));
  });
  console.log('  菜单项:', menuItems.map(m => m.text).join(' | '));

  // 点击"竞赛训练S0-S8"（如果有）
  const competitionLink = page.locator('.el-menu-item:has-text("竞赛")');
  if (await competitionLink.isVisible()) {
    await competitionLink.click();
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(400);
    console.log('  点击后URL:', page.url());
  }

  console.log('\n' + '═'.repeat(50));
  console.log('✅ 交互操作全部完成');
  await browser.close();
}

main().catch(err => { console.error('❌', err.message); process.exit(1); });
