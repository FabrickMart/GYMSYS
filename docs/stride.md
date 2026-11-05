# Fase 2: Ciberseguridad — GYMSYS-MMA

Documentación de la fase de ciberseguridad aplicada al sistema de gestión del gimnasio MG Team.

## Estado de los documentos

| # | Documento | Estado | Descripción |
|---|---|---|---|
| 1 | [STRIDE](stride.md) | ✅ **Completado** | Modelado de amenazas — 12 componentes, 100 mejoras |
| 2 | [OWASP Top 10](owasp.md) | ⏳ Pendiente | Auditoría contra las 10 categorías |
| 3 | [Cifrado](cifrado.md) | ⏳ Pendiente | CURP y datos personales |
| 4 | [Hardening](hardening.md) | ⏳ Pendiente | Django + MySQL + SO |
| 5 | [Dashboard](dashboard.md) | ⏳ Pendiente | Monitoreo de eventos |
| 6 | [Logging](logging.md) | ⏳ Pendiente | Configuración de logs |
| 7 | [SIEM (Wazuh)](wazuh.md) | ⏳ Pendiente | Laboratorio de monitoreo |
| 8 | [Pentesting](pentesting.md) | ⏳ Pendiente | Pruebas de seguridad |
| 9 | [ISO 27001/27032](iso.md) | ⏳ Pendiente | Alineación con estándares |

## Estándares de referencia

- **OWASP Top 10 (2021)** — Riesgos de aplicaciones web
- **ISO/IEC 27001:2022** — Sistemas de gestión de seguridad de la información
- **ISO/IEC 27032:2023** — Ciberseguridad
- **NIST SP 800-115** — Guía de pruebas de seguridad
- **STRIDE** — Modelo de amenazas de Microsoft

## Resumen del análisis STRIDE

- **Componentes analizados:** 12
- **Categorías por componente:** 6 (S, T, R, I, D, E)
- **Mejoras identificadas:** 100
  - Críticas: 15
  - Altas: 30
  - Medias: 35
  - Bajas: 20

## Próximos pasos

1. **F2.2 — OWASP Top 10:** auditoría de código contra las 10 categorías.
2. **F2.3 — Cifrado CURP:** mejora #12 (crítica).
3. **F2.4 — Hardening Django:** mejoras #8, #19, #25, #34, #51, #87, #88.
4. **F2.5 — Hardening MySQL:** mejoras #78, #79, #80, #81, #83, #86.
5. **F2.6 a F2.10:** dashboard, logging, Wazuh, pentesting, ISO.
