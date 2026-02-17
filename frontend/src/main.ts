import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import './styles/globals.css'

const router = createRouter({
    history: createWebHistory(),
    routes: [
        { path: '/', component: () => import('./views/Dashboard.vue') },
        { path: '/editor/:id?', component: () => import('./views/Editor.vue') },
        { path: '/history/:id', component: () => import('./views/History.vue') },
        { path: '/monitor/:runId', component: () => import('./views/Monitor.vue') },
        { path: '/settings', component: () => import('./views/Settings.vue') },
    ],
})

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
