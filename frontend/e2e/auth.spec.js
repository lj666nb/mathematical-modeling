/**
 * E2E 测试：用户认证流程
 * 测试默认账号登录、登出、路由守卫
 */
import { test, expect } from '@playwright/test';

const TEST_ACCOUNT = {
  username: 'guoketg',
  password: '123456',
};

test.describe('用户认证流程', () => {

  test('登录页面正常加载', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('input[type="text"], input[placeholder*="用户"], input[placeholder*="账号"]').first()).toBeVisible();
    await expect(page.locator('input[type="password"]').first()).toBeVisible();
  });

  test('使用默认测试账号登录成功', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');

    // 填写登录表单
    const usernameInput = page.locator('input[type="text"], input[placeholder*="用户"], input[placeholder*="账号"]').first();
    const passwordInput = page.locator('input[type="password"]').first();
    await usernameInput.fill(TEST_ACCOUNT.username);
    await passwordInput.fill(TEST_ACCOUNT.password);

    // 点击登录 (Vite SPA 客户端导航，click 自动等待)
    await page.locator('button:has-text("登录"), button:has-text("登 录"), button[type="submit"]').first().click();
    // 等待 SPA 路由完成
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);

    // 验证已跳转到需要认证的页面
    expect(page.url()).not.toContain('/login');
  });

  test('未登录时访问受保护页面应跳转登录页', async ({ page }) => {
    // 清除可能的 localStorage
    await page.goto('/');
    await page.evaluate(() => {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    });

    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);
    expect(page.url()).toContain('/login');
  });

  test('登录后可以访问 Dashboard', async ({ page }) => {
    // 使用 API 直接登录设置 token
    await page.goto('/login');
    await page.waitForLoadState('networkidle');

    const usernameInput = page.locator('input[type="text"], input[placeholder*="用户"], input[placeholder*="账号"]').first();
    const passwordInput = page.locator('input[type="password"]').first();
    await usernameInput.fill(TEST_ACCOUNT.username);
    await passwordInput.fill(TEST_ACCOUNT.password);

    await page.locator('button:has-text("登录"), button:has-text("登 录"), button[type="submit"]').first().click();
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);

    // 导航到 Dashboard
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    expect(page.url()).toContain('/dashboard');
  });
});
