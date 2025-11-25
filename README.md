# Browser Worker Agent

Microservicio con Playwright + OpenAI para exploración web autónoma.

Este servicio está pensado para ser llamado desde otra aplicación (por ejemplo, tu interfaz en Replit),
pasándole una URL inicial y un objetivo en lenguaje natural, y devolviendo:

- Los pasos de navegación que ha realizado (clicks, scroll, etc.).
- El contenido de texto que ha ido encontrando durante la exploración.

## Estructura del Proyecto
