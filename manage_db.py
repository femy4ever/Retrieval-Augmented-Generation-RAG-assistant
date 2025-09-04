import os
import chromadb

def manage_database():
    """Manage the ChromaDB database - list collections and optionally clear them."""
    
    # Use relative path that matches the app
    db_path = os.path.join(os.getcwd(), "database")
    
    print(f"Database path: {db_path}")
    
    # Check if directory exists
    if not os.path.exists(db_path):
        print(f"⚠️  Database directory does not exist: {db_path}")
        print("Creating database directory...")
        os.makedirs(db_path, exist_ok=True)
        print("✅ Database directory created.")
        return

    try:
        # Connect to the database
        chroma_client = chromadb.PersistentClient(path=db_path)

        # List all collections
        all_collections = chroma_client.list_collections()
        
        if not all_collections:
            print("📂 No collections found in the database.")
            return
            
        print(f"📚 Collections found: {len(all_collections)}")
        for collection in all_collections:
            print(f"  - {collection.name}")
            
            # Get collection info
            try:
                count = collection.count()
                print(f"    Documents: {count}")
            except Exception as e:
                print(f"    Error getting count: {e}")

        # Ask user if they want to clear the database
        if all_collections:
            print("\n" + "="*50)
            response = input("Do you want to clear the 'sme_db' collection? (yes/no): ").lower().strip()
            
            if response in ['yes', 'y']:
                collection_names = [c.name for c in all_collections]
                if 'sme_db' in collection_names:
                    chroma_client.delete_collection(name="sme_db")
                    print("🗑️  Collection 'sme_db' has been deleted.")
                else:
                    print("⚠️  Collection 'sme_db' does not exist.")
            else:
                print("❌ No changes made to the database.")

    except Exception as e:
        print(f"❌ Error accessing database: {e}")


def clear_all_collections():
    """Clear all collections in the database."""
    db_path = os.path.join(os.getcwd(), "database")
    
    try:
        chroma_client = chromadb.PersistentClient(path=db_path)
        all_collections = chroma_client.list_collections()
        
        if not all_collections:
            print("📂 No collections to clear.")
            return
            
        print(f"🗑️  Clearing {len(all_collections)} collections...")
        
        for collection in all_collections:
            chroma_client.delete_collection(name=collection.name)
            print(f"  ✅ Deleted: {collection.name}")
            
        print("🎉 All collections cleared!")
        
    except Exception as e:
        print(f"❌ Error clearing database: {e}")


if __name__ == "__main__":
    print("🔧 ChromaDB Management Tool")
    print("="*40)
    
    while True:
        print("\nOptions:")
        print("1. View database status")
        print("2. Clear all collections")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == '1':
            manage_database()
        elif choice == '2':
            confirm = input("⚠️  This will delete ALL data! Are you sure? (yes/no): ").lower().strip()
            if confirm in ['yes', 'y']:
                clear_all_collections()
            else:
                print("❌ Operation cancelled.")
        elif choice == '3':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.")