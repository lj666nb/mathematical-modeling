<!--
  DocLayout — 文档式双栏布局组件
  左栏: sticky sidebar (导航/筛选)
  右栏: 可滚动内容区 (文档正文)
  响应式: Desktop 双栏 / Tablet 窄 sidebar / Mobile overlay
  用法:
    <DocLayout>
      <template #sidebar> ...导航... </template>
      <template #default> ...内容... </template>
    </DocLayout>
-->
<template>
  <div class="doc-layout">
    <!-- 移动端遮罩层 -->
    <transition name="doc-fade">
      <div
        v-if="sidebarOpen && isMobile"
        class="doc-sidebar-backdrop"
        @click="closeSidebar"
      />
    </transition>

    <!-- 移动端切换按钮 -->
    <button
      v-if="isMobile"
      class="doc-mobile-toggle"
      :class="{ active: sidebarOpen }"
      @click="toggleSidebar"
      :title="sidebarOpen ? '关闭目录' : '打开目录'"
    >
      <span class="hamburger-line" />
      <span class="hamburger-line" />
      <span class="hamburger-line" />
    </button>

    <!-- 左侧 Sidebar -->
    <aside
      class="doc-sidebar"
      :class="{ open: sidebarOpen }"
      :style="{ '--doc-sidebar-width': isTablet ? sidebarTabletWidth : sidebarWidth }"
    >
      <div class="doc-sidebar-inner">
        <div v-if="sidebarTitle" class="doc-sidebar-title">
          {{ sidebarTitle }}
        </div>
        <slot name="sidebar" />
      </div>
    </aside>

    <!-- 右侧内容区 -->
    <main class="doc-content">
      <slot />
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  sidebarWidth: { type: String, default: '240px' },
  sidebarTabletWidth: { type: String, default: '200px' },
  sidebarTitle: { type: String, default: '' },
  mobileBreakpoint: { type: Number, default: 768 },
  tabletBreakpoint: { type: Number, default: 1200 },
})

const windowWidth = ref(window.innerWidth)
const sidebarOpen = ref(false)

const isMobile = computed(() => windowWidth.value < props.mobileBreakpoint)
const isTablet = computed(() =>
  windowWidth.value >= props.mobileBreakpoint && windowWidth.value < props.tabletBreakpoint
)

function onResize() {
  windowWidth.value = window.innerWidth
  // 从 mobile 切换到 desktop 时自动展开
  if (!isMobile.value) {
    sidebarOpen.value = false
  }
}

function toggleSidebar() {
  sidebarOpen.value = !sidebarOpen.value
}

function closeSidebar() {
  sidebarOpen.value = false
}

// 暴露方法给父组件（点击导航项后关闭 sidebar）
defineExpose({ closeSidebar, toggleSidebar })

onMounted(() => window.addEventListener('resize', onResize))
onUnmounted(() => window.removeEventListener('resize', onResize))
</script>

<style scoped lang="scss">
/* ============================================================
   DocLayout — 双栏文档布局
   ============================================================ */

.doc-layout {
  display: flex;
  gap: var(--space-7);
  align-items: flex-start;
  position: relative;

  @media (max-width: 1200px) {
    gap: var(--space-5);
  }

  @media (max-width: 768px) {
    display: block;
  }
}

/* —— 移动端切换按钮 —— */
.doc-mobile-toggle {
  display: none;
  position: fixed;
  top: var(--space-3);
  left: var(--space-3);
  width: 36px;
  height: 36px;
  padding: 8px 6px;
  background: var(--color-slate-700);
  border: var(--border-subtle);
  border-radius: var(--radius-md);
  cursor: pointer;
  z-index: 2001;
  flex-direction: column;
  justify-content: center;
  gap: 4px;
  box-shadow: var(--glow-card);

  @media (max-width: 768px) {
    display: flex;
  }

  .hamburger-line {
    display: block;
    height: 2px;
    background: var(--color-chalk);
    border-radius: 1px;
    transition: all var(--duration-fast) var(--ease-out);
  }

  &.active .hamburger-line {
    &:nth-child(1) { transform: rotate(45deg) translate(4px, 4px); }
    &:nth-child(2) { opacity: 0; }
    &:nth-child(3) { transform: rotate(-45deg) translate(4px, -4px); }
  }
}

/* —— 遮罩层 —— */
.doc-sidebar-backdrop {
  display: none;

  @media (max-width: 768px) {
    display: block;
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.4);
    z-index: 1999;
    backdrop-filter: blur(2px);
  }
}

/* —— 左侧 Sidebar —— */
.doc-sidebar {
  width: var(--doc-sidebar-width, 240px);
  flex-shrink: 0;
  position: sticky;
  top: var(--space-5);
  max-height: calc(100vh - var(--space-9));
  overflow-y: auto;

  @media (max-width: 1200px) {
    width: var(--doc-sidebar-width, 200px);
  }

  @media (max-width: 768px) {
    position: fixed;
    top: 0;
    left: 0;
    width: 280px;
    height: 100vh;
    max-height: 100vh;
    z-index: 2000;
    background: var(--color-slate-700);
    border-right: var(--border-subtle);
    box-shadow: var(--glow-modal);
    transform: translateX(-100%);
    transition: transform var(--duration-normal) var(--ease-out);
    padding: var(--space-8) var(--space-5) var(--space-5);

    &.open {
      transform: translateX(0);
    }
  }
}

.doc-sidebar-inner {
  @media (max-width: 768px) {
    padding-top: var(--space-8);
  }
}

.doc-sidebar-title {
  font-family: var(--font-display);
  font-size: var(--text-md);
  font-weight: var(--weight-semibold);
  color: var(--color-chalk);
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-3);
  border-bottom: var(--border-subtle);
}

/* —— 右侧内容区 —— */
.doc-content {
  flex: 1;
  min-width: 0; // 防止弹性溢出

  @media (max-width: 768px) {
    padding-top: var(--space-8); // 给 hamburger 按钮留空间
  }
}

/* —— 过渡动画 —— */
.doc-fade-enter-active,
.doc-fade-leave-active {
  transition: opacity var(--duration-fast) var(--ease-out);
}

.doc-fade-enter-from,
.doc-fade-leave-to {
  opacity: 0;
}
</style>
