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
    'user': 'openpg',             # PostgreSQL username
    'password': 'openpgpwd',      # PostgreSQL password
    'host': 'localhost',          # Database host
    'port': '5432'                # PostgreSQL port
}

def main():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("")
        print("=" * 60)
        print("FLOOR CREATED VALUES CHECK")
        print("=" * 60)
        
        # Check Projects
        print("")
        print("[PROJECTS] (property_project):")
        print("-" * 50)
        cursor.execute("SELECT id, name, floor_created FROM property_project ORDER BY id")
        projects = cursor.fetchall()
        if projects:
            for row in projects:
                pid = row[0]
                pname = str(row[1] if row[1] else "")
                if len(pname) > 30:
                    pname = pname[:30]
                floor_val = row[2]
                print("  ID: %s | Name: %s | floor_created: %s" % (pid, pname, floor_val))
        else:
            print("  No projects found.")
        
        # Check Sub Projects
        print("")
        print("[SUB PROJECTS] (property_sub_project):")
        print("-" * 50)
        cursor.execute("SELECT id, name, floor_created FROM property_sub_project ORDER BY id")
        sub_projects = cursor.fetchall()
        if sub_projects:
            for row in sub_projects:
                spid = row[0]
                spname = str(row[1] if row[1] else "")
                if len(spname) > 30:
                    spname = spname[:30]
                floor_val = row[2]
                print("  ID: %s | Name: %s | floor_created: %s" % (spid, spname, floor_val))
        else:
            print("  No sub-projects found.")
        
        print("")
        print("=" * 60)
        print("To RESET floor_created, run SQL:")
        print("  UPDATE property_project SET floor_created = 0 WHERE id = PROJECT_ID;")
        print("  UPDATE property_sub_project SET floor_created = 0 WHERE id = SUBPROJECT_ID;")
        print("=" * 60)
        print("")
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print("Database error: %s" % e)
    except Exception as e:
        print("Error: %s" % e)

if __name__ == "__main__":
    main()
