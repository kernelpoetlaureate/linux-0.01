"""
Process Management for Linux 0.01 Simulator
Based on kernel/sched.c and include/linux/sched.h
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from config import *
from physical_memory import PhysicalMemory
from virtual_memory import VirtualMemory

@dataclass
class TSS:
    """Task State Segment - simplified version"""
    esp0: int = 0
    ss0: int = 0x10
    cr3: int = 0  # Page directory physical address
    eip: int = 0
    eflags: int = 0x202
    esp: int = 0
    ebp: int = 0

@dataclass
class LDT:
    """Local Descriptor Table entries"""
    null: int = 0
    code: int = 0x9f  # Code segment
    data: int = 0x9f  # Data segment

class TaskStruct:
    """
    Process control block based on Linux 0.01 task_struct.
    Simplified version focusing on memory management aspects.
    """
    
    def __init__(self, pid: int, parent_pid: int = -1):
        # Basic process info
        self.pid = pid
        self.parent_pid = parent_pid
        self.state = TASK_RUNNING
        self.counter = 15  # Time slice counter
        self.priority = 15  # Process priority
        
        # Memory management
        self.end_code = 0      # End of code segment
        self.end_data = 0      # End of data segment  
        self.brk = 0           # Break point for heap
        self.start_stack = 0   # Start of stack
        
        # Process tree
        self.children: List[int] = []
        self.exit_code = 0
        
        # Memory context
        self.page_directory_addr = 0  # Physical address of page directory
        
        # TSS and LDT
        self.tss = TSS()
        self.ldt = LDT()
        
        # Statistics
        self.page_faults = 0
        self.cow_faults = 0
        self.memory_usage = 0  # Pages allocated
        
        # For visualization
        self.memory_regions: List[dict] = []
        
    def add_memory_region(self, start: int, end: int, region_type: str, permissions: str = "rw"):
        """Add a memory region for this process"""
        self.memory_regions.append({
            "start": start,
            "end": end,
            "type": region_type,
            "permissions": permissions,
            "size": end - start
        })
    
    def get_memory_layout(self) -> dict:
        """Get memory layout information"""
        return {
            "pid": self.pid,
            "end_code": self.end_code,
            "end_data": self.end_data,
            "brk": self.brk,
            "start_stack": self.start_stack,
            "regions": self.memory_regions.copy(),
            "page_directory": self.page_directory_addr,
            "memory_usage": self.memory_usage
        }
    
    def __str__(self) -> str:
        return f"Task(pid={self.pid}, state={self.state}, parent={self.parent_pid})"

class ProcessManager:
    """
    Manages processes and their memory contexts.
    Based on Linux 0.01 scheduler and task management.
    """
    
    def __init__(self, physical_memory: PhysicalMemory, virtual_memory: VirtualMemory):
        self.physical_memory = physical_memory
        self.virtual_memory = virtual_memory
        
        # Process table
        self.tasks: Dict[int, TaskStruct] = {}
        self.current_pid = 0
        self.next_pid = 1
        
        # Statistics
        self.total_forks = 0
        self.total_exits = 0
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize task 0 (init process)
        self.init_task_0()
        
        self.logger.info("Process manager initialized")
    
    def init_task_0(self):
        """Initialize the init task (PID 0)"""
        task0 = TaskStruct(0, -1)
        task0.state = TASK_RUNNING
        task0.end_code = 0x0
        task0.end_data = LOW_MEM
        task0.brk = LOW_MEM
        task0.start_stack = PAGE_SIZE
        
        # Task 0 uses the kernel page directory
        task0.page_directory_addr = 0  # Kernel page directory at address 0
        
        # Add kernel memory regions
        task0.add_memory_region(0x0, LOW_MEM, "kernel", "rx")
        task0.add_memory_region(LOW_MEM, BUFFER_END, "buffer", "rw")
        
        self.tasks[0] = task0
        self.current_pid = 0
        
        self.logger.info("Initialized task 0 (init)")
    
    def fork_process(self, parent_pid: int) -> int:
        """
        Create a new process by forking an existing one.
        
        Based on the fork() implementation in Linux 0.01:
        1. Allocate new task structure
        2. Copy parent's memory space with COW
        3. Set up page tables
        4. Initialize process state
        
        Args:
            parent_pid: PID of parent process
            
        Returns:
            PID of new process, or -1 on failure
        """
        if parent_pid not in self.tasks:
            self.logger.error(f"Parent process {parent_pid} not found")
            return -1
        
        parent = self.tasks[parent_pid]
        child_pid = self.next_pid
        self.next_pid += 1
        
        self.logger.debug(f"Forking process {parent_pid} -> {child_pid}")
        
        # Create child task structure
        child = TaskStruct(child_pid, parent_pid)
        
        # Copy memory layout from parent
        child.end_code = parent.end_code
        child.end_data = parent.end_data
        child.brk = parent.brk
        child.start_stack = parent.start_stack
        
        # Copy memory regions
        child.memory_regions = [region.copy() for region in parent.memory_regions]
        
        # Allocate page directory for child
        child_pg_dir_addr = self.physical_memory.get_free_page()
        if child_pg_dir_addr == 0:
            self.logger.error("Failed to allocate page directory for child")
            return -1
        
        child.page_directory_addr = child_pg_dir_addr
        child.tss.cr3 = child_pg_dir_addr
        
        # Copy page tables from parent
        # Note: This is a simplified version - in real Linux 0.01,
        # the child would share the parent's page directory initially
        memory_size = parent.brk - parent.end_code if parent.brk > parent.end_code else 0
        if memory_size > 0:
            # Round up to 4MB boundary for copy_page_tables
            aligned_size = (memory_size + 0x3FFFFF) & ~0x3FFFFF
            
            result = self.virtual_memory.copy_page_tables(
                parent.end_code,  # From address
                parent.end_code,  # To address (same virtual space)
                aligned_size
            )
            
            if result != 0:
                self.logger.error("Failed to copy page tables")
                self.physical_memory.free_page(child_pg_dir_addr)
                return -1
        
        # Add to process table
        self.tasks[child_pid] = child
        
        # Update parent's children list
        parent.children.append(child_pid)
        
        # Update statistics
        self.total_forks += 1
        
        # Set child's memory usage (estimate)
        child.memory_usage = parent.memory_usage
        
        self.logger.info(f"Created child process {child_pid} from parent {parent_pid}")
        return child_pid
    
    def exit_process(self, pid: int, exit_code: int = 0) -> bool:
        """
        Terminate a process and clean up its resources.
        
        Args:
            pid: Process ID to terminate
            exit_code: Exit status code
            
        Returns:
            True on success, False if process not found
        """
        if pid not in self.tasks:
            self.logger.error(f"Process {pid} not found")
            return False
        
        if pid == 0:
            self.logger.error("Cannot exit init process")
            return False
        
        task = self.tasks[pid]
        self.logger.debug(f"Exiting process {pid}")
        
        # Free memory regions
        for region in task.memory_regions:
            if region["type"] == "user":
                # Free pages in this region
                region_size = region["end"] - region["start"]
                if region_size > 0:
                    self.virtual_memory.free_page_tables(region["start"], region_size)
        
        # Free page directory
        if task.page_directory_addr != 0:
            self.physical_memory.free_page(task.page_directory_addr)
        
        # Update parent's children list
        if task.parent_pid in self.tasks:
            parent = self.tasks[task.parent_pid]
            if pid in parent.children:
                parent.children.remove(pid)
        
        # Reparent children to init (PID 0)
        for child_pid in task.children:
            if child_pid in self.tasks:
                self.tasks[child_pid].parent_pid = 0
                if 0 in self.tasks:
                    self.tasks[0].children.append(child_pid)
        
        # Set exit state
        task.state = TASK_ZOMBIE
        task.exit_code = exit_code
        
        # Switch to init if this was current process
        if self.current_pid == pid:
            self.current_pid = 0
        
        # Update statistics
        self.total_exits += 1
        
        self.logger.info(f"Process {pid} exited with code {exit_code}")
        return True
    
    def switch_to(self, pid: int) -> bool:
        """
        Switch to a different process (context switch).
        
        Args:
            pid: Process ID to switch to
            
        Returns:
            True on success, False if process not found or not runnable
        """
        if pid not in self.tasks:
            self.logger.error(f"Process {pid} not found")
            return False
        
        task = self.tasks[pid]
        
        if task.state != TASK_RUNNING:
            self.logger.debug(f"Process {pid} not in running state")
            return False
        
        old_pid = self.current_pid
        self.current_pid = pid
        
        # In real Linux 0.01, this would involve:
        # 1. Saving current register state
        # 2. Loading new page directory (CR3)
        # 3. Loading new TSS
        # 4. Restoring register state
        
        self.logger.debug(f"Switched from process {old_pid} to {pid}")
        return True
    
    def allocate_memory(self, pid: int, size: int, region_type: str = "user") -> Optional[int]:
        """
        Allocate memory for a process.
        
        Args:
            pid: Process ID
            size: Size in bytes to allocate
            region_type: Type of memory region
            
        Returns:
            Virtual address of allocated memory, or None on failure
        """
        if pid not in self.tasks:
            return None
        
        task = self.tasks[pid]
        
        # Find a suitable virtual address
        # For simplicity, allocate after the break point
        virtual_addr = task.brk
        
        # Align to page boundary
        virtual_addr = (virtual_addr + PAGE_SIZE - 1) & ~(PAGE_SIZE - 1)
        
        # Calculate number of pages needed
        pages_needed = (size + PAGE_SIZE - 1) // PAGE_SIZE
        
        # Allocate physical pages and map them
        for i in range(pages_needed):
            page_addr = virtual_addr + (i * PAGE_SIZE)
            physical_page = self.physical_memory.get_free_page()
            
            if physical_page == 0:
                # Out of memory - free what we allocated so far
                for j in range(i):
                    self.virtual_memory.free_page_tables(virtual_addr + (j * PAGE_SIZE), PAGE_SIZE)
                return None
            
            # Map the page
            if self.virtual_memory.put_page(physical_page, page_addr) == 0:
                self.physical_memory.free_page(physical_page)
                # Free what we allocated so far
                for j in range(i):
                    self.virtual_memory.free_page_tables(virtual_addr + (j * PAGE_SIZE), PAGE_SIZE)
                return None
        
        # Update task's memory info
        task.brk = virtual_addr + size
        task.memory_usage += pages_needed
        
        # Add memory region
        task.add_memory_region(virtual_addr, virtual_addr + size, region_type)
        
        self.logger.info(f"Allocated {size} bytes at 0x{virtual_addr:08x} for process {pid}")
        return virtual_addr
    
    def free_memory(self, pid: int, addr: int, size: int) -> bool:
        """
        Free memory for a process.
        
        Args:
            pid: Process ID
            addr: Virtual address to free
            size: Size in bytes to free
            
        Returns:
            True on success, False on failure
        """
        if pid not in self.tasks:
            return False
        
        task = self.tasks[pid]
        
        # Calculate number of pages to free
        pages_to_free = (size + PAGE_SIZE - 1) // PAGE_SIZE
        
        # Free the pages
        for i in range(pages_to_free):
            page_addr = addr + (i * PAGE_SIZE)
            physical_addr = self.virtual_memory.get_physical_address(page_addr)
            
            if physical_addr is not None:
                self.physical_memory.free_page(physical_addr)
        
        # Free page table entries
        self.virtual_memory.free_page_tables(addr, size)
        
        # Update memory usage
        task.memory_usage -= pages_to_free
        
        # Remove or update memory region
        # (Simplified - in reality this would be more complex)
        task.memory_regions = [
            region for region in task.memory_regions
            if not (region["start"] <= addr < region["end"])
        ]
        
        self.logger.info(f"Freed {size} bytes at 0x{addr:08x} for process {pid}")
        return True
    
    def handle_page_fault(self, pid: int, addr: int, error_code: int) -> bool:
        """
        Handle a page fault for a process.
        
        Args:
            pid: Process ID that faulted
            addr: Faulting virtual address
            error_code: Page fault error code
            
        Returns:
            True if fault handled successfully, False if process should be killed
        """
        if pid not in self.tasks:
            return False
        
        task = self.tasks[pid]
        task.page_faults += 1
        
        self.logger.debug(f"Page fault in process {pid} at 0x{addr:08x}, error=0x{error_code:x}")
        
        # Check fault type
        if error_code & PAGE_FAULT_PROTECTION:
            # Protection violation - likely copy-on-write
            if error_code & PAGE_FAULT_WRITE:
                task.cow_faults += 1
                return self.virtual_memory.do_wp_page(error_code, addr)
            else:
                # Read protection violation
                self.logger.error(f"Read protection violation in process {pid}")
                return False
        else:
            # Page not present - allocate new page
            return self.virtual_memory.do_no_page(error_code, addr)
    
    def get_process_list(self) -> List[dict]:
        """Get list of all processes with their information"""
        processes = []
        
        for pid, task in self.tasks.items():
            processes.append({
                "pid": pid,
                "parent_pid": task.parent_pid,
                "state": task.state,
                "counter": task.counter,
                "priority": task.priority,
                "memory_usage": task.memory_usage,
                "page_faults": task.page_faults,
                "cow_faults": task.cow_faults,
                "children": task.children.copy(),
                "memory_layout": task.get_memory_layout()
            })
        
        return processes
    
    def get_current_process(self) -> Optional[TaskStruct]:
        """Get currently running process"""
        return self.tasks.get(self.current_pid)
    
    def get_process(self, pid: int) -> Optional[TaskStruct]:
        """Get process by PID"""
        return self.tasks.get(pid)
    
    def get_statistics(self) -> dict:
        """Get process management statistics"""
        running_count = sum(1 for task in self.tasks.values() if task.state == TASK_RUNNING)
        zombie_count = sum(1 for task in self.tasks.values() if task.state == TASK_ZOMBIE)
        
        total_memory = sum(task.memory_usage for task in self.tasks.values())
        total_page_faults = sum(task.page_faults for task in self.tasks.values())
        total_cow_faults = sum(task.cow_faults for task in self.tasks.values())
        
        return {
            "total_processes": len(self.tasks),
            "running_processes": running_count,
            "zombie_processes": zombie_count,
            "current_pid": self.current_pid,
            "total_forks": self.total_forks,
            "total_exits": self.total_exits,
            "total_memory_pages": total_memory,
            "total_page_faults": total_page_faults,
            "total_cow_faults": total_cow_faults
        }
    
    def schedule(self) -> int:
        """
        Simple round-robin scheduler.
        
        Returns:
            PID of next process to run
        """
        # Find next runnable process
        candidates = [pid for pid, task in self.tasks.items() 
                     if task.state == TASK_RUNNING and task.counter > 0]
        
        if not candidates:
            # Reset all counters and try again
            for task in self.tasks.values():
                if task.state == TASK_RUNNING:
                    task.counter = (task.counter >> 1) + task.priority
            
            candidates = [pid for pid, task in self.tasks.items() 
                         if task.state == TASK_RUNNING and task.counter > 0]
        
        if not candidates:
            # Fall back to init process
            return 0
        
        # Find process with highest counter
        best_pid = max(candidates, key=lambda pid: self.tasks[pid].counter)
        
        # Decrement counter
        self.tasks[best_pid].counter -= 1
        
        return best_pid
    
    def reset(self):
        """Reset process manager to initial state"""
        self.tasks.clear()
        self.current_pid = 0
        self.next_pid = 1
        self.total_forks = 0
        self.total_exits = 0
        
        # Reinitialize task 0
        self.init_task_0()
        
        self.logger.info("Process manager reset to initial state")
    
    def __str__(self) -> str:
        """String representation for debugging"""
        stats = self.get_statistics()
        return (f"ProcessManager(processes={stats['total_processes']}, "
                f"current={stats['current_pid']}, "
                f"forks={stats['total_forks']})")