/**
 * E2E 测试：核心页面可访问性
 * 测试 Dashboard / LLM配置 / AI对话 / 题库 页面加载
 */
import { test, expect } from '@playwright/test';

const TEST_ACCOUNT = {
  username: 'guoketg',
  password: '123456',
};

test.beforeEach(async ({ page }) => {
  // 登录
  await page.goto('/login');
  await page.waitForLoadState('networkidle');

  const usernameInput = page.locator('input[type="text"], input[placeholder*="用户"], input[placeholder*="账号"]').first();
  const passwordInput = page.locator('input[type="password"]').first();
  await usernameInput.fill(TEST_ACCOUNT.username);
  await passwordInput.fill(TEST_ACCOUNT.password);

  await page.locator('button:has-text("登录"), button:has-text("登 录"), button[type="submit"]').first().click();
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(500);
});

test.describe('核心页面加载', () => {

  test('LLM API 配置页面正常加载', async ({ page }) => {
    await page.goto('/llm-config');
    await page.waitForLoadState('networkidle');
    expect(page.url()).toContain('/llm-config');
  });

  test('AI 智能体对话页面正常加载', async ({ page }) => {
    await page.goto('/agent-chat');
    await page.waitForLoadState('networkidle');
    expect(page.url()).toContain('/agent-chat');
  });

  test('实验题库页面正常加载', async ({ page }) => {
    await page.goto('/experiments');
    await page.waitForLoadState('networkidle');
    expect(page.url()).toContain('/experiments');
  });

  test('在线编程页面正常加载', async ({ page }) => {
    await page.goto('/code-editor');
    await page.waitForLoadState('networkidle');
    expect(page.url()).toContain('/code-editor');
  });

  test('教学统计页面对 admin 角色可访问', async ({ page }) => {
    await page.goto('/teacher-stats');
    await page.waitForLoadState('networkidle');
    expect(page.url()).toContain('/teacher-stats');
  });
});
