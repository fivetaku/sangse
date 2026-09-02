[English](README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | [日本語](README.ja.md) | Español

# sangse (상세) — Generador de páginas de detalle para e-commerce coreano

<p align="center">
  <img src="assets/sangse-hero.png" alt="sangse — ejemplo de corte ancla (producto ficticio)" width="320">
</p>

Un plugin de Claude Code que convierte los datos de un producto en una **hoja de cortes de imagen verificada** — el formato que realmente usan las páginas de detalle del comercio coreano (Kurly, Coupang, Naver Smart Store, tiendas de marca): entre 12 y 20 cortes de imagen apilados verticalmente con el texto renderizado dentro de la imagen, más un bloque legal en HTML.

Ejemplos en vivo (productos ficticios de alimentación saludable): https://fivetaku.github.io/sangse/

## Qué hace

1. **Comprobación de dependencias** — verifica el marketplace gptaku-plugins, `pumasi` (`/pumasi:image`, generación de imágenes con Codex), Playwright y python3; ofrece `--install`.
2. **Entrevista sobre el producto** — pregunta solo por los datos realmente inciertos (público objetivo, plataforma, fuente de tráfico, pruebas, política de devoluciones, categoría regulada), con un máximo de 4 preguntas × 2 rondas.
3. **Revisión de la oferta antes del texto** — una oferta es lo que recibe el cliente + qué preocupación elimina + por qué ahora. Las ofertas débiles se señalan antes de escribir una sola línea.
4. **Hoja de cortes** (`cuts.md` + `legal.md`) — 14 cortes por defecto, ordenados según las 8 preguntas que un cliente se hace en silencio antes de pagar (¿Es para mí → Qué recibo → Por qué de esta forma → Puedo hacerlo → Cuánto cuesta hacerlo → Qué es exactamente → Qué pasa si falla → Por qué ahora). Cada corte = un solo mensaje: titular ≤17 caracteres, ≤3 líneas de cuerpo, color de fondo, brief visual. 29 plantillas de corte medidas a partir de páginas reales (alimentación saludable, moda, servicios). Precios, teléfonos, tablas nutricionales y avisos legales se quedan en HTML.
5. **Verificación en tres puertas**
   - Puerta 1 `check_cuts.py` — determinista: límites de cada campo de la plantilla, cobertura de las preguntas, **cada cifra rastreada hasta la entrada**, palabras prohibidas por categoría, bloques legales, existencia de las imágenes.
   - Puerta 2 — cuatro agentes revisores independientes (cliente objetivo escéptico, examinador regulatorio, revisor de CRO, marketer de la competencia). Se aprueba cuando el cliente responde "sí" a las 8 preguntas y no hay ninguna infracción regulatoria; máximo 2 rondas.
   - Puerta 3 `render_check.py` — renderizado real con Playwright a 390/860 px, más una prueba de 5 segundos sobre la primera pantalla.
6. **Imágenes de los cortes** con `/pumasi:image` — primero el corte ancla, el resto encadenado con `--ref`; cada corte se inspecciona por exactitud del texto **y** verosimilitud del producto (envase sellado, cantidades, dedos).
7. **Ensamblado HTML** — cortes apilados sin separación, bloque legal debajo, Smart Store 860 px / web 720 px.

**Ley de hierro**: no se inventa nada que no esté en la entrada — ni casos, ni cifras, ni reseñas, ni condiciones de devolución, ni plazos. Los huecos se dejan como marcadores `[자료 필요: …]` y se listan en el informe.

## Para quién es (이런 분을 위한 도구입니다)

- Fundadores en solitario y vibe-coders que ya tienen un producto y ahora necesitan una página de detalle que venda, no una ficha técnica.
- Vendedores de Smart Store / Coupang / Kmong que quieren generar y verificar a la vez el texto, las imágenes y el bloque legal.
- Cualquiera que tenga que reescribir una página de producto tipo lista de características en el lenguaje del cliente sin inventar afirmaciones.

## Requisitos (요구사항)

- Claude Code con el marketplace gptaku-plugins; plugin `pumasi` para los cortes de imagen (opcional — sin él, la skill se detiene en el texto + marcadores HTML)
- Codex CLI con sesión iniciada y `image_generation` habilitado (backend de imágenes)
- python3 (las puertas y el ensamblador usan solo la biblioteca estándar)
- Node + Playwright para las comprobaciones de renderizado de la puerta 3 (opcional; `~/.insane-search/node/node_modules` se detecta automáticamente)
- `bash skills/sangse/scripts/check_deps.sh --install` comprueba e instala todo lo anterior

## Instalación

```bash
claude plugin marketplace add fivetaku/gptaku_plugins
claude plugin install sangse@gptaku-plugins
claude plugin install pumasi@gptaku-plugins     # image generation backend
codex features enable image_generation
```

Reinicia la sesión de Claude Code después de instalar. Luego:

```
/sangse <product info as text, a file path, or a URL>
/sangse 카피만 …        # stop after copy approval, no images
```

O simplemente di "상세페이지 만들어줘" — la skill se activa automáticamente.

## Componentes (구성요소)

| Ruta | Función |
|---|---|
| `commands/sangse.md` | Punto de entrada único (`/sangse`), enrutado de argumentos |
| `skills/sangse/SKILL.md` | Flujo de trabajo (Paso 0 comprobación de dependencias → entrevista → revisión de la oferta → hoja de cortes → 3 puertas → imágenes → HTML → informe), Ley de hierro, señales de alerta |
| `skills/sangse/references/` | `framework.md` (las 8 preguntas), `cut-sheet.md`, `reference-patterns.md` (7 páginas reales diseccionadas, 29 plantillas), `interview.md`, `compliance.md`, `verification.md`, `evidence.md`, `image-briefs.md`, `reference-capture.md` |
| `skills/sangse/scripts/` | `check_deps.sh`, `check_cuts.py`, `check_copy.py`, `assemble_html.py`, `render_check.py`, `capture_reference.js` |
| `skills/sangse/assets/` | `cut-templates.json`, `banned-words.json`, `template.html` |
| `setup/` | Configuración de primer arranque (estándar gptaku) |
| `examples/` | Tres productos ficticios con el rastro completo de artefactos y resultados en `qa/` |

## Cumplimiento normativo

`references/compliance.md` contiene filtros detallados para **alimentos y alimentos funcionales** (art. 8 de la Ley de Etiquetado y Publicidad de Alimentos, redacción aprobada de alegaciones funcionales, revisión previa, etiquetas obligatorias, reglas para alegaciones funcionales en alimentos generales) y un índice legal para cosméticos, dispositivos médicos, finanzas, educación, inmobiliaria y electrónica. Los filtros específicos de esas categorías están en desarrollo. Nada de esto constituye asesoramiento legal; la redacción final queda sujeta al organismo de revisión correspondiente.

## Disección de referencias

El formato se derivó capturando páginas de detalle reales en un navegador con interfaz y diseccionándolas corte por corte: Kurly, Coupang y una tienda de marca (el mismo producto de alimentación saludable en tres canales), Samsung.com, LG.com, Musinsa (moda) y Kmong (servicios). Los hallazgos, las mediciones y las 29 plantillas están en `references/reference-patterns.md`; el procedimiento de captura y las trampas propias de cada canal (muro de inicio de sesión de Smart Store, bloqueo de bots de Coupang) están en `references/reference-capture.md` junto con `scripts/capture_reference.js`.

## Registro de cambios

Consulta [CHANGELOG.md](CHANGELOG.md). El procedimiento de publicación (subida de versión → release en GitHub → puntero del submódulo en el marketplace → caché) sigue [gptaku_plugins/PLUGIN_STANDARD.md](https://github.com/fivetaku/gptaku_plugins/blob/main/PLUGIN_STANDARD.md); `tests/test-gates.sh` debe pasar antes de cada subida de versión.

## Licencia (라이선스)

MIT — consulta [LICENSE](LICENSE) y [DISCLAIMER.md](DISCLAIMER.md).
