"""
Clear Render PostgreSQL Database
Direct connection to clear all production data
"""

import psycopg2
from psycopg2 import sql
from werkzeug.security import generate_password_hash

# Render PostgreSQL credentials
DB_CONFIG = {
    'host': 'dpg-d66d9besb7us73an19bg-a.oregon-postgres.render.com',
    'port': 5432,
    'database': 'vtiu_db_mxus',
    'user': 'vtiu_db_mxus_user',
    'password': 'g0Zgb69qtKgP6CHZvXB6at3dkMDnUxnQ'
}

def clear_render_database():
    """Clear all data from Render PostgreSQL database"""
    
    print("🌐 Connecting to Render PostgreSQL database...")
    print("⚠️  WARNING: This will delete ALL production data!")
    
    confirm = input("Type 'CLEAR-RENDER-DB' to confirm: ")
    if confirm != 'CLEAR-RENDER-DB':
        print("❌ Operation cancelled.")
        return False
    
    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        cursor = conn.cursor()
        
        print("✅ Connected to database")
        
        # Get all table names
        cursor.execute("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"📋 Found {len(tables)} tables: {', '.join(tables)}")
        
        # Disable foreign key constraints
        cursor.execute("SET session_replication_role = replica;")
        
        # Clear data from all tables (except alembic_version)
        cleared_count = 0
        for table in tables:
            if table != 'alembic_version':
                try:
                    cursor.execute(sql.SQL("TRUNCATE TABLE {} RESTART IDENTITY CASCADE;").format(sql.Identifier(table)))
                    print(f"✅ Cleared table: {table}")
                    cleared_count += 1
                except Exception as e:
                    print(f"⚠️  Could not clear {table}: {e}")
        
        # Re-enable foreign key constraints
        cursor.execute("SET session_replication_role = DEFAULT;")
        
        # Create admin table if it doesn't exist and add SuperAdmin
        try:
            # Check if admin table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'admin'
                );
            """)
            admin_table_exists = cursor.fetchone()[0]
            
            if not admin_table_exists:
                # Create admin table
                cursor.execute("""
                    CREATE TABLE admin (
                        id SERIAL PRIMARY KEY,
                        admin_id TEXT UNIQUE NOT NULL,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT,
                        first_name TEXT,
                        last_name TEXT,
                        role TEXT,
                        password_hash TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                print("✅ Created admin table")
            
            # Insert SuperAdmin
            password_hash = generate_password_hash('admin123')
            cursor.execute("""
                INSERT INTO admin (admin_id, username, email, first_name, last_name, role, password_hash)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (admin_id) DO UPDATE SET
                    username = EXCLUDED.username,
                    email = EXCLUDED.email,
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    role = EXCLUDED.role,
                    password_hash = EXCLUDED.password_hash;
            """, ('SUP001', 'superadmin', 'superadmin@vtiu.edu.gh', 'System', 'Administrator', 'superadmin', password_hash))
            
            print("👤 Created/updated SuperAdmin account")
            
        except Exception as e:
            print(f"⚠️  Admin setup issue: {e}")
        
        # Commit all changes
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"\n🎉 SUCCESS! Cleared {cleared_count} tables in production database")
        print("👤 SuperAdmin credentials:")
        print("   Username: superadmin")
        print("   Password: admin123")
        print("   Admin ID: SUP001")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    clear_render_database()
