# Reglas del hackathon (verificadas)

**Verificado el 22 de octubre de 2026** en las páginas oficiales de AWS Builder Center. **El texto completo de las reglas
(pestaña *Rules*) no se pudo leer** desde fuera del navegador: lo que sigue sale de la página del evento y de dos
publicaciones oficiales. Las exclusiones por país y empleados **siguen sin verificarse** y debe revisarlas una persona en la
pestaña *Rules*.

Fuentes:
- [Agent Experience Hackathon: Strands Decider](https://builder.aws.com/build/hackathons/4f50957c-1d08-37ab-b11c-97516b9adeb4/agent-experience-hackathon) (página del evento)
- [Reglas (pestaña Rules)](https://builder.aws.com/build/hackathons/4f50957c-1d08-37ab-b11c-97516b9adeb4/agent-experience-hackathon?tab=rules)
- [Resumen: AWS Strands Decider 2B Hackathon, win $5,000 in credits](https://builder.aws.com/content/3KbRaXAR4Zoch6AR3ZjnLaYY3JG/aws-strands-decider-2b-hackathon-win-dollar5000-in-credits)
- [Decider 2B alojado por la comunidad (no es un producto de AWS)](https://builder.aws.com/content/3Ks9uHwd7uxGglJbLXmzB7l6Xed/strands-decider-2b-hosted-16-million-tokens-served-to-100-builders-2000-free-decisions-a-month-and-a-zero-downtime-fix-on-air)

## Fechas (hora del Pacífico)
- **Entrega: 23 de octubre de 2026, 11:59 PM PDT** (= 12:59 AM del sábado 24 en Guatemala).
- Resultados de la primera ronda: semana del 26 de octubre; segunda ronda: semana del 2 de noviembre; ganadores: semana del 9 de noviembre.

## Qué exige una entrega
| Requisito | Cómo estamos |
|---|---|
| Un agente **original** (no publicado antes) que use **Decider 2B en al menos una decisión significativa**, **junto con Amazon Bedrock para la parte generativa** | Decider real: sí. **Bedrock: no** (AWS denegó las cuotas; el agente corre con un modelo local) |
| **Artículo** en Builder Center que describa el agente y la decisión que se le deja a Decider 2B | Falta |
| **Repositorio público** con el código y **al menos un patrón de decisión reutilizable**: pregunta tipada con sus opciones, el cableado en la ruta del agente (por ejemplo un `InterventionHandler` de Strands) y una **nota de uso corta** | Código y cableado: sí (`agentshield/`). **Nota de uso: falta** |
| **Licencia** de código abierto aprobada | Apache 2.0 |
| **Video público de menos de 3 minutos** que muestre el agente y la decisión, **incluida la puntuación de confianza** | Falta grabarlo. La consola muestra las cuatro respuestas del Decider |
| **Dos etiquetas**: `#strands-decider-2b` y **una** de patrón (`#tool-selection`, `#guardrails`, `#policy`, `#model-routing`, `#context-memory`) | Etiquetas: `#strands-decider-2b` y `#guardrails` |
| **Declarar un patrón** | Guardrails |

Elegibilidad: mayores de 18 años con perfil de Builder Center. **Exclusiones por país y empleados: ver la pestaña *Rules***.
Tamaño de equipo: la página no lo dice.

## Cómo se puntúa
| Criterio | Peso |
|---|---|
| Creatividad y "factor wow" | 30 % |
| **Uso efectivo de Decider 2B** (incluye la calidad del patrón) | 30 % |
| Calidad de la comunicación | 25 % |
| Originalidad | 15 % |

Dos rondas: una primera con puntuación automática y humana (pasan las 100 mejores) y un panel de expertos de AWS que elige
tres ganadores. **Bonus (no obligatorio):** una mejora **medida** de latencia o costo al sacar una decisión del LLM cuenta
dentro de "uso efectivo".

## Lo que NO pide la página oficial (y nuestros documentos internos asumían)
- No exige **subtítulos en inglés** en el video ni fija el idioma del artículo. Conviene hacerlos de todos modos.
- No describe cómo obtener **cuota de Bedrock ni créditos**: los únicos créditos mencionados son el premio.

## Recurso disponible: Decider 2B alojado por la comunidad
Servicio **no oficial** (`awsugmdu.in`): llave de equipo, `/v1/decide` con el mismo formato tipado y 2,000 decisiones al mes
gratis (10 solicitudes por minuto). Ofrece también un LLM alojado para el agente, pero **la publicación aclara que Bedrock
sigue siendo obligatorio para la entrega**. No sustituye a Bedrock.
