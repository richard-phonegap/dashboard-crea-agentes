<template>
  <div class="dashboard">
    <div class="dashboard-header animate-fade-in">
      <div>
        <h1>Mis Equipos</h1>
        <p class="text-muted">Diseña y gestiona tus equipos de agentes IA</p>
      </div>
      <button class="btn btn-primary btn-lg" @click="showCreateModal = true">
        ✨ Nuevo Equipo
      </button>
    </div>

    <div class="crews-grid" v-if="crews.length > 0">
      <div
        v-for="crew in crews"
        :key="crew.id"
        class="crew-card card animate-fade-in"
        @click="openEditor(crew.id)"
      >
        <div class="crew-card-header">
          <div class="crew-icon">👥</div>
          <div class="crew-actions">
            <button class="btn btn-ghost btn-sm" @click.stop="openHistory(crew.id)" title="Historial">📋</button>
            <button class="btn btn-ghost btn-icon btn-sm" @click.stop="deleteCrew(crew.id)" title="Eliminar">🗑️</button>
          </div>
        </div>
        <h3 class="crew-name">{{ crew.name }}</h3>
        <p class="crew-desc text-muted text-sm">{{ crew.description || 'Sin descripción' }}</p>
        <div class="crew-stats">
          <span class="stat">
            <span class="stat-icon">🧠</span>
            {{ crew.agent_count }} agentes
          </span>
          <span class="stat">
            <span class="stat-icon">📋</span>
            {{ crew.task_count }} tareas
          </span>
        </div>
        <div class="crew-meta">
          <span class="badge badge-purple">{{ crew.process }}</span>
          <span class="text-sm text-muted">{{ formatDate(crew.updated_at) }}</span>
        </div>
      </div>
    </div>

    <div v-else class="empty-state animate-fade-in">
      <div class="empty-icon">🚀</div>
      <h2>¡Crea tu primer equipo!</h2>
      <p class="text-muted">
        Un equipo es un grupo de agentes IA que colaboran para completar tareas complejas.
      </p>
      <button class="btn btn-primary btn-lg" @click="showCreateModal = true">
        ✨ Crear Equipo
      </button>
    </div>

    <!-- Create Modal -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
      <div class="modal animate-fade-in">
        <h2>Nuevo Equipo</h2>
        <form @submit.prevent="createCrew">
          <div class="form-group">
            <label class="form-label">Nombre</label>
            <input class="input" v-model="newCrew.name" placeholder="Ej: Equipo de Investigación" required autofocus />
          </div>
          <div class="form-group">
            <label class="form-label">Descripción</label>
            <textarea class="textarea" v-model="newCrew.description" placeholder="¿Qué hace este equipo?" rows="3"></textarea>
          </div>
          <div class="form-group">
            <label class="form-label">Proceso</label>
            <select class="select" v-model="newCrew.process">
              <option value="sequential">Secuencial — Tareas en orden</option>
              <option value="hierarchical">Jerárquico — Un agente delega</option>
            </select>
          </div>
          <div class="modal-actions">
            <button type="button" class="btn btn-secondary" @click="showCreateModal = false">Cancelar</button>
            <button type="submit" class="btn btn-primary" :disabled="!newCrew.name">Crear Equipo</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { crewsApi, type CrewListItem } from '../api'

const router = useRouter()
const crews = ref<CrewListItem[]>([])
const showCreateModal = ref(false)
const newCrew = ref({ name: '', description: '', process: 'sequential' })

onMounted(async () => {
  await loadCrews()
})

async function loadCrews() {
  try {
    crews.value = await crewsApi.list()
  } catch (e) {
    console.error('Error loading crews:', e)
  }
}

async function createCrew() {
  try {
    const crew = await crewsApi.create(newCrew.value)
    showCreateModal.value = false
    newCrew.value = { name: '', description: '', process: 'sequential' }
    router.push(`/editor/${crew.id}`)
  } catch (e) {
    console.error('Error creating crew:', e)
  }
}

async function deleteCrew(id: string) {
  if (!confirm('¿Eliminar este equipo?')) return
  try {
    await crewsApi.delete(id)
    await loadCrews()
  } catch (e) {
    console.error('Error deleting crew:', e)
  }
}

function openEditor(id: string) {
  router.push(`/editor/${id}`)
}

function openHistory(id: string) {
  router.push(`/history/${id}`)
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('es', {
    day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit'
  })
}
</script>

<style scoped>
.dashboard {
  padding: 32px 40px;
  height: 100%;
  overflow-y: auto;
}

.dashboard-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 32px;
}

.crews-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.crew-card {
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 12px;
  position: relative;
}
.crew-card:hover {
  transform: translateY(-2px);
  border-color: var(--accent-primary);
  box-shadow: var(--shadow-glow-purple);
}

.crew-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.crew-icon {
  font-size: 28px;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  background: var(--accent-primary-glow);
}

.crew-name {
  font-size: 16px;
}

.crew-desc {
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.crew-stats {
  display: flex;
  gap: 16px;
}

.stat {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: var(--text-secondary);
}

.crew-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

/* ─── Empty State ─── */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 60%;
  gap: 16px;
  text-align: center;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 8px;
}

/* ─── Modal ─── */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: var(--bg-overlay);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.modal {
  background: var(--bg-card);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: var(--radius-lg);
  padding: 28px;
  width: 460px;
  max-width: 90vw;
  box-shadow: var(--shadow-lg);
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 8px;
}
</style>
