import json
import asyncio
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.models import Crew, Run, Agent, Task, LLMConfig

import litellm
from config import settings
from utils.email import send_workflow_report

# Configure Ollama API base for LiteLLM
import os
os.environ["OLLAMA_API_BASE"] = settings.OLLAMA_API_BASE



class Orchestrator:
    """Motor de orquestación que ejecuta crews de agentes secuencialmente."""

    # Global registry for active execution tasks: {run_id: asyncio.Task}
    _active_tasks: dict[str, asyncio.Task] = {}

    def __init__(self, db: AsyncSession = None):
        self.db = db
        self._ws_connections: dict[str, list] = {}

    async def process_run(self, run_id: str, crew_id: str):
        """Execute all tasks in a crew sequentially (background task) with self-managed session."""
        from db.database import async_session
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        
        async with async_session() as session:
            self.db = session
            
            # Re-fetch objects with the new session
            result = await session.execute(select(Run).where(Run.id == run_id))
            run = result.scalar_one_or_none()
            
            result_crew = await session.execute(
                select(Crew)
                .options(selectinload(Crew.agents), selectinload(Crew.tasks))
                .where(Crew.id == crew_id)
            )
            crew = result_crew.scalar_one_or_none()
            
            if not run or not crew:
                print(f"❌ Error: Run {run_id} or Crew {crew_id} not found in background task.")
                return

            # Register core task for cancellation
            try:
                current_task = asyncio.current_task()
                if current_task:
                    Orchestrator._active_tasks[run.id] = current_task
            except Exception:
                pass

            try:
                # 1. Prepare tasks
                if crew.tasks:
                    sorted_tasks = sorted(crew.tasks, key=lambda t: t.order)
                    task_items = [(task, self._find_agent_for_task(task, crew.agents)) for task in sorted_tasks]
                else:
                    task_items = []
                    for agent in crew.agents:
                        if agent.task_description:
                            v_task = Task(
                                name=f"Tarea de {agent.name}",
                                description=agent.task_description,
                                expected_output=agent.task_expected_output or ""
                            )
                            task_items.append((v_task, agent))

                # 2. Execute tasks
                results = []
                total_tokens = 0

                for task, agent in task_items:
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

                # 3. Finalize run
                final_result = "<br><hr><br>".join(
                    f"## {r['task']}\n**Agente:** {r['agent']}\n\n{r['output']}"
                    for r in results
                )

                run.status = "completed"
                run.result = final_result
                run.tokens_used = total_tokens
                run.cost = self._estimate_cost(total_tokens)
                run.completed_at = datetime.now(timezone.utc)
                run.add_log("🎉 Ejecución completada exitosamente.", level="success")
                
                # Send Email Report if configured
                if crew.output_email:
                    run.add_log(f"📧 Enviando reporte por email a: {crew.output_email}", level="info")
                    await send_workflow_report(crew.output_email, crew.name, final_result)

                await self.db.commit()

            except asyncio.CancelledError:
                run.status = "failed"
                run.result = "Ejecución cancelada por el usuario."
                run.completed_at = datetime.now(timezone.utc)
                run.add_log("🛑 La ejecución fue detenida manualmente.", level="warning")
                await self.db.commit()
                raise
            except Exception as e:
                run.status = "failed"
                run.result = f"Error: {str(e)}"
                run.completed_at = datetime.now(timezone.utc)
                run.add_log(f"❌ Error durante la ejecución: {str(e)}", level="error")
                await self.db.commit()
            finally:
                # Unregister task
                if run.id in Orchestrator._active_tasks:
                    del Orchestrator._active_tasks[run.id]
            
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

        # Handle Web Search Capability
        if getattr(agent, 'web_search_enabled', False):
            try:
                run.add_log(f"🔎 Buscando en la web sobre: {task.description[:50]}...", agent_name=agent.name, level="info")
                from tools.search import search_web
                # Use task description as search query
                search_results = await search_web(task.description[:200]) # Limit query length
                scraping_context += f"\n\n### Resultados de Búsqueda Web:\n{search_results}\n"
            except Exception as e:
                run.add_log(f"⚠️ Error en búsqueda web: {str(e)}", level="warning")

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
            # Check for dynamic LLM configuration
            model_name = agent.llm_model.strip()
            api_base = None
            
            # Query LLMConfig for custom settings using the model identifier
            result = await self.db.execute(select(LLMConfig).where(LLMConfig.model_id == model_name))
            llm_config = result.scalar_one_or_none()
            
            custom_api_key = None
            if llm_config:
                if llm_config.base_url:
                    api_base = llm_config.base_url
                if llm_config.api_key:
                    custom_api_key = llm_config.api_key
                
                # Ensure model name has provider prefix for LiteLLM (e.g., 'ollama/llama3')
                # But only if it doesn't already have a slash (which usually denotes a provider)
                if "/" not in model_name:
                    model_name = f"{llm_config.provider}/{model_name}"
            
            elif model_name.startswith("ollama/"):
                api_base = settings.OLLAMA_API_BASE
            elif "/" not in model_name:
                # Fallback: if no config found and no prefix, default to ollama for local-looking models
                model_name = f"ollama/{model_name}"
                api_base = settings.OLLAMA_API_BASE

            # Build kwargs
            kwargs = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": agent.temperature,
                "max_tokens": int(agent.max_tokens),
            }
            if api_base:
                kwargs["api_base"] = api_base
            if custom_api_key:
                kwargs["api_key"] = custom_api_key

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
    @classmethod
    def stop_run(cls, run_id: str):
        """Cancels a running task by its run_id."""
        task = cls._active_tasks.get(run_id)
        if task:
            task.cancel()
            return True
        return False
