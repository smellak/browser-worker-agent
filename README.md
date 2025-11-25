# Browser Worker Agent

Microservicio con Playwright + OpenAI para exploración web autónoma.

Este servicio está pensado para ser llamado desde otra aplicación (por ejemplo, tu interfaz en Replit),
pasándole una URL inicial y un objetivo en lenguaje natural, y devolviendo:

- Los pasos de navegación que ha realizado (clicks, scroll, etc.).
- El contenido de texto que ha ido encontrando durante la exploración.

## Estructura del Proyecto


proyecto/
├── app/
│ ├── init.py
│ ├── main.py # API FastAPI
│ ├── agent.py # Lógica del agente
│ ├── browser.py # Funciones de Playwright
│ └── state_encoder.py # Codificación de estado para LLM
├── requirements.txt
├── render.yaml
└── README.md

clean

## Uso

### Endpoint principal: POST /run-agent

```json
{
  "url": "https://example.com",
  "goal": "Encuentra información sobre precios",
  "max_steps": 20
}

Respuesta
json
{
  "start_url": "https://example.com",
  "goal": "Encuentra información sobre precios",
  "max_steps": 20,
  "steps": [...],
  "aggregated_content": "...",
  "finished_reason": "finish_action"
}
