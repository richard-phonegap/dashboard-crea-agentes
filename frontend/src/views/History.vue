<template>
  <div class="history">
    <div class="history-header animate-fade-in">
      <div>
        <h1>Historial de Ejecuciones</h1>
        <p class="text-muted" v-if="crew">Equipo: {{ crew.name }}</p>
      </div>
      <button class="btn btn-secondary" @click="$router.back()">← Volver</button>
    </div>

    <div class="runs-list animate-fade-in" v-if="runs.length > 0">
      <div v-for="run in runs" :key="run.id" class="run-row card" @click="viewRun(run.id)">
        <div class="run-info">
          <span class="badge" :class="statusClass(run.status)">{{ run.status }}</span>
          <div class="run-details">
            <span class="run-date">{{ formatDate(run.created_at) }}</span>
            <span class="run-id text-xs text-muted">ID: {{ run.id.slice(0, 8) }}</span>
          </div>
        </div>
        <div class="run-stats">
          <span class="stat">
            <span class="stat-icon">🪙</span>
            {{ run.tokens_used }} tokens
          </span>
          <span class="stat">
            <span class="stat-icon">💰</span>
            ${{ run.cost?.toFixed(4) }}
          </span>
        </div>
        <div class="run-actions">
          <button class="btn btn-ghost">Ver detalles →</button>
        </div>
      </div>
    </div>

    <div v-else-if="loading" class="loading-state">
      <div class="animate-pulse">⏳ Cargando historial...</div>
    </div>

    <div v-else class="empty-state">
      <div class="empty-icon">📅</div>
      <h2>No hay ejecuciones aún</h2>
      <p class="text-muted">Ejecuta este equipo desde el editor para ver los resultados aquí.</p>
      <button class="btn btn-primary" @click="$router.push(`/editor/${crewId}`)">Ir al Editor</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { runsApi, crewsApi, type Run, type Crew } from '../api'

const route = useRoute()
const router = useRouter()
const crewId = route.params.id as string

const runs = ref<Run[]>([])
const crew = ref<Crew | null>(null)
const loading = ref(true)

onMounted(async () => {
  try {
    const [runsData, crewData] = await Promise.all([
      runsApi.list(crewId),
      crewsApi.get(crewId)
    ])
    runs.value = runsData.sort((a,b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    crew.value = crewData
  } catch (e) {
    console.error('Error loading history:', e)
  } finally {
    loading.value = false
  }
})

function viewRun(runId: string) {
  router.push({
    path: `/monitor/${runId}`,
    query: { crewId }
  })
}

function statusClass(status: string) {
  switch (status) {
    case 'completed': return 'badge-success'
    case 'failed': return 'badge-error'
    case 'running': return 'badge-info'
    default: return 'badge-warning'
  }
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString('es', {
    day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit'
  })
}
</script>

<style scoped>
.history {
  padding: 32px 40px;
  height: 100%;
  overflow-y: auto;
}

.history-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.runs-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.run-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.run-row:hover {
  transform: translateX(4px);
  border-color: var(--accent-primary);
}

.run-info {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
}

.run-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.run-date {
  font-weight: 500;
}

.run-stats {
  display: flex;
  gap: 24px;
  margin-right: 40px;
}

.stat {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-secondary);
}

.loading-state, .empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 50%;
  text-align: center;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}
</style>
