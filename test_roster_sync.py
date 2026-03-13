#!/usr/bin/env python3
"""
Simple verification script for the roster sync functionality.
"""

def test_imports():
    """Test that we can import the modules."""
    try:
        import services.database
        print("✓ Successfully imported services.database")
        
        import tasks.roster_sync
        print("✓ Successfully imported tasks.roster_sync")
        
        # Run database tests
        import subprocess
        result = subprocess.run([
            sys.executable, "-m", "pytest", "tests/test_database.py", "-v"
        ], capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__)))
        
        if result.returncode == 0:
            print("✓ Database tests passed")
        else:
            print("✗ Database tests failed:")
            print(result.stdout)
            print(result.stderr)
            
        return result.returncode == 0
        
    except Exception as e:
        print(f"✗ Import test failed: {e}")
        return False

if __name__ == "__main__":
    import os
    import sys
    
    print("Verifying drama-emcee roster sync components...")
    
    if test_imports():
        print("\n✓ All components verified successfully!")
        print("\nYou can now use the roster sync functionality:")
        print("  python -m tasks.roster_sync")
    else:
        print("\n✗ Some components failed verification.")
        sys.exit(1)
