<template>
  <div class="settings-container">
    <header class="settings-header">
      <div class="header-content">
        <h1>⚙️ Ajustes</h1>
        <p class="text-muted">Configura tus modelos LLM y servidores MCP dinámicamente.</p>
      </div>
      <button class="btn btn-ghost" @click="$router.push('/')">← Volver al Dashboard</button>
    </header>

    <div class="settings-grid">
      <!-- LLM Configurations -->
      <section class="settings-section">
        <div class="section-header">
          <h2>🧠 Modelos LLM</h2>
          <button class="btn btn-primary btn-sm" @click="openLlmModal()">+ Añadir Modelo</button>
        </div>
        <div class="card-list">
          <div v-for="llm in llms" :key="llm.id" class="config-card">
            <div class="card-info">
              <h3>{{ llm.name }}</h3>
              <p class="text-xs text-muted">{{ llm.provider }} / {{ llm.model_id }}</p>
              <p v-if="llm.base_url" class="text-xs italic">{{ llm.base_url }}</p>
            </div>
            <div class="card-actions">
              <button class="btn btn-icon" @click="openLlmModal(llm)">✏️</button>
              <button class="btn btn-icon text-error" @click="deleteLlm(llm.id)">🗑️</button>
            </div>
          </div>
          <div v-if="llms.length === 0" class="empty-state">No hay modelos configurados.</div>
        </div>
      </section>

      <!-- MCP Servers -->
      <section class="settings-section">
        <div class="section-header">
          <h2>🛠️ Servidores MCP</h2>
          <button class="btn btn-primary btn-sm" @click="openMcpModal()">+ Añadir Servidor</button>
        </div>
        <div class="card-list">
          <div v-for="mcp in mcps" :key="mcp.id" class="config-card">
            <div class="card-info">
              <h3>{{ mcp.name }}</h3>
              <code>{{ mcp.command }} {{ mcp.args }}</code>
            </div>
            <div class="card-actions">
              <button class="btn btn-icon" @click="openMcpModal(mcp)">✏️</button>
              <button class="btn btn-icon text-error" @click="deleteMcp(mcp.id)">🗑️</button>
            </div>
          </div>
          <div v-if="mcps.length === 0" class="empty-state">No hay servidores MCP configurados.</div>
        </div>
      </section>
    </div>

    <!-- LLM Modal -->
    <div v-if="showLlmModal" class="modal-overlay">
      <div class="modal">
        <h3>{{ editingLlm ? 'Editar Modelo' : 'Nuevo Modelo' }}</h3>
        <div class="form-group">
          <label>Nombre Amigable</label>
          <input v-model="llmForm.name" placeholder="Ej: Mi Llama Local" />
        </div>
        <div class="form-group">
          <label>Proveedor</label>
          <select v-model="llmForm.provider">
            <option value="ollama">Ollama</option>
            <option value="openai">OpenAI</option>
            <option value="anthropic">Anthropic</option>
            <option value="google">Google</option>
          </select>
        </div>
        <div class="form-group">
          <label>ID del Modelo</label>
          <input v-model="llmForm.model_id" placeholder="Ej: llama3.2" />
        </div>
        <div class="form-group">
          <label>Base URL (Opcional)</label>
          <input v-model="llmForm.base_url" placeholder="http://..." />
        </div>
        <div class="form-group">
          <label>API Key (Opcional)</label>
          <input v-model="llmForm.api_key" type="password" placeholder="sk-..." />
        </div>
        <div class="modal-actions">
          <button class="btn btn-ghost" @click="showLlmModal = false">Cancelar</button>
          <button class="btn btn-primary" @click="saveLlm">Guardar</button>
        </div>
      </div>
    </div>

    <!-- MCP Modal -->
    <div v-if="showMcpModal" class="modal-overlay">
      <div class="modal">
        <h3>{{ editingMcp ? 'Editar Servidor' : 'Nuevo Servidor' }}</h3>
        <div class="form-group">
          <label>Nombre</label>
          <input v-model="mcpForm.name" placeholder="Ej: GitHub Tools" />
        </div>
        <div class="form-group">
          <label>Comando</label>
          <input v-model="mcpForm.command" placeholder="npx, python, etc." />
        </div>
        <div class="form-group">
          <label>Argumentos (JSON list)</label>
          <textarea v-model="mcpForm.args" placeholder='["@modelcontextprotocol/server-github", "--repo", "..."]'></textarea>
        </div>
        <div class="modal-actions">
          <button class="btn btn-ghost" @click="showMcpModal = false">Cancelar</button>
          <button class="btn btn-primary" @click="saveMcp">Guardar</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { configApi, LLMConfig, MCPServer } from '../api'

const llms = ref<LLMConfig[]>([])
const mcps = ref<MCPServer[]>([])

const showLlmModal = ref(false)
const editingLlm = ref<LLMConfig | null>(null)
const llmForm = ref({ name: '', provider: 'ollama', model_id: '', base_url: '', api_key: '' })

const showMcpModal = ref(false)
const editingMcp = ref<MCPServer | null>(null)
const mcpForm = ref({ name: '', command: '', args: '[]', env: '{}' })

const loadData = async () => {
  llms.value = await configApi.listLlms()
  mcps.value = await configApi.listMcp()
}

onMounted(loadData)

const openLlmModal = (llm?: LLMConfig) => {
  editingLlm.value = llm || null
  llmForm.value = llm 
    ? { 
        name: llm.name, 
        provider: llm.provider, 
        model_id: llm.model_id, 
        base_url: llm.base_url || '',
        api_key: llm.api_key || '' 
      } 
    : { name: '', provider: 'ollama', model_id: '', base_url: '', api_key: '' }
  showLlmModal.value = true
}

const saveLlm = async () => {
  if (editingLlm.value) {
    await configApi.updateLlm(editingLlm.value.id, llmForm.value)
  } else {
    await configApi.createLlm(llmForm.value)
  }
  showLlmModal.value = false
  loadData()
}

const deleteLlm = async (id: string) => {
  if (confirm('¿Eliminar esta configuración?')) {
    await configApi.deleteLlm(id)
    loadData()
  }
}

const openMcpModal = (mcp?: MCPServer) => {
  editingMcp.value = mcp || null
  mcpForm.value = mcp ? { ...mcp } : { name: '', command: '', args: '[]', env: '{}' }
  showMcpModal.value = true
}

const saveMcp = async () => {
  if (editingMcp.value) {
    await configApi.updateMcp(editingMcp.value.id, mcpForm.value)
  } else {
    await configApi.createMcp(mcpForm.value)
  }
  showMcpModal.value = false
  loadData()
}

const deleteMcp = async (id: string) => {
  if (confirm('¿Eliminar este servidor?')) {
    await configApi.deleteMcp(id)
    loadData()
  }
}
</script>

<style scoped>
.settings-container {
  padding: 2rem;
  max-width: 1000px;
  margin: 0 auto;
}
.settings-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
}
.settings-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
}
.settings-section {
  background: var(--bg-card);
  padding: 1.5rem;
  border-radius: 12px;
  border: 1px solid var(--border-color);
}
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}
.card-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.config-card {
  background: rgba(255, 255, 255, 0.05);
  padding: 1rem;
  border-radius: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.card-info h3 {
  font-size: 1rem;
  margin: 0;
}
.card-actions {
  display: flex;
  gap: 0.5rem;
}
.btn-icon {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
}
.btn-icon:hover {
  background: rgba(255, 255, 255, 0.1);
}
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.modal {
  background: var(--bg-dark);
  padding: 2rem;
  border-radius: 16px;
  width: 100%;
  max-width: 450px;
  border: 1px solid var(--border-color);
}
.form-group {
  margin-bottom: 1rem;
}
.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
  color: var(--text-muted);
}
.form-group input, .form-group select, .form-group textarea {
  width: 100%;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border-color);
  color: white;
  padding: 0.6rem;
  border-radius: 6px;
}
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 2rem;
}
.empty-state {
  text-align: center;
  padding: 2rem;
  color: var(--text-muted);
  font-style: italic;
}
</style>
