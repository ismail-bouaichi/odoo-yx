# -*- coding: utf-8 -*-
"""
Script to reset floor_created values to 0 for all sub-projects.

Usage: python reset_floor_created.py
"""

import psycopg2

# Database connection settings
DB_CONFIG = {
    'dbname': 'Relife',
    'user': 'openpg',
    'password': 'openpgpwd',
    'host': 'localhost',
    'port': '5432'
}

def main():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("")
        print("=" * 60)
        print("RESETTING floor_created VALUES")
        print("=" * 60)
        
        # Reset sub-projects
        cursor.execute("UPDATE property_sub_project SET floor_created = 0")
        sub_count = cursor.rowcount
        
        # Reset projects too
        cursor.execute("UPDATE property_project SET floor_created = 0")
        proj_count = cursor.rowcount
        
        # Commit the changes
        conn.commit()
        
        print("")
        print("SUCCESS!")
        print("  - Updated %s sub-projects" % sub_count)
        print("  - Updated %s projects" % proj_count)
        print("")
        print("All floor_created values are now set to 0.")
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
