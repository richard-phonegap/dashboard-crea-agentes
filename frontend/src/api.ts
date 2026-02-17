import axios from 'axios'

const api = axios.create({
    baseURL: '/api',
    headers: { 'Content-Type': 'application/json' },
})

// ─── Types ───

export interface Agent {
    id: string
    crew_id: string
    name: string
    role: string
    goal: string
    backstory: string
    llm_model: string
    temperature: number
    max_tokens: number
    position_x: number
    position_y: number
    skills: string
    is_manager: boolean
    task_description?: string
    task_expected_output?: string
    web_search_enabled?: boolean
    created_at: string
}

export interface Task {
    id: string
    crew_id: string
    agent_id: string | null
    name: string
    description: string
    expected_output: string
    order: number
    position_x: number
    position_y: number
    created_at: string
}

export interface Crew {
    id: string
    name: string
    description: string
    process: string
    schedule_type: string
    schedule_value: string | null
    is_public: boolean
    output_email?: string
    canvas_state: string
    agents: Agent[]
    tasks: Task[]
    created_at: string
    updated_at: string
}

export interface CrewListItem {
    id: string
    name: string
    description: string
    process: string
    agent_count: number
    task_count: number
    created_at: string
    updated_at: string
}

export interface Run {
    id: string
    crew_id: string
    status: string
    result: string
    logs: string
    tokens_used: number
    cost: number
    started_at: string | null
    completed_at: string | null
    created_at: string
}

export interface LogEntry {
    timestamp: string
    agent: string
    level: string
    message: string
}

export interface LLMConfig {
    id: string
    name: string
    model_id: string
    provider: string
    base_url?: string
    api_key?: string
    created_at: string
}

export interface MCPServer {
    id: string
    name: string
    command: string
    args: string
    env: string
    created_at: string
}

// ─── API Functions ───

export const crewsApi = {
    list: () => api.get<CrewListItem[]>('/crews').then(r => r.data),
    get: (id: string) => api.get<Crew>(`/crews/${id}`).then(r => r.data),
    create: (data: { name: string; description?: string; process?: string }) =>
        api.post<Crew>('/crews', data).then(r => r.data),
    update: (id: string, data: Partial<Crew>) =>
        api.put<Crew>(`/crews/${id}`, data).then(r => r.data),
    delete: (id: string) => api.delete(`/crews/${id}`),
}

export const agentsApi = {
    create: (crewId: string, data: Partial<Agent>) =>
        api.post<Agent>(`/crews/${crewId}/agents`, data).then(r => r.data),
    update: (crewId: string, agentId: string, data: Partial<Agent>) =>
        api.put<Agent>(`/crews/${crewId}/agents/${agentId}`, data).then(r => r.data),
    delete: (crewId: string, agentId: string) =>
        api.delete(`/crews/${crewId}/agents/${agentId}`),
}

export const tasksApi = {
    create: (crewId: string, data: Partial<Task>) =>
        api.post<Task>(`/crews/${crewId}/tasks`, data).then(r => r.data),
    update: (crewId: string, taskId: string, data: Partial<Task>) =>
        api.put<Task>(`/crews/${crewId}/tasks/${taskId}`, data).then(r => r.data),
    delete: (crewId: string, taskId: string) =>
        api.delete(`/crews/${crewId}/tasks/${taskId}`),
}

export const runsApi = {
    list: (crewId: string) =>
        api.get<Run[]>(`/crews/${crewId}/runs`).then(r => r.data),
    start: (crewId: string) =>
        api.post<Run>(`/crews/${crewId}/runs`).then(r => r.data),
    async get(crewId: string, runId: string): Promise<Run> {
        const res = await api.get(`/crews/${crewId}/runs/${runId}`)
        return res.data
    },
    async stop(crewId: string, runId: string): Promise<any> {
        const res = await api.post(`/crews/${crewId}/runs/${runId}/stop`)
        return res.data
    }
}

export const configApi = {
    listLlms: () => api.get<LLMConfig[]>('/config/llms').then(r => r.data),
    createLlm: (data: Partial<LLMConfig>) => api.post<LLMConfig>('/config/llms', data).then(r => r.data),
    updateLlm: (id: string, data: Partial<LLMConfig>) => api.put<LLMConfig>(`/config/llms/${id}`, data).then(r => r.data),
    deleteLlm: (id: string) => api.delete(`/config/llms/${id}`),

    listMcp: () => api.get<MCPServer[]>('/config/mcp').then(r => r.data),
    createMcp: (data: Partial<MCPServer>) => api.post<MCPServer>('/config/mcp', data).then(r => r.data),
    updateMcp: (id: string, data: Partial<MCPServer>) => api.put<MCPServer>(`/config/mcp/${id}`, data).then(r => r.data),
    deleteMcp: (id: string) => api.delete(`/config/mcp/${id}`),
}

export const llmApi = {
    models: () => api.get<any[]>('/llm-models').then(r => r.data),
}

export default api
