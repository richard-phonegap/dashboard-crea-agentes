<script setup>
import { ref, onMounted, computed } from 'vue'

const config = ref({
  tools: {
    llm: { enabled: false, provider: 'ollama', model: '', api_key: '', api_base: '' },
    scraper: { enabled: false, user_agent: '' },
    database: { enabled: false, connections: [] }
  }
})
const loading = ref(true)
const saving = ref(false)
const fetchingModels = ref(false)
const message = ref('')
const messageType = ref('info') // info, success, error
const availableModels = ref([])

const API_URL = 'http://localhost:8002/api' // Base API URL

const showMessage = (msg, type = 'info') => {
  message.value = msg
  messageType.value = type
  setTimeout(() => { message.value = '' }, 5000)
}

const fetchConfig = async () => {
  try {
    const res = await fetch(`${API_URL}/config`)
    const data = await res.json()
    if (data && data.tools) {
      // Merge defaults to avoid undefined errors
      config.value = {
        tools: {
          llm: { 
            enabled: false, provider: 'ollama', model: '', api_key: '', api_base: '',
            ...data.tools?.llm 
          },
          scraper: { 
            enabled: false, user_agent: '',
            ...data.tools?.scraper 
          },
          database: { 
            enabled: false, connections: [],
            ...data.tools?.database 
          }
        }
      }
    }
  } catch (e) {
    console.error(e)
    showMessage('Error loading config: ' + e.message, 'error')
  } finally {
    loading.value = false
  }
}

const saveConfig = async () => {
  saving.value = true
  try {
    const payload = { config: config.value }
    const res = await fetch(`${API_URL}/config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    if (!res.ok) throw new Error('Failed to save')
    showMessage('Configuration saved successfully!', 'success')
  } catch (e) {
    showMessage('Error saving: ' + e.message, 'error')
  } finally {
    saving.value = false
  }
}

const fetchOllamaModels = async () => {
  if (!config.value.tools.llm.api_base) {
    showMessage('Please enter an API Base URL first.', 'error')
    return
  }
  
  fetchingModels.value = true
  try {
    const res = await fetch(`${API_URL}/ollama/models`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ api_base: config.value.tools.llm.api_base })
    })
    
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || 'Failed to fetch models')
    }
    
    const data = await res.json()
    availableModels.value = data.models || []
    showMessage(`Successfully fetched ${availableModels.value.length} models.`, 'success')
    
    // Auto-select first model if none selected
    if (!config.value.tools.llm.model && availableModels.value.length > 0) {
      config.value.tools.llm.model = availableModels.value[0]
    }
  } catch (e) {
    showMessage('Connection failed: ' + e.message, 'error')
    availableModels.value = []
  } finally {
    fetchingModels.value = false
  }
}

const addDbConnection = () => {
  if (!config.value.tools.database.connections) {
    config.value.tools.database.connections = []
  }
  config.value.tools.database.connections.push({ name: 'new_db', uri: '' })
}

const removeDbConnection = (index) => {
  config.value.tools.database.connections.splice(index, 1)
}

onMounted(fetchConfig)
</script>

<template>
  <div class="app-container">
    <header class="app-header">
      <div class="header-content">
        <h1>🤖 AI Agent Dashboard</h1>
        <p>Configure your MCP Server tools and capabilities</p>
      </div>
    </header>

    <main v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Loading configuration...</p>
    </main>
    
    <main v-else class="main-content">
      
      <!-- LLM SETTINGS -->
      <section class="card">
        <div class="card-header">
          <div class="toggle-switch">
             <input type="checkbox" id="llm-toggle" v-model="config.tools.llm.enabled" />
             <label for="llm-toggle"></label>
          </div>
          <h2>LLM Configuration</h2>
        </div>
        
        <div v-if="config.tools.llm.enabled" class="card-body">
          <div class="form-group">
            <label>Provider</label>
            <select v-model="config.tools.llm.provider">
              <option value="ollama">Ollama (Local)</option>
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
            </select>
          </div>

          <!-- OLLAMA SPECIFIC UI -->
          <div v-if="config.tools.llm.provider === 'ollama'" class="provider-section">
            <div class="form-group">
              <label>Server URL</label>
              <div class="input-with-button">
                <input v-model="config.tools.llm.api_base" placeholder="http://host.docker.internal:11434" />
                <button @click="fetchOllamaModels" :disabled="fetchingModels" class="secondary-btn">
                  {{ fetchingModels ? 'Connecting...' : 'Test & Fetch Models' }}
                </button>
              </div>
              <small class="hint">Use <code>http://host.docker.internal:11434</code> to access Ollama on host machine.</small>
            </div>

            <div class="form-group">
              <label>Model</label>
              <select v-if="availableModels.length > 0" v-model="config.tools.llm.model">
                <option v-for="m in availableModels" :key="m" :value="m">{{ m }}</option>
              </select>
              <input v-else v-model="config.tools.llm.model" placeholder="e.g. llama3 (Fetch to populate list)" />
            </div>
          </div>

          <!-- GENERIC PROVIDER UI -->
          <div v-else class="provider-section">
             <div class="form-group">
              <label>Model Name</label>
              <input v-model="config.tools.llm.model" placeholder="gpt-4, claude-3-opus, etc" />
            </div>
            
            <div class="form-group">
              <label>API Key</label>
              <input v-model="config.tools.llm.api_key" type="password" placeholder="sk-..." />
            </div>
          </div>
        </div>
      </section>

      <!-- SCRAPER SETTINGS -->
      <section class="card">
        <div class="card-header">
           <div class="toggle-switch">
             <input type="checkbox" id="scraper-toggle" v-model="config.tools.scraper.enabled" />
             <label for="scraper-toggle"></label>
          </div>
          <h2>Web Scraper</h2>
        </div>
        <div v-if="config.tools.scraper.enabled" class="card-body">
          <div class="form-group">
            <label>User Agent</label>
            <input v-model="config.tools.scraper.user_agent" placeholder="Mozilla/5.0..." />
          </div>
        </div>
      </section>

      <!-- DATABASE SETTINGS -->
      <section class="card">
        <div class="card-header">
           <div class="toggle-switch">
             <input type="checkbox" id="db-toggle" v-model="config.tools.database.enabled" />
             <label for="db-toggle"></label>
          </div>
          <h2>Database Tools</h2>
        </div>
        <div v-if="config.tools.database.enabled" class="card-body">
          <div v-for="(conn, idx) in config.tools.database.connections" :key="idx" class="db-row">
            <div class="form-group compact">
              <input v-model="conn.name" placeholder="Connection Name" />
            </div>
            <div class="form-group flex-grow">
               <input v-model="conn.uri" placeholder="postgresql://user:pass@host/db" />
            </div>
            <button @click="removeDbConnection(idx)" class="icon-btn" title="Remove">✕</button>
          </div>
          <button @click="addDbConnection" class="secondary-btn small-btn">+ Add Connection</button>
        </div>
      </section>

    </main>
    
    <!-- FOOTER ACTIONS -->
    <footer class="app-footer">
       <div v-if="message" :class="['message-toast', messageType]">{{ message }}</div>
       <button @click="saveConfig" :disabled="saving" class="primary-btn big-btn">
          {{ saving ? 'Saving Changes...' : 'Save Configuration' }}
        </button>
    </footer>
  </div>
</template>

<style scoped>
/* Modern Reset & Base */
.app-container {
  max-width: 900px;
  margin: 0 auto;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #f8fafc;
  color: #1e293b;
}

/* Header */
.app-header {
  background: white;
  padding: 2rem 1rem;
  border-bottom: 1px solid #e2e8f0;
  margin-bottom: 2rem;
}
.header-content { text-align: center; }
h1 { font-size: 1.8rem; margin: 0; color: #0f172a; font-weight: 700; }
p { color: #64748b; margin-top: 0.5rem; }

/* Cards */
.card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  margin-bottom: 1.5rem;
  overflow: hidden;
  border: 1px solid #e2e8f0;
}
.card-header {
  padding: 1.25rem 1.5rem;
  background: #f1f5f9;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  gap: 1rem;
}
.card-header h2 { margin: 0; font-size: 1.1rem; font-weight: 600; color: #334155; }
.card-body { padding: 1.5rem; }

/* Forms */
.form-group { margin-bottom: 1.25rem; display: flex; flex-direction: column; gap: 0.5rem; }
.form-group label { font-size: 0.875rem; font-weight: 500; color: #475569; }
input, select {
  padding: 0.75rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 0.95rem;
  transition: border-color 0.2s;
  width: 100%;
  box-sizing: border-box;
}
input:focus, select:focus { outline: none; border-color: #3b82f6; ring: 2px solid #93c5fd; }

.input-with-button { display: flex; gap: 0.5rem; }
.input-with-button input { flex-grow: 1; }

.db-row { display: flex; gap: 0.75rem; align-items: flex-start; margin-bottom: 1rem; }
.flex-grow { flex-grow: 1; }
.compact { width: 150px; flex-shrink: 0; }
.hint { font-size: 0.8rem; color: #94a3b8; }

/* Buttons */
button { border: none; font-family: inherit; cursor: pointer; border-radius: 6px; transition: all 0.2s; }
.primary-btn { background: #2563eb; color: white; font-weight: 600; padding: 0.75rem 1.5rem; }
.primary-btn:hover { background: #1d4ed8; }
.primary-btn:disabled { background: #94a3b8; cursor: not-allowed; }

.secondary-btn { background: #e2e8f0; color: #334155; padding: 0.75rem 1rem; font-weight: 500; white-space: nowrap; }
.secondary-btn:hover { background: #cbd5e1; }

.icon-btn { background: transparent; color: #ef4444; font-size: 1.2rem; padding: 0.5rem; }
.icon-btn:hover { background: #fee2e2; }

.big-btn { width: 100%; font-size: 1.1rem; padding: 1rem; }
.small-btn { padding: 0.5rem 1rem; font-size: 0.9rem; }

/* Toggle Switch */
.toggle-switch { position: relative; width: 44px; height: 24px; }
.toggle-switch input { opacity: 0; width: 0; height: 0; }
.toggle-switch label {
  position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0;
  background-color: #cbd5e1; transition: .4s; border-radius: 34px;
}
.toggle-switch label:before {
  position: absolute; content: ""; height: 18px; width: 18px; left: 3px; bottom: 3px;
  background-color: white; transition: .4s; border-radius: 50%;
}
.toggle-switch input:checked + label { background-color: #3b82f6; }
.toggle-switch input:checked + label:before { transform: translateX(20px); }

/* Footer & Toast */
.app-footer {
  position: sticky; bottom: 0; background: white; padding: 1.5rem;
  border-top: 1px solid #e2e8f0; margin-top: auto;
  display: flex; flex-direction: column; align-items: center; gap: 1rem;
}
.message-toast {
  padding: 0.75rem 1.5rem; border-radius: 8px; font-weight: 500; font-size: 0.95rem; width: 100%; text-align: center;
}
.info { background: #e0f2fe; color: #0369a1; }
.success { background: #dcfce7; color: #15803d; }
.error { background: #fee2e2; color: #b91c1c; }

/* Loading */
.loading-state { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 50vh; color: #64748b; }
.spinner {
  width: 40px; height: 40px; border: 4px solid #e2e8f0; border-top: 4px solid #3b82f6; border-radius: 50%;
  animation: spin 1s linear infinite; margin-bottom: 1rem;
}
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
</style>
