#!/usr/bin/env python3
"""
Command-line interface for Linux 0.01 Memory Management Simulator
Provides interactive testing and demonstration capabilities
"""

import sys
import cmd
import json
from memory_simulator import MemorySimulator
from config import *

class SimulatorCLI(cmd.Cmd):
    """Interactive command-line interface for the memory simulator"""
    
    intro = """
Linux 0.01 Memory Management Simulator
======================================

Type 'help' for available commands.
Type 'demo' to run a basic demonstration.
Type 'quit' to exit.
"""
    prompt = '(mm-sim) '
    
    def __init__(self):
        super().__init__()
        self.simulator = MemorySimulator()
        self.simulator.start_simulation()
    
    def do_stats(self, args):
        """Show memory and process statistics"""
        stats = self.simulator.get_memory_statistics()
        
        print("\n=== Memory Statistics ===")
        phys = stats['physical_memory']
        print(f"Physical Memory: {phys['free_pages']}/{phys['total_pages']} pages free")
        print(f"Memory Usage: {phys['used_memory']//1024}KB used, {phys['free_memory']//1024}KB free")
        print(f"Fragmentation: {phys['fragmentation']:.2%}")
        
        print("\n=== Virtual Memory ===")
        vmem = stats['virtual_memory']
        print(f"Page Faults: {vmem['page_faults']} total, {vmem['cow_faults']} COW")
        print(f"Page Tables: {vmem['page_tables']}")
        print(f"Mappings: {vmem['mappings']}")
        
        print("\n=== Processes ===")
        proc = stats['processes']
        print(f"Total Processes: {proc['total_processes']}")
        print(f"Running: {proc['running_processes']}, Zombies: {proc['zombie_processes']}")
        print(f"Current PID: {proc['current_pid']}")
        print(f"Total Forks: {proc['total_forks']}, Exits: {proc['total_exits']}")
        
        print("\n=== Simulation ===")
        sim = stats['simulation']
        print(f"Time: {sim['time']:.1f}, Operations: {sim['operations']}")
        print(f"Events: {sim['events']}, Uptime: {sim['uptime']:.1f}s")
    
    def do_processes(self, args):
        """Show process list"""
        processes = self.simulator.get_process_list()
        
        print("\n=== Process List ===")
        print(f"{'PID':<4} {'PPID':<5} {'State':<6} {'Memory':<8} {'Faults':<8} {'Children'}")
        print("-" * 60)
        
        for proc in processes:
            children_str = ','.join(map(str, proc['children'])) if proc['children'] else '-'
            print(f"{proc['pid']:<4} {proc['parent_pid']:<5} {proc['state']:<6} "
                  f"{proc['memory_usage']:<8} {proc['page_faults']:<8} {children_str}")
    
    def do_memory(self, args):
        """Show memory map visualization"""
        memory_map = self.simulator.get_physical_memory_map()
        
        print("\n=== Physical Memory Map ===")
        print(f"Each character represents {PAGE_SIZE//1024}KB")
        print("Legend: . = free, # = allocated, + = shared")
        
        # Display memory map in rows of 64 pages
        for i in range(0, len(memory_map), 64):
            row = memory_map[i:i+64]
            chars = []
            for page_ref in row:
                if page_ref == 0:
                    chars.append('.')
                elif page_ref == 1:
                    chars.append('#')
                else:
                    chars.append('+')
            print(f"{i//64:3}: {''.join(chars)}")
        
        print(f"\nTotal pages: {len(memory_map)}")
    
    def do_mappings(self, args):
        """Show virtual memory mappings"""
        mappings = self.simulator.get_memory_mappings()
        
        print("\n=== Virtual Memory Mappings ===")
        print(f"{'Virtual':<12} {'Physical':<12} {'Size':<8} {'Perms'}")
        print("-" * 45)
        
        for mapping in mappings[:20]:  # Show first 20 mappings
            perms = ""
            if mapping['writable']:
                perms += "w"
            if mapping['user']:
                perms += "u"
            
            print(f"0x{mapping['virtual_address']:08x} 0x{mapping['physical_address']:08x} "
                  f"{mapping['size']:<8} {perms}")
        
        if len(mappings) > 20:
            print(f"... and {len(mappings) - 20} more mappings")
    
    def do_events(self, args):
        """Show recent simulation events"""
        event_type = args.strip() if args.strip() else None
        events = self.simulator.get_events(event_type, limit=10)
        
        print(f"\n=== Recent Events {'(' + event_type + ')' if event_type else ''} ===")
        
        for event in reversed(events):  # Show most recent first
            print(f"[{event.timestamp:6.1f}] {event.event_type:10} {event.description}")
    
    def do_alloc(self, args):
        """Allocate a physical page"""
        addr = self.simulator.allocate_page()
        if addr != 0:
            print(f"Allocated page at 0x{addr:08x}")
        else:
            print("Failed to allocate page - out of memory")
    
    def do_free(self, args):
        """Free a physical page: free <address>"""
        try:
            addr = int(args.strip(), 0)  # Support hex (0x...) and decimal
            success = self.simulator.free_page(addr)
            if success:
                print(f"Freed page at 0x{addr:08x}")
            else:
                print(f"Failed to free page at 0x{addr:08x}")
        except ValueError:
            print("Usage: free <address>")
    
    def do_map(self, args):
        """Map physical page to virtual address: map <physical> <virtual>"""
        try:
            parts = args.strip().split()
            if len(parts) != 2:
                print("Usage: map <physical_addr> <virtual_addr>")
                return
            
            phys_addr = int(parts[0], 0)
            virt_addr = int(parts[1], 0)
            
            success = self.simulator.map_page(phys_addr, virt_addr)
            if success:
                print(f"Mapped 0x{phys_addr:08x} -> 0x{virt_addr:08x}")
            else:
                print("Mapping failed")
        except ValueError:
            print("Usage: map <physical_addr> <virtual_addr>")
    
    def do_translate(self, args):
        """Translate virtual address to physical: translate <virtual_addr>"""
        try:
            virt_addr = int(args.strip(), 0)
            phys_addr = self.simulator.translate_address(virt_addr)
            
            if phys_addr is not None:
                print(f"0x{virt_addr:08x} -> 0x{phys_addr:08x}")
                
                # Show page table info
                page_info = self.simulator.get_page_table_info(virt_addr)
                if page_info:
                    print(f"  Page directory index: {page_info['pg_dir_index']}")
                    print(f"  Page table index: {page_info['pg_table_index']}")
                    print(f"  Page offset: {page_info['page_offset']}")
            else:
                print(f"0x{virt_addr:08x} -> Not mapped")
        except ValueError:
            print("Usage: translate <virtual_addr>")
    
    def do_fork(self, args):
        """Create a new process: fork [parent_pid]"""
        try:
            parent_pid = int(args.strip()) if args.strip() else 0
            child_pid = self.simulator.create_process(parent_pid)
            
            if child_pid != -1:
                print(f"Created process {child_pid} (parent: {parent_pid})")
            else:
                print("Fork failed")
        except ValueError:
            print("Usage: fork [parent_pid]")
    
    def do_exit(self, args):
        """Terminate a process: exit <pid> [exit_code]"""
        try:
            parts = args.strip().split()
            if len(parts) < 1:
                print("Usage: exit <pid> [exit_code]")
                return
            
            pid = int(parts[0])
            exit_code = int(parts[1]) if len(parts) > 1 else 0
            
            success = self.simulator.terminate_process(pid, exit_code)
            if success:
                print(f"Process {pid} exited with code {exit_code}")
            else:
                print(f"Failed to exit process {pid}")
        except ValueError:
            print("Usage: exit <pid> [exit_code]")
    
    def do_fault(self, args):
        """Simulate page fault: fault <pid> <addr> [error_code]"""
        try:
            parts = args.strip().split()
            if len(parts) < 2:
                print("Usage: fault <pid> <addr> [error_code]")
                return
            
            pid = int(parts[0])
            addr = int(parts[1], 0)
            error_code = int(parts[2], 0) if len(parts) > 2 else 0
            
            success = self.simulator.simulate_page_fault(pid, addr, error_code)
            if success:
                print(f"Page fault handled successfully")
            else:
                print(f"Page fault killed process {pid}")
        except ValueError:
            print("Usage: fault <pid> <addr> [error_code]")
    
    def do_switch(self, args):
        """Switch to a process: switch <pid>"""
        try:
            pid = int(args.strip())
            success = self.simulator.switch_process(pid)
            if success:
                print(f"Switched to process {pid}")
            else:
                print(f"Failed to switch to process {pid}")
        except ValueError:
            print("Usage: switch <pid>")
    
    def do_step(self, args):
        """Execute one simulation step"""
        self.simulator.step_simulation()
        print(f"Simulation step completed (time: {self.simulator.simulation_time})")
    
    def do_demo(self, args):
        """Run demonstration: demo [basic|fork|stress]"""
        demo_type = args.strip() if args.strip() else "basic"
        
        print(f"Running {demo_type} demonstration...")
        
        if demo_type == "basic":
            self.simulator.run_basic_demo()
        elif demo_type == "fork":
            self.simulator.run_fork_demo()
        elif demo_type == "stress":
            self.simulator.run_stress_test()
        else:
            print("Available demos: basic, fork, stress")
            return
        
        print("Demonstration completed. Use 'stats' to see results.")
    
    def do_reset(self, args):
        """Reset simulation to initial state"""
        self.simulator.reset_simulation()
        self.simulator.start_simulation()
        print("Simulation reset to initial state")
    
    def do_save(self, args):
        """Save current state to file: save <filename>"""
        filename = args.strip()
        if not filename:
            print("Usage: save <filename>")
            return
        
        try:
            state = {
                "statistics": self.simulator.get_memory_statistics(),
                "processes": self.simulator.get_process_list(),
                "mappings": self.simulator.get_memory_mappings(),
                "events": [
                    {
                        "timestamp": e.timestamp,
                        "event_type": e.event_type,
                        "description": e.description,
                        "details": e.details
                    }
                    for e in self.simulator.get_events(limit=100)
                ]
            }
            
            with open(filename, 'w') as f:
                json.dump(state, f, indent=2)
            
            print(f"State saved to {filename}")
        except Exception as e:
            print(f"Failed to save state: {e}")
    
    def do_help_memory(self, args):
        """Show help about memory management concepts"""
        print("""
Memory Management Concepts in Linux 0.01:

1. Physical Memory:
   - 8MB total memory (configurable)
   - 1MB reserved for kernel
   - 1MB for buffers  
   - 6MB for user pages (1536 pages of 4KB each)
   - mem_map[] array tracks page allocation

2. Virtual Memory:
   - 2-level page table system
   - Page directory (1024 entries, each covers 4MB)
   - Page tables (1024 entries each, each covers 4KB)
   - Pages can be present, writable, user-accessible

3. Copy-on-Write:
   - Parent and child share pages after fork()
   - Pages marked read-only initially
   - Write fault triggers page copying
   - Saves memory for fork() operations

4. Page Faults:
   - Generated when accessing unmapped pages
   - Protection faults for COW or permission violations
   - do_no_page() allocates new pages
   - do_wp_page() handles COW faults

Use 'help <command>' for specific command help.
""")
    
    def do_quit(self, args):
        """Exit the simulator"""
        print("Goodbye!")
        self.simulator.stop_simulation()
        return True
    
    def do_exit_cli(self, args):
        """Exit the simulator"""
        return self.do_quit(args)
    
    def default(self, line):
        """Handle unknown commands"""
        print(f"Unknown command: {line}")
        print("Type 'help' for available commands.")

def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        # Non-interactive mode for running demos
        simulator = MemorySimulator()
        simulator.start_simulation()
        
        command = sys.argv[1]
        if command == "basic":
            simulator.run_basic_demo()
        elif command == "fork":
            simulator.run_fork_demo()
        elif command == "stress":
            simulator.run_stress_test()
        else:
            print(f"Unknown demo: {command}")
            print("Available demos: basic, fork, stress")
            return 1
        
        # Print final statistics
        stats = simulator.get_memory_statistics()
        print(f"\nSimulation completed:")
        print(f"  Operations: {stats['simulation']['operations']}")
        print(f"  Page faults: {stats['virtual_memory']['page_faults']}")
        print(f"  Processes: {stats['processes']['total_processes']}")
        print(f"  Memory usage: {stats['physical_memory']['used_memory']//1024}KB")
        
        return 0
    else:
        # Interactive mode
        cli = SimulatorCLI()
        try:
            cli.cmdloop()
        except KeyboardInterrupt:
            print("\nExiting...")
        return 0

if __name__ == "__main__":
    sys.exit(main())