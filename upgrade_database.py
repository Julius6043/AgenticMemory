"""
Database upgrade script for Enhanced AgenticMemory System.

This script upgrades existing Supabase tables to support the new features
from the Ground_version integration, including memory links and enhanced metadata.
"""

import os
import sys
from typing import Optional

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from src.database.supabase_client import SupabaseMemoryClient
from src.database.supabase_config import SupabaseConfigManager


class DatabaseUpgrader:
    """Handles database schema upgrades for enhanced memory system."""

    def __init__(self, supabase_client: Optional[SupabaseMemoryClient] = None):
        """Initialize the upgrader.

        Args:
            supabase_client: Optional Supabase client instance
        """
        self.client = supabase_client or SupabaseMemoryClient()

    def check_connection(self) -> bool:
        """Check if we can connect to Supabase.

        Returns:
            bool: True if connection successful
        """
        try:
            return self.client.test_connection()
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False

    def check_table_exists(self, table_name: str) -> bool:
        """Check if a table exists.

        Args:
            table_name: Name of the table to check

        Returns:
            bool: True if table exists
        """
        try:
            # Try to query the table
            result = (
                self.client.client.table(table_name).select("*").range(0, 0).execute()
            )
            return True
        except Exception:
            return False

    def check_column_exists(self, table_name: str, column_name: str) -> bool:
        """Check if a column exists in a table.

        Args:
            table_name: Name of the table
            column_name: Name of the column

        Returns:
            bool: True if column exists
        """
        try:
            # Try to select the specific column
            result = (
                self.client.client.table(table_name)
                .select(column_name)
                .range(0, 0)
                .execute()
            )
            return True
        except Exception:
            return False

    def upgrade_memories_table(self) -> bool:
        """Upgrade the memories table with new columns.

        Returns:
            bool: True if upgrade successful
        """
        print("🔄 Upgrading memories table...")

        try:
            # Check if linked_memory_ids column exists
            if not self.check_column_exists("memories", "linked_memory_ids"):
                print("   Adding linked_memory_ids column...")

                # Execute SQL to add the column
                sql = """
                ALTER TABLE memories 
                ADD COLUMN IF NOT EXISTS linked_memory_ids UUID[] DEFAULT '{}';
                """

                result = self.client.client.rpc("exec_sql", {"sql": sql}).execute()
                print("   ✅ Added linked_memory_ids column")
            else:
                print("   ✅ linked_memory_ids column already exists")

            # Check if evolution_count column exists
            if not self.check_column_exists("memories", "evolution_count"):
                print("   Adding evolution_count column...")

                sql = """
                ALTER TABLE memories 
                ADD COLUMN IF NOT EXISTS evolution_count INTEGER DEFAULT 0;
                """

                result = self.client.client.rpc("exec_sql", {"sql": sql}).execute()
                print("   ✅ Added evolution_count column")
            else:
                print("   ✅ evolution_count column already exists")

            return True

        except Exception as e:
            print(f"   ❌ Failed to upgrade memories table: {e}")
            return False

    def create_memory_links_table(self) -> bool:
        """Create the memory_links table if it doesn't exist.

        Returns:
            bool: True if creation successful
        """
        print("🔄 Creating memory_links table...")

        try:
            if self.check_table_exists("memory_links"):
                print("   ✅ memory_links table already exists")
                return True

            sql = """
            CREATE TABLE IF NOT EXISTS memory_links (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                source_memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
                target_memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
                link_type TEXT DEFAULT 'related',
                strength REAL DEFAULT 1.0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                UNIQUE(source_memory_id, target_memory_id, link_type)
            );
            """

            result = self.client.client.rpc("exec_sql", {"sql": sql}).execute()
            print("   ✅ Created memory_links table")

            # Create indexes
            index_sql = """
            CREATE INDEX IF NOT EXISTS idx_memory_links_source ON memory_links(source_memory_id);
            CREATE INDEX IF NOT EXISTS idx_memory_links_target ON memory_links(target_memory_id);
            """

            result = self.client.client.rpc("exec_sql", {"sql": index_sql}).execute()
            print("   ✅ Created memory_links indexes")

            return True

        except Exception as e:
            print(f"   ❌ Failed to create memory_links table: {e}")
            return False

    def create_helper_functions(self) -> bool:
        """Create helper functions for memory link management.

        Returns:
            bool: True if creation successful
        """
        print("🔄 Creating helper functions...")

        try:
            # Function to update linked memory IDs
            sql = """
            CREATE OR REPLACE FUNCTION update_linked_memory_ids()
            RETURNS TRIGGER AS $$
            BEGIN
                -- Update source memory's linked_memory_ids
                UPDATE memories 
                SET linked_memory_ids = array_append(
                    COALESCE(linked_memory_ids, '{}'), 
                    NEW.target_memory_id
                )
                WHERE id = NEW.source_memory_id 
                AND NOT (NEW.target_memory_id = ANY(COALESCE(linked_memory_ids, '{}')));
                
                -- Update target memory's linked_memory_ids  
                UPDATE memories 
                SET linked_memory_ids = array_append(
                    COALESCE(linked_memory_ids, '{}'), 
                    NEW.source_memory_id
                )
                WHERE id = NEW.target_memory_id 
                AND NOT (NEW.source_memory_id = ANY(COALESCE(linked_memory_ids, '{}')));
                
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            """

            result = self.client.client.rpc("exec_sql", {"sql": sql}).execute()
            print("   ✅ Created update_linked_memory_ids function")

            # Create trigger
            trigger_sql = """
            DROP TRIGGER IF EXISTS trigger_update_linked_memory_ids ON memory_links;
            CREATE TRIGGER trigger_update_linked_memory_ids
                AFTER INSERT ON memory_links
                FOR EACH ROW EXECUTE FUNCTION update_linked_memory_ids();
            """

            result = self.client.client.rpc("exec_sql", {"sql": trigger_sql}).execute()
            print("   ✅ Created memory links trigger")

            return True

        except Exception as e:
            print(f"   ❌ Failed to create helper functions: {e}")
            return False

    def run_full_upgrade(self) -> bool:
        """Run the complete database upgrade.

        Returns:
            bool: True if all upgrades successful
        """
        print("🚀 Starting Enhanced AgenticMemory Database Upgrade")
        print("=" * 60)

        if not self.check_connection():
            print("❌ Cannot connect to database. Please check your configuration.")
            return False

        print("✅ Connected to Supabase successfully")

        success = True

        # Upgrade memories table
        if not self.upgrade_memories_table():
            success = False

        # Create memory_links table
        if not self.create_memory_links_table():
            success = False

        # Create helper functions
        if not self.create_helper_functions():
            success = False

        if success:
            print("\n" + "=" * 60)
            print("🎉 Database upgrade completed successfully!")
            print("=" * 60)
            print("\nYour database now supports:")
            print("✅ Memory linking functionality")
            print("✅ Enhanced metadata tracking")
            print("✅ Evolution counting")
            print("✅ Bidirectional link management")
            print("✅ Automatic link synchronization")
        else:
            print("\n" + "=" * 60)
            print("❌ Database upgrade completed with errors!")
            print("=" * 60)
            print("Please check the error messages above and retry.")

        return success

    def verify_upgrade(self) -> bool:
        """Verify that the upgrade was successful.

        Returns:
            bool: True if verification successful
        """
        print("\n🔍 Verifying database upgrade...")

        checks = [
            ("memories table", lambda: self.check_table_exists("memories")),
            ("memory_links table", lambda: self.check_table_exists("memory_links")),
            (
                "linked_memory_ids column",
                lambda: self.check_column_exists("memories", "linked_memory_ids"),
            ),
            (
                "evolution_count column",
                lambda: self.check_column_exists("memories", "evolution_count"),
            ),
        ]

        all_passed = True

        for check_name, check_func in checks:
            try:
                if check_func():
                    print(f"   ✅ {check_name}")
                else:
                    print(f"   ❌ {check_name}")
                    all_passed = False
            except Exception as e:
                print(f"   ❌ {check_name}: {e}")
                all_passed = False

        if all_passed:
            print("\n✅ All verification checks passed!")
        else:
            print("\n❌ Some verification checks failed!")

        return all_passed


def main():
    """Main upgrade function."""

    # Check environment variables
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"):
        print("❌ Missing SUPABASE_URL or SUPABASE_KEY environment variables")
        print("Please set these variables before running the upgrade")
        sys.exit(1)

    # Create upgrader and run upgrade
    upgrader = DatabaseUpgrader()

    # Run the upgrade
    success = upgrader.run_full_upgrade()

    if success:
        # Verify the upgrade
        verification_success = upgrader.verify_upgrade()

        if verification_success:
            print("\n🎯 Next steps:")
            print(
                "1. Test the enhanced system with: python test_enhanced_memory_system.py"
            )
            print("2. Use the new SupabaseAgenticMemorySystem class in your code")
            print("3. Enjoy enhanced memory linking and evolution features!")
        else:
            print("\n⚠️ Upgrade completed but verification failed.")
            print("Please check your database manually.")
            sys.exit(1)
    else:
        print("\n❌ Upgrade failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
