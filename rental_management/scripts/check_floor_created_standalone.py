# -*- coding: utf-8 -*-
"""
Standalone script to check floor_created values.
This connects directly to PostgreSQL without Odoo dependencies.

Usage: python check_floor_created_standalone.py
"""

import psycopg2

# Database connection settings - UPDATE THESE
DB_CONFIG = {
    'dbname': 'Relife',           # Your database name
    'user': 'openpg',               # PostgreSQL username
    'password': 'openpgpwd',       # PostgreSQL password
    'host': 'localhost',          # Database host
    'port': '5432'                # PostgreSQL port
}

def main():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("\n" + "="*60)
        print("FLOOR CREATED VALUES CHECK")
        print("="*60)
        
        # Check Projects
        print("\n📁 PROJECTS (property_project):")
        print("-" * 50)
        cursor.execute("SELECT id, name, floor_created FROM property_project ORDER BY id")
        projects = cursor.fetchall()
        if projects:
            for p in projects:
                name = (p[1] or "")[:30]
                print(f"  ID: {p[0]:4} | Name: {name:30} | floor_created: {p[2]}")
        else:
            print("  No projects found.")
        
        # Check Sub Projects
        print("\n📂 SUB PROJECTS (property_sub_project):")
        print("-" * 50)
        cursor.execute("SELECT id, name, floor_created FROM property_sub_project ORDER BY id")
        sub_projects = cursor.fetchall()
        if sub_projects:
            for sp in sub_projects:
                name = (sp[1] or "")[:30]
                print(f"  ID: {sp[0]:4} | Name: {name:30} | floor_created: {sp[2]}")
        else:
            print("  No sub-projects found.")
        
        print("\n" + "="*60)
        print("To RESET floor_created, run SQL:")
        print("  UPDATE property_project SET floor_created = 0 WHERE id = PROJECT_ID;")
        print("  UPDATE property_sub_project SET floor_created = 0 WHERE id = SUBPROJECT_ID;")
        print("="*60 + "\n")
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
