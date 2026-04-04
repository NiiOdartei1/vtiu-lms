"""
Force Production Database Reset
Drops and recreates all tables - complete reset
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import *

def force_reset_production():
    """Complete production database reset"""
    
    print("🔥 FORCE RESET: Production Database")
    print("⚠️  This will DELETE EVERYTHING in production!")
    
    confirm = input("Type 'DELETE-ALL-PRODUCTION-DATA' to confirm: ")
    if confirm != 'DELETE-ALL-PRODUCTION-DATA':
        print("❌ Reset cancelled.")
        return False
    
    with app.app_context():
        try:
            # Drop everything
            db.drop_all()
            print("🗑️  Dropped all tables")
            
            # Recreate everything
            db.create_all()
            print("✅ Recreated all tables")
            
            # Create SuperAdmin
            from models import Admin
            superadmin = Admin(
                admin_id='SUP001',
                username='superadmin',
                email='superadmin@vtiu.edu.gh',
                first_name='System',
                last_name='Administrator',
                role='superadmin'
            )
            superadmin.set_password('admin123')
            db.session.add(superadmin)
            db.session.commit()
            
            print("👤 SuperAdmin created in production")
            print("🎉 Production database completely reset!")
            return True
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

if __name__ == "__main__":
    force_reset_production()
