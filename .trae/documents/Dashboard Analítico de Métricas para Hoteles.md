## Arquitectura
- Backend: Django + Django Ninja para API (`/api/analytics/*`), app nueva `analytics`.
- BD: PostgreSQL con particiones por mes para tablas de hechos; índices compuestos por fecha/hotel/segmento.
- Capa ETL: jobs programados (Celery + Beat) para extracción, limpieza, normalización y cargas incrementales.
- Cache distribuida: Redis (cluster) para KPIs, filtros y agregaciones frecuentes.
- Frontend: Templates Django + JS (ECharts + DataTables) para visualizaciones interactivas.

## Modelo de Datos
- Hechos: `BookingFact`, `RevenueFact`, `OpsFact`, `SatisfactionFact` (granular por día/hotel/segmento).
- Dimensiones: `DimHotel`, `DimDate`, `DimRoom`, `DimClient`, `DimChannel`, `DimSegment`.
- Agregados: tablas materializadas `AggDaily`, `AggWeekly`, `AggMonthly` con métricas precomputadas (ocupación, ADR, RevPAR, ingresos, costos, NPS, tiempos de limpieza/mantenimiento).
- Benchmarks: `IndustryBenchmark` con estándares STR, HotStats, CBRE por categoría y región.

## ETL y Procesamiento
- Conexión segura: soportar API REST existente y conexión directa (DSN/credenciales via env) con roles mínimos.
- Limpieza: normalización de fechas/moneda, imputación de nulos (medianas/forward-fill), validación de claves foráneas.
- Transformación: derivar ADR, RevPAR, GOPPAR, índices de ocupación, tasas de cancelación/no-show, NPS, CSAT.
- Correlaciones: cálculo batch de matrices de correlación (>50 dimensiones) con Pearson/Spearman y almacenamiento en `CorrelationMatrix`.

## Dataset Sintético
- Comando `manage.py seed_analytics` que genera:
  - 20 hoteles (ubicación, categoría, tamaño, plan) con variación realista.
  - 10,000+ reservas (2022–2023) con estacionalidad (picos verano/feriados/fines de semana).
  - 5,000+ clientes con perfiles demográficos y segmentos (business/leisure/family).
  - Datos de ocupación, ingresos, costos operativos, satisfacción (NPS/CSAT), tiempos de limpieza/mantenimiento.
- Parámetros para densidad estacional, efecto canal, variaciones regionales.

## API de Analytics
- Endpoints:
  - `GET /api/analytics/kpis`: 10 KPIs en tiempo real (ocupación, ADR, RevPAR, ingresos, costos, margen, NPS, tasa cancelación, no-show, lead-time).
  - `GET /api/analytics/heatmap/occupancy`: heatmap por día/mes vs tipo de habitación.
  - `GET /api/analytics/timeseries`: series de tiempo con comparativas YoY/QoQ/MoM/WoW/DoD.
  - `GET /api/analytics/drilldown`: 3 niveles (portfolio → categoría → hotel → segmento).
  - `GET /api/analytics/benchmarks`: comparación con STR/HotStats/CBRE.
  - `POST /api/analytics/insights`: generar y persistir insights (>15 por categoría) con reglas (>5% variación).
  - Export: `GET /api/analytics/export.{pdf,xlsx,png,csv}`.

## Visualización y UX
- 8 gráficos: líneas, barras, áreas, heatmaps, scatter, boxplots, sankey (canales → reservas → ingresos), mapas coropléticos (por región).
- Panel principal: 10 KPIs con actualización vía WebSocket (canal de Redis) y fallback polling.
- Drill-down: clic sobre barra/serie abre detalle (nivel 1–3) con breadcrumbs.
- 15 filtros: rango de fechas, hotel, categoría, región, tipo habitación, segmento cliente, canal, tarifa, estado reserva, país/edad cliente, día semana, temporada, plan, fuente marketing, status operaciones.
- Tooltips enriquecidos: `hotel`, `fecha`, `segmento`, `valor`, `% variación`, benchmark, metadatos.
- Storytelling mode: modo presentación con pasos anotados, layout de diapositivas y export a PDF.

## Alertas y Oportunidades
- Motor de reglas: umbrales configurables con 3 severidades (info/warn/critical), detección de anomalías.
- Notificaciones: panel de alertas + opcional email; registro en `ActionLog`.

## Seguridad y Acceso
- OAuth 2.0 (django-oauth-toolkit): roles `admin`, `analyst`, `viewer` con scopes (lectura/descarga, creación de insights, configuración de alertas).
- Rate limiting por token y auditoría completa.

## Performance y Cache
- SLA: <2s para 1M+ registros apoyándose en agregados y cache.
- Pre-aggregación: cron de refresco (por hora/día) y recalculo incremental.
- Redis: claves por hash de filtros; TTL y invalidación en cambios de datos.

## Exportaciones
- PDF: WeasyPrint/WKHTML; Excel: openpyxl; CSV streaming; PNG: export desde ECharts o captura headless.
- Lotes y unitaria, con metadatos de filtros y timestamp.

## Accesibilidad y Diseño
- 6 secciones: Resumen ejecutivo, Desempeño financiero, Ocupación y tarifas, Satisfacción cliente, Benchmarking competitivo, Alertas y oportunidades.
- Responsive 4 breakpoints; WCAG AA: contraste, ARIA roles, focus visible, navegación por teclado.

## Logging y Documentación
- Logging: auditoría de consultas, filtros aplicados, exportaciones; integrar con `ActionLog`.
- Documentación técnica: diagrama de arquitectura (texto + gráfico), modelo de datos, manual de implementación (ETL, despliegue), guía de estilo de visualización (colores/leyendas/tooltip).

## Plan de Implementación
1. Crear app `analytics`, modelos de hechos/dimensiones/aggregados.
2. ETL inicial + jobs programados; comandos de seed sintético.
3. Endpoints Ninja y caché Redis; websockets para KPIs.
4. Templates y componentes JS (ECharts/DataTables) con filtros/drilldown/tooltips.
5. Motor de alertas e insights; benchmarking.
6. Exportaciones y storytelling mode.
7. OAuth2 y permisos; logging/auditoría.
8. Documentación técnica y validaciones de performance/accesibilidad.

## Validación
- Pruebas unitarias de ETL/aggregation/insights.
- Pruebas de carga (1M+ registros) con medición de TTFB y latencia.
- Tests de accesibilidad (axe-core) y contraste.

¿Confirmas este plan para comenzar con la implementación?