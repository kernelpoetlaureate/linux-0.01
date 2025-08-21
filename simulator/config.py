"""
Linux 0.01 Memory Management Configuration
Based on include/linux/config.h and mm/memory.c
"""

# Memory layout constants from config.h
HIGH_MEMORY = 0x800000  # 8MB total memory
BUFFER_END = 0x200000   # 2MB buffer end
LOW_MEM = 0x100000      # 1MB - start of paging memory

# Calculated constants from memory.c
PAGING_MEMORY = HIGH_MEMORY - LOW_MEM  # 7MB of pageable memory
PAGE_SIZE = 4096                       # 4KB pages
PAGING_PAGES = PAGING_MEMORY // PAGE_SIZE  # 1792 pages

# Page directory and table constants
PG_DIR_SIZE = 1024      # Page directory entries
PG_TABLE_SIZE = 1024    # Page table entries per table

# Memory map constants
def MAP_NR(addr):
    """Convert address to page number"""
    return (addr - LOW_MEM) >> 12

# Task constants from sched.h
NR_TASKS = 64           # Maximum number of tasks
HZ = 100               # Timer frequency

# Task states
TASK_RUNNING = 0
TASK_INTERRUPTIBLE = 1
TASK_UNINTERRUPTIBLE = 2
TASK_ZOMBIE = 3
TASK_STOPPED = 4

# Page protection bits
PAGE_PRESENT = 0x1      # Page is present
PAGE_WRITE = 0x2        # Page is writable
PAGE_USER = 0x4         # Page is user accessible

# Default page attributes
PAGE_DEFAULT = PAGE_PRESENT | PAGE_WRITE | PAGE_USER  # 0x7

# Address manipulation macros
def GET_PG_DIR_INDEX(addr):
    """Get page directory index from address"""
    return (addr >> 22) & 0x3FF

def GET_PG_TABLE_INDEX(addr):
    """Get page table index from address"""
    return (addr >> 12) & 0x3FF

def GET_PAGE_OFFSET(addr):
    """Get offset within page"""
    return addr & 0xFFF

# Memory region types for visualization
MEMORY_KERNEL = "kernel"
MEMORY_BUFFER = "buffer"
MEMORY_USER = "user"
MEMORY_FREE = "free"

# Colors for GUI visualization
COLORS = {
    MEMORY_KERNEL: "#FF6B6B",  # Red
    MEMORY_BUFFER: "#4ECDC4",  # Teal
    MEMORY_USER: "#45B7D1",    # Blue
    MEMORY_FREE: "#F8F9FA"     # Light gray
}

# Simulation parameters
DEFAULT_SIMULATION_SPEED = 1000  # milliseconds per step
MAX_SIMULATION_SPEED = 100       # minimum delay
MIN_SIMULATION_SPEED = 5000      # maximum delay

# Error codes for page faults (from page.s)
PAGE_FAULT_PROTECTION = 0x1  # Protection violation
PAGE_FAULT_WRITE = 0x2       # Write fault
PAGE_FAULT_USER = 0x4        # User mode fault

# Assembly instruction mappings for visualization
ASM_INSTRUCTIONS = {
    "get_free_page": [
        "std ; repne ; scasw",
        "jne 1f",
        "movw $1,2(%edi)",
        "sall $12,%ecx",
        "movl %ecx,%edx",
        "addl LOW_MEM,%edx",
        "movl $1024,%ecx",
        "leal 4092(%edx),%edi",
        "rep ; stosl",
        "movl %edx,%eax"
    ],
    "free_page": [
        "check addr < LOW_MEM",
        "check addr > HIGH_MEMORY", 
        "addr -= LOW_MEM",
        "addr >>= 12",
        "mem_map[addr]--"
    ],
    "put_page": [
        "get page directory entry",
        "check if page table exists",
        "allocate page table if needed",
        "set page table entry",
        "return physical address"
    ]
}

# Help text for educational features
HELP_TEXT = {
    "get_free_page": """
    Allocates a free physical page from the memory pool.
    
    Algorithm:
    1. Scan mem_map array backwards for free page (value 0)
    2. Mark page as allocated (set to 1)
    3. Clear the allocated page (4096 bytes)
    4. Return physical address of page
    
    Returns 0 if no free pages available.
    """,
    
    "free_page": """
    Releases a physical page back to the free pool.
    
    Algorithm:
    1. Validate address is in paging range
    2. Convert address to page number
    3. Decrement reference count in mem_map
    4. Set to 0 if count reaches zero
    
    Panics if trying to free already free page.
    """,
    
    "put_page": """
    Maps a physical page to a virtual address.
    
    Algorithm:
    1. Get page directory entry for virtual address
    2. If page table doesn't exist, allocate one
    3. Set page table entry with physical address
    4. Set appropriate permission bits
    
    Returns physical address on success, 0 on failure.
    """,
    
    "copy_page_tables": """
    Copies page tables from parent to child process (fork).
    
    Algorithm:
    1. Validate 4MB alignment of addresses
    2. For each page directory entry:
       - Allocate new page table for child
       - Copy entries from parent table
       - Set copy-on-write for shared pages
       - Increment reference counts
    
    Used exclusively by fork() system call.
    """,
    
    "do_wp_page": """
    Handles write protection faults (copy-on-write).
    
    Algorithm:
    1. Find page table entry causing fault
    2. If page reference count = 1, just set write bit
    3. Otherwise, allocate new page
    4. Copy page contents to new page
    5. Update page table entry
    6. Decrement old page reference count
    
    Implements copy-on-write optimization.
    """,
    
    "do_no_page": """
    Handles page faults for unmapped pages.
    
    Algorithm:
    1. Allocate a new physical page
    2. Map page to faulting virtual address
    3. Page is initially zeroed
    4. If allocation fails, kill process
    
    Creates new anonymous pages on demand.
    """
}

# Validation functions
def is_valid_address(addr):
    """Check if address is valid for the system"""
    return 0 <= addr < HIGH_MEMORY

def is_paging_address(addr):
    """Check if address is in paging memory range"""
    return LOW_MEM <= addr < HIGH_MEMORY

def is_page_aligned(addr):
    """Check if address is page aligned"""
    return (addr & (PAGE_SIZE - 1)) == 0

# Debug and logging
DEBUG_LEVELS = {
    "ERROR": 0,
    "WARN": 1, 
    "INFO": 2,
    "DEBUG": 3,
    "TRACE": 4
}

DEFAULT_DEBUG_LEVEL = "INFO"