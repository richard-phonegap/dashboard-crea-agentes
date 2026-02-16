<template>
  <div class="app-layout">
    <header class="app-header">
      <div class="header-left">
        <router-link to="/" class="logo">
          <span class="logo-icon">⚡</span>
          <span class="logo-text">AgentForge</span>
        </router-link>
      </div>
      <nav class="header-nav">
        <router-link to="/" class="nav-link" active-class="active">
          <span class="nav-icon">📊</span> Dashboard
        </router-link>
        <router-link to="/editor" class="nav-link" active-class="active">
          <span class="nav-icon">🎨</span> Editor
        </router-link>
      </nav>
      <div class="header-right">
        <span class="badge badge-purple">v0.1.0</span>
      </div>
    </header>
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<style>
.app-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: var(--header-height);
  padding: 0 20px;
  background: var(--bg-secondary);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  flex-shrink: 0;
  z-index: 100;
}

.header-left {
  display: flex;
  align-items: center;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: var(--text-heading);
}

.logo-icon {
  font-size: 22px;
  filter: drop-shadow(0 0 8px rgba(108, 92, 231, 0.6));
}

.logo-text {
  font-size: 18px;
  font-weight: 700;
  background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.3px;
}

.header-nav {
  display: flex;
  gap: 4px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: var(--radius-sm);
  text-decoration: none;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  transition: all var(--transition-fast);
}

.nav-link:hover {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.05);
}

.nav-link.active {
  color: var(--accent-primary);
  background: var(--accent-primary-glow);
}

.nav-icon {
  font-size: 14px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.app-main {
  flex: 1;
  overflow: hidden;
  position: relative;
}
</style>
