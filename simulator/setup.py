#!/usr/bin/env python3
"""
Setup and test script for Linux 0.01 Memory Management Simulator
"""

import sys
import os
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        return False
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def run_basic_test():
    """Run basic functionality test"""
    print("\n=== Running Basic Test ===")
    
    try:
        # Import and test core modules
        from memory_simulator import MemorySimulator
        from physical_memory import PhysicalMemory
        from virtual_memory import VirtualMemory
        from process_manager import ProcessManager
        import config
        
        print("✓ All modules imported successfully")
        
        # Create simulator instance
        simulator = MemorySimulator(debug_level="ERROR")  # Quiet mode for testing
        print("✓ Simulator instance created")
        
        # Test basic operations
        simulator.start_simulation()
        
        # Test page allocation
        page1 = simulator.allocate_page()
        assert page1 != 0, "Page allocation failed"
        print("✓ Page allocation works")
        
        # Test process creation
        pid = simulator.create_process()
        assert pid != -1, "Process creation failed"
        print("✓ Process creation works")
        
        # Test memory allocation for process
        addr = simulator.allocate_process_memory(pid, 4096)
        assert addr is not None, "Process memory allocation failed"
        print("✓ Process memory allocation works")
        
        # Test page fault simulation
        success = simulator.simulate_page_fault(pid, 0x500000, 0)
        assert success, "Page fault handling failed"
        print("✓ Page fault handling works")
        
        # Test statistics
        stats = simulator.get_memory_statistics()
        assert stats is not None, "Statistics retrieval failed"
        assert stats['physical_memory']['total_pages'] == config.PAGING_PAGES
        print("✓ Statistics collection works")
        
        simulator.stop_simulation()
        print("✓ Basic functionality test passed!")
        return True
        
    except Exception as e:
        print(f"✗ Basic test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_demo_tests():
    """Run demonstration scenarios"""
    print("\n=== Running Demo Tests ===")
    
    try:
        from memory_simulator import MemorySimulator
        
        simulator = MemorySimulator(debug_level="ERROR")
        simulator.start_simulation()
        
        # Test basic demo
        print("Running basic demo...")
        simulator.run_basic_demo()
        print("✓ Basic demo completed")
        
        # Reset for next test
        simulator.reset_simulation()
        simulator.start_simulation()
        
        # Test fork demo
        print("Running fork demo...")
        simulator.run_fork_demo()
        print("✓ Fork demo completed")
        
        # Test with some stress
        simulator.reset_simulation()
        simulator.start_simulation()
        
        print("Running mini stress test...")
        simulator.run_stress_test(10)  # Small stress test
        print("✓ Stress test completed")
        
        simulator.stop_simulation()
        print("✓ All demo tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Demo tests failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_cli_test():
    """Test CLI interface"""
    print("\n=== Testing CLI Interface ===")
    
    try:
        # Test non-interactive mode
        result = subprocess.run([
            sys.executable, "cli.py", "basic"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✓ CLI basic demo works")
            return True
        else:
            print(f"✗ CLI test failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("✗ CLI test timed out")
        return False
    except Exception as e:
        print(f"✗ CLI test failed: {e}")
        return False

def check_file_structure():
    """Check if all required files are present"""
    print("\n=== Checking File Structure ===")
    
    required_files = [
        "config.py",
        "physical_memory.py", 
        "virtual_memory.py",
        "process_manager.py",
        "memory_simulator.py",
        "cli.py",
        "requirements.txt",
        "ARCHITECTURE.md"
    ]
    
    all_present = True
    for filename in required_files:
        if os.path.exists(filename):
            print(f"✓ {filename}")
        else:
            print(f"✗ {filename} missing")
            all_present = False
    
    return all_present

def display_usage_info():
    """Display usage information"""
    print("""
=== Linux 0.01 Memory Management Simulator ===

Usage:
  python setup.py          - Run this setup and test script
  python cli.py            - Start interactive CLI
  python cli.py basic      - Run basic demo
  python cli.py fork       - Run fork/COW demo  
  python cli.py stress     - Run stress test

Key Features:
  ✓ Accurate Linux 0.01 memory management simulation
  ✓ Physical page allocation with mem_map[] tracking
  ✓ 2-level page table system (page directory + page tables)
  ✓ Copy-on-write (COW) implementation
  ✓ Process management with fork() simulation
  ✓ Page fault handling (do_no_page, do_wp_page)
  ✓ Interactive command-line interface
  ✓ Real-time statistics and visualization
  ✓ Educational step-by-step execution

Memory Layout:
  0x000000 - 0x100000 (1MB)  : Kernel space
  0x100000 - 0x200000 (1MB)  : Buffer space  
  0x200000 - 0x800000 (6MB)  : User pages (1536 pages)

For detailed architecture information, see ARCHITECTURE.md
""")

def main():
    """Main setup and test function"""
    print("Linux 0.01 Memory Management Simulator Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return 1
    
    # Check file structure
    if not check_file_structure():
        print("\n✗ Some required files are missing!")
        return 1
    
    # Add current directory to Python path for testing
    sys.path.insert(0, os.getcwd())
    
    # Run tests
    tests_passed = 0
    total_tests = 3
    
    if run_basic_test():
        tests_passed += 1
    
    if run_demo_tests():
        tests_passed += 1
    
    if run_cli_test():
        tests_passed += 1
    
    # Summary
    print(f"\n=== Test Summary ===")
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("✓ All tests passed! Simulator is ready to use.")
        display_usage_info()
        return 0
    else:
        print("✗ Some tests failed. Please check the error messages above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())