# Linux 0.01 Memory Management Simulator

A comprehensive, educational Python simulator that accurately models the memory management system from the original Linux 0.01 kernel. This simulator provides an interactive way to understand early Unix/Linux memory management concepts including physical page allocation, virtual memory with 2-level page tables, copy-on-write, and process management.

## 🎯 Educational Objectives

This simulator helps students and developers understand:

- **Physical Memory Management**: Page-based allocation, free page tracking, and memory fragmentation
- **Virtual Memory**: 2-level page table system, address translation, and memory protection  
- **Process Memory Management**: Memory context switching, copy-on-write optimization, and memory inheritance
- **Page Fault Handling**: Allocation faults and protection faults (COW)
- **Historical Computing**: How memory management worked in early Linux systems

## 🏗️ Architecture

Based on the authentic Linux 0.01 source code from 1991, the simulator implements:

### Memory Layout
```
Physical Memory (8MB total):
├── 0x000000-0x100000 (1MB)  : Kernel code and data
├── 0x100000-0x200000 (1MB)  : Buffer cache  
└── 0x200000-0x800000 (6MB)  : User pages (1792 × 4KB pages)
```

### Core Components
- **PhysicalMemory**: Manages the `mem_map[]` array and page allocation
- **VirtualMemory**: Implements 2-level page tables and address translation
- **ProcessManager**: Handles process creation, memory contexts, and scheduling
- **MemorySimulator**: Coordinates all components and provides simulation control

### Key Algorithms Implemented
- `get_free_page()` - Physical page allocation using backward scanning
- `put_page()` - Virtual to physical address mapping  
- `copy_page_tables()` - Page table copying for fork() with COW setup
- `do_no_page()` - New page allocation on page faults
- `do_wp_page()` - Copy-on-write page fault handling

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- No external dependencies (uses only Python standard library)

### Installation & Testing
```bash
cd simulator/
python3 setup.py    # Run comprehensive tests
```

### Basic Usage
```bash
# Interactive CLI mode
python3 cli.py

# Run demonstrations
python3 cli.py basic    # Basic memory operations
python3 cli.py fork     # Process forking and COW
python3 cli.py stress   # Stress testing
```

## 📖 Usage Examples

### Interactive CLI Commands

```bash
# Memory operations
(mm-sim) alloc                    # Allocate a physical page
(mm-sim) free 0x7ff000           # Free a physical page
(mm-sim) map 0x7ff000 0x400000   # Map physical to virtual address
(mm-sim) translate 0x400000      # Translate virtual to physical

# Process management  
(mm-sim) fork                    # Create new process
(mm-sim) fork 1                  # Create child of process 1
(mm-sim) switch 1                # Switch to process 1
(mm-sim) exit 1                  # Terminate process 1

# Simulation
(mm-sim) fault 1 0x500000        # Simulate page fault
(mm-sim) step                    # Execute one simulation step
(mm-sim) demo basic              # Run basic demonstration

# Information
(mm-sim) stats                   # Show memory/process statistics
(mm-sim) memory                  # Show physical memory map
(mm-sim) processes               # List all processes
(mm-sim) mappings                # Show virtual memory mappings
(mm-sim) events                  # Show recent events
```

### Programmatic Usage

```python
from memory_simulator import MemorySimulator

# Create and start simulator
sim = MemorySimulator()
sim.start_simulation()

# Allocate physical pages
page1 = sim.allocate_page()
page2 = sim.allocate_page()

# Create a process and allocate memory
pid = sim.create_process()
virt_addr = sim.allocate_process_memory(pid, 8192)  # 2 pages

# Simulate page fault
sim.simulate_page_fault(pid, 0x400000, 0)

# Get statistics
stats = sim.get_memory_statistics()
print(f"Free pages: {stats['physical_memory']['free_pages']}")
```

## 🎓 Educational Features

### Step-by-Step Execution
The simulator supports step-by-step execution to understand algorithm flow:

```bash
(mm-sim) step    # Execute one simulation step
(mm-sim) stats   # See the results
```

### Real-time Visualization
- Physical memory allocation bitmap display
- Process memory layout visualization  
- Page table hierarchy inspection
- Event timeline with detailed logging

### Algorithm Annotation
Each major operation includes:
- Source code comments referencing original Linux 0.01
- Assembly instruction simulation for key algorithms
- Detailed error checking and validation
- Educational help text explaining concepts

## 🔍 Key Demonstrations

### 1. Basic Memory Management
```bash
python3 cli.py basic
```
Demonstrates:
- Physical page allocation and deallocation
- Virtual memory mapping
- Basic process creation
- Page fault handling

### 2. Fork and Copy-on-Write
```bash
python3 cli.py fork
```
Shows:
- Process forking with shared memory
- Copy-on-write page protection
- Write fault triggering page copying
- Memory inheritance between parent/child

### 3. Stress Testing
```bash
python3 cli.py stress
```
Tests:
- Memory pressure scenarios
- Fragmentation effects
- Process management under load
- Error handling and recovery

## 🧪 Technical Accuracy

The simulator faithfully implements Linux 0.01 algorithms:

### Memory Map Array
- `mem_map[1792]` tracks page reference counts
- Backward scanning allocation (matches assembly code)
- Proper reference counting for shared pages

### 2-Level Page Tables
- Page directory (1024 entries × 4MB each)
- Page tables (1024 entries × 4KB each)  
- Exact bit layout and permission handling

### Copy-on-Write
- Pages marked read-only after fork()
- Write protection faults trigger copying
- Reference counting prevents premature freeing

### Process Management
- Task structure based on original `task_struct`
- Memory context switching simulation
- Proper parent-child relationships

## 📊 Statistics and Monitoring

The simulator provides comprehensive statistics:

```python
stats = simulator.get_memory_statistics()

# Physical memory
print(f"Total pages: {stats['physical_memory']['total_pages']}")
print(f"Free pages: {stats['physical_memory']['free_pages']}")
print(f"Fragmentation: {stats['physical_memory']['fragmentation']:.2%}")

# Virtual memory
print(f"Page faults: {stats['virtual_memory']['page_faults']}")
print(f"COW faults: {stats['virtual_memory']['cow_faults']}")

# Processes
print(f"Total processes: {stats['processes']['total_processes']}")
print(f"Total forks: {stats['processes']['total_forks']}")
```

## 🐛 Debugging and Development

### Logging Levels
```python
simulator = MemorySimulator(debug_level="DEBUG")  # Verbose logging
simulator = MemorySimulator(debug_level="INFO")   # Normal logging  
simulator = MemorySimulator(debug_level="ERROR")  # Errors only
```

### Event Tracking
```python
# Register callbacks for specific events
simulator.register_event_callback("memory", my_memory_callback)
simulator.register_event_callback("page_fault", my_fault_callback)

# Get event history
events = simulator.get_events("memory", limit=50)
for event in events:
    print(f"{event.timestamp}: {event.description}")
```

### State Export/Import
```bash
(mm-sim) save state.json    # Save current state
```

## 🔧 Configuration

Key constants from `config.py`:

```python
HIGH_MEMORY = 0x800000     # 8MB total memory
LOW_MEM = 0x100000         # 1MB kernel reservation
PAGE_SIZE = 4096           # 4KB pages
PAGING_PAGES = 1792        # User pages available
```

Easily modify these for different memory configurations or experiments.

## 🎯 Use Cases

### Educational Settings
- Operating systems courses
- Computer architecture classes
- Systems programming tutorials
- Historical computing studies

### Research and Development
- Algorithm visualization and understanding
- Memory management research
- Performance analysis and optimization
- Historical system behavior study

### Personal Learning
- Understanding early Unix/Linux internals
- Learning memory management concepts
- Exploring system call implementation
- Debugging memory-related issues

## 🤝 Contributing

This simulator serves as both an educational tool and a historical preservation project. Areas for enhancement:

- GUI interface with graphical memory visualization
- Additional Linux 0.01 subsystem simulations
- Performance benchmarking tools
- Extended documentation and tutorials

## 📚 References

- Original Linux 0.01 source code (1991)
- "The Design of the Unix Operating System" by Maurice Bach
- "Understanding the Linux Kernel" by Bovet & Cesati
- Linux kernel development documentation

## 📄 License

This educational simulator is provided for learning purposes. The original Linux 0.01 code was released under early Linux license terms.

---

**Note**: This simulator is designed for educational purposes to understand historical operating system concepts. It accurately models Linux 0.01 behavior but is not intended for production use.