"""
Virtual Memory Manager for Linux 0.01 Simulator
Based on mm/memory.c implementation with 2-level page tables
"""

import logging
from typing import Optional, Dict, List, Tuple
from config import *
from physical_memory import PhysicalMemory

class PageTableEntry:
    """Represents a page table entry"""
    
    def __init__(self, value: int = 0):
        self.value = value
    
    @property 
    def present(self) -> bool:
        return bool(self.value & PAGE_PRESENT)
    
    @present.setter
    def present(self, val: bool):
        if val:
            self.value |= PAGE_PRESENT
        else:
            self.value &= ~PAGE_PRESENT
    
    @property
    def writable(self) -> bool:
        return bool(self.value & PAGE_WRITE)
    
    @writable.setter
    def writable(self, val: bool):
        if val:
            self.value |= PAGE_WRITE
        else:
            self.value &= ~PAGE_WRITE
    
    @property
    def user(self) -> bool:
        return bool(self.value & PAGE_USER)
    
    @user.setter
    def user(self, val: bool):
        if val:
            self.value |= PAGE_USER
        else:
            self.value &= ~PAGE_USER
    
    @property
    def physical_address(self) -> int:
        return self.value & 0xFFFFF000
    
    @physical_address.setter
    def physical_address(self, addr: int):
        self.value = (self.value & 0xFFF) | (addr & 0xFFFFF000)
    
    def __str__(self) -> str:
        flags = []
        if self.present: flags.append("P")
        if self.writable: flags.append("W")
        if self.user: flags.append("U")
        return f"PTE(0x{self.physical_address:08x}, {','.join(flags)})"

class PageTable:
    """Represents a page table with 1024 entries"""
    
    def __init__(self):
        self.entries: List[PageTableEntry] = [PageTableEntry() for _ in range(PG_TABLE_SIZE)]
        self.physical_address = 0  # Physical address of this page table
    
    def get_entry(self, index: int) -> PageTableEntry:
        if 0 <= index < PG_TABLE_SIZE:
            return self.entries[index]
        raise IndexError(f"Page table index {index} out of range")
    
    def set_entry(self, index: int, physical_addr: int, flags: int = PAGE_DEFAULT):
        """Set page table entry"""
        if 0 <= index < PG_TABLE_SIZE:
            self.entries[index].value = (physical_addr & 0xFFFFF000) | (flags & 0xFFF)
        else:
            raise IndexError(f"Page table index {index} out of range")
    
    def clear_entry(self, index: int):
        """Clear page table entry"""
        if 0 <= index < PG_TABLE_SIZE:
            self.entries[index].value = 0
        else:
            raise IndexError(f"Page table index {index} out of range")

class VirtualMemory:
    """
    Virtual memory manager implementing Linux 0.01 2-level page table system.
    Based on the page directory and page table implementation in memory.c
    """
    
    def __init__(self, physical_memory: PhysicalMemory):
        """Initialize virtual memory manager"""
        self.physical_memory = physical_memory
        
        # Page directory (1024 entries, each covering 4MB)
        self.pg_dir: List[int] = [0] * PG_DIR_SIZE
        
        # Page tables (dynamically allocated)
        self.page_tables: Dict[int, PageTable] = {}
        
        # Statistics
        self.page_faults = 0
        self.cow_faults = 0
        self.allocation_faults = 0
        
        # For visualization
        self.last_mapped_address = None
        self.last_fault_address = None
        self.current_instruction = None
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Virtual memory manager initialized")

    def put_page(self, page: int, address: int) -> int:
        """
        Map a physical page to a virtual address.
        
        Based on put_page() in memory.c:
        page_table = (unsigned long *) ((address>>20) & 0xffc);
        if ((*page_table)&1)
            page_table = (unsigned long *) (0xfffff000 & *page_table);
        else {
            if (!(tmp=get_free_page()))
                return 0;
            *page_table = tmp|7;
            page_table = (unsigned long *) tmp;
        }
        page_table[(address>>12) & 0x3ff] = page | 7;
        
        Args:
            page: Physical address of page to map
            address: Virtual address to map to
            
        Returns:
            Physical address on success, 0 on failure
        """
        self.current_instruction = "put_page"
        
        # Validate inputs
        if not is_paging_address(page):
            self.logger.error(f"Invalid physical page address 0x{page:08x}")
            return 0
        
        # Check memory map consistency
        page_info = self.physical_memory.get_page_info(page)
        if page_info and page_info["reference_count"] != 1:
            self.logger.warning(f"mem_map disagrees with page 0x{page:08x} at 0x{address:08x}")
        
        # Get page directory index
        pg_dir_index = GET_PG_DIR_INDEX(address)
        pg_table_index = GET_PG_TABLE_INDEX(address)
        
        self.logger.debug(f"Mapping page 0x{page:08x} to virtual 0x{address:08x} "
                         f"(pgdir[{pg_dir_index}], pgtbl[{pg_table_index}])")
        
        # Check if page table exists
        if self.pg_dir[pg_dir_index] & PAGE_PRESENT:
            # Page table exists, get it
            page_table_addr = self.pg_dir[pg_dir_index] & 0xFFFFF000
            page_table_id = (page_table_addr - LOW_MEM) >> 12
        else:
            # Need to allocate page table
            page_table_addr = self.physical_memory.get_free_page()
            if page_table_addr == 0:
                self.logger.error("Failed to allocate page table")
                return 0
            
            # Create page table object
            page_table_id = (page_table_addr - LOW_MEM) >> 12
            self.page_tables[page_table_id] = PageTable()
            self.page_tables[page_table_id].physical_address = page_table_addr
            
            # Set page directory entry
            self.pg_dir[pg_dir_index] = page_table_addr | PAGE_DEFAULT
            
            self.logger.debug(f"Allocated new page table at 0x{page_table_addr:08x}")
        
        # Get or create page table
        if page_table_id not in self.page_tables:
            self.page_tables[page_table_id] = PageTable()
            self.page_tables[page_table_id].physical_address = page_table_addr
        
        page_table = self.page_tables[page_table_id]
        
        # Set page table entry
        page_table.set_entry(pg_table_index, page, PAGE_DEFAULT)
        
        self.last_mapped_address = address
        self.logger.info(f"Mapped physical 0x{page:08x} to virtual 0x{address:08x}")
        
        return page

    def get_physical_address(self, virtual_addr: int) -> Optional[int]:
        """
        Translate virtual address to physical address.
        
        Args:
            virtual_addr: Virtual address to translate
            
        Returns:
            Physical address or None if not mapped
        """
        pg_dir_index = GET_PG_DIR_INDEX(virtual_addr)
        pg_table_index = GET_PG_TABLE_INDEX(virtual_addr)
        page_offset = GET_PAGE_OFFSET(virtual_addr)
        
        # Check page directory entry
        if not (self.pg_dir[pg_dir_index] & PAGE_PRESENT):
            return None
        
        # Get page table
        page_table_addr = self.pg_dir[pg_dir_index] & 0xFFFFF000
        page_table_id = (page_table_addr - LOW_MEM) >> 12
        
        if page_table_id not in self.page_tables:
            return None
        
        page_table = self.page_tables[page_table_id]
        entry = page_table.get_entry(pg_table_index)
        
        # Check page table entry
        if not entry.present:
            return None
        
        return entry.physical_address + page_offset

    def copy_page_tables(self, from_addr: int, to_addr: int, size: int) -> int:
        """
        Copy page tables from one address space to another (used by fork).
        
        Based on copy_page_tables() in memory.c:
        from_dir = (unsigned long *) ((from>>20) & 0xffc);
        to_dir = (unsigned long *) ((to>>20) & 0xffc);
        size = ((unsigned) (size+0x3fffff)) >> 22;
        for( ; size-->0 ; from_dir++,to_dir++) {
            ...
        }
        
        Args:
            from_addr: Source virtual address
            to_addr: Destination virtual address  
            size: Size to copy in bytes
            
        Returns:
            0 on success, -1 on failure
        """
        self.current_instruction = "copy_page_tables"
        
        # Validate 4MB alignment
        if (from_addr & 0x3FFFFF) or (to_addr & 0x3FFFFF):
            self.logger.error("copy_page_tables called with wrong alignment")
            return -1
        
        # Calculate number of page directory entries to copy
        num_entries = ((size + 0x3FFFFF) >> 22)
        from_pg_dir_index = GET_PG_DIR_INDEX(from_addr)
        to_pg_dir_index = GET_PG_DIR_INDEX(to_addr)
        
        self.logger.debug(f"Copying {num_entries} page dir entries from {from_pg_dir_index} to {to_pg_dir_index}")
        
        for i in range(num_entries):
            from_index = from_pg_dir_index + i
            to_index = to_pg_dir_index + i
            
            # Check destination doesn't already exist
            if self.pg_dir[to_index] & PAGE_PRESENT:
                self.logger.error("copy_page_tables: destination already exists")
                return -1
            
            # Check if source exists
            if not (self.pg_dir[from_index] & PAGE_PRESENT):
                continue
            
            # Get source page table
            from_page_table_addr = self.pg_dir[from_index] & 0xFFFFF000
            from_page_table_id = (from_page_table_addr - LOW_MEM) >> 12
            
            if from_page_table_id not in self.page_tables:
                continue
            
            from_page_table = self.page_tables[from_page_table_id]
            
            # Allocate new page table for destination
            to_page_table_addr = self.physical_memory.get_free_page()
            if to_page_table_addr == 0:
                self.logger.error("Out of memory allocating page table")
                return -1
            
            to_page_table_id = (to_page_table_addr - LOW_MEM) >> 12
            to_page_table = PageTable()
            to_page_table.physical_address = to_page_table_addr
            self.page_tables[to_page_table_id] = to_page_table
            
            # Set destination page directory entry
            self.pg_dir[to_index] = to_page_table_addr | PAGE_DEFAULT
            
            # Determine number of page table entries to copy
            # Special case for kernel space (from==0): only copy first 160 entries (640KB)
            num_pages = 160 if from_addr == 0 else PG_TABLE_SIZE
            
            # Copy page table entries
            for j in range(num_pages):
                from_entry = from_page_table.get_entry(j)
                
                if not from_entry.present:
                    continue
                
                # Copy entry and remove write permission for COW
                to_entry_value = from_entry.value & ~PAGE_WRITE
                to_page_table.entries[j].value = to_entry_value
                
                # Set COW on source page too (if above LOW_MEM)
                if from_entry.physical_address > LOW_MEM:
                    from_page_table.entries[j].value = to_entry_value
                    # Increment reference count
                    self.physical_memory.increment_page_ref(from_entry.physical_address)
        
        self.logger.info(f"Copied page tables from 0x{from_addr:08x} to 0x{to_addr:08x}, size {size}")
        return 0

    def free_page_tables(self, from_addr: int, size: int) -> int:
        """
        Free page tables for a memory region.
        
        Based on free_page_tables() in memory.c
        
        Args:
            from_addr: Starting virtual address
            size: Size of region to free
            
        Returns:
            0 on success
        """
        self.current_instruction = "free_page_tables"
        
        # Validate alignment
        if from_addr & 0x3FFFFF:
            self.logger.error("free_page_tables called with wrong alignment")
            return -1
        
        if from_addr == 0:
            self.logger.error("Trying to free up swapper memory space")
            return -1
        
        # Calculate number of page directory entries
        num_entries = (size + 0x3FFFFF) >> 22
        pg_dir_index = GET_PG_DIR_INDEX(from_addr)
        
        self.logger.debug(f"Freeing {num_entries} page dir entries starting at {pg_dir_index}")
        
        for i in range(num_entries):
            dir_index = pg_dir_index + i
            
            if not (self.pg_dir[dir_index] & PAGE_PRESENT):
                continue
            
            # Get page table
            page_table_addr = self.pg_dir[dir_index] & 0xFFFFF000
            page_table_id = (page_table_addr - LOW_MEM) >> 12
            
            if page_table_id in self.page_tables:
                page_table = self.page_tables[page_table_id]
                
                # Free all pages in the page table
                for j in range(PG_TABLE_SIZE):
                    entry = page_table.get_entry(j)
                    if entry.present:
                        self.physical_memory.free_page(entry.physical_address)
                        page_table.clear_entry(j)
                
                # Remove page table
                del self.page_tables[page_table_id]
            
            # Free the page table itself
            self.physical_memory.free_page(page_table_addr)
            self.pg_dir[dir_index] = 0
        
        self.logger.info(f"Freed page tables for region 0x{from_addr:08x}, size {size}")
        return 0

    def do_no_page(self, error_code: int, address: int) -> bool:
        """
        Handle page fault for unmapped page.
        
        Based on do_no_page() in memory.c:
        if (tmp=get_free_page())
            if (put_page(tmp,address))
                return;
        do_exit(SIGSEGV);
        
        Args:
            error_code: Page fault error code
            address: Faulting virtual address
            
        Returns:
            True on success, False if should terminate process
        """
        self.current_instruction = "do_no_page"
        self.page_faults += 1
        self.allocation_faults += 1
        self.last_fault_address = address
        
        self.logger.debug(f"Page fault at 0x{address:08x}, error_code=0x{error_code:x}")
        
        # Allocate new physical page
        new_page = self.physical_memory.get_free_page()
        if new_page == 0:
            self.logger.error("Out of memory handling page fault")
            return False
        
        # Map the page
        if self.put_page(new_page, address) == 0:
            self.logger.error("Failed to map page in page fault handler")
            self.physical_memory.free_page(new_page)
            return False
        
        self.logger.info(f"Allocated new page 0x{new_page:08x} for fault at 0x{address:08x}")
        return True

    def do_wp_page(self, error_code: int, address: int) -> bool:
        """
        Handle write protection fault (copy-on-write).
        
        Based on do_wp_page() in memory.c
        
        Args:
            error_code: Page fault error code
            address: Faulting virtual address
            
        Returns:
            True on success, False on error
        """
        self.current_instruction = "do_wp_page"
        self.page_faults += 1
        self.cow_faults += 1
        self.last_fault_address = address
        
        self.logger.debug(f"Write protection fault at 0x{address:08x}")
        
        # Find the page table entry
        pg_dir_index = GET_PG_DIR_INDEX(address)
        pg_table_index = GET_PG_TABLE_INDEX(address)
        
        if not (self.pg_dir[pg_dir_index] & PAGE_PRESENT):
            self.logger.error("Page directory entry not present in wp fault")
            return False
        
        page_table_addr = self.pg_dir[pg_dir_index] & 0xFFFFF000
        page_table_id = (page_table_addr - LOW_MEM) >> 12
        
        if page_table_id not in self.page_tables:
            self.logger.error("Page table not found in wp fault")
            return False
        
        page_table = self.page_tables[page_table_id]
        entry = page_table.get_entry(pg_table_index)
        
        if not entry.present:
            self.logger.error("Page table entry not present in wp fault")
            return False
        
        old_page = entry.physical_address
        old_ref_count = self.physical_memory.get_reference_count(old_page)
        
        if old_ref_count == 1:
            # Only one reference, just make it writable
            entry.writable = True
            self.logger.debug(f"Made page 0x{old_page:08x} writable (only reference)")
        else:
            # Multiple references, need to copy
            new_page = self.physical_memory.get_free_page()
            if new_page == 0:
                self.logger.error("Out of memory in COW fault")
                return False
            
            # Copy page contents (simulated)
            self.logger.debug(f"Copying page 0x{old_page:08x} to 0x{new_page:08x}")
            
            # Update page table entry
            page_table.set_entry(pg_table_index, new_page, PAGE_DEFAULT)
            
            # Decrement old page reference count
            self.physical_memory.free_page(old_page)
            
            self.logger.info(f"COW: copied page 0x{old_page:08x} to 0x{new_page:08x}")
        
        return True

    def write_verify(self, address: int) -> bool:
        """
        Verify write access to address.
        
        Based on write_verify() in memory.c
        
        Args:
            address: Virtual address to verify
            
        Returns:
            True if write allowed, False otherwise
        """
        page = self.get_physical_address(address & ~(PAGE_SIZE - 1))
        if page is None:
            return False
        
        # Get page table entry
        pg_dir_index = GET_PG_DIR_INDEX(address)
        pg_table_index = GET_PG_TABLE_INDEX(address)
        
        if not (self.pg_dir[pg_dir_index] & PAGE_PRESENT):
            return False
        
        page_table_addr = self.pg_dir[pg_dir_index] & 0xFFFFF000
        page_table_id = (page_table_addr - LOW_MEM) >> 12
        
        if page_table_id not in self.page_tables:
            return False
        
        page_table = self.page_tables[page_table_id]
        entry = page_table.get_entry(pg_table_index)
        
        # Check if present but not writable (COW page)
        if entry.present and not entry.writable:
            # Trigger COW
            return self.do_wp_page(PAGE_FAULT_WRITE, address)
        
        return entry.present and entry.writable

    def get_page_table_info(self, virtual_addr: int) -> Optional[dict]:
        """Get detailed page table information for an address"""
        pg_dir_index = GET_PG_DIR_INDEX(virtual_addr)
        pg_table_index = GET_PG_TABLE_INDEX(virtual_addr)
        page_offset = GET_PAGE_OFFSET(virtual_addr)
        
        info = {
            "virtual_address": virtual_addr,
            "pg_dir_index": pg_dir_index,
            "pg_table_index": pg_table_index,
            "page_offset": page_offset,
            "pg_dir_entry": self.pg_dir[pg_dir_index],
            "pg_dir_present": bool(self.pg_dir[pg_dir_index] & PAGE_PRESENT)
        }
        
        if info["pg_dir_present"]:
            page_table_addr = self.pg_dir[pg_dir_index] & 0xFFFFF000
            page_table_id = (page_table_addr - LOW_MEM) >> 12
            info["page_table_address"] = page_table_addr
            
            if page_table_id in self.page_tables:
                page_table = self.page_tables[page_table_id]
                entry = page_table.get_entry(pg_table_index)
                info["pg_table_entry"] = entry.value
                info["pg_table_present"] = entry.present
                info["pg_table_writable"] = entry.writable
                info["pg_table_user"] = entry.user
                info["physical_address"] = entry.physical_address + page_offset if entry.present else None
        
        return info

    def get_memory_mappings(self) -> List[dict]:
        """Get all current memory mappings for visualization"""
        mappings = []
        
        for dir_index in range(PG_DIR_SIZE):
            if self.pg_dir[dir_index] & PAGE_PRESENT:
                page_table_addr = self.pg_dir[dir_index] & 0xFFFFF000
                page_table_id = (page_table_addr - LOW_MEM) >> 12
                
                if page_table_id in self.page_tables:
                    page_table = self.page_tables[page_table_id]
                    
                    for table_index in range(PG_TABLE_SIZE):
                        entry = page_table.get_entry(table_index)
                        if entry.present:
                            virtual_addr = (dir_index << 22) | (table_index << 12)
                            mappings.append({
                                "virtual_address": virtual_addr,
                                "physical_address": entry.physical_address,
                                "writable": entry.writable,
                                "user": entry.user,
                                "size": PAGE_SIZE
                            })
        
        return mappings

    def reset(self):
        """Reset virtual memory to initial state"""
        self.pg_dir = [0] * PG_DIR_SIZE
        self.page_tables.clear()
        self.page_faults = 0
        self.cow_faults = 0
        self.allocation_faults = 0
        self.last_mapped_address = None
        self.last_fault_address = None
        self.logger.info("Virtual memory reset to initial state")

    def __str__(self) -> str:
        """String representation for debugging"""
        num_page_tables = len(self.page_tables)
        mappings = len(self.get_memory_mappings())
        return (f"VirtualMemory(page_tables={num_page_tables}, "
                f"mappings={mappings}, "
                f"page_faults={self.page_faults})")