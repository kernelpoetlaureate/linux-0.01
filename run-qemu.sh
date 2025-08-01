#!/bin/sh
# Build the kernel and run in QEMU
set -e
make
make floppy.img
qemu-system-i386 -fda floppy.img -boot a -serial stdio
