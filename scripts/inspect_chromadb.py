#!/usr/bin/env python3
"""
Script to inspect ChromaDB contents.
Query and view tweets stored in the RAG system.
"""

import sys
import os
import chromadb

# Try to import tabulate for nice formatting, fallback to simple print
try:
    from tabulate import tabulate
    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def get_collection():
    """Get the ChromaDB collection"""
    # Path where ChromaDB is stored (from tweety_bot.py initialization)
    db_path = os.path.join(os.getcwd(), '.rag_data')

    if not os.path.exists(db_path):
        print(f"❌ ChromaDB path not found: {db_path}")
        print("   Make sure you've run the bot at least once to create the database.")
        return None

    client = chromadb.PersistentClient(path=db_path)

    try:
        collection = client.get_collection(name="tech_twitter_style")
        return collection
    except Exception as e:
        print(f"❌ Error getting collection: {e}")
        return None

def show_stats(collection):
    """Show collection statistics"""
    print("\n" + "="*70)
    print("CHROMADB STATISTICS")
    print("="*70)

    count = collection.count()
    print(f"Total tweets in database: {count}")

    if count == 0:
        print("\n⚠️  Database is empty. Run timeline reading with auto_add_to_rag=True to populate.")
        return

    # Get all items to compute stats
    results = collection.get()

    if results['metadatas']:
        # Count by author
        authors = {}
        categories = {}

        for metadata in results['metadatas']:
            author = metadata.get('author', 'unknown')
            authors[author] = authors.get(author, 0) + 1

            category = metadata.get('category', 'uncategorized')
            categories[category] = categories.get(category, 0) + 1

        print(f"\nTop 10 authors:")
        sorted_authors = sorted(authors.items(), key=lambda x: x[1], reverse=True)[:10]
        for author, count in sorted_authors:
            print(f"  @{author}: {count} tweets")

        print(f"\nBy category:")
        for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            print(f"  {category}: {count} tweets")

def list_tweets(collection, limit=20, category=None, author=None):
    """List tweets in the collection"""
    print("\n" + "="*70)
    print(f"LISTING TWEETS (limit: {limit})")
    print("="*70)

    # Build query
    where_filters = []
    if category:
        where_filters.append({"category": category})
    if author:
        where_filters.append({"author": author})

    # Get items
    if where_filters:
        results = collection.get(where={"$and": where_filters}, limit=limit)
    else:
        results = collection.get(limit=limit)

    if not results['documents']:
        print("No tweets found.")
        return

    # Display results
    if HAS_TABULATE:
        data = []
        for i in range(len(results['documents'])):
            doc = results['documents'][i]
            metadata = results['metadatas'][i] if results['metadatas'] else {}

            data.append([
                i+1,
                metadata.get('author', 'unknown')[:15],
                metadata.get('category', 'N/A')[:15],
                doc[:60] + "..." if len(doc) > 60 else doc,
                metadata.get('engagement', 0),
                metadata.get('length', 0)
            ])

        headers = ["#", "Author", "Category", "Tweet", "Engage", "Words"]
        print(tabulate(data, headers=headers, tablefmt="grid"))
    else:
        # Simple fallback without tabulate
        for i in range(len(results['documents'])):
            doc = results['documents'][i]
            metadata = results['metadatas'][i] if results['metadatas'] else {}

            print(f"\n{i+1}. @{metadata.get('author', 'unknown')} [{metadata.get('category', 'N/A')}]")
            print(f"   {doc}")
            print(f"   Engagement: {metadata.get('engagement', 0)} | Words: {metadata.get('length', 0)}")

def search_tweets(collection, query, n=5):
    """Search for similar tweets using vector similarity"""
    print("\n" + "="*70)
    print(f"SEARCHING FOR: '{query}'")
    print("="*70)

    # Need to create embeddings for search
    # For now, just do text search
    results = collection.get()

    if not results['documents']:
        print("No tweets in database.")
        return

    # Simple text search (case insensitive)
    matches = []
    for i, doc in enumerate(results['documents']):
        if query.lower() in doc.lower():
            metadata = results['metadatas'][i] if results['metadatas'] else {}
            matches.append({
                'author': metadata.get('author', 'unknown'),
                'tweet': doc,
                'category': metadata.get('category', 'N/A'),
                'engagement': metadata.get('engagement', 0)
            })

    if not matches:
        print("No matches found.")
        return

    print(f"\nFound {len(matches)} matches:\n")
    for i, match in enumerate(matches[:n], 1):
        print(f"{i}. @{match['author']} ({match['category']})")
        print(f"   {match['tweet']}")
        print(f"   Engagement: {match['engagement']}\n")

def delete_by_category(collection, category):
    """Delete all tweets in a category"""
    print(f"\n⚠️  Deleting all tweets with category: {category}")
    confirm = input("Are you sure? (yes/no): ")

    if confirm.lower() != 'yes':
        print("Cancelled.")
        return

    results = collection.get(where={"category": category})
    if results['ids']:
        collection.delete(ids=results['ids'])
        print(f"✓ Deleted {len(results['ids'])} tweets")
    else:
        print("No tweets found with that category.")

def main():
    """Main interactive menu"""
    collection = get_collection()

    if not collection:
        return

    while True:
        print("\n" + "="*70)
        print("CHROMADB INSPECTOR")
        print("="*70)
        print("1. Show statistics")
        print("2. List all tweets (limit 20)")
        print("3. List tweets by category")
        print("4. List tweets by author")
        print("5. Search tweets (text search)")
        print("6. Delete by category")
        print("7. Clear entire database")
        print("8. Exit")
        print("="*70)

        choice = input("\nChoice (1-8): ").strip()

        try:
            if choice == "1":
                show_stats(collection)

            elif choice == "2":
                limit = input("How many to show? (default 20): ").strip()
                limit = int(limit) if limit else 20
                list_tweets(collection, limit=limit)

            elif choice == "3":
                category = input("Category name: ").strip()
                list_tweets(collection, limit=50, category=category)

            elif choice == "4":
                author = input("Author username (without @): ").strip()
                list_tweets(collection, limit=50, author=author)

            elif choice == "5":
                query = input("Search query: ").strip()
                n = input("How many results? (default 5): ").strip()
                n = int(n) if n else 5
                search_tweets(collection, query, n)

            elif choice == "6":
                category = input("Category to delete: ").strip()
                delete_by_category(collection, category)

            elif choice == "7":
                print("\n⚠️  WARNING: This will delete ALL tweets from the database!")
                confirm = input("Are you REALLY sure? Type 'DELETE ALL': ")
                if confirm == "DELETE ALL":
                    ids = collection.get()['ids']
                    if ids:
                        collection.delete(ids=ids)
                        print(f"✓ Deleted {len(ids)} tweets")
                    else:
                        print("Database already empty.")
                else:
                    print("Cancelled.")

            elif choice == "8":
                print("Goodbye!")
                break

            else:
                print("Invalid choice.")

        except KeyboardInterrupt:
            print("\nInterrupted. Exiting...")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
