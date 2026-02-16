<template>
  <div class="editor-layout" v-if="crew">
    <!-- Sidebar: Node Palette -->
    <aside class="editor-sidebar">
      <div class="sidebar-header">
        <h3>{{ crew.name }}</h3>
        <button class="btn btn-ghost btn-sm" @click="$router.push('/')">← Volver</button>
      </div>

      <div class="sidebar-section">
        <p class="form-label">Arrastrar al Canvas</p>
        <div class="node-palette">
          <div
            class="palette-item agent"
            draggable="true"
            @dragstart="onDragStart($event, 'agent')"
          >
            <span class="palette-icon">🧠</span>
            <span>Agente</span>
          </div>
          <div
            class="palette-item task"
            draggable="true"
            @dragstart="onDragStart($event, 'task')"
          >
            <span class="palette-icon">📋</span>
            <span>Tarea</span>
          </div>
        </div>
      </div>

      <div class="sidebar-section">
        <p class="form-label">Proceso</p>
            <select class="select" :value="crew.process" @change="updateCrewProperty('process', ($event.target as HTMLSelectElement).value)">
              <option value="sequential">Secuencial</option>
              <option value="hierarchical">Jerárquico</option>
            </select>
      </div>

      <div class="sidebar-section grow">
        <p class="form-label">Resumen</p>
        <div class="summary-stats">
          <div class="summary-stat">
            <span class="stat-num">{{ crew.agents.length }}</span>
            <span class="stat-label">Agentes</span>
          </div>
          <div class="summary-stat">
            <span class="stat-num">{{ crew.tasks.length }}</span>
            <span class="stat-label">Tareas</span>
          </div>
        </div>
      </div>

      <div class="sidebar-actions">
        <button
          class="btn btn-primary"
          style="width: 100%; margin-bottom: 8px;"
          :disabled="crew.agents.length === 0 || crew.tasks.length === 0 || running"
          @click="executeCrew"
        >
          {{ running ? '⏳ Ejecutando...' : '▶️ Ejecutar Equipo' }}
        </button>
        <button
          class="btn btn-secondary"
          style="width: 100%"
          @click="openHistory"
        >
          📋 Historial de Ejecuciones
        </button>
      </div>
    </aside>

    <!-- Main Canvas -->
    <div class="editor-canvas" @drop="onDrop" @dragover.prevent>
      <VueFlow
        :nodes="nodes"
        :edges="edges"
        :default-viewport="{ x: 50, y: 50, zoom: 0.85 }"
        :snap-to-grid="true"
        :snap-grid="[20, 20]"
        @nodes-change="onNodesChange"
        @edges-change="onEdgesChange"
        @connect="onConnect"
        @node-click="onNodeClick"
        fit-view-on-init
        class="vue-flow-canvas"
      >
        <template #node-agent="{ data, id }">
          <div class="custom-node agent-node" :class="{ selected: selectedNodeId === id }">
            <div class="node-header agent">
              <span class="node-type-icon">🧠</span>
              <span class="node-title">{{ data.label }}</span>
              <button class="node-delete" @click.stop="deleteNode(id, 'agent')">×</button>
            </div>
            <div class="node-body">
              <div class="node-field"><span class="field-label">Rol:</span> {{ data.role || 'Sin definir' }}</div>
              <div class="node-field"><span class="field-label">LLM:</span> {{ data.llm_model || 'gpt-4o-mini' }}</div>
            </div>
            <Handle type="source" :position="Position.Right" class="handle-source" />
            <Handle type="target" :position="Position.Left" class="handle-target" />
          </div>
        </template>

        <template #node-task="{ data, id }">
          <div class="custom-node task-node" :class="{ selected: selectedNodeId === id }">
            <div class="node-header task">
              <span class="node-type-icon">📋</span>
              <span class="node-title">{{ data.label }}</span>
              <button class="node-delete" @click.stop="deleteNode(id, 'task')">×</button>
            </div>
            <div class="node-body">
              <div class="node-field truncate"><span class="field-label">Desc:</span> {{ data.description || 'Sin descripción' }}</div>
              <div class="node-field" v-if="data.agent_name">
                <span class="field-label">Agente:</span> {{ data.agent_name }}
              </div>
            </div>
            <Handle type="source" :position="Position.Right" class="handle-source" />
            <Handle type="target" :position="Position.Left" class="handle-target" />
          </div>
        </template>

        <Background :gap="20" :size="1" pattern-color="rgba(255,255,255,0.03)" />
        <MiniMap
          :node-stroke-color="() => 'rgba(255,255,255,0.2)'"
          :node-color="nodeColor"
          :mask-color="'rgba(10, 14, 26, 0.8)'"
        />
        <Controls position="bottom-right" />
      </VueFlow>
    </div>

    <!-- Config Panel -->
    <aside class="config-panel animate-slide-in" v-if="selectedNode || crew">
      <div class="panel-header">
        <h3 v-if="selectedNode">{{ selectedNode.type === 'agent' ? '🧠 Agente' : '📋 Tarea' }}</h3>
        <h3 v-else>⚙️ Configuración del Equipo</h3>
        <button class="btn btn-ghost btn-icon btn-sm" @click="selectedNodeId = null">✕</button>
      </div>

      <div class="panel-tabs" v-if="!selectedNode">
        <button class="menu-item" :class="{ active: activeTab === 'config' }" @click="activeTab = 'config'">⚙️ Config</button>
        <button class="menu-item" :class="{ active: activeTab === 'schedule' }" @click="activeTab = 'schedule'">⏰ Horario</button>
        <button class="menu-item" :class="{ active: activeTab === 'public' }" @click="activeTab = 'public'">🌐 Público</button>
      </div>

      <!-- Config Tab (Crew) -->
      <div v-if="!selectedNode && activeTab === 'config'">
        <div class="panel-body">
          <div class="form-group">
            <label class="form-label">Nombre del Equipo</label>
            <input class="input" v-model="crew.name" @change="updateCrewProperty('name', ($event.target as HTMLInputElement).value)" />
          </div>
          <div class="form-group">
            <label class="form-label">Descripción</label>
            <textarea class="textarea" v-model="crew.description" @change="updateCrewProperty('description', ($event.target as HTMLTextAreaElement).value)" rows="3"></textarea>
          </div>
          <div class="form-group">
            <label class="form-label">Proceso de Ejecución</label>
            <select class="select" v-model="crew.process" @change="updateCrewProperty('process', ($event.target as HTMLSelectElement).value)">
              <option value="sequential">Secuencial — Tareas en orden</option>
              <option value="hierarchical">Jerárquico — Un agente delega</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Scheduling Tab -->
      <div v-if="!selectedNode && activeTab === 'schedule'">
        <div class="panel-body">
          <div class="form-group">
            <label class="form-label">Tipo de Planificación</label>
            <select class="select" v-model="crew.schedule_type" @change="updateCrewProperty('schedule_type', ($event.target as HTMLSelectElement).value)">
              <option value="none">Manual (Sin horario)</option>
              <option value="interval">Intervalo (Minutos)</option>
              <option value="cron">Cron (Expresión)</option>
              <option value="once">Una vez (Fecha)</option>
            </select>
          </div>
          
          <div v-if="crew.schedule_type !== 'none'" class="form-group mt-2">
            <label class="form-label">
              {{ crew.schedule_type === 'interval' ? 'Minutos entre ejecuciones' : 
                 crew.schedule_type === 'cron' ? 'Expresión Cron (ej: 0 * * * *)' : 
                 'Fecha y Hora (ISO)' }}
            </label>
            <input class="input" v-model="crew.schedule_value" @change="updateCrewProperty('schedule_value', ($event.target as HTMLInputElement).value)" :placeholder="crew.schedule_type === 'cron' ? '* * * * *' : ''" />
            <p class="text-xs text-muted mt-1 italic" v-if="crew.schedule_type === 'cron'">
              Minuto Hora Dia Mes DiaSemana
            </p>
          </div>

          <div class="alert alert-info mt-4" v-if="crew.schedule_type !== 'none'">
            <span class="icon">ℹ️</span>
            <p class="text-xs">El equipo se ejecutará en background según la configuración definida.</p>
          </div>
        </div>
      </div>

      <!-- Public Service Tab -->
      <div v-if="!selectedNode && activeTab === 'public'">
        <div class="panel-body">
          <div class="form-group checkbox-group">
            <label class="checkbox-label">
              <input type="checkbox" v-model="crew.is_public" @change="updateCrewProperty('is_public', ($event.target as HTMLInputElement).checked)" />
              <span>Exponer como API Pública</span>
            </label>
          </div>

          <div v-if="crew.is_public" class="public-info mt-4">
            <label class="form-label">Endpoint de Servicio</label>
            <div class="api-endpoint-box">
              <code>/api/v1/services/{{ crew.id }}/run</code>
              <button class="btn btn-ghost btn-xs" @click="copyToClipboard(`/api/v1/services/${crew.id}/run`)">📋</button>
            </div>
            <p class="text-xs text-muted mt-2">
              Cualquier aplicación externa puede ejecutar este equipo llamando a este endpoint vía POST.
            </p>
          </div>
        </div>
      </div>

      <!-- Agent Config -->
      <div class="panel-body" v-if="selectedNode && selectedNode.type === 'agent'">
        <div class="form-group">
          <label class="form-label">Perfil Predeterminado</label>
          <select class="select" @change="applyProfile(($event.target as HTMLSelectElement).value)">
            <option value="">Seleccionar perfil...</option>
            <option v-for="p in agentProfiles" :key="p.name" :value="p.name">{{ p.name }}</option>
          </select>
        </div>
        <div class="form-group checkbox-group">
          <label class="checkbox-label">
            <input type="checkbox" :checked="selectedNode.data.is_manager" @change="updateNodeData('is_manager', ($event.target as HTMLInputElement).checked)" />
            <span :class="{ 'text-purple font-bold': selectedNode.data.is_manager }">
              {{ selectedNode.data.is_manager ? '🌟 Manager del Equipo' : 'Es Manager del Equipo' }}
            </span>
          </label>
        </div>
        <div class="divider"></div>
        <div class="form-group">
          <label class="form-label">Nombre</label>
          <input class="input" :value="selectedNode.data.label" @change="updateNodeData('label', ($event.target as HTMLInputElement).value)" />
        </div>
        <div class="form-group">
          <label class="form-label">Rol</label>
          <div class="role-selector">
            <input class="input" :value="selectedNode.data.role" @change="updateNodeData('role', ($event.target as HTMLInputElement).value)" placeholder="Ej: Investigador Senior" />
            <select class="select select-sm mt-1" @change="updateNodeData('role', ($event.target as HTMLSelectElement).value)">
              <option value="">Roles sugeridos...</option>
              <option value="Investigador Senior">Investigador Senior</option>
              <option value="Analista de Datos">Analista de Datos</option>
              <option value="Redactor Creativo">Redactor Creativo</option>
              <option value="Especialista SEO">Especialista SEO</option>
              <option value="Project Manager">Project Manager</option>
              <option value="QA Engineer">QA Engineer</option>
            </select>
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">Objetivo</label>
          <textarea class="textarea" :value="selectedNode.data.goal" @change="updateNodeData('goal', ($event.target as HTMLTextAreaElement).value)" placeholder="¿Qué debe lograr este agente?" rows="3"></textarea>
        </div>
        <div class="form-group">
          <label class="form-label">Backstory</label>
          <textarea class="textarea" :value="selectedNode.data.backstory" @change="updateNodeData('backstory', ($event.target as HTMLTextAreaElement).value)" placeholder="Historia y experiencia del agente..." rows="3"></textarea>
        </div>
        <div class="form-group">
          <label class="form-label">Modelo LLM</label>
          <select class="select" :value="selectedNode.data.llm_model" @change="updateNodeData('llm_model', ($event.target as HTMLSelectElement).value)">
            <option v-for="m in llmModels" :key="m.id" :value="m.id">{{ m.name }}</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Temperatura: {{ selectedNode.data.temperature }}</label>
          <input type="range" min="0" max="1" step="0.1" class="range-input"
            :value="selectedNode.data.temperature"
            @input="updateNodeData('temperature', parseFloat(($event.target as HTMLInputElement).value))"
          />
        </div>

        <!-- Skills Section -->
        <div class="divider"></div>
        <div class="form-group">
          <label class="form-label">Habilidades (Skills)</label>
          <div class="skills-list">
            <div v-for="(skill, index) in agentSkills" :key="index" class="skill-item">
              <div class="skill-info">
                <strong>{{ skill.name }}</strong>
                <p v-if="skill.target">{{ skill.target }}</p>
              </div>
              <button class="btn btn-ghost btn-sm btn-icon" @click="removeSkill(Number(index))">🗑️</button>
            </div>
            <div v-if="agentSkills.length === 0" class="text-xs text-muted italic">Sin habilidades configuradas</div>
          </div>
          
          <div class="add-skill-box">
            <select class="select select-sm" v-model="newSkillType">
              <option value="">+ Agregar habilidad...</option>
              <option value="scraping">Web Scraping</option>
              <option value="mcp">MCP Connection</option>
              <option value="custom">Personalizada</option>
            </select>
            <div v-if="newSkillType" class="skill-params mt-2">
              <input v-if="newSkillType === 'scraping'" class="input input-sm" placeholder="URL a scrapear..." v-model="newSkillTarget" />
              <input v-if="newSkillType === 'mcp'" class="input input-sm" placeholder="Servidor MCP..." v-model="newSkillTarget" />
              <input v-if="newSkillType === 'custom'" class="input input-sm" placeholder="Nombre de habilidad..." v-model="newSkillName" />
              <button class="btn btn-primary btn-sm mt-1 w-full" @click="addSkill">Agregar</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Task Config -->
      <div class="panel-body" v-else-if="selectedNode && selectedNode.type === 'task'">
        <div class="form-group">
          <label class="form-label">Nombre</label>
          <input class="input" :value="selectedNode.data.label" @change="updateNodeData('label', ($event.target as HTMLInputElement).value)" />
        </div>
        <div class="form-group">
          <label class="form-label">Descripción</label>
          <textarea class="textarea" :value="selectedNode.data.description" @change="updateNodeData('description', ($event.target as HTMLTextAreaElement).value)" placeholder="Describe la tarea en detalle..." rows="4"></textarea>
        </div>
        <div class="form-group">
          <label class="form-label">Output Esperado</label>
          <textarea class="textarea" :value="selectedNode.data.expected_output" @change="updateNodeData('expected_output', ($event.target as HTMLTextAreaElement).value)" placeholder="¿Qué formato y contenido se espera?" rows="3"></textarea>
        </div>
        <div class="form-group">
          <label class="form-label">Agente Asignado</label>
          <select class="select"
            :value="selectedNode.data.agent_id || ''"
            @change="assignAgent(($event.target as HTMLSelectElement).value)"
          >
            <option value="">Sin asignar</option>
            <option v-for="a in crew.agents" :key="a.id" :value="a.id">{{ a.name }}</option>
          </select>
        </div>
      </div>

      <div class="panel-footer" v-if="selectedNode">
        <button class="btn btn-danger btn-sm" @click="deleteNode(selectedNodeId!, selectedNode.type!)">
          🗑️ Eliminar
        </button>
      </div>
    </aside>

    <!-- Run Result Modal -->
    <div v-if="runResult" class="modal-overlay" @click.self="runResult = null">
      <div class="modal result-modal animate-fade-in">
        <div class="result-header">
          <h2>{{ runResult.status === 'completed' ? '✅ Ejecución Completada' : '❌ Error' }}</h2>
          <button class="btn btn-ghost btn-icon" @click="runResult = null">✕</button>
        </div>
        <div class="result-meta">
          <span class="badge" :class="runResult.status === 'completed' ? 'badge-success' : 'badge-error'">{{ runResult.status }}</span>
          <span class="text-sm text-muted">{{ runResult.tokens_used }} tokens · ${{ runResult.cost?.toFixed(4) }}</span>
        </div>
        <div class="result-logs">
          <h3>📋 Logs</h3>
          <div class="log-entries">
            <div v-for="(log, i) in parsedLogs" :key="i" class="log-entry" :class="'log-' + log.level">
              <span class="log-time">{{ formatTime(log.timestamp) }}</span>
              <span class="log-agent" v-if="log.agent">{{ log.agent }}</span>
              <span class="log-msg">{{ log.message }}</span>
            </div>
          </div>
        </div>
        <div class="result-output" v-if="runResult.result">
          <h3>📄 Resultado</h3>
          <div class="output-content" v-html="renderMarkdown(runResult.result)"></div>
        </div>
      </div>
    </div>
  </div>

  <!-- Loading -->
  <div v-else class="loading-state">
    <div class="animate-pulse">⚡ Cargando editor...</div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { VueFlow, Position, Handle } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { MiniMap } from '@vue-flow/minimap'
import { Controls } from '@vue-flow/controls'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import '@vue-flow/minimap/dist/style.css'
import '@vue-flow/controls/dist/style.css'
import { marked } from 'marked'

import {
  crewsApi, agentsApi, tasksApi, runsApi, llmApi,
  type Crew, type Agent, type Task, type Run, type LLMModel, type LogEntry,
} from '../api'

const route = useRoute()
const router = useRouter()

const crew = ref<Crew | null>(null)
const nodes = ref<any[]>([])
const edges = ref<any[]>([])
const selectedNodeId = ref<string | null>(null)
const llmModels = ref<LLMModel[]>([])
const running = ref(false)
const runResult = ref<Run | null>(null)
const activeTab = ref('config') // 'config', 'schedule', 'public'

// Skills & Profiles logic
const newSkillType = ref('')
const newSkillTarget = ref('')
const newSkillName = ref('')

const agentProfiles = [
  { name: 'Investigador Web', role: 'Experto en búsqueda y extracción de datos web', goal: 'Extraer información relevante de sitios web y documentarla.' },
  { name: 'Analista de Datos', role: 'Científico de datos especializado en análisis estadístico', goal: 'Procesar datos complejos y generar insights accionables.' },
  { name: 'Redactor de Contenido', role: 'Copywriter creativo y editor', goal: 'Generar contenido de alta calidad, atractivo y bien estructurado.' },
  { name: 'MCP Connector', role: 'Intermediario de protocolos de contexto de modelo', goal: 'Conectarse a servidores MCP y facilitar el intercambio de información.' },
]

const agentSkills = computed(() => {
  if (!selectedNode.value || selectedNode.value.type !== 'agent') return []
  const skillsJson = selectedNode.value.data.skills || '[]'
  try { return JSON.parse(skillsJson) } catch { return [] }
})

const selectedNode = computed(() => {
  if (!selectedNodeId.value) return null
  return nodes.value.find(n => n.id === selectedNodeId.value) || null
})

const parsedLogs = computed<LogEntry[]>(() => {
  if (!runResult.value?.logs) return []
  try { return JSON.parse(runResult.value.logs) } catch { return [] }
})

onMounted(async () => {
  llmModels.value = await llmApi.models()

  const crewId = route.params.id as string
  if (crewId) {
    await loadCrew(crewId)
  } else {
    // Create a new crew
    const newCrew = await crewsApi.create({ name: 'Nuevo Equipo' })
    router.replace(`/editor/${newCrew.id}`)
    await loadCrew(newCrew.id)
  }
})

async function loadCrew(id: string) {
  crew.value = await crewsApi.get(id)
  buildNodesFromCrew()
}

function buildNodesFromCrew() {
  if (!crew.value) return

  const newNodes: any[] = []
  const newEdges: any[] = []

  crew.value.agents.forEach((a) => {
    newNodes.push({
      id: a.id,
      type: 'agent',
      position: { x: a.position_x, y: a.position_y },
      data: {
        label: a.name,
        role: a.role,
        goal: a.goal,
        backstory: a.backstory,
        llm_model: a.llm_model,
        temperature: a.temperature,
        skills: a.skills,
        is_manager: a.is_manager,
        dbId: a.id,
      },
    })
  })

  crew.value.tasks.forEach((t) => {
    const agentName = crew.value!.agents.find(a => a.id === t.agent_id)?.name
    newNodes.push({
      id: t.id,
      type: 'task',
      position: { x: t.position_x, y: t.position_y },
      data: {
        label: t.name,
        description: t.description,
        expected_output: t.expected_output,
        agent_id: t.agent_id,
        agent_name: agentName,
        order: t.order,
        dbId: t.id,
      },
    })

    // Auto-create edge from agent to task
    if (t.agent_id) {
      newEdges.push({
        id: `e-${t.agent_id}-${t.id}`,
        source: t.agent_id,
        target: t.id,
        animated: true,
        style: { stroke: 'var(--accent-primary)', strokeWidth: 2 },
      })
    }
  })

  nodes.value = newNodes
  edges.value = newEdges
}

function onDragStart(event: DragEvent, nodeType: string) {
  if (event.dataTransfer) {
    event.dataTransfer.setData('nodeType', nodeType)
    event.dataTransfer.effectAllowed = 'move'
  }
}

async function onDrop(event: DragEvent) {
  if (!event.dataTransfer || !crew.value) return
  const nodeType = event.dataTransfer.getData('nodeType')
  if (!nodeType) return

  const canvasRect = (event.currentTarget as HTMLElement).getBoundingClientRect()
  const x = event.clientX - canvasRect.left - 80
  const y = event.clientY - canvasRect.top - 20

  if (nodeType === 'agent') {
    const count = crew.value.agents.length + 1
    const agent = await agentsApi.create(crew.value.id, {
      name: `Agente ${count}`,
      role: 'Define el rol...',
      goal: 'Define el objetivo...',
      backstory: '',
      position_x: x,
      position_y: y,
    })
    crew.value.agents.push(agent)
    buildNodesFromCrew()
    selectedNodeId.value = agent.id
  } else if (nodeType === 'task') {
    const count = crew.value.tasks.length + 1
    const task = await tasksApi.create(crew.value.id, {
      name: `Tarea ${count}`,
      description: 'Describe la tarea...',
      expected_output: '',
      order: count,
      position_x: x,
      position_y: y,
    })
    crew.value.tasks.push(task)
    buildNodesFromCrew()
    selectedNodeId.value = task.id
  }
}

function onNodesChange(changes: any[]) {
  // Handle position updates
  for (const change of changes) {
    if (change.type === 'position' && change.position && !change.dragging && crew.value) {
      const nodeType = nodes.value.find(n => n.id === change.id)?.type
      if (nodeType === 'agent') {
        agentsApi.update(crew.value.id, change.id, {
          position_x: change.position.x,
          position_y: change.position.y,
        }).catch(() => {})
      } else if (nodeType === 'task') {
        tasksApi.update(crew.value.id, change.id, {
          position_x: change.position.x,
          position_y: change.position.y,
        }).catch(() => {})
      }
    }
  }
}

function onEdgesChange(_changes: any[]) {}

async function onConnect(event: any) {
  if (!crew.value) return
  const sourceNode = nodes.value.find(n => n.id === event.source)
  const targetNode = nodes.value.find(n => n.id === event.target)

  // Connect agent → task
  if (sourceNode?.type === 'agent' && targetNode?.type === 'task') {
    await tasksApi.update(crew.value.id, event.target, { agent_id: event.source })
    const task = crew.value.tasks.find(t => t.id === event.target)
    if (task) task.agent_id = event.source
    buildNodesFromCrew()
  }
}

function onNodeClick(event: { node: any }) {
  selectedNodeId.value = event.node.id
}

async function updateNodeData(field: string, value: any) {
  if (!selectedNodeId.value || !crew.value) return
  const node = selectedNode.value
  if (!node) return

  // Update local node data
  node.data = { ...node.data, [field]: value }

  // Persist to backend
  const fieldMap: Record<string, string> = { label: 'name' }
  const backendField = fieldMap[field] || field

  if (node.type === 'agent') {
    await agentsApi.update(crew.value.id, node.id, { [backendField]: value })
    const a = crew.value.agents.find(ag => ag.id === node.id)
    if (a) (a as any)[backendField] = value
  } else if (node.type === 'task') {
    await tasksApi.update(crew.value.id, node.id, { [backendField]: value })
    const t = crew.value.tasks.find(ta => ta.id === node.id)
    if (t) (t as any)[backendField] = value
  }
}

async function assignAgent(agentId: string) {
  if (!selectedNodeId.value || !crew.value) return
  const aid = agentId || null
  await tasksApi.update(crew.value.id, selectedNodeId.value, { agent_id: aid } as any)
  const t = crew.value.tasks.find(ta => ta.id === selectedNodeId.value)
  if (t) t.agent_id = aid
  buildNodesFromCrew()
}

async function deleteNode(id: string, type: string) {
  if (!crew.value) return
  if (type === 'agent') {
    await agentsApi.delete(crew.value.id, id)
    crew.value.agents = crew.value.agents.filter(a => a.id !== id)
  } else {
    await tasksApi.delete(crew.value.id, id)
    crew.value.tasks = crew.value.tasks.filter(t => t.id !== id)
  }
  selectedNodeId.value = null
  buildNodesFromCrew()
}

function applyProfile(profileName: string) {
  const profile = agentProfiles.find(p => p.name === profileName)
  if (!profile) return
  updateNodeData('role', profile.role)
  updateNodeData('goal', profile.goal)
  updateNodeData('label', profile.name)
}

async function addSkill() {
  if (!selectedNode.value || !newSkillType.value) return
  
  const skillName = newSkillType.value === 'scraping' ? 'Web Scraping' : 
                    newSkillType.value === 'mcp' ? 'MCP Connection' : 
                    newSkillName.value || 'Nueva Habilidad'
                    
  const newSkill = {
    type: newSkillType.value,
    name: skillName,
    target: newSkillTarget.value,
    description: `Habilidad de ${skillName}` + (newSkillTarget.value ? ` en ${newSkillTarget.value}` : '')
  }
  
  const currentSkills = [...agentSkills.value, newSkill]
  await updateNodeData('skills', JSON.stringify(currentSkills))
  
  // Reset fields
  newSkillType.value = ''
  newSkillTarget.value = ''
  newSkillName.value = ''
}

async function removeSkill(index: number) {
  const currentSkills = [...agentSkills.value]
  currentSkills.splice(index, 1)
  await updateNodeData('skills', JSON.stringify(currentSkills))
}

async function updateCrewProperty(field: string, value: any) {
  if (!crew.value) return
  // Update local crew data
  ;(crew.value as any)[field] = value

  // Persist to backend
  await crewsApi.update(crew.value.id, { [field]: value })
}

function copyToClipboard(text: string) {
  const fullUrl = window.location.origin + text
  navigator.clipboard.writeText(fullUrl)
  alert('Copiado al portapapeles: ' + fullUrl)
}

function openHistory() {
  if (crew.value) {
    router.push(`/history/${crew.value.id}`)
  }
}

async function executeCrew() {
  if (!crew.value || running.value) return
  running.value = true
  try {
    const run = await runsApi.start(crew.value.id)
    runResult.value = run
  } catch (e) {
    console.error('Execution error:', e)
  } finally {
    running.value = false
  }
}

function nodeColor(node: any) {
  return node.type === 'agent' ? '#6c5ce7' : '#00cec9'
}

function formatTime(ts: string) {
  return new Date(ts).toLocaleTimeString('es', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

function renderMarkdown(text: string) {
  return marked.parse(text) as string
}
</script>

<style scoped>
.editor-layout {
  display: flex;
  height: 100%;
  overflow: hidden;
}

/* ─── Sidebar ─── */
.editor-sidebar {
  width: var(--sidebar-width);
  background: var(--bg-secondary);
  border-right: 1px solid rgba(255, 255, 255, 0.06);
  display: flex;
  flex-direction: column;
  padding: 16px;
  gap: 20px;
  flex-shrink: 0;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.sidebar-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.node-palette {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.palette-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: var(--radius-sm);
  cursor: grab;
  font-size: 13px;
  font-weight: 500;
  transition: all var(--transition-fast);
  border: 1px dashed;
}
.palette-item:active {
  cursor: grabbing;
}
.palette-item.agent {
  background: var(--node-agent-bg);
  border-color: var(--node-agent-border);
  color: var(--node-agent);
}
.palette-item.agent:hover {
  background: rgba(108, 92, 231, 0.15);
  box-shadow: var(--shadow-glow-purple);
}
.palette-item.task {
  background: var(--node-task-bg);
  border-color: var(--node-task-border);
  color: var(--node-task);
}
.palette-item.task:hover {
  background: rgba(0, 206, 201, 0.15);
  box-shadow: var(--shadow-glow-teal);
}

.palette-icon {
  font-size: 18px;
}

.summary-stats {
  display: flex;
  gap: 12px;
}

.summary-stat {
  flex: 1;
  background: var(--bg-card);
  border-radius: var(--radius-sm);
  padding: 12px;
  text-align: center;
}

.stat-num {
  display: block;
  font-size: 22px;
  font-weight: 700;
  color: var(--accent-primary);
}

.stat-label {
  font-size: 11px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.sidebar-actions {
  padding-top: 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

/* ─── Canvas ─── */
.editor-canvas {
  flex: 1;
  position: relative;
  background: var(--bg-primary);
}

.vue-flow-canvas {
  width: 100%;
  height: 100%;
}

/* ─── Custom Nodes ─── */
.custom-node {
  min-width: 200px;
  max-width: 260px;
  border-radius: var(--radius-md);
  overflow: hidden;
  box-shadow: var(--shadow-md);
  transition: all var(--transition-fast);
  border: 1.5px solid transparent;
}
.custom-node:hover {
  transform: scale(1.02);
}
.custom-node.selected {
  border-color: var(--accent-primary);
  box-shadow: var(--shadow-glow-purple);
}

.node-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  font-size: 13px;
  font-weight: 600;
  position: relative;
}
.node-header.agent {
  background: var(--node-agent);
  color: white;
}
.node-header.task {
  background: var(--node-task);
  color: white;
}

.node-type-icon { font-size: 14px; }
.node-title { flex: 1; }

.node-delete {
  background: rgba(255,255,255,0.2);
  border: none;
  color: white;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity var(--transition-fast);
}
.custom-node:hover .node-delete { opacity: 1; }
.node-delete:hover { background: rgba(255,255,255,0.35); }

.node-body {
  padding: 10px 12px;
  background: var(--bg-card);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.node-field {
  font-size: 11px;
  color: var(--text-secondary);
  line-height: 1.4;
}

.field-label {
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  font-size: 10px;
}

.agent-node { border-color: var(--node-agent-border); }
.task-node { border-color: var(--node-task-border); }

/* Handles */
.handle-source, .handle-target {
  width: 10px !important;
  height: 10px !important;
  border: 2px solid var(--accent-primary) !important;
  background: var(--bg-card) !important;
}
.handle-source:hover, .handle-target:hover {
  background: var(--accent-primary) !important;
}

/* ─── Config Panel ─── */
.config-panel {
  width: var(--panel-width);
  background: var(--bg-secondary);
  border-left: 1px solid rgba(255, 255, 255, 0.06);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  overflow-y: auto;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.panel-body {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex: 1;
}

.panel-footer {
  padding: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.range-input {
  width: 100%;
  accent-color: var(--accent-primary);
  cursor: pointer;
}

/* ─── Profiles & Skills ─── */
.divider {
  height: 1px;
  background: rgba(255, 255, 255, 0.06);
  margin: 8px 0;
}

.skills-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.skill-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: var(--radius-sm);
}

.skill-info {
  flex: 1;
}

.skill-info strong {
  display: block;
  font-size: 11px;
  color: var(--text-primary);
}

.skill-info p {
  font-size: 10px;
  color: var(--text-muted);
  margin: 2px 0 0 0;
  word-break: break-all;
}

.add-skill-box {
  background: rgba(255, 255, 255, 0.02);
  padding: 10px;
  border-radius: var(--radius-sm);
  border: 1px dashed rgba(255, 255, 255, 0.1);
}

.mt-2 { margin-top: 8px; }
.mt-1 { margin-top: 4px; }
.w-full { width: 100%; }

.checkbox-group {
  margin: 12px 0;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 13px;
  color: var(--text-primary);
}

.checkbox-label input[type="checkbox"] {
  width: 16px;
  height: 16px;
  accent-color: var(--accent-primary);
}

.api-endpoint-box {
  background: rgba(0, 0, 0, 0.2);
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  border: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.api-endpoint-box code {
  font-family: monospace;
  font-size: 11px;
  color: var(--accent-primary);
  word-break: break-all;
}

.alert-info {
  background: var(--accent-primary-glow);
  border: 1px solid var(--accent-primary);
  padding: 10px;
  border-radius: var(--radius-sm);
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

/* ─── Result Modal ─── */
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

.result-modal {
  width: 700px;
  max-width: 90vw;
  max-height: 85vh;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.result-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.result-logs, .result-output {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.log-entries {
  background: var(--bg-input);
  border-radius: var(--radius-sm);
  padding: 12px;
  max-height: 200px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
  font-family: 'SF Mono', 'Fira Code', monospace;
}

.log-entry {
  display: flex;
  gap: 8px;
  align-items: baseline;
  padding: 2px 0;
}

.log-time {
  color: var(--text-muted);
  flex-shrink: 0;
}

.log-agent {
  color: var(--accent-primary);
  font-weight: 600;
  flex-shrink: 0;
}

.log-msg { color: var(--text-primary); }
.log-success .log-msg { color: var(--color-success); }
.log-error .log-msg { color: var(--color-error); }
.log-warning .log-msg { color: var(--color-warning); }

.output-content {
  background: var(--bg-input);
  border-radius: var(--radius-sm);
  padding: 16px;
  line-height: 1.7;
  font-size: 13px;
}

.output-content :deep(h2) {
  margin-top: 16px;
  font-size: 16px;
}

.output-content :deep(p) {
  margin: 8px 0;
}

/* ─── Loading ─── */
.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  font-size: 18px;
  color: var(--text-secondary);
}
</style>
