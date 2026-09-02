[English](README.md) | [한국어](README.ko.md) | [中文](README.zh.md) | [日本語](README.ja.md) | Español

# sangse (상세)

<p align="center">
  <img src="assets/sangse-hero-01.png" alt="sangse" width="320">
</p>

> **Convierte un producto en una página de detalle que vende — una hoja de cortes de imagen verificada, no una ficha técnica.**

Dale los datos del producto. Recibe el formato que el comercio coreano usa de verdad: 12~20 cortes de imagen apilados verticalmente con el copy dentro de la imagen, más un bloque legal en HTML — cada afirmación rastreada hasta tu input.

[Inicio rápido](#inicio-rápido) • [¿Por qué sangse?](#por-qué-sangse-이런-분을-위한-도구입니다) • [Cómo funciona](#cómo-funciona) • [Características](#características) • [Requisitos](#requisitos-요구사항)

Ejemplos en vivo (productos ficticios de alimentación saludable): https://fivetaku.github.io/sangse/

---

## Inicio rápido

### 1. Añade el marketplace (una sola vez)

```
/plugin marketplace add https://github.com/fivetaku/gptaku_plugins.git
```

### 2. Instala

```
/plugin install sangse
/plugin install pumasi          # backend de generación de imágenes (/pumasi:image)
```

Reinicia Claude Code después de la instalación.

### 3. Activa el backend de imágenes

```bash
codex features enable image_generation
```

### 4. Ejecuta

```
/sangse <información del producto como texto, ruta de archivo o URL>
/sangse 카피만 <información del producto>        # se detiene tras aprobar el copy, sin imágenes
/sangse check sangse/<slug>          # vuelve a ejecutar las puertas de verificación sobre una carpeta existente
```

O simplemente dilo — "상세페이지 만들어줘", "haz una página de detalle para este producto".

---

## ¿Por qué sangse? (이런 분을 위한 도구입니다)

- **Construiste un producto, no una página de ventas** — fundadores en solitario y vibe-coders que necesitan una página de detalle que convierta, no una lista de funciones.
- **Vendes en Kurly, Coupang o Naver Smart Store** — el resultado es la hoja de cortes de imagen que esos canales usan de verdad, dimensionada para subirla (Smart Store 860 px / web 720 px).
- **Necesitas que el copy, las imágenes y el bloque legal se verifiquen juntos** — tres puertas detectan desbordes de plantilla, números sin rastrear, afirmaciones prohibidas y etiquetas obligatorias ausentes antes de publicar.
- **No aceptarás afirmaciones inventadas** — la Ley de Hierro: nada que no esté en el input se escribe. Los huecos se convierten en marcadores `[자료 필요: …]` y en una tabla de pendientes.

---

## Cómo funciona

```
datos del producto (texto / archivo / URL)
        │
        ▼
Step 0  comprobación de dependencias   check_deps.sh  (--install)
Step 1  entrevista de producto         solo los huecos inciertos · ≤4 preguntas × 2 rondas
Step 2  comprobación de la oferta      qué recibe el cliente + qué ansiedad elimina + por qué ahora
Step 3  hoja de cortes                 cuts.md (14 cortes por defecto) + legal.md
        │
        ├─ Gate 1  check_cuts.py       determinista: límites de slot · cobertura Q · cada número rastreado · palabras prohibidas · bloques legales
        ├─ Gate 2  4 agentes revisores cliente escéptico · examinador regulatorio · revisor CRO · marketer de la competencia
        └─ aprobación del copy
        │
Step 4  imágenes de los cortes         /pumasi:image — primero el corte ancla, el resto encadenado con --ref, texto + plausibilidad física inspeccionados
Step 5  ensamblaje HTML                assemble_html.py — cortes apilados borde con borde, bloque legal debajo
        │
        └─ Gate 3  render_check.py     render con Playwright a 390 / 860 px + prueba de 5 segundos en la primera pantalla
        │
        ▼
sangse/<slug>/  cuts.md · legal.md · images/ · index.html · qa/ · scorecard
```

Los cortes siguen las **8 preguntas que un cliente se hace en silencio antes de pagar**: ¿Es para mí → Qué obtengo → Por qué de esta forma → Puedo hacerlo → Qué tan difícil es → Qué recibo exactamente → Qué pasa si falla → Por qué ahora.

---

## Características

| Característica | Descripción |
|---------|-------------|
| Formato de hoja de cortes de imagen | 12~20 cortes, 1000 px de ancho, copy renderizado dentro de la imagen; precios, teléfonos, tablas nutricionales y avisos legales se quedan en HTML |
| 29 plantillas de corte medidas | Diseccionadas de páginas reales — Kurly, Coupang, una tienda de marca, Samsung, LG, Musinsa (moda), Kmong (servicios) |
| Entrevista guiada por la incertidumbre | Pregunta solo lo que no puede inferirse del input; como máximo 4 preguntas × 2 rondas |
| Comprobación de la oferta antes del copy | Las ofertas débiles se señalan antes de escribir una sola línea de copy |
| Gate 1 — verificador determinista | `check_cuts.py`: límites de slot de plantilla, cobertura Q1~Q8, cada número rastreado hasta el input, palabras prohibidas por categoría, bloques legales obligatorios, existencia de imágenes |
| Gate 2 — cuatro agentes revisores | Separados del redactor; aprobado = el cliente responde "sí" a las 8 preguntas y cero infracciones regulatorias, máximo 2 rondas |
| Gate 3 — render real | `render_check.py`: render con Playwright a 390 / 860 px más una prueba de 5 segundos en la primera pantalla |
| Imágenes de cortes con inspección | Ancla `/pumasi:image` → cadena `--ref`; cada corte se comprueba en exactitud del texto **y** plausibilidad del producto (envase sellado, cantidades, dedos) |
| Filtros de cumplimiento | `references/compliance.md`: reglas detalladas para alimentos y alimentos funcionales (art. 8 de la Ley de Etiquetado y Publicidad de Alimentos, afirmaciones funcionales aprobadas, revisión previa, etiquetas obligatorias) y un índice legal para cosméticos, dispositivos médicos, finanzas, educación, inmobiliaria y electrónica — los filtros específicos por categoría para estos están en desarrollo |
| Ley de Hierro | Sin casos, números, reseñas, condiciones de reembolso ni plazos inventados — marcadores en su lugar |

Nada de esto es asesoramiento legal; la redacción final queda sujeta al organismo de revisión correspondiente.

---

## Comandos

| Comando | Descripción |
|---------|-------------|
| `/sangse <información del producto>` | Ejecución completa: entrevista → hoja de cortes → puertas → imágenes → HTML → scorecard |
| `/sangse 카피만 <información del producto>` | Solo copy — se detiene tras la puerta de aprobación del copy |
| `/sangse 스마트스토어 <información del producto>` | Fija la plataforma de antemano (también `웹`, `크몽`) y omite esa pregunta de la entrevista |
| `/sangse check <dir>` | Ejecuta solo las puertas de verificación sobre una carpeta `sangse/<slug>` existente |

### Disparadores en lenguaje natural

- "상세페이지 만들어줘", "스마트스토어 상세 만들어줘", "세일즈 페이지 써줘", "이 제품 소개 페이지 써줘"
- "haz una página de detalle", "copy para página de producto", "copy para página de ventas", "copy para landing page"

---

## Componentes (구성요소)

| Ruta | Rol |
|---|---|
| `commands/sangse.md` | Punto de entrada único (`/sangse`), enrutamiento de argumentos |
| `skills/sangse/SKILL.md` | Flujo de trabajo (Step 0 → entrevista → comprobación de la oferta → hoja de cortes → 3 puertas → imágenes → HTML → informe), Ley de Hierro, señales de alerta |
| `skills/sangse/references/` | `framework.md` (8 preguntas), `cut-sheet.md`, `reference-patterns.md` (7 páginas reales diseccionadas, 29 plantillas), `interview.md`, `compliance.md`, `verification.md`, `evidence.md`, `image-briefs.md`, `reference-capture.md` |
| `skills/sangse/scripts/` | `check_deps.sh`, `check_cuts.py`, `check_copy.py`, `assemble_html.py`, `render_check.py`, `capture_reference.js` |
| `skills/sangse/assets/` | `cut-templates.json`, `banned-words.json`, `template.html` |
| `setup/` | Configuración de primera ejecución (estándar gptaku) |
| `tests/test-gates.sh` | Regresión: gate 1 PASS en los tres ejemplos, smoke del ensamblador, comprobación de dependencias, contrato del frontmatter |
| `examples/` | Tres productos ficticios con el rastro completo de artefactos y resultados en `qa/` |

---

## Requisitos (요구사항)

- CLI de [Claude Code](https://docs.anthropic.com/claude-code) con el marketplace gptaku-plugins
- Plugin `pumasi` para las imágenes de los cortes (opcional — sin él, la ejecución se detiene en copy + marcadores HTML)
- [Codex CLI](https://github.com/openai/codex) con sesión iniciada y `image_generation` activado (backend de imágenes)
- python3 — las puertas y el ensamblador usan solo la biblioteca estándar
- (opcional) Node + Playwright para las comprobaciones de render del gate 3; `~/.insane-search/node/node_modules` se detecta automáticamente
- `bash skills/sangse/scripts/check_deps.sh --install` comprueba e instala lo anterior

---

## Changelog

Consulta [CHANGELOG.md](CHANGELOG.md). El procedimiento de release (subida de versión → release en GitHub → puntero del submódulo en el marketplace → caché) sigue [gptaku_plugins/PLUGIN_STANDARD.md](https://github.com/fivetaku/gptaku_plugins/blob/main/PLUGIN_STANDARD.md); `tests/test-gates.sh` debe pasar antes de cada subida de versión.

---

## Licencia (라이선스)

MIT — consulta [LICENSE](LICENSE) y [DISCLAIMER.md](DISCLAIMER.md).

---

<div align="center">

**Entran los datos del producto. Sale una página de detalle que vende — sin nada inventado.**

</div>
