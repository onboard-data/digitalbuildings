#!/usr/bin/env python3
import csv

from validate import generate_universe

universe = generate_universe.BuildUniverse()
types_by_ns = universe.entity_type_universe.type_namespaces_map
rows = []

for namespace, entities in types_by_ns.items():
  print(f"\n-- working on namespace '{namespace}'--\n")

  # if namespace == 'HVAC':
  #     __import__("IPython").embed()

  for entity_name, entity in entities.valid_types_map.items():
    print(f"Entity '{entity_name}'")

    # if entity_name == 'AHU_BSPC_CO2M_DX4SC_ECON_EFSS_EFVSC_FDPM4X_HTSC_MOAFC_OAFC_SFSS_SFVSC_SSPC':
    #     __import__("IPython").embed()

    entity_row = {
      'guid': entity.guid,
      'namespace': namespace,
      'name': entity_name,
      'is_canonical': entity.is_canonical,
      'is_abstract': entity.is_abstract,
      'description': entity.description,
      'parents': "|".join([p.typename for p in entity.parent_names.values()]),
    }

    # many canonical types don't define any new fields, they mix-in existing abstract
    # types e.g. AHU_BSPC_CO2M_DX4SC_ECON_EFSS_EFVSC_FDPM4X_HTSC_MOAFC_OAFC_SFSS_SFVSC_SSPC
    if not entity.local_field_names:
      canonical_row = {
        **entity_row,
        'dbo.point_type': None,
        'field_optional': None,
      }
      rows.append(canonical_row)

    for field_name, field in entity.local_field_names.items():
      increment = field.field.increment
      field_row = {
        **entity_row,
        'dbo.point_type': field.field.field,
        'dbo.point_type_increment': increment,
        'field_optional': field.optional,
      }
      rows.append(field_row)

if rows:
  rows.sort(key=lambda r: r['guid'])

  with open('flat_ontology.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, rows[0].keys(), delimiter=',', lineterminator='\n', quoting=csv.QUOTE_MINIMAL)
    writer.writeheader()
    writer.writerows(rows)
else:
  sys.stderr.write(
    "No rows generated, ensure the validator is installed & updated (tools/validators/ontology_validator/README.md)")
