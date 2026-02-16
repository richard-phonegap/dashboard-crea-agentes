import json
import asyncio
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from models.models import Crew, Run, Agent, Task

import litellm
from config import settings

# Configure Ollama API base for LiteLLM
import os
os.environ["OLLAMA_API_BASE"] = settings.OLLAMA_API_BASE


class Orchestrator:
    """Motor de orquestación que ejecuta crews de agentes secuencialmente."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._ws_connections: dict[str, list] = {}

    async def execute_crew(self, crew: Crew) -> Run:
        """Execute all tasks in a crew sequentially."""
        run = Run(
            crew_id=crew.id,
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(run)
        await self.db.commit()
        await self.db.refresh(run)

        try:
            # Sort tasks by order
            sorted_tasks = sorted(crew.tasks, key=lambda t: t.order)
            results = []
            total_tokens = 0

            for task in sorted_tasks:
                agent = self._find_agent_for_task(task, crew.agents)
                if not agent:
                    run.add_log(
                        f"⚠️ Tarea '{task.name}' no tiene agente asignado, usando el primero disponible.",
                        level="warning"
                    )
                    agent = crew.agents[0]

                run.add_log(
                    f"🚀 Iniciando tarea: {task.name}",
                    agent_name=agent.name,
                    level="info"
                )
                await self.db.commit()

                # Execute the task with the assigned agent
                result, tokens = await self._execute_task(task, agent, results, run)

                total_tokens += tokens
                results.append({
                    "task": task.name,
                    "agent": agent.name,
                    "output": result,
                })

                run.add_log(
                    f"✅ Tarea completada: {task.name}",
                    agent_name=agent.name,
                    level="success"
                )
                await self.db.commit()

            # Compile final result
            final_result = "\n\n---\n\n".join(
                f"## {r['task']}\n**Agente:** {r['agent']}\n\n{r['output']}"
                for r in results
            )

            run.status = "completed"
            run.result = final_result
            run.tokens_used = total_tokens
            run.cost = self._estimate_cost(total_tokens)
            run.completed_at = datetime.now(timezone.utc)
            run.add_log("🎉 Ejecución completada exitosamente.", level="success")

        except Exception as e:
            run.status = "failed"
            run.result = f"Error: {str(e)}"
            run.completed_at = datetime.now(timezone.utc)
            run.add_log(f"❌ Error: {str(e)}", level="error")

        await self.db.commit()
        await self.db.refresh(run)
        return run

    async def _execute_task(
        self, task: Task, agent: Agent, previous_results: list[dict], run: Run
    ) -> tuple[str, int]:
        """Execute a single task using an LLM via LiteLLM."""
        # Handle Skills: Web Scraping
        skills_json = agent.skills or "[]"
        scraping_context = ""
        try:
            skills_list = json.loads(skills_json)
            for skill in skills_list:
                if skill.get('type') == 'scraping' and skill.get('target'):
                    url = skill.get('target')
                    run.add_log(f"🌐 Scraping content from: {url}", agent_name=agent.name, level="info")
                    from tools.scraper import scrape_url
                    content = await scrape_url(url)
                    scraping_context += f"\n\n### Contenido extraído de {url}:\n{content[:5000]}\n"
        except Exception as e:
            run.add_log(f"⚠️ Error in skill execution: {str(e)}", level="warning")

        # Build context from previous results
        context = ""
        if previous_results:
            context = "\n\n### Resultados previos:\n" + "\n".join(
                f"- **{r['task']}** ({r['agent']}): {r['output'][:500]}"
                for r in previous_results
            )

        system_prompt = (
            f"Eres {agent.name}, un agente de IA con el siguiente perfil:\n"
            f"**Rol:** {agent.role}\n"
            f"**Objetivo:** {agent.goal}\n"
            f"**Historia:** {agent.backstory}\n"
        )

        # Manager context for hierarchical process
        manager = next((a for a in run.crew.agents if a.is_manager), None)
        if run.crew.process == "hierarchical" and manager and manager.id != agent.id:
            system_prompt += f"\n**Manager del Equipo:** {manager.name} ({manager.role}). Tu trabajo es supervisado por este manager.\n"

        # Append skills context if any
        skills_json = agent.skills or "[]"
        try:
            skills_list = json.loads(skills_json)
            if skills_list:
                skills_text = "\n".join([f"- {s.get('name')}: {s.get('description')}" for s in skills_list])
                system_prompt += f"\n**Habilidades / Herramientas:**\n{skills_text}\n"
        except Exception:
            pass

        system_prompt += "\nDebes completar la tarea con precisión y profesionalismo."
        
        # If the crew is public, suggest JSON output to the agent
        if run.crew.is_public:
            system_prompt += "\n**IMPORTANTE:** Como este es un servicio automatizado, intenta que tu respuesta final sea un objeto JSON válido si la tarea lo permite."

        user_prompt = (
            f"## Tarea: {task.name}\n\n"
            f"{task.description}\n\n"
            f"**Output esperado:** {task.expected_output}\n"
            f"{scraping_context}"
            f"{context}"
        )

        try:
            # Build kwargs, include api_base for Ollama models
            kwargs = {
                "model": agent.llm_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": agent.temperature,
                "max_tokens": int(agent.max_tokens),
            }
            if agent.llm_model.startswith("ollama/"):
                kwargs["api_base"] = settings.OLLAMA_API_BASE

            response = await litellm.acompletion(**kwargs)

            content = response.choices[0].message.content
            tokens = response.usage.total_tokens if response.usage else 0
            return content, tokens

        except Exception as e:
            return f"[Error ejecutando con {agent.llm_model}]: {str(e)}", 0

    def _find_agent_for_task(self, task: Task, agents: list[Agent]) -> Agent | None:
        """Find the agent assigned to a task."""
        if task.agent_id:
            for agent in agents:
                if agent.id == task.agent_id:
                    return agent
        return None

    def _estimate_cost(self, tokens: int) -> float:
        """Rough cost estimation based on token usage."""
        # Approximate cost per 1K tokens (blended input/output)
        return round(tokens * 0.000015, 6)
