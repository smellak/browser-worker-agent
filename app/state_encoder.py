from typing import Dict


def encode_state_for_llm(snapshot: Dict, goal: str, step: int, max_steps: int) -> str:
    """
    Convierte el estado actual de Playwright en un prompt comprensible para el LLM.
    snapshot contiene:
      - url
      - title
      - visible_text
      - clickable_elements (lista de {index, type, text})
    """

    url = snapshot.get("url", "")
    title = snapshot.get("title", "")
    visible_text = snapshot.get("visible_text", "")
    clickable_elements = snapshot.get("clickable_elements", [])

    # Recortar texto visible si es muy largo
    max_chars = 3500
    if len(visible_text) > max_chars:
        visible_text = visible_text[:max_chars] + "\n...[texto truncado]"

    # Listar elementos clicables
    if clickable_elements:
        clickable_list = "\n".join(
            f"{el.get('index')}. ({el.get('type')}) '{el.get('text')[:100]}'"
            for el in clickable_elements
        )
    else:
        clickable_list = "[No se encontraron elementos clicables relevantes]"

    # Construir prompt para el modelo
    prompt = f"""
[ESTADO ACTUAL — PASO {step}/{max_steps}]
URL actual: {url}
Título: {title}

[OBJETIVO GLOBAL]
{goal}

[TEXTO VISIBLE RESUMIDO]
{visible_text}

[ELEMENTOS CLICABLES DETECTADOS]
{clickable_list}

[INSTRUCCIONES PARA EL AGENTE]
Eres un agente experto en navegación web. Debes decidir la siguiente acción para alcanzar el objetivo.
Opciones:
- "click": hacer clic en uno de los elementos (target_index obligatorio)
- "scroll": bajar la página
- "finish": terminar si ya recibiste suficiente información o no hay buenas acciones

Devuelve SOLO un JSON válido con este formato:
{
  "action": "click" | "scroll" | "finish",
  "reason": "Explica por qué eliges esta acción",
  "target_index": <número o null>,
  "note_for_extraction": "Qué información buscas obtener ahora"
}
"""
    return prompt.strip()
