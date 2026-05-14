"""Verify database contents and check for duplicates."""

import sqlite3
from pathlib import Path
from collections import Counter

def verify_database(db_path: Path) -> None:
    """
    Verify database integrity and check for duplicates.
    
    Args:
        db_path: Path to SQLite database file
    """
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    print("=" * 70)
    print("DATABASE VERIFICATION REPORT")
    print("=" * 70)
    
    # 1. Total record count
    cursor.execute("SELECT COUNT(*) FROM jobs")
    total_records = cursor.fetchone()[0]
    print(f"\n📊 Total records in database: {total_records}")
    
    # 2. Count distinct source_ids
    cursor.execute("SELECT COUNT(DISTINCT source_id) FROM jobs")
    unique_records = cursor.fetchone()[0]
    print(f"📊 Distinct source_ids: {unique_records}")
    
    # 3. Check for duplicates
    if total_records != unique_records:
        print(f"\n⚠️ DUPLICATES FOUND: {total_records - unique_records} duplicate records")
        
        # Find duplicate source_ids
        cursor.execute("""
            SELECT source_id, COUNT(*) as count 
            FROM jobs 
            GROUP BY source_id 
            HAVING COUNT(*) > 1
        """)
        duplicates = cursor.fetchall()
        
        print("\n📋 Duplicate source_ids:")
        for source_id, count in duplicates:
            print(f"   - {source_id}: appears {count} times")
            
            # Show details of each duplicate
            cursor.execute("""
                SELECT job_title, company, created_at 
                FROM jobs 
                WHERE source_id = ?
            """, (source_id,))
            rows = cursor.fetchall()
            for i, row in enumerate(rows, 1):
                print(f"     [{i}] {row[0]} | {row[1]} | {row[2]}")
    else:
        print("\n✅ NO DUPLICATES FOUND - Database is clean!")
    
    # 4. Compare with Silver JSON files
    silver_path = Path("data/2_silver")
    if silver_path.exists():
        json_files = list(silver_path.glob("*.json"))
        print(f"\n📁 Silver JSON files: {len(json_files)}")
        
        if total_records != len(json_files):
            print(f"⚠️ Mismatch: Database has {total_records}, Silver has {len(json_files)}")
    
    # 5. Show sample of records (first 10)
    print("\n" + "=" * 70)
    print("SAMPLE RECORDS (first 10):")
    print("=" * 70)
    cursor.execute("""
        SELECT source_id, job_title, company, created_at 
        FROM jobs 
        LIMIT 10
    """)
    
    for i, row in enumerate(cursor.fetchall(), 1):
        source_id, job_title, company, created_at = row
        print(f"\n{i}. ID: {source_id}")
        print(f"   Title: {job_title[:60]}..." if len(job_title) > 60 else f"   Title: {job_title}")
        print(f"   Company: {company}")
        print(f"   Created: {created_at}")
    
    # 6. Check for NULL or empty values
    print("\n" + "=" * 70)
    print("DATA QUALITY CHECK:")
    print("=" * 70)
    
    for field in ['source_id', 'job_title', 'company', 'description']:
        cursor.execute(f"SELECT COUNT(*) FROM jobs WHERE {field} IS NULL OR {field} = ''")
        null_count = cursor.fetchone()[0]
        if null_count > 0:
            print(f"⚠️ {field}: {null_count} records have NULL or empty values")
        else:
            print(f"✅ {field}: All records have valid values")
    
    # 7. Check for description length issues
    cursor.execute("""
        SELECT COUNT(*) FROM jobs 
        WHERE LENGTH(description) < 10
    """)
    short_desc = cursor.fetchone()[0]
    if short_desc > 0:
        print(f"⚠️ Description: {short_desc} records have very short descriptions (<10 chars)")
    
    # 8. List all source_ids with their counts
    print("\n" + "=" * 70)
    print("SOURCE_ID DISTRIBUTION:")
    print("=" * 70)
    cursor.execute("""
        SELECT source_id, COUNT(*) as count 
        FROM jobs 
        GROUP BY source_id 
        ORDER BY source_id
    """)
    
    all_ids = cursor.fetchall()
    print(f"Total unique source_ids: {len(all_ids)}")
    
    # Show first 20 source_ids
    print("\nFirst 20 source_ids:")
    for source_id, count in all_ids[:20]:
        print(f"   {source_id}: {count} time(s)")
    
    conn.close()
    
    print("\n" + "=" * 70)
    print("VERIFICATION COMPLETE")
    print("=" * 70)

def find_specific_duplicates(db_path: Path, source_id: str = None) -> None:
    """
    Check for a specific source_id or list all duplicates.
    
    Args:
        db_path: Path to SQLite database
        source_id: Optional specific source_id to check
    """
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    if source_id:
        # Check specific source_id
        cursor.execute("""
            SELECT source_id, job_title, company, created_at 
            FROM jobs 
            WHERE source_id = ?
        """, (source_id,))
        rows = cursor.fetchall()
        
        if len(rows) > 1:
            print(f"\n⚠️ Source_id {source_id} appears {len(rows)} times:")
            for i, row in enumerate(rows, 1):
                print(f"   [{i}] {row[1]} | {row[2]} | {row[3]}")
        elif len(rows) == 1:
            print(f"\n✅ Source_id {source_id} appears once (clean)")
        else:
            print(f"\n❌ Source_id {source_id} not found")
    else:
        # Find all duplicates
        cursor.execute("""
            SELECT source_id, COUNT(*) as count 
            FROM jobs 
            GROUP BY source_id 
            HAVING COUNT(*) > 1
        """)
        duplicates = cursor.fetchall()
        
        if duplicates:
            print(f"\n⚠️ Found {len(duplicates)} duplicate source_ids:")
            for source_id, count in duplicates:
                print(f"   {source_id}: {count} times")
        else:
            print("\n✅ No duplicates found in database")
    
    conn.close()

if __name__ == "__main__":
    db_path = Path("data/3_gold/jobs.db")
    
    # Run full verification
    verify_database(db_path)
    
    # Optional: Check for specific source_id
    # find_specific_duplicates(db_path, "91241058")