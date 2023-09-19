# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the License);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an AS IS BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either exintess or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Module to help perform operations on an ABEL model instance or instances."""

from typing import List

from model import entity
from model import entity_enumerations
from model import entity_operation
from model import model_builder as mb
from validate import field_translation as ft


def _GetLinkScore(
    current_links: List[ft.FieldTranslation],
    updated_links: List[ft.FieldTranslation],
) -> float:
  """Function to help determine how similar two virtual entities' links are.

  Args:
    current_links: A list of FieldTranslation instances which are links for a
      current entity.
    updated_links: An entity instance from an updated building config. This
      updated entity is the same as the entity which contains current_links.

  Returns:
    A score within range [0, 1] modeling the similarity between two lists of
    linked field translations.
  """
  current_link_set = set(current_links)
  updated_link_set = set(updated_links)
  link_score = len(updated_link_set.intersection(current_link_set)) / len(
      current_link_set
  )
  return link_score


def DetermineReportingEntityUpdateMask(current_entity, updated_entity):
  """Returns a list with EntityUpdateMaskAttribute for a reporting entity.

  Args:
    current_entity: An Entity instance from a building config exported from DB
      API.
    updated_entity: An Entity instance from an updated building config.
  """
  update_mask = []
  if updated_entity.code != current_entity.code:
    update_mask.append(entity_enumerations.EntityUpdateMaskAttribute.CODE)
  if updated_entity.type_name != current_entity.type_name:
    update_mask.append(entity_enumerations.EntityUpdateMaskAttribute.TYPE)
  if set(updated_entity.connections).difference(
      set(current_entity.connections)
  ):
    update_mask.append(
        entity_enumerations.EntityUpdateMaskAttribute.CONNECTIONS
    )
  if set(updated_entity.translations).intersection(
      set(current_entity.translations)
  ) != set(current_entity.translations):
    if updated_entity.code == 'VAV-3':
      print(set(updated_entity.translations))
      print(set(current_entity.translations))
      print(
          set(updated_entity.translations).intersection(
              set(current_entity.translations)
          )
      )
    update_mask.append(
        entity_enumerations.EntityUpdateMaskAttribute.TRANSLATION
    )
  return update_mask


def DetermineVirtualEntityUpdateMask(current_entity, updated_entity):
  """Returns a list with EntityUpdateMaskAttribute for a virtual entity.

  Args:
    current_entity: An Entity instance from a building config exported from DB
      API.
    updated_entity: An Entity instance from an updated building config.
  """
  update_mask = []
  if updated_entity.code != current_entity.code:
    update_mask.append(entity_enumerations.EntityUpdateMaskAttribute.CODE)
  if updated_entity.type_name != current_entity.type_name:
    update_mask.append(entity_enumerations.EntityUpdateMaskAttribute.TYPE)
  if set(updated_entity.connections).difference(
      set(current_entity.connections)
  ):
    update_mask.append(
        entity_enumerations.EntityUpdateMaskAttribute.CONNECTIONS
    )
  # Facilities entities don't have links but are virtual so do the following
  # check to ensure a division by zero error is not thrown.
  if (
      current_entity.links
      and updated_entity.links
      and (
          _GetLinkScore(
              current_links=current_entity.links,
              updated_links=updated_entity.links,
          )
          < 0.9
      )
  ):
    update_mask.append(entity_enumerations.EntityUpdateMaskAttribute.LINKS)
  return update_mask


def DetermineEntityOperations(
    current_model: mb.Model, updated_model: mb.Model
) -> List[entity_operation.EntityOperation]:
  """Function to determine entity operations between two model instances.

  Args:
    current_model: Model instance parsed from a building config exported from DB
      API.
    updated_model: Model instance parsed from an updated building config.

  Returns:
    A list of Entity operation instances containing the updated entity and the
    operation which is being performed on it.
  """
  operations = []
  for import_entity in updated_model.entities:
    if import_entity.bc_guid not in set(
        entity.bc_guid for entity in current_model.entities
    ):
      operations.append(
          entity_operation.EntityOperation(
              import_entity,
              operation=entity_enumerations.EntityOperationType.ADD,
          )
      )
      continue

    export_entity = current_model.GetEntity(import_entity.bc_guid)
    if isinstance(import_entity, entity.VirtualEntity) and isinstance(
        export_entity, entity.VirtualEntity
    ):
      update_mask = DetermineVirtualEntityUpdateMask(
          export_entity, import_entity
      )
    elif isinstance(import_entity, entity.ReportingEntity) and isinstance(
        export_entity, entity.ReportingEntity
    ):
      update_mask = DetermineReportingEntityUpdateMask(
          export_entity, import_entity
      )
    else:
      raise TypeError(
          f'GUID: {import_entity.bc_guid} Maps to both a reporting entity and'
          ' a virtual entity.'
      )
    if update_mask:
      operations.append(
          entity_operation.EntityOperation(
              import_entity,
              operation=entity_enumerations.EntityOperationType.UPDATE,
              update_mask=update_mask,
          )
      )

  return operations


def ReconcileOperations(
    model_operations: List[entity_operation.EntityOperation],
    generated_operations: List[entity_operation.EntityOperation],
) -> List[entity_operation.EntityOperation]:
  """Function to reconcile two lists of entity operations.

  Two lists of operations will be generated for a set of entities. One is parsed
  from a spreadsheet/building config. The other is generated by comparing two
  models. Two operation types that cannot be generated computationally are
  DELETE and EXPORT. These two types will come from either a spreadsheet or
  building config.

  All operations take precedence over EXPORT and DELETE takes precedence over
  all operations.

  Args:
    model_operations: List of EntityOperation instances manually imported from a
      spreadsheet or building config.
    generated_operations: List of Entityoperation instances generated
      automatically from comparing two model instances.

  Returns:
     A list of EntityOperation instances.
  """
  return_operations = []
  generated_operation_map = {
      operation.entity.bc_guid: operation for operation in generated_operations
  }
  for model_operation in model_operations:
    generated_operation = generated_operation_map.get(
        model_operation.entity.bc_guid
    )
    if not generated_operation:
      return_operations.append(model_operation)
    elif (
        model_operation.operation
        == entity_enumerations.EntityOperationType.DELETE
    ):
      return_operations.append(model_operation)
    elif (
        model_operation.operation
        == entity_enumerations.EntityOperationType.EXPORT
        and generated_operation.operation
        != entity_enumerations.EntityOperationType.EXPORT
    ):
      return_operations.append(generated_operation)
    else:
      return_operations.append(generated_operation)
  return return_operations