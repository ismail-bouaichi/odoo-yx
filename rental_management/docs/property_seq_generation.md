# Property Code (`property_seq`) Generation

This document explains how the `property_seq` (Property Code) field is generated in the rental_management module.

## Overview

The `property_seq` field is a unique identifier for each property unit. It can be generated in two ways:

1. **Automatically via the Unit Creation Wizard** - Uses a structured format
2. **Via Odoo Sequence** - Fallback when created manually

---

## Method 1: Unit Creation Wizard

When creating units in bulk via the wizard, the code follows this format:

```
{prefix}{floor:02d}-{unit:02d}
```

### Example

| Prefix | Floor | Unit | Generated Code |
|--------|-------|------|----------------|
| BL1-   | 2     | 3    | `BL1-02-03`    |
| A-     | 5     | 12   | `A-05-12`      |
| RDC-   | 0     | 1    | `RDC-00-01`    |

### Source Code

**File:** `wizard/unit_creation.py`

```python
code = "%s%s-%s" % (
    self.property_code_prefix,
    str(floor).zfill(2),
    str(unit).zfill(2)
)
property_data.append({
    "property_seq": code,
    ...
})
```

---

## Method 2: Automatic Sequence (Fallback)

When a property is created manually (without the wizard) and no `property_seq` is provided, the system uses an Odoo sequence.

### Source Code

**File:** `models/property_details.py`

```python
@api.model_create_multi
def create(self, vals_list):
    for vals in vals_list:
        if not vals.get('property_seq'):
            vals['property_seq'] = self.env['ir.sequence'].next_by_code(
                'property.details') or ''
    res = super(PropertyDetails, self).create(vals_list)
    return res
```

The sequence `property.details` is defined in the module's data files.

---

## Summary

| Creation Method         | Code Format              | Example       |
|------------------------|--------------------------|---------------|
| Unit Creation Wizard   | `{prefix}{floor}-{unit}` | `BL1-02-03`   |
| Manual Form Creation   | Auto-sequence            | `PROP00001`   |

---

## Special Floor Feature

The wizard also supports a **Special Floor** scenario where one floor can have a different number of units:

- `has_special_floor`: Enable exception
- `special_floor_number`: The floor with different units
- `special_floor_units`: Number of units on that floor

This allows flexible unit generation for buildings with irregular floor layouts.
