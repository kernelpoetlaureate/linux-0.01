#!/usr/bin/env python3
"""
Examples demonstrating Linux 0.01 Memory Management Simulator features
"""

from memory_simulator import MemorySimulator
import time

def example_basic_memory_operations():
    """Demonstrate basic memory allocation and mapping"""
    print("=== Basic Memory Operations Example ===")
    
    sim = MemorySimulator(debug_level="INFO")
    sim.start_simulation()
    
    print("\n1. Initial state:")
    stats = sim.get_memory_statistics()
    print(f"   Free pages: {stats['physical_memory']['free_pages']}")
    
    print("\n2. Allocating physical pages:")
    pages = []
    for i in range(5):
        page = sim.allocate_page()
        if page != 0:
            pages.append(page)
            print(f"   Allocated page at 0x{page:08x}")
    
    print("\n3. Creating virtual mappings:")
    for i, page in enumerate(pages):
        virt_addr = 0x400000 + (i * 0x1000)  # 4KB apart
        success = sim.map_page(page, virt_addr)
        if success:
            print(f"   Mapped 0x{page:08x} -> 0x{virt_addr:08x}")
    
    print("\n4. Testing address translation:")
    for i in range(len(pages)):
        virt_addr = 0x400000 + (i * 0x1000)
        phys_addr = sim.translate_address(virt_addr)
        if phys_addr:
            print(f"   0x{virt_addr:08x} -> 0x{phys_addr:08x}")
    
    print("\n5. Final statistics:")
    stats = sim.get_memory_statistics()
    print(f"   Pages allocated: {stats['physical_memory']['allocated_pages']}")
    print(f"   Virtual mappings: {stats['virtual_memory']['mappings']}")

def example_process_management():
    """Demonstrate process creation and memory management"""
    print("\n=== Process Management Example ===")
    
    sim = MemorySimulator(debug_level="INFO")
    sim.start_simulation()
    
    print("\n1. Creating initial process:")
    pid1 = sim.create_process()
    print(f"   Created process {pid1}")
    
    print("\n2. Allocating memory for process:")
    addr1 = sim.allocate_process_memory(pid1, 8192)  # 2 pages
    if addr1:
        print(f"   Allocated 8KB at 0x{addr1:08x}")
    
    print("\n3. Forking process (copy-on-write):")
    pid2 = sim.create_process(pid1)
    if pid2 != -1:
        print(f"   Forked process {pid1} -> {pid2}")
    
    print("\n4. Triggering copy-on-write:")
    if addr1:
        # Simulate write to shared page
        success = sim.simulate_page_fault(pid2, addr1, 0x3)  # Write fault
        if success:
            print(f"   COW triggered for address 0x{addr1:08x}")
    
    print("\n5. Process statistics:")
    processes = sim.get_process_list()
    for proc in processes:
        print(f"   PID {proc['pid']}: {proc['memory_usage']} pages, "
              f"{proc['page_faults']} faults")

def example_page_fault_handling():
    """Demonstrate page fault scenarios"""
    print("\n=== Page Fault Handling Example ===")
    
    sim = MemorySimulator(debug_level="INFO")
    sim.start_simulation()
    
    # Create a process
    pid = sim.create_process()
    
    print("\n1. Allocation page fault (new page):")
    success = sim.simulate_page_fault(pid, 0x500000, 0x0)  # Not present
    if success:
        print("   New page allocated and mapped")
    
    print("\n2. Protection fault (copy-on-write):")
    # First allocate some memory
    addr = sim.allocate_process_memory(pid, 4096)
    if addr:
        # Fork to create shared page
        child_pid = sim.create_process(pid)
        if child_pid != -1:
            # Child writes to shared page
            success = sim.simulate_page_fault(child_pid, addr, 0x3)  # Write fault
            if success:
                print("   Copy-on-write page created")
    
    print("\n3. Page fault statistics:")
    stats = sim.get_memory_statistics()
    print(f"   Total page faults: {stats['virtual_memory']['page_faults']}")
    print(f"   COW faults: {stats['virtual_memory']['cow_faults']}")

def example_memory_visualization():
    """Demonstrate memory state visualization"""
    print("\n=== Memory Visualization Example ===")
    
    sim = MemorySimulator(debug_level="ERROR")  # Quiet mode
    sim.start_simulation()
    
    # Allocate some pages in a pattern
    pages = []
    for i in range(10):
        if i % 3 == 0:  # Create fragmentation
            page = sim.allocate_page()
            if page != 0:
                pages.append(page)
    
    # Free every other page
    for i in range(0, len(pages), 2):
        sim.free_page(pages[i])
    
    print("\n1. Memory map visualization:")
    memory_map = sim.get_physical_memory_map()
    
    # Show last 128 pages (most interesting)
    start_page = len(memory_map) - 128
    print("   Legend: . = free, # = allocated")
    print(f"   Showing pages {start_page}-{len(memory_map)-1}:")
    
    for i in range(start_page, len(memory_map), 32):
        row = memory_map[i:i+32]
        chars = ['.' if ref == 0 else '#' for ref in row]
        print(f"   {i:4}: {''.join(chars)}")
    
    print("\n2. Memory statistics:")
    stats = sim.get_memory_statistics()
    print(f"   Fragmentation: {stats['physical_memory']['fragmentation']:.2%}")
    print(f"   Free pages: {stats['physical_memory']['free_pages']}")

def example_simulation_control():
    """Demonstrate simulation control and monitoring"""
    print("\n=== Simulation Control Example ===")
    
    sim = MemorySimulator(debug_level="ERROR")  # Quiet mode
    sim.start_simulation()
    
    print("\n1. Running simulation steps:")
    for step in range(5):
        sim.step_simulation()
        stats = sim.get_memory_statistics()
        print(f"   Step {step+1}: Time {stats['simulation']['time']}, "
              f"Operations {stats['simulation']['operations']}")
        
        # Do some work each step
        if step % 2 == 0:
            sim.allocate_page()
        else:
            sim.create_process()
    
    print("\n2. Event history:")
    events = sim.get_events(limit=5)
    for event in reversed(events):
        print(f"   [{event.timestamp:4.0f}] {event.event_type}: {event.description}")
    
    print("\n3. Pausing and resuming:")
    sim.pause_simulation()
    print("   Simulation paused")
    
    sim.resume_simulation()
    print("   Simulation resumed")

def main():
    """Run all examples"""
    print("Linux 0.01 Memory Management Simulator Examples")
    print("=" * 50)
    
    try:
        example_basic_memory_operations()
        time.sleep(1)
        
        example_process_management()
        time.sleep(1)
        
        example_page_fault_handling()
        time.sleep(1)
        
        example_memory_visualization()
        time.sleep(1)
        
        example_simulation_control()
        
        print("\n" + "=" * 50)
        print("All examples completed successfully!")
        print("\nTry the interactive CLI with: python3 cli.py")
        
    except Exception as e:
        print(f"\nExample failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()