# Model export schema

Generated from analysis/src/export_web.py. Keys and shapes only. `[]` marks an array, `*` any map key.
Numbers are rounded to 8 decimals. Each file is under 2 MB.

## model.json

| Path | Type |
| --- | --- |
| `version` | string |
| `sectors[]` | string |
| `sizes[]` | string |
| `assets[]` | string |
| `categories[]` | string |
| `attack.feature_order[]` | string |
| `attack.sectors[]` | string |
| `attack.reference_levels.sector` | string |
| `attack.reference_levels.size` | string |
| `attack.models.*.intercept` | number |
| `attack.models.*.coefficients.*` | number |
| `impact.target` | string |
| `impact.features[]` | string |
| `impact.intercept` | number |
| `impact.coefficients.*` | number |
| `impact.residual_sd` | number |
| `impact.reference_levels.sector` | string |
| `impact.reference_levels.size` | string |
| `impact.sectors[]` | string |
| `personas.feature_order[]` | string |
| `personas.scaler.type` | string |
| `personas.scaler.mean[]` | number |
| `personas.scaler.scale[]` | number |
| `personas.scaler.reason` | string |
| `personas.centroids[][]` | number |
| `personas.names[]` | string |
| `personas.attack_mix.*.*` | number |
| `controls[].control` | string |
| `controls[].mitigates[]` | string |
| `controls[].effectiveness` | number|null |
| `controls[].effectiveness_key` | string |
| `controls[].effectiveness_url` | string |
| `controls[].effectiveness_fallback_level` | string |
| `controls[].annual_cost_inr` | number|null |
| `controls[].cost_basis` | string |
| `controls[].cost_url` | string |
| `controls[].cost_excerpt` | string |
| `controls[].coverage.*` | number |
| `config.*.value` | number |
| `config.*.unit` | string |
| `config.*.fallback_level` | string |
| `config.*.source_key` | string |

## sources.json

| Path | Type |
| --- | --- |
| `values[].key` | string |
| `values[].value` | number |
| `values[].unit` | string |
| `values[].publisher` | string |
| `values[].url` | string |
| `values[].excerpt` | string |
| `values[].fallback_level` | string |
| `bibliography[].publisher` | string |
| `bibliography[].title` | string |
| `bibliography[].year` | string |
| `bibliography[].url` | string |
| `bibliography[].used_for` | string |
| `cases[].name` | string |
| `cases[].year` | string |
| `cases[].sector` | string |
| `cases[].size_bucket` | string |
| `cases[].assets` | string |
| `cases[].actual_actions` | string |
| `cases[].summary` | string |
| `cases[].source_url` | string |
| `cases[].accessed` | string |

## lineage.json

| Path | Type |
| --- | --- |
| `steps[].step` | string |
| `steps[].rows` | number |
| `steps[].rule` | string |
| `example_incident.source` | string |
| `example_incident.incident` | object |
| `example_incident.flattened` | object |
| `datasets[].dataset` | string |
| `datasets[].publisher` | string |
| `datasets[].url` | string |
| `datasets[].version` | string |
| `datasets[].access_date` | string |
| `datasets[].sha256` | string |
| `datasets[].files` | string |
| `datasets[].notes` | string |

## cards.json

| Path | Type |
| --- | --- |
| `[].id` | string |
| `[].order` | number |
| `[].stage` | string |
| `[].used_live` | boolean |
| `[].title` | string |
| `[].card` | object |
