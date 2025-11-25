import os
import json
from typing import Dict, Any, List
from openai import OpenAI
from .browser import (
    launch_browser,
    goto_url,
    get_page_snapshot,
    click_element_by_index,
    scroll_down,
)
from .state_encoder import encode_state_for_llm

client = OpenAI()

SYSTEM_PROMPT = """
Eres un agente experto en navegación web.
Recibes el estado actual de una página (URL, título, texto visible resumido
y una lista de elementos clicables) y un objetivo global.

Debes decidir entre:
- "click": hacer clic en uno de los elementos clicables (target_index obligatorio),
- "scroll": hacer scroll hacia abajo,
- "finish": terminar si el objetivo está cumplido o no merece la pena seguir.

Evita quedarte atrapado en menús repetitivos, navegación infinita
o secciones poco relevantes.

Devuelves SIEMPRE un JSON válido con este esquema y NADA más:

{
  "action": "click" | "scroll" | "finish",
  "reason": "Explicación breve de por qué tomas esta decisión",
  "target_index": <índice del elemento clicable o null>,
  "note_for_extraction": "Qué tipo de información intentas localizar o extraer en el siguiente paso"
}
""".strip()

def call_llm_for_action(snapshot: Dict, goal: str, step: int, max_steps: int) -> Dict:
    """Llama al LLM para decidir la siguiente acción"""
    prompt = encode_state_for_llm(snapshot, goal, step, max_steps)
    model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        content = response.choices[0].message.content.strip()
        
        # Intenta extraer JSON si viene envuelto en markdown
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        data = json.loads(content)
        return data
    except Exception as e:
        return {
            "action": "finish",
            "reason": f"Error al procesar respuesta del modelo: {str(e)}",
            "target_index": None,
            "note_for_extraction": "N/A",
        }

def run_agent(start_url: str, goal: str, max_steps: int = 20) -> Dict[str, Any]:
    """Ejecuta el agente de navegación web"""
    playwright = None
    browser = None
    page = None
    steps_log: List[Dict[str, Any]] = []
    aggregated_content_parts: List[str] = []
    finished_reason = "max_steps_reached"

    try:
        # Lanzar navegador
        playwright, browser, page = launch_browser()
        goto_url(page, start_url)

        for step in range(1, max_steps + 1):
            # Obtener snapshot de la página
            snapshot = get_page_snapshot(page)

            # Acumular texto visible
            visible = snapshot.get("visible_text", "").strip()
            if visible:
                aggregated_content_parts.append(visible)

            # Llamar al LLM para decidir acción
            action_dict = call_llm_for_action(snapshot, goal, step, max_steps)
            action = action_dict.get("action", "finish")
            reason = action_dict.get("reason", "")
            target_index = action_dict.get("target_index")
            note = action_dict.get("note_for_extraction", "")

            # Registrar paso
            steps_log.append(
                {
                    "step": step,
                    "url": snapshot.get("url"),
                    "action": action,
                    "reason": reason,
                    "target_index": target_index,
                    "note_for_extraction": note,
                }
            )

            # Ejecutar acción
            if action == "finish":
                finished_reason = "finish_action"
                break
            elif action == "scroll":
                scroll_down(page)
                page.wait_for_timeout(1000)
            elif action == "click":
                try:
                    if target_index is not None:
                        click_element_by_index(page, snapshot, int(target_index))
                        page.wait_for_timeout(2000)
                    else:
                        steps_log[-1]["reason"] += " (sin target_index, no se hizo click)"
                except Exception as e:
                    steps_log[-1]["reason"] += f" (click fallido: {str(e)})"
            else:
                finished_reason = f"unknown_action_{action}"
                break

        # Determinar razón de finalización
        if len(steps_log) >= max_steps and finished_reason != "finish_action":
            finished_reason = "max_steps_reached"

        # Agregar contenido acumulado
        aggregated_content = "\n\n---\n\n".join(aggregated_content_parts)

        return {
            "start_url": start_url,
            "goal": goal,
            "max_steps": max_steps,
            "steps": steps_log,
            "aggregated_content": aggregated_content,
            "finished_reason": finished_reason,
        }
    
    except Exception as e:
        return {
            "start_url": start_url,
            "goal": goal,
            "max_steps": max_steps,
            "steps": steps_log,
            "aggregated_content": "\n\n---\n\n".join(aggregated_content_parts),
            "finished_reason": f"error: {str(e)}",
        }
    
    finally:
        # Cerrar recursos
        if browser is not None:
            try:
                browser.close()
            except Exception:
                pass
        if playwright is not None:
            try:
                playwright.stop()
            except Exception:
                pass
