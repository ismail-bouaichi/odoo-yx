# -*- coding: utf-8 -*-
"""
Script to check floor_created values for projects and sub-projects.
Run this script using Odoo shell:

    python odoo-bin shell -d YOUR_DATABASE_NAME < scripts/check_floor_created.py

Or in interactive shell:
    
    python odoo-bin shell -d YOUR_DATABASE_NAME
    >>> exec(open('odoo/custom_addons/rental_management/scripts/check_floor_created.py').read())
"""

print("\n" + "="*60)
print("FLOOR CREATED VALUES CHECK")
print("="*60)

# Check Projects
print("\n📁 PROJECTS (property.project):")
print("-" * 50)
projects = env['property.project'].search([])
if projects:
    for p in projects:
        print(f"  ID: {p.id:4} | Name: {p.name[:30]:30} | floor_created: {p.floor_created}")
else:
    print("  No projects found.")

# Check Sub Projects
print("\n📂 SUB PROJECTS (property.sub.project):")
print("-" * 50)
sub_projects = env['property.sub.project'].search([])
if sub_projects:
    for sp in sub_projects:
        print(f"  ID: {sp.id:4} | Name: {sp.name[:30]:30} | floor_created: {sp.floor_created}")
else:
    print("  No sub-projects found.")

print("\n" + "="*60)
print("To reset floor_created, run in Odoo shell:")
print("  env['property.project'].browse(PROJECT_ID).floor_created = 0")
print("  env['property.sub.project'].browse(SUBPROJECT_ID).floor_created = 0")
print("  env.cr.commit()")
print("="*60 + "\n")
