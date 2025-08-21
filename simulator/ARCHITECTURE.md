# Linux 0.01 Memory Management Simulator Architecture

## Overview

This Python GUI simulator provides an educational, interactive visualization of the Linux 0.01 memory management system. It accurately models the kernel's memory management algorithms while providing step-by-step execution and real-time visualization.

## Core System Architecture

### 1. Memory Layout (Based on linux/config.h)

```
Physical Memory Layout (8MB total):
┌─────────────────┬─────────────┬─────────────────────────────────┐
│   Kernel Code   │   Buffers   │         Paging Memory          │
│   0x0 - 1MB     │ 1MB - 2MB   │        2MB - 8MB               │
└─────────────────┴─────────────┴─────────────────────────────────┘

Constants:
- HIGH_MEMORY = 0x800000 (8MB)
- BUFFER_END = 0x200000 (2MB)  
- LOW_MEM = 0x100000 (1MB)
- PAGING_MEMORY = 7MB
- PAGING_PAGES = 1792 pages
- PAGE_SIZE = 4096 bytes
```

### 2. Data Structures

#### Memory Map Array
```python
class MemoryMap:
    """Tracks page allocation status"""
    def __init__(self):
        self.mem_map = [0] * PAGING_PAGES  # 1792 entries
        # 0 = free, >0 = reference count
```

#### Page Directory and Tables
```python
class PageDirectory:
    """2-level page table system"""
    def __init__(self):
        self.pg_dir = [0] * 1024  # Page directory entries
        self.page_tables = {}     # Dynamic page table allocation
```

#### Task Structure
```python
class TaskStruct:
    """Process control block with memory info"""
    def __init__(self, pid):
        self.pid = pid
        self.state = TASK_RUNNING
        self.mm_context = MemoryContext()
        # ... other fields from sched.h
```

## Core Components

### 1. Physical Memory Manager (`PhysicalMemory`)

**Functions:**
- `get_free_page()` - Find and allocate free physical page
- `free_page(addr)` - Release physical page  
- `calc_mem()` - Calculate memory statistics

**Visualization:**
- Page allocation bitmap
- Free page counter
- Memory usage graphs

### 2. Virtual Memory Manager (`VirtualMemory`)

**Functions:**
- `put_page(page, address)` - Map physical page to virtual address
- `copy_page_tables(from, to, size)` - Copy page tables for fork
- `free_page_tables(from, size)` - Free page tables on exit

**Visualization:**
- Virtual address space layout
- Page table hierarchy
- Address translation walkthrough

### 3. Page Fault Handler (`PageFaultHandler`)

**Functions:**
- `do_no_page(error_code, address)` - Handle unmapped pages
- `do_wp_page(error_code, address)` - Handle write protection
- `write_verify(address)` - Check write permissions

**Visualization:**
- Page fault flow diagram
- Copy-on-write demonstration
- Permission checking steps

### 4. Process Memory Context (`ProcessManager`)

**Functions:**
- `fork_process()` - Create new process with copied memory
- `exit_process(pid)` - Clean up process memory
- `switch_context(pid)` - Switch memory context

**Visualization:**
- Process memory maps
- Parent-child memory sharing
- Memory inheritance on fork

## GUI Architecture

### 1. Main Window Layout

```
┌─────────────────────────────────────────────────────────────┐
│                    Linux 0.01 MM Simulator                 │
├─────────────────┬───────────────────────────────────────────┤
│   Control Panel │            Memory Visualization           │
│                 │                                           │
│  - Play/Pause   │  ┌─────────────────────────────────────┐  │
│  - Step         │  │       Physical Memory Map          │  │
│  - Reset        │  │  [■][■][□][□][■][□][■][■][□][□]...   │  │
│  - Speed        │  └─────────────────────────────────────┘  │
│                 │                                           │
│  Function Calls │  ┌─────────────────────────────────────┐  │
│  - get_free_page│  │      Virtual Memory Spaces         │  │
│  - put_page     │  │                                     │  │
│  - fork         │  │  Process 0: [████████████████████]  │  │
│  - do_wp_page   │  │  Process 1: [████████████████████]  │  │
│                 │  └─────────────────────────────────────┘  │
├─────────────────┼───────────────────────────────────────────┤
│   Statistics    │            Code Execution               │
│                 │                                           │
│  Pages Free: 1200│  Executing: get_free_page()            │
│  Pages Used: 592 │  ┌─────────────────────────────────────┐ │
│  Processes: 3    │  │ __asm__("std ; repne ; scasw\n\t"   │ │
│  Page Faults: 15 │  │ "jne 1f\n\t"                       │ │
│                 │  │ "movw $1,2(%%edi)\n\t"             │ │
│                 │  └─────────────────────────────────────┘ │
└─────────────────┴───────────────────────────────────────────┘
```

### 2. Specialized Views

#### Page Table Inspector
- Hierarchical view of page directory and tables
- Address translation visualization
- Permission bit display

#### Process Memory Map
- Virtual memory layout per process
- Shared vs private pages
- Memory protection regions

#### Algorithm Animator
- Step-by-step algorithm execution
- Register and memory state changes
- Assembly code visualization

## Implementation Plan

### Phase 1: Core Memory Management
1. Implement `PhysicalMemory` class with page allocation
2. Create `VirtualMemory` class with address translation
3. Build basic GUI framework with memory visualization
4. Add simple allocation/deallocation operations

### Phase 2: Process Management
1. Implement `TaskStruct` and `ProcessManager`
2. Add fork simulation with page table copying
3. Implement copy-on-write mechanism
4. Create process memory visualization

### Phase 3: Page Fault Handling
1. Implement page fault simulation
2. Add write protection handling
3. Create interactive fault scenarios
4. Build fault handling visualization

### Phase 4: Educational Features
1. Add step-by-step execution mode
2. Implement algorithm animation
3. Create guided tutorials
4. Add comprehensive documentation

### Phase 5: Advanced Features
1. Memory fragmentation analysis
2. Performance metrics
3. Comparison with modern systems
4. Export/import scenarios

## Educational Objectives

### Students Will Learn:
1. **Physical Memory Management**
   - Page-based allocation
   - Free page tracking
   - Memory fragmentation

2. **Virtual Memory Concepts**
   - Address translation
   - Page table hierarchy
   - Memory protection

3. **Process Memory Management**
   - Memory context switching
   - Copy-on-write optimization
   - Memory inheritance

4. **System Call Interface**
   - Memory allocation syscalls
   - Page fault handling
   - Kernel-user interaction

## Technical Requirements

### Dependencies:
- Python 3.8+
- tkinter (GUI framework)
- matplotlib (visualization)
- numpy (numerical operations)

### Performance Considerations:
- Efficient page tracking algorithms
- Optimized GUI updates
- Memory usage optimization for large simulations

### Testing Strategy:
- Unit tests for all memory management functions
- Integration tests for complex scenarios
- Performance benchmarks
- Educational effectiveness validation