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
El botón "Curva par–rpm" (junto a Comparar, activo en cuanto hay A o B) abre la ventana de la
gráfica.

## Flujo de la curva par–rpm

Sin puerto nuevo: es una lectura de un solo fichero que reutiliza `DcfReader` y `ValueDecoder`.

1. `infrastructure/motor_profile_loader.py` carga `knowledge/motor_profile.toml` →
   `MotorProfileSpec` (qué objetos forman los mapas par–velocidad, las líneas de referencia y las
   constantes; `RuleError` si una entrada está mal).
2. `application/motor_profile.py`: `MotorProfileExtractor.extract(doc)` → `MotorProfile` (puntos en
   orden del fichero, valores ya escalados por el DCF; nunca lanza: objeto ausente ⇒ punto o
   constante sin valor; mapa opcional todo a 0 ⇒ se omite). `LoadMotorProfiles.execute(paths)`
   lee 1 o 2 ficheros.
3. `CompareController.show_motor_chart()` (hilo de trabajo, como `compare`) usa las rutas A y/o B
   seleccionadas (no hace falta haber comparado) → `build_motor_chart(a, b)` →
   `MotorChartViewModel` (series con kW por punto, referencias, filas de constantes A/B con
   `changed`) → `view.show_motor_chart(vm)`.
4. `SevconDiffApp` importa `widgets/torque_chart.py` de forma perezosa (si falta matplotlib,
   muestra un error) y reutiliza una única `TorqueChartWindow` (`CTkToplevel` con
   `FigureCanvasTkAgg` + barra de navegación + tabla de constantes). El dibujo está en
   `widgets/torque_plot.py::draw_torque_chart(fig, vm, show_power, dark)`, sin Tk ni pyplot, para
   poder renderizarlo sin pantalla (tests, PNG).

CLI de depuración: `python -m sevcon_diff --profile FICHERO [FICHERO ...]`.

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
- Añadir un mapa par–velocidad, una línea de referencia o una constante del motor a la gráfica →
  `motor_profile.toml` (`[[torque_speed_map]]`, `[[reference_line]]`, `[[constant]]`).
