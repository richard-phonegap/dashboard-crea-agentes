<template>
  <div class="monitor" v-if="run">
    <div class="monitor-header animate-fade-in">
      <div>
        <h1>Monitor de Ejecución</h1>
        <p class="text-muted">Run ID: {{ run.id.slice(0, 8) }}...</p>
      </div>
      <div class="flex gap-12 items-center">
        <span class="badge" :class="statusClass">{{ run.status }}</span>
        <button class="btn btn-secondary" @click="$router.back()">← Volver</button>
      </div>
    </div>

    <div class="monitor-grid">
      <!-- Stats -->
      <div class="stats-row animate-fade-in">
        <div class="stat-card card">
          <div class="stat-value">{{ run.tokens_used }}</div>
          <div class="stat-label text-muted text-sm">Tokens</div>
        </div>
        <div class="stat-card card">
          <div class="stat-value">${{ run.cost?.toFixed(4) }}</div>
          <div class="stat-label text-muted text-sm">Costo</div>
        </div>
        <div class="stat-card card">
          <div class="stat-value">{{ duration }}</div>
          <div class="stat-label text-muted text-sm">Duración</div>
        </div>
      </div>

      <!-- Logs -->
      <div class="card animate-fade-in">
        <h3 style="margin-bottom: 12px">📋 Logs de Ejecución</h3>
        <div class="log-container">
          <div v-for="(log, i) in parsedLogs" :key="i" class="log-line" :class="'log-' + log.level">
            <span class="log-ts">{{ formatTime(log.timestamp) }}</span>
            <span class="log-agent" v-if="log.agent">[{{ log.agent }}]</span>
            <span class="log-text">{{ log.message }}</span>
          </div>
          <div v-if="parsedLogs.length === 0" class="text-muted text-center" style="padding: 20px">
            Sin logs disponibles
          </div>
        </div>
      </div>

      <!-- Result -->
      <div class="card animate-fade-in" v-if="run.result">
        <h3 style="margin-bottom: 12px">📄 Resultado</h3>
        <div class="result-body" v-html="renderMarkdown(run.result)"></div>
      </div>
    </div>
  </div>

  <div v-else class="loading-state">
    <div class="animate-pulse">⏳ Cargando...</div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { marked } from 'marked'
import type { Run, LogEntry } from '../api'

const route = useRoute()
const run = ref<Run | null>(null)

const parsedLogs = computed<LogEntry[]>(() => {
  if (!run.value?.logs) return []
  try { return JSON.parse(run.value.logs) } catch { return [] }
})

const statusClass = computed(() => {
  switch (run.value?.status) {
    case 'completed': return 'badge-success'
    case 'failed': return 'badge-error'
    case 'running': return 'badge-info'
    default: return 'badge-warning'
  }
})

const duration = computed(() => {
  if (!run.value?.started_at || !run.value?.completed_at) return '—'
  const start = new Date(run.value.started_at).getTime()
  const end = new Date(run.value.completed_at).getTime()
  const secs = Math.round((end - start) / 1000)
  return secs < 60 ? `${secs}s` : `${Math.floor(secs/60)}m ${secs%60}s`
})

onMounted(async () => {
  const runId = route.params.runId as string
  // Fetch run details — for now from the API
  // We'd need to know the crewId; for now accept it from query
  const crewId = route.query.crewId as string
  if (crewId && runId) {
    const { runsApi } = await import('../api')
    run.value = await runsApi.get(crewId, runId)
  }
})

function formatTime(ts: string) {
  return new Date(ts).toLocaleTimeString('es', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

function renderMarkdown(text: string) {
  return marked.parse(text) as string
}
</script>

<style scoped>
.monitor {
  padding: 32px 40px;
  height: 100%;
  overflow-y: auto;
}

.monitor-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.monitor-grid {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.stat-card { text-align: center; }

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--accent-primary);
}

.log-container {
  background: var(--bg-input);
  border-radius: var(--radius-sm);
  padding: 12px;
  max-height: 300px;
  overflow-y: auto;
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 12px;
}

.log-line {
  display: flex;
  gap: 8px;
  padding: 3px 0;
  align-items: baseline;
}

.log-ts { color: var(--text-muted); flex-shrink: 0; }
.log-agent { color: var(--accent-primary); font-weight: 600; flex-shrink: 0; }
.log-text { color: var(--text-primary); }
.log-success .log-text { color: var(--color-success); }
.log-error .log-text { color: var(--color-error); }
.log-warning .log-text { color: var(--color-warning); }

.result-body {
  line-height: 1.7;
  font-size: 14px;
}

.result-body :deep(h2) {
  margin-top: 16px;
  margin-bottom: 8px;
}

.result-body :deep(p) {
  margin: 8px 0;
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  font-size: 18px;
  color: var(--text-secondary);
}
</style>
