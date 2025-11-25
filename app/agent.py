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
    prompt = encode_state_for_llm(snapshot, goal, step, max_steps)
    model_name = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    content = response.choices[0].message.content.strip()
    try:
        data = json.loads(content)
        return data
    except Exception:
        return {
            "action": "finish",
            "reason": "Respuesta no JSON válida del modelo",
            "target_index": None,
            "note_for_extraction": "N/A",
        }

def run_agent(start_url: str, goal: str, max_steps: int = 20) -> Dict[str, Any]:
    browser = None
    page = None
    steps_log: List[Dict[str, Any]] = []
    aggregated_content_parts: List[str] = []
    finished_reason = "max_steps_reached"

    try:
        browser, page = launch_browser()
        goto_url(page, start_url)

        for step in range(1, max_steps + 1):
            snapshot = get_page_snapshot(page)

            # acumulamos texto visible
            visible = snapshot.get("visible_text", "").strip()
            if visible:
                aggregated_content_parts.append(visible)

            action_dict = call_llm_for_action(snapshot, goal, step, max_steps)
            action = action_dict.get("action", "finish")
            reason = action_dict.get("reason", "")
            target_index = action_dict.get("target_index")
            note = action_dict.get("note_for_extraction", "")

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

            if action == "finish":
                finished_reason = "finish_action"
                break
            elif action == "scroll":
                scroll_down(page)
            elif action == "click":
                try:
                    if target_index is not None:
                        click_element_by_index(page, snapshot, int(target_index))
                    else:
                        steps_log[-1]["reason"] += " (sin target_index, no se hizo click)"
                except Exception:
                    steps_log[-1]["reason"] += " (click fallido)"
            else:
                finished_reason = f"unknown_action_{action}"
                break

        if len(steps_log) >= max_steps and finished_reason != "finish_action":
            finished_reason = "max_steps_reached"

        aggregated_content = "\n\n---\n\n".join(aggregated_content_parts)

        return {
            "start_url": start_url,
            "goal": goal,
            "max_steps": max_steps,
            "steps": steps_log,
            "aggregated_content": aggregated_content,
            "finished_reason": finished_reason,
        }
    finally:
        if browser is not None:
            browser.close()
