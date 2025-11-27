#!/usr/bin/env python
"""Database initialization script for Twende Tours.

This script initializes the tours database with default tour data.
It can be run standalone or called from app startup to ensure
the database is populated with tour data.

Usage:
    python scripts/init_tours.py [--force]
    
Options:
    --force     Clear existing tours and repopulate with defaults
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from app import app, db
from models import Tour
from data.tours_data import DEFAULT_TOURS


def init_tours(force=False):
    """Initialize the tours database with default data.
    
    Args:
        force: If True, delete existing tours and repopulate.
               If False, only add tours that don't exist.
    
    Returns:
        dict with counts of created, existing, and total tours
    """
    with app.app_context():
        if force:
            # Delete all existing tours
            deleted_count = Tour.query.delete()
            db.session.commit()
            print(f"Deleted {deleted_count} existing tours")
        
        created_tours = []
        existing_tours = []
        
        for tour_data in DEFAULT_TOURS:
            # Check if tour exists
            existing = Tour.query.filter(Tour.title == tour_data['title']).first()
            
            if existing:
                existing_tours.append(existing.title)
            else:
                new_tour = Tour(**tour_data)
                db.session.add(new_tour)
                created_tours.append(tour_data['title'])
        
        db.session.commit()
        
        # Get total count
        total_count = Tour.query.count()
        
        return {
            'created_count': len(created_tours),
            'existing_count': len(existing_tours),
            'total_count': total_count,
            'created_tours': created_tours,
            'existing_tours': existing_tours
        }


def main():
    """Main entry point for the script."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Initialize the Twende Tours database with default tours.'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Delete existing tours and repopulate with defaults'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress output except errors'
    )
    
    args = parser.parse_args()
    
    if not args.quiet:
        print("Twende Tours Database Initialization")
        print("=" * 40)
        if args.force:
            print("WARNING: Force mode - all existing tours will be deleted!")
            response = input("Continue? (y/N): ")
            if response.lower() != 'y':
                print("Aborted.")
                sys.exit(0)
    
    try:
        result = init_tours(force=args.force)
        
        if not args.quiet:
            print(f"\nResults:")
            print(f"  Created: {result['created_count']} tours")
            print(f"  Existing: {result['existing_count']} tours")
            print(f"  Total: {result['total_count']} tours")
            
            if result['created_tours']:
                print(f"\nNewly created tours:")
                for title in result['created_tours']:
                    print(f"  - {title}")
        
            print("\nDatabase initialization complete!")
        
    except Exception as e:
        print(f"Error initializing database: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
