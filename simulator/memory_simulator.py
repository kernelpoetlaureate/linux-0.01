"""
Linux 0.01 Memory Management Simulator
Main simulator class that orchestrates all components
"""

import logging
import time
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from config import *
from physical_memory import PhysicalMemory
from virtual_memory import VirtualMemory
from process_manager import ProcessManager

@dataclass
class SimulationEvent:
    """Represents a simulation event"""
    timestamp: float
    event_type: str
    description: str
    details: Dict[str, Any]

class MemorySimulator:
    """
    Main Linux 0.01 Memory Management Simulator.
    
    Coordinates all memory management components and provides
    a unified interface for simulation and visualization.
    """
    
    def __init__(self, debug_level: str = DEFAULT_DEBUG_LEVEL):
        """Initialize the memory management simulator"""
        
        # Set up logging
        self.setup_logging(debug_level)
        self.logger = logging.getLogger(__name__)
        
        # Initialize core components
        self.physical_memory = PhysicalMemory()
        self.virtual_memory = VirtualMemory(self.physical_memory)
        self.process_manager = ProcessManager(self.physical_memory, self.virtual_memory)
        
        # Simulation state
        self.simulation_time = 0.0
        self.is_running = False
        self.is_paused = False
        self.step_mode = False
        self.simulation_speed = DEFAULT_SIMULATION_SPEED
        
        # Event tracking
        self.events: List[SimulationEvent] = []
        self.event_callbacks: Dict[str, List[Callable]] = {}
        
        # Performance metrics
        self.start_time = time.time()
        self.total_operations = 0
        
        # For GUI integration
        self.update_callbacks: List[Callable] = []
        
        self.logger.info("Linux 0.01 Memory Simulator initialized")
        self.log_event("system", "Simulator initialized", {})
    
    def setup_logging(self, level: str):
        """Configure logging for the simulator"""
        logging.basicConfig(
            level=getattr(logging, level.upper(), logging.INFO),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('simulator.log')
            ]
        )
    
    def log_event(self, event_type: str, description: str, details: Dict[str, Any]):
        """Log a simulation event"""
        event = SimulationEvent(
            timestamp=self.simulation_time,
            event_type=event_type,
            description=description,
            details=details
        )
        self.events.append(event)
        
        # Trigger callbacks
        for callback in self.event_callbacks.get(event_type, []):
            callback(event)
        
        # Trigger general update callbacks
        for callback in self.update_callbacks:
            callback()
    
    def register_event_callback(self, event_type: str, callback: Callable):
        """Register a callback for specific event types"""
        if event_type not in self.event_callbacks:
            self.event_callbacks[event_type] = []
        self.event_callbacks[event_type].append(callback)
    
    def register_update_callback(self, callback: Callable):
        """Register a callback for any simulation updates"""
        self.update_callbacks.append(callback)
    
    # Core Memory Management Operations
    
    def allocate_page(self) -> int:
        """
        Allocate a physical page.
        
        Returns:
            Physical address of allocated page, or 0 if failed
        """
        self.total_operations += 1
        addr = self.physical_memory.get_free_page()
        
        if addr != 0:
            self.log_event("memory", f"Allocated page at 0x{addr:08x}", {
                "operation": "get_free_page",
                "address": addr,
                "page_number": (addr - LOW_MEM) >> 12
            })
        else:
            self.log_event("memory", "Page allocation failed - out of memory", {
                "operation": "get_free_page",
                "error": "out_of_memory"
            })
        
        return addr
    
    def free_page(self, addr: int) -> bool:
        """
        Free a physical page.
        
        Args:
            addr: Physical address to free
            
        Returns:
            True on success, False on failure
        """
        self.total_operations += 1
        success = self.physical_memory.free_page(addr)
        
        if success:
            self.log_event("memory", f"Freed page at 0x{addr:08x}", {
                "operation": "free_page",
                "address": addr,
                "page_number": (addr - LOW_MEM) >> 12
            })
        else:
            self.log_event("memory", f"Failed to free page at 0x{addr:08x}", {
                "operation": "free_page",
                "address": addr,
                "error": "invalid_address"
            })
        
        return success
    
    def map_page(self, physical_addr: int, virtual_addr: int) -> bool:
        """
        Map a physical page to a virtual address.
        
        Args:
            physical_addr: Physical page address
            virtual_addr: Virtual address to map to
            
        Returns:
            True on success, False on failure
        """
        self.total_operations += 1
        result = self.virtual_memory.put_page(physical_addr, virtual_addr)
        
        if result != 0:
            self.log_event("memory", f"Mapped 0x{physical_addr:08x} -> 0x{virtual_addr:08x}", {
                "operation": "put_page",
                "physical_address": physical_addr,
                "virtual_address": virtual_addr
            })
            return True
        else:
            self.log_event("memory", f"Failed to map 0x{physical_addr:08x} -> 0x{virtual_addr:08x}", {
                "operation": "put_page",
                "physical_address": physical_addr,
                "virtual_address": virtual_addr,
                "error": "mapping_failed"
            })
            return False
    
    def translate_address(self, virtual_addr: int) -> Optional[int]:
        """
        Translate virtual address to physical address.
        
        Args:
            virtual_addr: Virtual address to translate
            
        Returns:
            Physical address or None if not mapped
        """
        return self.virtual_memory.get_physical_address(virtual_addr)
    
    def simulate_page_fault(self, pid: int, virtual_addr: int, error_code: int) -> bool:
        """
        Simulate a page fault.
        
        Args:
            pid: Process ID that faulted
            virtual_addr: Faulting virtual address
            error_code: Page fault error code
            
        Returns:
            True if fault handled, False if process should be killed
        """
        self.total_operations += 1
        
        fault_type = "protection" if error_code & PAGE_FAULT_PROTECTION else "not_present"
        write_fault = bool(error_code & PAGE_FAULT_WRITE)
        
        self.log_event("page_fault", f"Page fault at 0x{virtual_addr:08x}", {
            "pid": pid,
            "virtual_address": virtual_addr,
            "error_code": error_code,
            "fault_type": fault_type,
            "write_fault": write_fault
        })
        
        success = self.process_manager.handle_page_fault(pid, virtual_addr, error_code)
        
        if success:
            self.log_event("page_fault", f"Page fault handled successfully", {
                "pid": pid,
                "virtual_address": virtual_addr
            })
        else:
            self.log_event("page_fault", f"Page fault killed process {pid}", {
                "pid": pid,
                "virtual_address": virtual_addr,
                "result": "process_killed"
            })
        
        return success
    
    # Process Management Operations
    
    def create_process(self, parent_pid: int = 0) -> int:
        """
        Create a new process (fork).
        
        Args:
            parent_pid: Parent process ID
            
        Returns:
            New process PID, or -1 on failure
        """
        self.total_operations += 1
        new_pid = self.process_manager.fork_process(parent_pid)
        
        if new_pid != -1:
            self.log_event("process", f"Created process {new_pid}", {
                "operation": "fork",
                "parent_pid": parent_pid,
                "child_pid": new_pid
            })
        else:
            self.log_event("process", f"Failed to create process", {
                "operation": "fork",
                "parent_pid": parent_pid,
                "error": "fork_failed"
            })
        
        return new_pid
    
    def terminate_process(self, pid: int, exit_code: int = 0) -> bool:
        """
        Terminate a process.
        
        Args:
            pid: Process ID to terminate
            exit_code: Exit status code
            
        Returns:
            True on success, False on failure
        """
        self.total_operations += 1
        success = self.process_manager.exit_process(pid, exit_code)
        
        if success:
            self.log_event("process", f"Process {pid} exited", {
                "operation": "exit",
                "pid": pid,
                "exit_code": exit_code
            })
        else:
            self.log_event("process", f"Failed to exit process {pid}", {
                "operation": "exit",
                "pid": pid,
                "error": "process_not_found"
            })
        
        return success
    
    def allocate_process_memory(self, pid: int, size: int) -> Optional[int]:
        """
        Allocate memory for a process.
        
        Args:
            pid: Process ID
            size: Size in bytes to allocate
            
        Returns:
            Virtual address of allocated memory, or None on failure
        """
        self.total_operations += 1
        addr = self.process_manager.allocate_memory(pid, size)
        
        if addr is not None:
            self.log_event("process", f"Allocated {size} bytes for process {pid}", {
                "operation": "allocate",
                "pid": pid,
                "size": size,
                "address": addr
            })
        else:
            self.log_event("process", f"Failed to allocate memory for process {pid}", {
                "operation": "allocate",
                "pid": pid,
                "size": size,
                "error": "allocation_failed"
            })
        
        return addr
    
    def switch_process(self, pid: int) -> bool:
        """
        Switch to a different process.
        
        Args:
            pid: Process ID to switch to
            
        Returns:
            True on success, False on failure
        """
        old_pid = self.process_manager.current_pid
        success = self.process_manager.switch_to(pid)
        
        if success:
            self.log_event("process", f"Context switch {old_pid} -> {pid}", {
                "operation": "switch_to",
                "old_pid": old_pid,
                "new_pid": pid
            })
        
        return success
    
    # Simulation Control
    
    def start_simulation(self):
        """Start the simulation"""
        self.is_running = True
        self.is_paused = False
        self.start_time = time.time()
        self.log_event("system", "Simulation started", {})
    
    def pause_simulation(self):
        """Pause the simulation"""
        self.is_paused = True
        self.log_event("system", "Simulation paused", {})
    
    def resume_simulation(self):
        """Resume the simulation"""
        self.is_paused = False
        self.log_event("system", "Simulation resumed", {})
    
    def stop_simulation(self):
        """Stop the simulation"""
        self.is_running = False
        self.is_paused = False
        self.log_event("system", "Simulation stopped", {})
    
    def reset_simulation(self):
        """Reset simulation to initial state"""
        self.stop_simulation()
        
        # Reset all components
        self.physical_memory.reset()
        self.virtual_memory.reset()
        self.process_manager.reset()
        
        # Reset simulation state
        self.simulation_time = 0.0
        self.total_operations = 0
        self.events.clear()
        
        self.log_event("system", "Simulation reset", {})
    
    def step_simulation(self):
        """Execute one simulation step"""
        if not self.step_mode:
            self.step_mode = True
        
        # Advance simulation time
        self.simulation_time += 1.0
        
        # Simple scheduling - switch to next process
        current_pid = self.process_manager.current_pid
        next_pid = self.process_manager.schedule()
        
        if next_pid != current_pid:
            self.switch_process(next_pid)
    
    # Information and Statistics
    
    def get_memory_statistics(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics"""
        phys_stats = self.physical_memory.calc_mem()
        proc_stats = self.process_manager.get_statistics()
        
        return {
            "physical_memory": phys_stats,
            "virtual_memory": {
                "page_faults": self.virtual_memory.page_faults,
                "cow_faults": self.virtual_memory.cow_faults,
                "allocation_faults": self.virtual_memory.allocation_faults,
                "page_tables": len(self.virtual_memory.page_tables),
                "mappings": len(self.virtual_memory.get_memory_mappings())
            },
            "processes": proc_stats,
            "simulation": {
                "time": self.simulation_time,
                "operations": self.total_operations,
                "events": len(self.events),
                "uptime": time.time() - self.start_time,
                "is_running": self.is_running,
                "is_paused": self.is_paused
            }
        }
    
    def get_process_list(self) -> List[Dict[str, Any]]:
        """Get list of all processes"""
        return self.process_manager.get_process_list()
    
    def get_memory_mappings(self) -> List[Dict[str, Any]]:
        """Get all current memory mappings"""
        return self.virtual_memory.get_memory_mappings()
    
    def get_physical_memory_map(self) -> List[int]:
        """Get physical memory allocation map"""
        return self.physical_memory.get_memory_map()
    
    def get_page_table_info(self, virtual_addr: int) -> Optional[Dict[str, Any]]:
        """Get page table information for an address"""
        return self.virtual_memory.get_page_table_info(virtual_addr)
    
    def get_events(self, event_type: Optional[str] = None, 
                   limit: Optional[int] = None) -> List[SimulationEvent]:
        """Get simulation events"""
        events = self.events
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        if limit:
            events = events[-limit:]
        
        return events
    
    # Demo and Testing Functions
    
    def run_basic_demo(self):
        """Run a basic demonstration of memory management"""
        self.logger.info("Running basic memory management demo")
        
        # Allocate some pages
        pages = []
        for i in range(5):
            page = self.allocate_page()
            if page != 0:
                pages.append(page)
        
        # Create a process
        child_pid = self.create_process()
        
        # Allocate memory for the process
        if child_pid != -1:
            self.allocate_process_memory(child_pid, 8192)  # 2 pages
        
        # Simulate some page faults
        self.simulate_page_fault(child_pid, 0x400000, PAGE_FAULT_WRITE)
        self.simulate_page_fault(child_pid, 0x401000, 0)  # New page
        
        # Free some pages
        for page in pages[:2]:
            self.free_page(page)
        
        self.logger.info("Basic demo completed")
    
    def run_fork_demo(self):
        """Demonstrate process forking and copy-on-write"""
        self.logger.info("Running fork and COW demo")
        
        # Create initial process
        pid1 = self.create_process()
        if pid1 == -1:
            return
        
        # Allocate memory for it
        addr = self.allocate_process_memory(pid1, 4096)
        if addr is None:
            return
        
        # Fork the process
        pid2 = self.create_process(pid1)
        if pid2 == -1:
            return
        
        # Simulate write to shared page (triggers COW)
        self.simulate_page_fault(pid2, addr, PAGE_FAULT_PROTECTION | PAGE_FAULT_WRITE)
        
        # Create another child
        pid3 = self.create_process(pid1)
        
        self.logger.info("Fork and COW demo completed")
    
    def run_stress_test(self, num_operations: int = 100):
        """Run a stress test with many operations"""
        self.logger.info(f"Running stress test with {num_operations} operations")
        
        for i in range(num_operations):
            if i % 10 == 0:
                # Create a process occasionally
                self.create_process()
            
            if i % 3 == 0:
                # Allocate a page
                self.allocate_page()
            
            if i % 7 == 0:
                # Simulate page fault
                current_pid = self.process_manager.current_pid
                self.simulate_page_fault(current_pid, 0x500000 + (i * 4096), 0)
        
        self.logger.info("Stress test completed")
    
    def __str__(self) -> str:
        """String representation for debugging"""
        stats = self.get_memory_statistics()
        return (f"MemorySimulator(time={self.simulation_time:.1f}, "
                f"ops={self.total_operations}, "
                f"procs={stats['processes']['total_processes']}, "
                f"pages_free={stats['physical_memory']['free_pages']})")