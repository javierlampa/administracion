# Diccionario Maestro de Mapeo: SharePoint -> Supabase

Este documento es la "Piedra de Rosetta" del sistema. Mapea los nombres que ve el usuario en SharePoint, los nombres técnicos que devuelve la API de Microsoft Graph (JSON) y las columnas correspondientes en la base de datos Supabase.

## 1. Tabla: `ordenes_publicidad` (Maestra)
| SharePoint (Display) | SharePoint (JSON/Técnico) | Supabase (Destino) | Tipo |
| :--- | :--- | :--- | :--- |
| OP | `OP` | `op` | String (Key) |
| Total | `Total` | `importe_total` | Numeric |
| Fecha de la Orden | `Fecha_x0020_de_x0020_la_x0020_Or` | `fecha_orden` | Date |
| Programa | `Programa` | `programa_nombre` | String |
| Empresa | `Empresa` | `empresa` | String |
| UnidaddeNegocio2 | `UnidaddeNegocio2` | `numero_factura` | String |
| EstaFacturado | `EstaFacturado` | `esta_facturado` | Boolean |
| EsFacturado | `EsFacturado` | `tipo_factura` | String |
| Inicio de la Pauta | `Inicio_x0020_de_x0020_la_x0020_P` | `inicio_pauta` | Date |
| Fin de la Pauta | `Fin_x0020_de_x0020_la_x0020_Paut` | `fin_pauta` | Date |
| EsCanjelaPublicidad | `EsCanjelaPublicidad` | `es_canje` | Boolean |
| Venta COMBO | `Venta_x0020_COMBO` | `venta_combo` | Boolean |

## 2. Tabla: `unidades_negocio` (Hija)
| SharePoint (Display) | SharePoint (JSON/Técnico) | Supabase (Destino) | Tipo |
| :--- | :--- | :--- | :--- |
| OP_UNN | `OP_UNN` | `op_numero` | String (Link) |
| Unidad de Negocio | `Unidaddenegocio0` | `unidad_negocio` | String |
| Importe Total | `ImporteTotal` | `importe_total` | Numeric |
| IVA | `IVA0` | `iva` | String |
| Importe sin IVA | `ImportesinIVA` | `importe_sin_iva` | Numeric |
| fecha_creacion_UN | `fecha_creacion_UN` | `fecha_creacion` | DateTime |

## 3. Tabla: `tv` (Hija - Lista "TV")
| SharePoint (Display) | SharePoint (JSON/Técnico) | Supabase (Destino) | Tipo |
| :--- | :--- | :--- | :--- |
| OP_TP | `OP_TP` | `op_numero` | String (Link) |
| TipodePublicidad | `TipodePublicidad` | `tipo` | String |
| ImporteTotal | `ImporteTotal` | `importe_total` | Numeric |
| IVA | `IVA` | `iva` | Numeric |
| Importe sin IVA | `ImporteSinSIVA` | `importe_sin_iva` | Numeric |
| Programa (Lookup) | `ProgramasLookupId` | `programa_id` | Integer (FK) |
| SegundosdeTV | `SegundosdeTV` | `segundos` | Integer |
| Valor del Segundo | `Valor_x0020_del_x0020_Segundo` | `valor_segundo` | Numeric |

> ⚠️ **OJO con Nombres Similares:**
> - En la lista `TV`: el campo de IVA es `IVA` y sin-IVA es `ImporteSinSIVA` (S mayúscula).
> - En la lista `Unidad de Negocio`: el campo de IVA es `IVA0` y sin-IVA es `ImportesinIVA` (s minúscula).
> Estos nombres son incompatibles entre sí y **no deben mezclarse**.

## 4. Tabla: `pagos` (Hija)
| SharePoint (Display) | SharePoint (JSON/Técnico) | Supabase (Destino) | Tipo |
| :--- | :--- | :--- | :--- |
| OP | `OP` | `op_numero` | String (Link) |
| FechadePago | `FechadePago` | `fecha_pago` | Date |
| ImportePago | `ImportePago` | `importe_pago` | Numeric |
| ReciboNúmero | `ReciboNumero` | `recibo_numero` | String |

---
**NOTA PARA FUTURAS MODIFICACIONES:**
Si se agrega una columna en SharePoint, se debe consultar el nombre técnico mediante la herramienta de inspección (`get_real_names.py`) y actualizar este diccionario ANTES de tocar el código del sincronizador.
