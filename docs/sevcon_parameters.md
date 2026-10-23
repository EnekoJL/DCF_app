# Sevcon Gen4 Size 6 — Mapa de parámetros relevantes

Base de conocimiento para el comparador y, en el futuro, para el agente que estime el
efecto de los cambios. Fuentes: los propios DCF (`data/samples/`), `docs/datasheets/gen4-product-manual-v2-0-30-01-2009.pdf`,
`docs/datasheets/DVT Customer Manual.pdf`, `docs/datasheets/DVT Tutorial.pdf`, TFG Castelló Díez (2022) y TFM García Fuente (2016).

> **La fuente de verdad es el DCF.** El manual Gen4 es de 2009 y cita objetos (6410h, 4610h,
> 4613h, 607Eh, 2905h, 2925h, 46B0h…) que **no existen** en este firmware. Nombres, escalado y
> unidades se leen siempre de las líneas `;SEVCONFIELD` del propio fichero.

## 1. Formato DCF

- INI CANopen (DSP306), CRLF, ASCII. Secciones `[1000]`, `[4641]` (cabecera de record,
  `ObjectType=9`, `SubNumber`) y `[4641sub2]` (sub en hex sin relleno: `subA`, `sub1D`).
- Claves: `ParameterName`, `ParameterValue` (hex, puede faltar o estar vacío), `ObjectType`,
  `DataType`, `AccessType`, `LowLimit`, `HighLimit` (decimal o `0x..`), `DefaultValue`, `PDOMapping`.
- Metadatos `;SEVCONFIELD KEY=VALUE` (pueden repetirse, p.ej. `DESCRIPTION`):
  - `SCALING` → **físico = raw × SCALING** (sin SCALING ⇒ 1). Confirmado en manual (1/256 V/bit en entradas analógicas; 0..1 = 0..32767).
  - `UNITS` (solo etiqueta), `CATEGORY` (CONFIGURATION / MONITORING / LOGGING; en el padre, la heredan las subs),
    `ACCESS_LEVEL` (1 Usuario, 2 Service, 3 Dealer, 4 OEM Engineering, 5 Sevcon), `WRITE_IN_PREOPERATIONAL_ONLY=TRUE`.
  - Enumeraciones: `;SEVCONFIELD 5=SIN/COS` (ojo: a veces `410 = inclinometer` con espacios).
  - `NUMBER_FORMAT=BIT_SPLIT`, `NUMBER_SPLIT=n`, y bloques repetidos
    `SPLIT=k / PARAMETERNAME / BITMASK / BITSHIFT / LOW_LIMIT / HIGH_LIMIT / NUMBERFORMAT` + enums propios del campo.
    Campo = `(raw & BITMASK) >> BITSHIFT`. (Nota: `NUMBERFORMAT` sin guion bajo dentro del split.)
- `DataType`: 1 BOOL, 2 INT8, 3 INT16, 4 INT32 (complemento a 2: `0xfe0c` = −500), 5 UINT8, 6 UINT16,
  7 UINT32, 9 VISIBLE_STRING, 15 DOMAIN (blob hex de varios kB).
- Mapeo PDO: `index<<16 | sub<<8 | bits` (p.ej. `0x606c0020`).
- `5620h` Configuration Checksum: 16 bits de todos los items de configuración. Útil como
  indicador "la configuración difiere", no como cambio en sí.
- Cabecera `[FileInfo]` (fechas, FileName) y `[DeviceInfo]` (`ProductNumber`, `RevisionNumber` = firmware).
  DVT solo acepta "Send DCF to Unit" con la misma plataforma HW/SW → avisar si `RevisionNumber` difiere.

## 2. Grupos funcionales (implementados en `src/sevcon_diff/infrastructure/knowledge/parameter_groups.toml`)

| Grupo | Objetos | Notas (escalado del DCF) |
|---|---|---|
| ★ Datos base del motor | 4641 sub2 Is max (A rms), sub3 Im min (INT16, A rms, negativo), sub5 pares de polos, sub7 corriente nominal, subC tensión nominal batería (0.0625 V), sub12 Ke (1/32768 V/rad/s); 6075 límite corriente (0.001 A); 6076 *Peak torque* (0.001 Nm); 6080 velocidad máx (rpm); 2916sub1 par nominal; 4617sub2 descripción del motor | En CiA 402 genérico 6076 es "rated torque"; aquí Sevcon lo llama Peak torque. |
| ★ Modelo eléctrico | 4641 subA Ls (5.96e-2 µH/bit), sub2B saturación mínima Ls (%), subE Iq headroom; 4617 sub1 (tablas lookup del motor, DOMAIN ~9.5 kB), sub3 versión, sub4 checksum; 4621 sub4-7 variación de resistencia con temperatura | No hay objetos Rs/Ld/Lq explícitos en este firmware. |
| ★ Lazo de corriente | 4641 subD Kp (1/256), subF Ki (1/32768), sub21 Kp eje d, sub22 Ki eje d | |
| ★ Lazo de velocidad | 4651 sub1 Kp (1/4096), sub2 Ki (1/256), sub3/5 Kp/Ki baja velocidad, sub4 rollback Ki, sub6 dw/dt, sub7 init integral, sub8 polo filtro, sub9 pre-limit, subA rampa bajada límite; 2900 modo control; 290A S-curve; 2933 S-curve par | |
| ★ Límites par/corriente | 6072 par máx (0.1 % de pico); 4611 mapa potencia (9 puntos par 0.0625 Nm vs rpm); 4615 mapa secundario + 4652 trigger; 2920/2921/2922/2936 sub1-4 (par en drive / cambio dirección / neutral / freno, 0.1 %); 2930sub2; 5840 | |
| ★ Límites de velocidad | 4624 sobrevelocidad (rpm); 2920-2922/2936 sub5/6 máx adelante/atrás, subF/10 rampas límite; 291E; 2906-2908; 2929sub2; 290Csub2; 2930sub3; 2919sub1; 2915 | |
| ★ Debilitamiento de campo | 4641 sub16 FW% arranque lazo abierto, sub19/1A Kp/Ki control de índice de modulación, sub1E/1F índice de modulación máx drive/brake (0.0244 %) | Inferido por nombre (el manual no lo documenta). Im min (sub3) también limita el Id negativo. |
| ★ Límites de tensión | 4612 mapa cutback por tensión (9 puntos: V 0.0625, ganancia 1/32768); 2C00 nominal, 2C01 sobretensión, 2C02 subtensión, 2C03 retardo; 462B; 5820/5821/5824 precarga | |
| ★ Encoder | 4630 (tipo enum, offset sub4/sub10, umbrales sin/cos sub5-8, latencias, avisos); 4631 PLL; 6090 pulsos/rev; 60F8 | 4630 sub9-C son *medidas* → ruido. |
| ★ Térmica | 4620 termistor motor; 4621 I²t / temp máx motor; 461E mapa cutback temperatura; 461F mapa termistor usuario; 5A01 ventiladores | |
| Perfiles tracción | 2910 throttle (flags BIT_SPLIT), 2911 footbrake, 2912 economy, 2913 steering, 2914 FS1; 2920 baseline, 2921/2922/2936 perfiles; 2931 triggers; 6083 aceleración; 6087 pendiente par; 2901-2904, 2909, 290B-290E, 2918-291C, 2929, 2930 | |
| Batería | 4623 límites corriente carga/descarga; 2870 límite corriente master; 2872; 2C30/2C31 BDI | |
| E/S | 4680-46C4, 6802, 6C43/44, 2D00-2D02, 2820, 2840, 2850, VPDO 3000-3400, 5800, 4658 cortocircuito activo, 5830/5831 PWM | |
| CAN/PDO | 1005-1017, SDO 1200-1287, RPDO 1400-1604, TPDO 1800-1A04, 5900-5906 | |

Cambios reales observados entre los 4 DCF de muestra: 2910, 2915, 2920, 2921, 2870, 4611, 4612,
4623, 4624, 461E, 4621sub3, 4630sub10, 4641 (sub2/3/5/A/D/F/12/21/22), 4651 sub1/2, 6075, 6076,
6080, 6083, 6087, 5821, PDO/VPDO (1800-1804, 1A00-1A04, 3300), 4617sub2.

## 3. Ruido (implementado en `noise_rules.toml`)

CATEGORY ∈ {MONITORING, LOGGING} o AccessType ∈ {ro, const}, más la lista explícita: horas
(2781-2786, 4601, 5200), odómetro (29A0/29A1), FIFOs y contadores de eventos (4000, 4100-4112,
4200-420A, 4300/4301, 5300, 5310, 5320, 5600, 1001), medidas (4600, 4602, 4603, 4605, 5100, 46D0,
6C01, 6800, 6C11, 6079, 4630 sub9-C, 2871, 4617 subA-C), estado (6040, 6041, 606x, 5110, 2800) y
estado de aplicación (2020-2060, 2101-2184, 2220-2241, 2400-2460, 2620-2641, 2720-2760, 278F, 2790).

## 4. Referencia de motor (TFG Castelló Díez, Size 6 + ENGIRO MS1920)

| Dato | Valor |
|---|---|
| Nominal | 22 Nm, 13 kW, 5720 rpm, 156 A rms, 96 V DC, 381 Hz, FP 0.75 |
| Máximo | 95 Nm, 42 kW, 8000 rpm, 781 A rms, 200 V DC |
| Polos | 8 (4 pares de polos), trifásico, PMSM saliente, encoder sin/cos, termistor KTY84 |
| Kt | 0.14 Nm/A rms; Ke 0.022 V/(rad/s) rms (0.031 pico); BEMF 9.1 V rms/krpm |
| Inercia | 0.009 kg·m²; T máx motor 120 °C |
| Por unidad | flujo 0.77 pu (0.0869 V·s/rad), Lq 0.64 pu (0.36 saturada), Ld 0.25 pu, Id óptima −0.361 pu, Id medida −61.4 A |
| Lazo corriente (simulación, serie Kp(1+Ti s)/(Ti s), MF 60°) | d: ωc 1425 rad/s, Kp 0.03558, Ti 4.36e-5 · q: ωc 531 rad/s, Kp 0.03319, Ti 1.12e-3 (no trasladables directamente a Sevcon) |
| Lazo velocidad | arranque Kp 0.015, resto 0; Ki final 0; límite 7000 rpm |
| Batería | ~108 V (máx. competición 126 V); Size 6 72–80 V nominal, hasta 150 V |

Procedimiento de puesta en marcha PMAC (DVT): Ke = 0 → "PMAC Commissioning Help" identifica Ke y
Ls → "Finalize" calcula T_max ≈ √3·Ke·npp·Is_max e Id_min ≈ −Ke/(√3·Ls) → "Setup basic current
gains" → calibración sin/cos y offset del encoder → ajuste de lazo de velocidad.

## 5. Efecto esperado de los cambios (semilla para el futuro agente)

- **Kp lazo corriente ↑**: respuesta de par más rápida; demasiado ⇒ oscilación/ruido de corriente, disparos de sobrecorriente. Regla práctica DVT: si inestable tras "basic current gains", ×/÷2.
- **Ki lazo corriente ↑**: elimina error estacionario; excesivo ⇒ sobreoscilación. Lazo de corriente mal ajustado pierde la referencia a alta corriente (picos de Id → sobrecorriente).
- **Lazo de velocidad**: solo actúa al alcanzar el límite de velocidad. Mal ajuste ⇒ oscilación de velocidad en el límite y peor seguimiento de corriente. (El TFG observó mayor estabilidad con más Ki — evidencia contradictoria con la teoría.)
- **Im min (Id negativa) más negativa**: más debilitamiento de campo y par de reluctancia a alta velocidad; riesgo de desmagnetización, sobrecorriente y calentamiento (en la práctica el límite es térmico).
- **Is max / 6075 / 6076 ↑**: más par de pico y aceleración; más estrés térmico en inversor y motor, más caída de batería.
- **Mapa 4611 (par vs rpm)**: define la curva de potencia; subir puntos altos ⇒ más potencia a alta velocidad (limitado por tensión).
- **Mapa 4612 (cutback por tensión)**: protege la batería; puntos más altos o ganancias menores ⇒ recorte de par antes.
- **6080 / 4624 / perfiles sub5-6**: techo de velocidad del vehículo / disparo de sobrevelocidad.
- **Rampas 2920 sub7-E**: aceleración/frenado más bruscos o más suaves (driveability).
- **Pares de polos / Ls / Ke / offset encoder**: parámetros de identificación; un error ⇒ control vectorial desorientado (par reducido, vibración, pérdida de control). Cambios aquí son **críticos**.
- **Temp. máx motor (4621)**: por encima, par rampa de 100 % a 0 %.
- **BDI / subtensión mal ajustados**: falsos "Low batt" que paran la moto.
- **Demasiados TPDO o SYNC corto**: satura el bus CAN, trazas planas en el log.
