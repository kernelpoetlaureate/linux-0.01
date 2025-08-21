"""
Physical Memory Manager for Linux 0.01 Simulator
Based on mm/memory.c implementation
"""

import logging
from typing import Optional, List, Tuple
from config import *

class PhysicalMemory:
    """
    Manages physical memory allocation using the same algorithms as Linux 0.01.
    Implements the mem_map array and page allocation functions.
    """
    
    def __init__(self):
        """Initialize physical memory manager"""
        # Memory map array - tracks page allocation status
        # 0 = free, >0 = reference count
        self.mem_map: List[int] = [0] * PAGING_PAGES
        
        # Statistics
        self.total_pages = PAGING_PAGES
        self.allocated_pages = 0
        self.allocation_count = 0
        self.free_count = 0
        
        # For visualization and debugging
        self.last_allocated_page = None
        self.last_freed_page = None
        self.allocation_history: List[Tuple[str, int, int]] = []  # (operation, page_num, timestamp)
        
        # Simulation state
        self.current_instruction = None
        self.step_mode = False
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Physical memory initialized: {self.total_pages} pages ({PAGING_MEMORY // 1024}KB)")

    def get_free_page(self) -> int:
        """
        Allocate a free physical page.
        
        Based on the assembly implementation in memory.c:
        __asm__("std ; repne ; scasw\\n\\t"
                "jne 1f\\n\\t" 
                "movw $1,2(%%edi)\\n\\t"
                ...
        
        Returns:
            Physical address of allocated page, or 0 if no free pages
        """
        self.current_instruction = "get_free_page"
        self.logger.debug("Searching for free page...")
        
        # Scan backwards through mem_map (std = set direction flag)
        for i in range(PAGING_PAGES - 1, -1, -1):
            if self.mem_map[i] == 0:  # Found free page
                # Mark as allocated
                self.mem_map[i] = 1
                
                # Calculate physical address
                physical_addr = LOW_MEM + (i * PAGE_SIZE)
                
                # Update statistics
                self.allocated_pages += 1
                self.allocation_count += 1
                self.last_allocated_page = i
                
                # Record for visualization
                self.allocation_history.append(("alloc", i, self.allocation_count))
                
                self.logger.info(f"Allocated page {i} at address 0x{physical_addr:08x}")
                return physical_addr
        
        # No free pages found
        self.logger.warning("No free pages available!")
        return 0

    def free_page(self, addr: int) -> bool:
        """
        Free a physical page.
        
        Based on free_page() in memory.c:
        if (addr<LOW_MEM) return;
        if (addr>HIGH_MEMORY) panic("trying to free nonexistent page");
        addr -= LOW_MEM;
        addr >>= 12;
        if (mem_map[addr]--) return;
        mem_map[addr]=0;
        panic("trying to free free page");
        
        Args:
            addr: Physical address to free
            
        Returns:
            True on success, False on error
        """
        self.current_instruction = "free_page"
        
        # Validate address range
        if addr < LOW_MEM:
            self.logger.warning(f"Attempt to free kernel memory at 0x{addr:08x}")
            return False
            
        if addr >= HIGH_MEMORY:
            self.logger.error(f"Attempt to free nonexistent page at 0x{addr:08x}")
            return False
        
        # Convert to page number
        page_num = (addr - LOW_MEM) >> 12
        
        if page_num >= PAGING_PAGES:
            self.logger.error(f"Invalid page number {page_num}")
            return False
        
        # Check if page is allocated
        if self.mem_map[page_num] == 0:
            self.logger.error(f"Attempt to free already free page {page_num}")
            return False
        
        # Decrement reference count
        self.mem_map[page_num] -= 1
        
        # If reference count reaches 0, page is truly free
        if self.mem_map[page_num] == 0:
            self.allocated_pages -= 1
            self.free_count += 1
            self.last_freed_page = page_num
            
            # Record for visualization
            self.allocation_history.append(("free", page_num, self.allocation_count))
            
            self.logger.info(f"Freed page {page_num} at address 0x{addr:08x}")
        else:
            self.logger.debug(f"Decremented ref count for page {page_num} to {self.mem_map[page_num]}")
        
        return True

    def get_page_info(self, addr: int) -> Optional[dict]:
        """
        Get information about a page at given address.
        
        Args:
            addr: Physical address
            
        Returns:
            Dictionary with page information or None if invalid
        """
        if not is_paging_address(addr):
            return None
            
        page_num = (addr - LOW_MEM) >> 12
        if page_num >= PAGING_PAGES:
            return None
            
        return {
            "page_number": page_num,
            "physical_address": LOW_MEM + (page_num * PAGE_SIZE),
            "reference_count": self.mem_map[page_num],
            "is_free": self.mem_map[page_num] == 0,
            "offset_in_page": addr & (PAGE_SIZE - 1)
        }

    def calc_mem(self) -> dict:
        """
        Calculate memory statistics.
        
        Based on calc_mem() in memory.c:
        for(i=0 ; i<PAGING_PAGES ; i++)
            if (!mem_map[i]) free++;
        printk("%d pages free (of %d)\\n\\r",free,PAGING_PAGES);
        
        Returns:
            Dictionary with memory statistics
        """
        self.current_instruction = "calc_mem"
        
        free_pages = 0
        allocated_pages = 0
        shared_pages = 0
        
        for i in range(PAGING_PAGES):
            if self.mem_map[i] == 0:
                free_pages += 1
            elif self.mem_map[i] == 1:
                allocated_pages += 1
            else:
                shared_pages += 1
        
        stats = {
            "total_pages": PAGING_PAGES,
            "free_pages": free_pages,
            "allocated_pages": allocated_pages,
            "shared_pages": shared_pages,
            "total_memory": PAGING_MEMORY,
            "free_memory": free_pages * PAGE_SIZE,
            "used_memory": (allocated_pages + shared_pages) * PAGE_SIZE,
            "fragmentation": self._calculate_fragmentation()
        }
        
        self.logger.info(f"Memory stats: {free_pages} pages free (of {PAGING_PAGES})")
        return stats

    def _calculate_fragmentation(self) -> float:
        """Calculate memory fragmentation percentage"""
        if self.allocated_pages == 0:
            return 0.0
            
        # Find largest contiguous free block
        max_free_block = 0
        current_free_block = 0
        
        for i in range(PAGING_PAGES):
            if self.mem_map[i] == 0:
                current_free_block += 1
                max_free_block = max(max_free_block, current_free_block)
            else:
                current_free_block = 0
        
        # Fragmentation = 1 - (largest_free_block / total_free_pages)
        free_pages = PAGING_PAGES - self.allocated_pages
        if free_pages == 0:
            return 0.0
            
        return 1.0 - (max_free_block / free_pages)

    def get_memory_map(self) -> List[int]:
        """Return copy of memory map for visualization"""
        return self.mem_map.copy()

    def get_free_page_ranges(self) -> List[Tuple[int, int]]:
        """
        Get ranges of contiguous free pages.
        
        Returns:
            List of (start_page, length) tuples
        """
        ranges = []
        start = None
        
        for i in range(PAGING_PAGES):
            if self.mem_map[i] == 0:  # Free page
                if start is None:
                    start = i
            else:  # Allocated page
                if start is not None:
                    ranges.append((start, i - start))
                    start = None
        
        # Handle case where free range extends to end
        if start is not None:
            ranges.append((start, PAGING_PAGES - start))
            
        return ranges

    def allocate_specific_page(self, page_num: int) -> bool:
        """
        Allocate a specific page number (for testing/demonstration).
        
        Args:
            page_num: Page number to allocate
            
        Returns:
            True if successful, False if page already allocated
        """
        if page_num >= PAGING_PAGES or page_num < 0:
            return False
            
        if self.mem_map[page_num] != 0:
            return False
            
        self.mem_map[page_num] = 1
        self.allocated_pages += 1
        self.allocation_count += 1
        self.last_allocated_page = page_num
        
        self.allocation_history.append(("alloc", page_num, self.allocation_count))
        return True

    def increment_page_ref(self, addr: int) -> bool:
        """
        Increment reference count for a page (used in copy-on-write).
        
        Args:
            addr: Physical address
            
        Returns:
            True on success, False on error
        """
        if not is_paging_address(addr):
            return False
            
        page_num = (addr - LOW_MEM) >> 12
        if page_num >= PAGING_PAGES:
            return False
            
        if self.mem_map[page_num] == 0:
            return False  # Can't increment free page
            
        self.mem_map[page_num] += 1
        self.logger.debug(f"Incremented ref count for page {page_num} to {self.mem_map[page_num]}")
        return True

    def get_reference_count(self, addr: int) -> int:
        """
        Get reference count for a page.
        
        Args:
            addr: Physical address
            
        Returns:
            Reference count, or -1 if invalid address
        """
        if not is_paging_address(addr):
            return -1
            
        page_num = (addr - LOW_MEM) >> 12
        if page_num >= PAGING_PAGES:
            return -1
            
        return self.mem_map[page_num]

    def reset(self):
        """Reset all memory to initial state"""
        self.mem_map = [0] * PAGING_PAGES
        self.allocated_pages = 0
        self.allocation_count = 0
        self.free_count = 0
        self.last_allocated_page = None
        self.last_freed_page = None
        self.allocation_history.clear()
        self.logger.info("Physical memory reset to initial state")

    def __str__(self) -> str:
        """String representation for debugging"""
        stats = self.calc_mem()
        return (f"PhysicalMemory(total={stats['total_pages']}, "
                f"free={stats['free_pages']}, "
                f"allocated={stats['allocated_pages']}, "
                f"shared={stats['shared_pages']})")