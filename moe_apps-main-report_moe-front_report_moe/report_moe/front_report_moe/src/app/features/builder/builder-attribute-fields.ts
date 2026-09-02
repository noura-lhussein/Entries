import type { Attribute } from '../../core/services/builder.service';
import type { FormFieldConfig } from '../../shared/components/dynamic-form/dynamic-form.component';
import { FORM_FILE_ACCEPT, FORM_IMAGE_ACCEPT } from './form-accept.constants';
import { ENTITY_ATTRIBUTE_TYPES, isEntityAttributeType } from './entity-attribute-types';

export { isEntityAttributeType } from './entity-attribute-types';

/** Synthetic form control key when the schema has `district` but no `city` attribute. */
export const VIRTUAL_CITY_FIELD_KEY = '__virtual_city__';

export interface LocationOption {
  id: number;
  name: string;
}

export interface LocationCascadeOptions {
  governorates: LocationOption[];
  districts: LocationOption[];
  subdistricts: LocationOption[];
  communities: LocationOption[];
  selectedGovernorateId: number | null;
  selectedDistrictId: number | null;
  selectedSubdistrictId: number | null;
}

const LOCATION_TYPES = ['city', 'district', 'sub_district', 'community'] as const;

export function isLocationAttributeType(type: string): boolean {
  return (LOCATION_TYPES as readonly string[]).includes(type);
}

export function getEffectiveCityFieldKey(attrs: Attribute[]): string | null {
  const cityAttr = attrs.find((a) => a.type === 'city');
  if (cityAttr) return String(cityAttr.id);
  const hasDistrictOnly =
    attrs.some((a) => a.type === 'district') && !attrs.some((a) => a.type === 'city');
  return hasDistrictOnly ? VIRTUAL_CITY_FIELD_KEY : null;
}

export function getLocationAttributeKey(attrs: Attribute[], type: string): string | null {
  const attr = attrs.find((a) => a.type === type);
  return attr ? String(attr.id) : null;
}

export function getDistrictAttributeKey(attrs: Attribute[]): string | null {
  return getLocationAttributeKey(attrs, 'district');
}

export function getSubDistrictAttributeKey(attrs: Attribute[]): string | null {
  return getLocationAttributeKey(attrs, 'sub_district');
}

export function getCommunityAttributeKey(attrs: Attribute[]): string | null {
  return getLocationAttributeKey(attrs, 'community');
}

export function mapAttributeTypeToFormFieldType(type: string): FormFieldConfig['type'] {
  const map: Record<string, FormFieldConfig['type']> = {
    text: 'input',
    textarea: 'textarea',
    number: 'input',
    date: 'date',
    boolean: 'checkbox',
    select: 'select',
    city: 'select',
    district: 'select',
    sub_district: 'select',
    community: 'select',
    image: 'file',
    file: 'file',
  };
  for (const entityType of ENTITY_ATTRIBUTE_TYPES) {
    map[entityType] = 'select';
  }
  return map[type] || 'input';
}

export function mapAttributeInputType(type: string): FormFieldConfig['inputType'] {
  if (type === 'number') return 'number';
  return 'text';
}

export function buildFormFieldsFromAttributes(params: {
  attrs: Attribute[];
  location: LocationCascadeOptions;
  effectiveCityFieldKey: string | null;
  cityVirtualLabel: string;
  entityOptionsByType?: Record<string, LocationOption[]>;
}): FormFieldConfig[] {
  const { attrs, location, effectiveCityFieldKey, cityVirtualLabel, entityOptionsByType } =
    params;
  const {
    governorates,
    districts,
    subdistricts,
    communities,
    selectedGovernorateId,
    selectedDistrictId,
    selectedSubdistrictId,
  } = location;

  const hasCityAttribute = attrs.some((a) => a.type === 'city');
  const hasDistrictAttribute = attrs.some((a) => a.type === 'district');

  const fields: FormFieldConfig[] = attrs.map((attr) => {
    const formType = mapAttributeTypeToFormFieldType(attr.type);
    const field: FormFieldConfig = {
      key: attr.id.toString(),
      type: formType,
      label: attr.label,
      required: attr.required,
    };

    if (formType === 'input') {
      field.inputType = mapAttributeInputType(attr.type);
    }

    if (formType === 'select') {
      if (attr.type === 'city') {
        field.options = governorates.map((c) => ({ value: c.id, label: c.name }));
      } else if (attr.type === 'district') {
        field.options = districts.map((d) => ({ value: d.id, label: d.name }));
        field.disabled = !!effectiveCityFieldKey && !selectedGovernorateId;
      } else if (attr.type === 'sub_district') {
        field.options = subdistricts.map((s) => ({ value: s.id, label: s.name }));
        field.disabled = !selectedDistrictId;
      } else if (attr.type === 'community') {
        field.options = communities.map((c) => ({ value: c.id, label: c.name }));
        field.disabled = !selectedSubdistrictId;
      } else if (isEntityAttributeType(attr.type)) {
        const opts = entityOptionsByType?.[attr.type] ?? [];
        field.options = opts.map((o) => ({ value: o.id, label: o.name }));
      } else {
        field.options = (attr.options || []).map((o) => ({
          value: o.value ?? o.label,
          label: o.label,
        }));
      }
    }

    if (formType === 'file') {
      field.fileKind = attr.type === 'image' ? 'image' : 'file';
      field.fileAccept = attr.type === 'image' ? FORM_IMAGE_ACCEPT : FORM_FILE_ACCEPT;
    }

    return field;
  });

  if (hasDistrictAttribute && !hasCityAttribute) {
    const districtIndex = fields.findIndex((f) => {
      const a = attrs.find((x) => String(x.id) === f.key);
      return a?.type === 'district';
    });
    const virtualCityField: FormFieldConfig = {
      key: VIRTUAL_CITY_FIELD_KEY,
      type: 'select',
      label: cityVirtualLabel,
      required: true,
      options: governorates.map((c) => ({ value: c.id, label: c.name })),
    };
    if (districtIndex >= 0) {
      fields.splice(districtIndex, 0, virtualCityField);
    } else {
      fields.push(virtualCityField);
    }
  }

  return fields;
}
