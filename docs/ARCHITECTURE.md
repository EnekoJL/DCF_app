# Arquitectura — Sevcon DCF Diff

## Capas y regla de dependencias

```
presentation  ──►  application  ──►  domain  ◄──  infrastructure
(customtkinter)    (casos de uso)    (modelos,      (parser DCF, TOML,
                                      Protocols)     exportadores)
                    ▲
             __main__.py (composition root: único sitio que conoce todas las clases concretas)
```

- `domain/`: dataclasses inmutables y `typing.Protocol`. **Sin I/O, sin tkinter, sin librerías externas.**
- `application/`: lógica pura que solo depende de `domain` (decodificador de valores, motor de diff,
  filtros, caso de uso `CompareDcfFiles`). Recibe los puertos por constructor (DIP).
- `infrastructure/`: implementaciones de los puertos (lectura de ficheros, reglas TOML, HTML/PDF).
- `presentation/`: GUI. Widgets pasivos + `CompareController` (presenter) que habla con la capa de
  aplicación y entrega *view models* ya formateados. Ningún widget importa `infrastructure`.

## Puertos (`domain/ports.py`)

| Protocol | Método | Implementación v1 |
|---|---|---|
| `DcfReader` | `read(path) -> DcfDocument` | `SevconDcfReader` |
| `ParameterClassifier` | `classify(param) -> FunctionalGroup`, `groups()` | `TomlRuleClassifier` |
| `NoiseFilter` | `noise_reason(param) -> str \| None`, `checksum_key` | `TomlNoiseFilter` |
| `ReportExporter` | `export(result, path) -> None` | `HtmlReportExporter`, `PdfReportExporter` |
| `ChangeImpactAnalyzer` | `analyze(result) -> ImpactReport` | **ninguna (futuro agente IA)** |

## Flujo de comparación

1. `CompareDcfFiles.execute(path_a, path_b)` → `DcfReader.read` ×2.
2. `DcfDiffEngine.diff(doc_a, doc_b)` → unión de `ObjectKey`, compara el **valor decodificado**
   (`ValueDecoder`) → `ParameterChange` (MODIFIED/ADDED/REMOVED) con bitfields cambiados.
3. Cada cambio se enriquece con `ParameterClassifier` (grupo) y `NoiseFilter` (ruido + motivo).
   El objeto checksum (`[indicators]` de `noise_rules.toml`) se excluye del diff; no se muestra
   en la UI ni en los informes (cambia con cualquier parámetro, no aporta).
4. `DiffResult` (cambios + `DiffSummary` + metadatos de ambos ficheros + checksum + aviso de firmware).
5. La UI aplica `DiffQuery` (texto, área, foco) sin recalcular el diff. Por defecto solo muestra
   las áreas de foco (`motor_control = true` en el TOML: control de motor y límites de motor,
   batería y tensión); el interruptor "Otras áreas" añade el resto. La monitorización (ruido) y
   los parámetros sin cambios nunca se muestran ni se cuentan en la GUI.

## GUI (presentation)

De arriba abajo: cabecera (título + tema) → selectores A ⇄ B + Comparar → barra de resumen
(nº de cambios, firmware, búsqueda, desplegable de área, interruptor "Otras áreas") → tabla a
ancho completo agrupada por área (Parámetro · Antes · ▲/▼ · Después · Unidad; los bitfields como
filas hijas) → línea de ayuda con objeto y descripción Sevcon de la fila seleccionada → exportar.

## Extensión prevista: agente de impacto

`ChangeImpactAnalyzer` recibirá un `DiffResult` filtrado (sin ruido) y devolverá un `ImpactReport`
(resumen + riesgos por cambio). La implementación irá en `infrastructure/ai/` (cliente Claude API),
usando `docs/sevcon_parameters.md` como contexto. Cuando exista, se añadirá un botón
"Analizar impacto" en el pie de la ventana. `DiffResult` debe seguir siendo autocontenido (nombre, grupo,
valores físicos, unidades, descripción Sevcon) para poder serializarlo a prompt/JSON (`to_dict()`).

## Cómo extender sin tocar código existente (OCP)

- Reclasificar un objeto o crear un grupo → `infrastructure/knowledge/parameter_groups.toml`.
- Falso positivo/negativo de ruido → `noise_rules.toml` (`[[noise]]` / `[[keep]]`).
- Nuevo formato de informe → nueva clase `ReportExporter` + registrarla en `__main__.py`.
