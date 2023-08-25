#!/usr/bin/env python3
# ArmSim Host (or Armsim SHell, if you prefer)
# (c) 2016-2023, Bob Jones University
import argparse
import ast
import csv
import ctypes
import hashlib
import mmap
import os
import re
import queue
import struct
import sys
import threading
import time

__version__ = "2016-11-18-1300"

try:
    import msvcrt

    class GetchThread(threading.Thread):
        def __init__(self, input_queue, notifier=None):
            super().__init__()
            self._inputq = input_queue
            self._notify = notifier
            self._done = threading.Event()

        def halt(self):
            self._done.set()

        def run(self):
            while not self._done.wait(0.01):
                if msvcrt.kbhit():
                    self._inputq.put(ord(msvcrt.getch()) & 0xff)
                    if self._notify:
                        self._notify()
except ImportError:
    import termios
    import tty
    import select

    class GetchThread(threading.Thread):
        def __init__(self, input_queue, notifier=None):
            super().__init__()
            self._inputq = input_queue
            self._notify = notifier
            self._done = threading.Event()

        def halt(self):
            self._done.set()

        def run(self):
            fd = sys.stdin.fileno()
            attrs = termios.tcgetattr(fd)
            tty.setcbreak(fd)
            try:
                while not self._done.wait(0.1):
                    rds, _, _ = select.select([fd], [], [], 0)
                    if rds:
                        data = os.read(fd, 16)
                        for b in data:
                            b &= 0xff
                            self._inputq.put(13 if b == 10 else b)  # Hack: send '\r' if the user hits '\n'
                        if self._notify:
                            self._notify()
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, attrs)


# Constants
#######################################################################

RGX_MEM_SIZE = re.compile(r"^(?P<size>\d+)(?P<scale>[kmg])b?$")

MEM_SCALE = {
    'k': 1024,
    'm': 1024**2,
    'g': 1024**3,
}

ELF_HEADER = struct.Struct("<4s5B7x2H5I6H")
EH_MAGIC = 0
EH_CLASS = 1
EH_DATA = 2
EH_MACHINE = 7
EH_ENTRY = 9
EH_PHOFF = 10
EH_SHOFF = 11
EH_PHENTSIZE = 14
EH_PHENTNUM = 15
EH_SHENTSIZE = 16
EH_SHENTNUM = 17
EH_SHSTRNDX = 18
ET_EXEC = 2

PROGRAM_HEADER = struct.Struct("<8I")
PH_TYPE = 0
PH_OFFSET = 1
PH_VADDR = 2
PH_FILESZ = 4
PH_MEMSZ = 5
PT_LOAD = 1

SECTION_HEADER = struct.Struct("<6I16x")
SH_NAME = 0
SH_OFFSET = 4
SH_SIZE = 5

# Mode index constants (for register banks)
NIL, USR, FIQ, IRQ, SVC, SYS = -1, 0, 1, 2, 3, 4

MODE_MAP = {
    "usr": (0x10, "usr", USR),   # "usr" mode has mode bits 10000 and requires the "usr" feature
    "svc": (0x13, "svc", SVC),   # "svc" mode has mode bits 10011 and requires the "svc" feature
    "irq": (0x12, "irq", IRQ),   # "irq" mode has mode bits 10010 and requires the "irq" feature
    "fiq": (0x11, "fiq", FIQ),   # "fiq" mode has mode bits 10001 and requires the "fiq" feature
    "sys": (0x1f, "svc", SYS),   # "sys" mode has mode bits 11111 and requires the "svc" feature
}

REG_NAME_MAP = {
    "r0": 0, "r1": 1, "r2": 2, "r3": 3,
    "r4": 4, "r5": 5, "r6": 6, "r7": 7,
    "r8": 8, "r9": 9, "r10": 10, "r11": 11,
    "r12": 12, "r13": 13, "r14": 14, "r15": 15,
    "sp": 13, "lr": 14, "pc": 15,
}

# Keyed by CPSR mode bit values (computed from the master MODE_MAP
MODE_NAMES = { v[0] : k for k, v in MODE_MAP.items() }

# Config flags
AC_NOTHING      = 0X00000000
AC_TRACE_LOG    = 0X00000001
AC_MPU_ON       = 0X00000002
AC_CACHE_ON     = 0X00000004

# Signal enum
AS_HALT = 0
AS_IRQ  = 1
AS_FIQ  = 2

# Poor-man's [thread-compatible] atexit alternative
SHUTDOWN = []
def shutdown():
    for func in SHUTDOWN:
        func()

def panic(msg, *args, **kwargs):
    """Called to abort all activity and die with an error message to stderr.
    
    Useful to handle fatal errors in Python callbacks invoked by C code, since
    otherwise ctypes swallows the Python exception and allows things to continue.
    """
    print("PANIC: " + msg, *args, **kwargs)
    shutdown()
    sys.exit(1)


class ElfFile(object):
    """Simplistic ELF executable file loader for ARM(EL) binaries.
    """
    def __init__(self, filename):
        # Map the file into memory instead of slurping it into an array
        with open(filename, 'rb') as fd:
            self._raw = mmap.mmap(fd.fileno(), 0, access=mmap.ACCESS_READ)
        
        # Parse as a 32-bit ELF header
        fields = ELF_HEADER.unpack_from(self._raw)

        # Simple sanity checks
        assert (fields[EH_MAGIC] == b"\x7fELF"), "{0} is *not* an ELF file!".format(filename)
        assert (fields[EH_CLASS] == 1), "{0} is not a 32-bit ELF file!".format(filename)
        assert (fields[EH_DATA] == 1), "{0} uses big-endian data formatting!".format(filename)
        assert (fields[EH_MACHINE] == 0x28), "{0} is not an ARM binary!".format(filename)
        
        # Carve up section header table
        sh_table_size = fields[EH_SHENTSIZE] * fields[EH_SHENTNUM]
        sh_table_start = fields[EH_SHOFF]
        sh_table_end = sh_table_start + sh_table_size
        sh_table_data = self._raw[sh_table_start:sh_table_end]
        self._sections = [sh for sh in SECTION_HEADER.iter_unpack(sh_table_data)]
        
        # Find the section-name-string-table section and extract string names
        strtab_sh = self._sections[fields[EH_SHSTRNDX]]
        strtab_start = strtab_sh[SH_OFFSET]
        strtab_end = strtab_start + strtab_sh[SH_SIZE]
        strtab_data = self._raw[strtab_start:strtab_end]
        
        self._section_names = []
        for s in self._sections:
            name_start = s[SH_NAME]
            name_end = strtab_data.index(b'\0', name_start)
            self._section_names.append(strtab_data[name_start:name_end].decode('utf-8'))
        
        # Extract entry point
        self._entry = fields[EH_ENTRY]

        # Find all program header entries
        ph_table_size = fields[EH_PHENTSIZE] * fields[EH_PHENTNUM]
        ph_table_start = fields[EH_PHOFF]
        ph_table_end = ph_table_start + ph_table_size
        ph_table_data = self._raw[ph_table_start:ph_table_end]
        self._segments = [ph for ph in PROGRAM_HEADER.iter_unpack(ph_table_data)
                             if ph[PH_TYPE] == PT_LOAD]
    
    @property
    def entry(self):
        return self._entry

    @property
    def segments(self):
        for _, src_off, dst_addr, _, src_size, dst_size, flags, _ in self._segments:
            chunk = self._raw[src_off:src_off + src_size]
            if dst_size > src_size:
                chunk += b'\0'*(dst_size - src_size)
            yield (dst_addr, flags, chunk)

    def get_section(self, name):
        """Return the raw bytes of a named section (or None if there is no such section).
        """
        try:
            index = self._section_names.index(name)
        except ValueError:
            return None
        else:
            sh = self._sections[index]
            start = sh[SH_OFFSET]
            end = start + sh[SH_SIZE]
            return self._raw[start:end]


class ArmsimElfCompatScript:
    """A bundle of name=value pair configuration settings that can be embedded in an ELF file.

    Used to inform the ArmSim system what the expectations of the program are (e.g., starting mode,
    initial register values, etc.)

    If the script includes a command to set a register to "entry", "entry" is replaced by the
    address of the entry-point from the originating ELF file.
    """
    def __init__(self, armsim_section: bytes, elf_entry_point: int = 0):
        self._mode = None
        self._regs = []

        chunks = armsim_section.decode('utf-8').lower().split()
        for c in chunks:
            name, value = c.split('=', 1)
            if name == "mode":
                self._mode = value
            else:
                if value == "entry":
                    value = elf_entry_point
                else:
                    value = int(value, 0)

                info = name.split('_')
                if len(info) == 1:
                    # No mode info; use -1 as the bank selector ("current or n/a mode")
                    reg = REG_NAME_MAP[name]
                    bank = -1
                else:
                    reg = REG_NAME_MAP[info[0]]
                    bank = MODE_MAP[info[1]][2] # Get 3rd element (mode index/enum value) of mode-map tuple for this mode name
                self._regs.append((bank, reg, value))

    def apply(self, ask):
        """Apply a compatibiliy setting script to an already-initialized/reset kernel.
        """
        if self._mode:
            bits, requires, enum = MODE_MAP[self._mode]
            if requires not in ask.info():
                panic("Starting mode {0} requires feature '{1}', which is not supported!".format(self._mode, requires))
            ask.cpsr_set((ask.cpsr_get() & ~0x1f) | bits)
        
        for bank, reg, value in self._regs:
            ask.reg_set(reg, value, bank)


class AskHostServices(ctypes.Structure):
    """Python analog to the ask_host_services_t struct in C.
    
    Contains function pointers (ctypes callbacks) that allows a loaded
    kernel to call host-provided memory load/store functions and host-provided
    message logging functions.
    """
    MEM_LOAD_TYPE = ctypes.CFUNCTYPE(ctypes.c_uint, ctypes.c_uint)
    MEM_STORE_TYPE = ctypes.CFUNCTYPE(None, ctypes.c_uint, ctypes.c_uint)
    LOG_TRACE_TYPE = ctypes.CFUNCTYPE(None, *([ctypes.c_uint]*18))  # 16 GPRS plus 2: step count and CPSR
    LOG_MSG_TYPE = ctypes.CFUNCTYPE(None, ctypes.c_char_p)
    PANIC_TYPE = ctypes.CFUNCTYPE(None, ctypes.c_char_p)
    
    
    _fields_ = [
        ("mem_load",    MEM_LOAD_TYPE),
        ("mem_store",   MEM_STORE_TYPE),
        ("log_trace",   LOG_TRACE_TYPE),
        ("log_msg",     LOG_MSG_TYPE),
        ("panic",       PANIC_TYPE),
    ]


class AskHostStats(ctypes.Structure):
    """Stats counters published by ArmSim kernels.
    """
    _fields_ = [
        ("instructions", ctypes.c_uint),
        ("loads", ctypes.c_uint),
        ("stores", ctypes.c_uint),
        ("load_misses", ctypes.c_uint),
        ("store_misses", ctypes.c_uint)
    ]


class AskMockHost:
    """Fake ArmSim host used for sanity testing mockup simulators.

    Basically just records calls to host API function pointers for later verification.
    """
    def __init__(self):
        self._hs = AskHostServices()
        self._calls = {}
        for aname, atype in AskHostServices._fields_:
            setattr(self._hs, aname, atype(getattr(self, aname)))
            self._calls[aname] = []

    @property
    def host_services(self):
        return self._hs

    def reset(self):
        """Delete all mock call records.
        """
        for call_list in self._calls.values():
            call_list.clear()

    def check(self, call_name, count=1, clear=True):
        """Assert/return a set number of call records for a given host API routine.
        """
        if len(self._calls[call_name]) != count:
            panic("Did not detect expected number/type of calls to '{0}'...".format(call_name))
        calls = self._calls[call_name][:]
        if clear:
            self._calls[call_name].clear()
        return calls if count != 1 else calls[0]

    def mem_load(self, *args):
        self._calls["mem_load"].append(args)
        return 0

    def mem_store(self, *args):
        self._calls["mem_store"].append(args)

    def log_trace(self, *args):
        self._calls["log_trace"].append(args)

    def log_msg(self, *args):
        self._calls["log_msg"].append(args)

    def panic(self, *args):
        self._calls["panic"].append(args)


# No-op MMIO stub functions
###################################

def mmio_nop_load(address):
    return 0


def mmio_nop_store(address, value):
    pass


class ArmSimShell:
    """Class representing the host system that contains an ArmSim kernel.
    
    Provides simulated RAM & peripherals along with logging/tracing support.
    """
    
    MMIO_BASE = 0x80000000
    
    def __init__(self, mem_size, trace_log=None, debug_log=None, checksum=False, show_mode=False):
        """Create an ArmSim host system with <mem_size> bytes of RAM.
        
        If <trace_log> is not None, generate a trace log to that file (STDERR if <trace_log> is '-').
        If <debug_log> is not None, generate a debug log to that file (STDERR if <debug_log> is '-').
        """
        # Ensure sane/legal memory sizes (word-aligned)
        assert (0x1000 <= mem_size < self.MMIO_BASE)
        assert ((mem_size & 0b11) == 0)
        
        self._show_md5 = checksum
        self._show_mode = show_mode
        if trace_log:
            self._tlog = open(trace_log, "wt", encoding="utf-8") if trace_log != '-' else sys.stderr
        else:
            self._tlog = None
        
        if debug_log:
            self._dlog = open(debug_log, "wt", encoding="utf-8") if debug_log != '-' else sys.stderr
        else:
            self._dlog = None
        
        # Allocate a ctypes-array of words that size
        RamType = ctypes.c_uint * (mem_size >> 2)
        self._ramlen = mem_size
        self._ram = RamType()
        
        # Set up host services callbacks
        hs = AskHostServices()
        hs.mem_load = AskHostServices.MEM_LOAD_TYPE(self.mem_load)
        hs.mem_store = AskHostServices.MEM_STORE_TYPE(self.mem_store)
        hs.log_trace = AskHostServices.LOG_TRACE_TYPE(self.log_trace)
        hs.log_msg = AskHostServices.LOG_MSG_TYPE(self.log_msg)
        hs.panic = AskHostServices.PANIC_TYPE(self.panic)
        self._hs = hs
        
        # Create MMIO and heartbeat registries
        self._mmio = {}
        self._beats = []
    
    # Host Services (callbacks)
    #############################
    
    @property
    def host_services(self):
        return self._hs
    
    def mem_load(self, address):
        # Must always be word-aligned
        if (address & 0b11):
            panic("misaligned load @ {0:08x}".format(address))
        
        # Is this an MMIO load?
        if address >= self.MMIO_BASE:
            try:
                return self._mmio[address][0](address)
            except KeyError:
                panic("unimplemented MMIO load from {0:#x}".format(address))
        else:
            # Nope; RAM load; bounds-check and return
            if address >= self._ramlen:
                panic("out-of-RAM load @ {0:08x}".format(address))
            return self._ram[address >> 2]
    
    def mem_store(self, address, value):
        # Must always be word-aligned
        if (address & 0b11):
            panic("misaligned store @ {0:08x}".format(address))
        
        # Is it MMIO?
        if address >= self.MMIO_BASE:
            try:
                self._mmio[address][1](address, value)
            except KeyError:
                panic("unimplemented MMIO store to {0:#x}".format(address))
        else:
            if address >= self._ramlen:
                panic("out-of-RAM store @ {0:08x}".format(address))
            self._ram[address >> 2] = value
    
    def log_trace(self, step, pc, cpsr, *gprs):
        if self._tlog:
            cksum = self.md5() if self._show_md5 else "-"*32
            smode = MODE_NAMES.get(cpsr & 0x1f, "???") if self._show_mode else "---"
            flags = (cpsr >> 28) & 0b1111
            print("""\
{0:06} {1:08x} {2} {3} {4:04b}  0={5:08x} 1={6:08x} 2={7:08x}\n\
        3={8:08x}  4={9:08x}  5={10:08x}  6={11:08x}  7={12:08x}  8={13:08x}\n\
        9={14:08x} 10={15:08x} 11={16:08x} 12={17:08x} 13={18:08x} 14={19:08x}\
""".format(step, pc, cksum, smode, flags, *gprs), file=self._tlog)
            self._tlog.flush()

        for listener in self._beats:
            listener.heartbeat(step)
    
    def log_msg(self, msg):
        if self._dlog:
            print(msg.decode("ascii"), file=self._dlog)
            self._dlog.flush()
    
    def panic(self, msg):
        panic(msg.decode("ascii"))

    # Utilities
    #################################
    def _getbyte(self, address):
        waddr, baddr = address >> 2, address & 0b11
        word = self._ram[waddr]
        return (word >> (baddr << 3)) & 0xff
    
    def _putbyte(self, address, value):
        waddr, baddr = address >> 2, address & 0b11
        word = self._ram[waddr]
        shift = baddr << 3
        word &= ~(0xff << shift) & 0xffffffff
        word |= (value << (baddr << 3)) & 0xffffffff
        self._ram[waddr] = word
    
    # Public (python-facing) utilities
    ###################################

    def register_mmio(self, mmio_offset, on_load=mmio_nop_load, on_store=mmio_nop_store):
        """Register a load/store handler pair for MMIO accesses at MMIO_BASE + <mmio_offset>.

        If either (or both!) <on_load> or <on_store> is not provided, no-op defaults are used.
        """
        self._mmio[self.MMIO_BASE + mmio_offset] = (on_load, on_store)

    def register_heartbeat(self, listener):
        """Register a <listener> object with a heartbeat(cycles) method for heartbeat notifications.

        When a simulator is running with tracing enabled, all heartbeat listeners will be notified
        with the current cycle count on each tracing callback.
        """
        self._beats.append(listener)
    
    def flush(self):
        if self._tlog:
            self._tlog.flush()
        if self._dlog:
            self._dlog.flush()

    
    def md5(self):
        """Return the MD5 checksum of all RAM as a hex string.
        """
        hash = hashlib.md5()
        if sys.byteorder == "little":
            # We simulate little-endian ARM, so the data is already in correct order--just hash it as-is (FAST)
            hash.update(self._ram)
        else:
            # Ugh--what kind of crazy machine are you using?  We have to do it backwards!
            for i in range(self._ramlen):
                hash.update(bytes((self._getbyte(i),)))     # EEEEEEEEEEEK, slow.....
        return hash.hexdigest()
    
    def load_elf(self, obj: ElfFile):
        for addr, _, blob in obj.segments:
            for i, b in enumerate(blob):
                self._putbyte(addr + i, b)
    
    def hexdump(self, start, length):
        ascii = []
        for i, addr in enumerate(range(start, start + length)):
            if not ascii:
                print("{0:08x}  ".format(i), end="")
            b = self._getbyte(addr)
            ascii.append(bytes((b,)))
            if (i + 1) & 0xf:
                term = " "
            else:
                adisp = ''.join(a if len(str(a)) == 1 else '.' for a in ascii)
                term = "  {0}\n".format(adisp)
                ascii = []
            print("{0:02x}".format(b), end=term)
        if i & 0xf:
            print("   " * (15 - (i & 0xf)), end=" ")
            print(''.join(a if a.isprintable() else '.' for a in ascii))
        
    def dump_ram_location(self):
        print("ProTip: RAM @ {0:#x}".format(ctypes.addressof(self._ram)))

def input_playback(stream):
    """Parse a text input stream to yield a sequence of (timestamp: int, data: bytes) tuples.
    """
    pts = 0
    for line in stream:
        line = line.rstrip('\n')
        if line:    # only non-empty lines
            if line[0].isspace():
                ts = pts + 1
                dstr = line.lstrip()
            else:
                ts, dstr = line.split(None, maxsplit=1)
                ts = int(ts, 0)
            if ts <= pts:
                raise ValueError("cannot run the clock backwards!")
            data = ast.literal_eval('"{0}"'.format(dstr)).encode('ascii')
            yield ts, data
            pts = ts


class ArmSimConsole:
    """Toy serial console device implementation for and ArmSim system.

    output: always sent to a Python file object (default: sys.stdout)
    input: can be interactive (read from console using getch()) or
            recorded ("played back" from a formatted text stream)

    "Playback" format:
    [CYCLE_COUNT] CHARS

    * CYCLE_COUNT is an optional integer telling when in a program's execution
        this input becomes available (which may trigger a simulated interrupt)
    * CHARS is a string of ASCII chars (interpreted using Python's escape rules)
    * they must be separated by whitespace
    * if CYCLE_COUNT is ommitted, the line must begin with whitespace
        (and an implied cycle count of <previous + 1> is assumed, or 0 if there
        is no previous entry)
    """

    # MMIO offsets for accessing serial console
    WRITE_PORT_OFFSET = 0
    READ_PORT_OFFSET = 4

    def __init__(self, source=None, sink=sys.stdout, notifier=None):
        """Initialize a console object.

        source: if None (the default), use getch() to fetch raw input from the [real] console
                otherwise, treat the input as a file stream and parse it for playback
        sink: always a Python file-like object we write output to
        notifier: arg-less callable used to notify someone that we have new input
                    (must be a thread-safe notification, since it may be called from
                    a background thread)
        """
        self._notify = notifier
        self._sink = sink

        # Not attached to an ArmSim system host yet
        self._host = None

        # Input flows through this...
        self._inputq = queue.Queue()

        # ...but what feeds it?
        if source is None:
            # The real console
            self._playback = False

            self._worker = GetchThread(self._inputq, self._notify)
            self._worker.start()
        else:
            # A playback file
            self._playback = True
            self._playsrc = input_playback(source)
            self._playpair = next(self._playsrc, None)

    def close(self):
        if not self._playback:
            self._worker.halt()

    def heartbeat(self, cycles):
        """Callback by which the host can notify us that a given number of cycles has been reached.

        (The callback will happen only if tracing is enabled in the underlying simulation kernel.)
        """
        if self._playback:
            send_irq = False
            while self._playpair and (self._playpair[0] <= cycles):
                for byte in self._playpair[1]:
                    self._inputq.put(byte)
                    send_irq = True
                self._playpair = next(self._playsrc, None)

            if send_irq and self._notify:
                self._notify()

    def attach(self, host: ArmSimShell):
        """Attach this console to a given ArmSimShell instance.

        Registers itself for MMIO and triggering input interrupts.
        """
        self._host = host
        host.register_mmio(self.READ_PORT_OFFSET, on_load=self._mmio_on_load)
        host.register_mmio(self.WRITE_PORT_OFFSET, on_store=self._mmio_on_store)
        host.register_heartbeat(self)

    def _mmio_on_load(self, address):
        """Read a pending byte from the console (return 0 if no such byte available).
        """
        try:
            return self._inputq.get(False)
        except queue.Empty:
            return 0

    def _mmio_on_store(self, address, value):
        """Push a character into the output stream.
        """
        c = chr((value & 0xff) if value != 13 else 10)
        self._sink.write(c)
        self._sink.flush()


class ArmSimKernel:
    """Wrapper/facade class representing a loaded ArmSim kernel implementation.
    
    Provides methods to handle all interactions with the kernel.
    """
    def __init__(self, loaded_library):
        self._dll = loaded_library
        
        # ask_info() -> char ** (NULL terminated list of NUL-terminated C strings)
        self._dll.ask_info.restype = ctypes.POINTER(ctypes.c_char_p)
        self._dll.ask_info.argtypes = ()
        
        # ask_init(struct ask_host_services_t *host) -> void
        self._dll.ask_init.restype = None
        self._dll.ask_init.argtypes = (ctypes.POINTER(AskHostServices),)
        
        # ask_stats_report(struct ask_stats *stats) -> void
        self._dll.ask_stats_report.restype = None
        self._dll.ask_stats_report.argtypes = (ctypes.POINTER(AskHostStats),)
        
        # ask_reg_get(enum mode, int index) -> uint
        self._dll.ask_reg_get.restype = ctypes.c_uint
        self._dll.ask_reg_get.argtypes = (ctypes.c_int, ctypes.c_int)
        
        # ask_reg_set(enum mode, int index, uint value) -> void
        self._dll.ask_reg_set.restype = None
        self._dll.ask_reg_set.argtypes = (ctypes.c_int, ctypes.c_int, ctypes.c_uint)
        
        # ask_cpsr_get(void) -> uint
        self._dll.ask_cpsr_get.restype = ctypes.c_uint
        self._dll.ask_cpsr_get.argtypes = ()
        
        # ask_cpsr_set(uint value) -> void
        self._dll.ask_cpsr_set.restype = None
        self._dll.ask_cpsr_set.argtypes = (ctypes.c_uint,)
        
        # ask_config_get(void) -> bitflags
        self._dll.ask_config_get.restype = ctypes.c_uint
        self._dll.ask_config_get.argtypes = ()
        
        # ask_config_set(enum) -> void
        self._dll.ask_config_set.restype = None
        self._dll.ask_config_set.argtypes = (ctypes.c_uint,)
        
        # ask_cpu_running() -> int
        self._dll.ask_cpu_running.restype = ctypes.c_int
        self._dll.ask_cpu_running.argtypes = ()
        
        # ask_cpu_run(int cycles) -> int
        self._dll.ask_cpu_run.restype = ctypes.c_int
        self._dll.ask_cpu_run.argtypes = (ctypes.c_int,)
        
        # ask_cpu_signal(enum signal) -> void
        self._dll.ask_cpu_signal.restype = None
        self._dll.ask_cpu_signal.argtypes = (ctypes.c_int,)
    
    def info(self):
        """Calls ask_info() from the loaded kernel library.
        
        Returns a dictionary of {"name": "value"} parsed from the list of "name=value" strings.
        """
        info = {}
        cstrings = self._dll.ask_info()
        if cstrings:
            i = 0
            while cstrings[i] is not None:
                fields = cstrings[i].decode('ascii').split('=', 1)
                if len(fields) == 2:
                    info[fields[0]] = fields[1]
                else:
                    info[fields[0]] = True
                i += 1
        return info
    
    def init(self, host_services):
        """Calls ask_init(...), passing in a structure of callbacks.
        """
        return self._dll.ask_init(host_services)
    
    def stats(self) -> AskHostStats:
        """Calls ask_stats_report(...) and returns the populated struct.
        """
        stats = AskHostStats()
        self._dll.ask_stats_report(stats)
        return stats
    
    def config_get(self):
        """Pass-through to ask_config_get()...
        """
        return self._dll.ask_config_get()
    
    def config_set(self, config_flags):
        """Pass-through to ask_config_set(...)...
        """
        self._dll.ask_config_set(config_flags)
    
    def reg_get(self, index, bank=NIL):
        """Calls ask_reg_get(bank, index) and returns the result.
        """
        return self._dll.ask_reg_get(bank, index)
    
    def reg_set(self, index, value, bank=NIL):
        """Calls ask_reg_get(bank, index, value).
        """
        self._dll.ask_reg_set(bank, index, value)
    
    def cpsr_get(self):
        """Pass-through to ask_cpsr_get()...
        """
        return self._dll.ask_cpsr_get()
    
    def cpsr_set(self, value):
        """Pass-through to ask_cpsr_set(value)...
        """
        self._dll.ask_cpsr_set(value)
    
    def is_running(self):
        """Calls ask_cpu_running() and returns the result.
        """
        return self._dll.ask_cpu_running()
    
    def run(self, cycles):
        """Pass-through to ask_cpu_run(cycles)...
        """
        return self._dll.ask_cpu_run(cycles)
    
    def signal(self, signal):
        """Pass-through to ask_cpu_signal(signal)...
        """
        self._dll.ask_cpu_signal(signal)

    def signal_irq(self):
        """Convenience short-cut for ask_cpu_signal(as_irq).
        """
        self.signal(AS_IRQ)


def mockup_tests(ask):
    """Perform a round of mockup testing on a given kernel (starting with init testing).

    A properly-implemented mockup should withstand any number of these tests, one after the other.
    """
    import random

    mock = AskMockHost()

    # Validate ask_init()
    ask.init(mock.host_services)
    if ask.config_get() != 0:
        panic("Config flags not zero'd by ask_init...")
    for i in range(16):
        if ask.reg_get(i) != 0:
            panic("Register {0} not zero'd by ask_init...".format(i))
    if ask.stats().instructions != 0:
        panic("Instruction count not reset to 0 by CPU initialization...")
    if mock.check("log_msg")[0] != b"CPU initialized":
        panic("Stipulated 'CPU initialized' log message not detected")
    mock.reset()

    # Does config setting work?
    ask.config_set(AC_TRACE_LOG)
    if not (ask.config_get() & AC_TRACE_LOG):
        panic("Unable to verify that ask_config_set/ask_config_set work...")

    # How about register setting?
    regvalues = [random.randint(0, 2**32-1) for i in range(16)]
    for i, val in enumerate(regvalues):
        ask.reg_set(i, val)
    for i, val in enumerate(regvalues):
        if ask.reg_get(i) != val:
            panic("Unable to verify that ask_reg_set/ask_reg_get work...")

    # How about step counts?
    ask.run(1)
    if ask.stats().instructions != 1:
        panic("Unable to verify that ask_cpu_run can increment instruction count by 1...")
    steps = random.randint(3, 100)
    ask.run(steps)
    if ask.stats().instructions != (steps + 1):
        panic("Unable to verify that ask_cpu_run can increment instruction count by more than 1...")


def scaled_size(text):
    M = RGX_MEM_SIZE.match(text.strip().lower())
    if not M:
        raise ValueError(text)
    else:
        size, scale = M.group("size"), M.group("scale")
        if scale not in MEM_SCALE:
            raise ValueError(scale)
        else:
            return int(size) * MEM_SCALE[scale]


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("-c", "--checksum", dest="checksum", action="store_true", default=False,
                    help="Compute and display the RAM checksum with every trace log entry (SLOW).")
    ap.add_argument("-d", "--debug-log", dest="debug_log", metavar="FILE", default=None,
                    help="Save debug log messages to FILE (or STDERR if FILE is '-')")
    ap.add_argument("-i", "--console-input", dest="input_file", metavar="FILE", default=None,
                    help="Take console input from playback FILE instead of host TTY.")
    ap.add_argument("-m", "--mode", dest="mode", action="store_true", default=False,
                    help="Show the current processor mode name on every trace log entry.")
    ap.add_argument("-p", "--pause", dest="pause", action="store_true", default=False,
                    help="Pause (after printing PID) to allow debugger attachment.")
    ap.add_argument("-r", "--ram", dest="mem_size", metavar="SIZE", type=scaled_size, default="32k",
                    help="Size of memory in bytes (k/m/g valid as scale suffixen)")
    ap.add_argument("-t", "--trace-log", dest="trace_log", metavar="FILE", default=None,
                    help="Save trace log messages to FILE (or STDERR if FILE is '-')")
    ap.add_argument("-k", "--cache", action="store_true", default=False,
                    help="Enable memory cache (if implemented by KERNEL)")
    ap.add_argument("-s", "--stats-log", dest="stats_log", metavar="CSV_FILE", default=None,
                    help="Append performance stats to CSV_FILE")
    ap.add_argument("-f", "--fiq-interval", dest="fiq_int", metavar="CYCLES", default=0, type=int,
                    help="Cycles (i.e., instructions) between triggering FIQ interrupts (default: no FIQ).")
    ap.add_argument("kernel", metavar="KERNEL_BIN",
                    help="Name of/path to loadable ArmSim kernel library.")
    ap.add_argument("module", metavar="ARM_ELF_BIN", nargs="?",
                    help="Path to ARM ELF file to load into simulated RAM "
                         "(if none specified, nothing is loaded/executed, but mockup tests may be performed).")

    print("ArmSim Host, Version:", __version__)
    args = ap.parse_args(argv)
    if args.mem_size < 32*1024:
        print("Memory size must be at least 32KB!")
        exit(1)

    # Load kernel and create RAM array
    ask = ArmSimKernel(ctypes.cdll.LoadLibrary(args.kernel))
    shell = ArmSimShell(mem_size=args.mem_size,
                        trace_log=args.trace_log,
                        debug_log=args.debug_log,
                        checksum=args.checksum,
                        show_mode=args.mode)

    # If so asked, pause and wait for input at this point
    if args.pause:
        # And dump out useful debugging tips (our PID and the address of the RAM array)
        shell.dump_ram_location()
        input("press ENTER to go continue (pid={0})".format(os.getpid()))

    # Check core metadata
    info = ask.info()
    try:
        if info["api"] != "1.0":
            print("Unsupported API version ({0}); aborting...".format(info["api"]))
            exit(1)
    except KeyError:
        print("No API version reported; aborting...")
        exit(1)
    try:
        print("Author({0}): {1}".format(args.kernel, info["author"]))
    except KeyError:
        print("No author reported; aborting...")
        exit(1)

    # Validate args/features; warn about possibly bad stuff
    if args.cache and ("cache" not in info):
        print("WARNING: --cache specified, but {0} does not implement 'cache'...".format(args.kernel))
    if args.fiq_int and ("fiq" not in info):
        print("WARNING: --fiq-interval specified, but {0} does not implement 'fiq'...".format(args.kernel))
    if ("usr" in info) and (args.mem_size < 64*1024):
        print("WARNING: {0} supports 'usr' mode; you should probably have at least 64KB of RAM...".format(args.kernel))

    # If there's something to load/run, do it...
    if args.module:
        elf = ElfFile(args.module)
        shell.load_elf(elf)
        print("MD5({0}): {1}".format(args.module, shell.md5()))

        console = ArmSimConsole(source=open(args.input_file, "rt", encoding="ascii") if args.input_file else None,
                                notifier=ask.signal_irq if 'irq' in info else None)
        console.attach(shell)
        SHUTDOWN.append(console.close)

        # Initialize the CPU
        ask.init(shell.host_services)

        # Set config flags (if any)
        cflags = AC_NOTHING
        if args.trace_log or args.input_file:
            # In order for input file playback to be synchronized with clock cycles inside
            # the simulator, we MUST enable tracing (even if we don't have a trace log getting saved)
            cflags |= AC_TRACE_LOG
        if args.cache:
            cflags |= AC_CACHE_ON
        ask.config_set(cflags)

        # Pre-configure processor based on embedded ".armsim" section in ELF file (if it exists)
        elf_compat = elf.get_section(".armsim")
        if elf_compat:
            script = ArmsimElfCompatScript(elf_compat, elf.entry)
            script.apply(ask)

        print()
        print("-" * 60)

        # Run until done; keep timing stats...
        _fiq_int = args.fiq_int
        start = time.perf_counter()
        while ask.run(_fiq_int) == _fiq_int:
            ask.signal(AS_FIQ)
        stop = time.perf_counter()

        # Make sure log output gets flushed/saved
        shell.flush()
        print()
        print("-"*60)
        print()

        # Print performance stats
        stats = ask.stats()
        span = stop - start
        try:
            ips = round(stats.instructions / span, 1)
            print("{0:,} instructions in {1:.3} seconds ({2:,} IPS)".format(stats.instructions, span, ips))
        except ZeroDivisionError:
            print("{0:,} instructions in <mumble-mumble> seconds (<mumble-mumble> IPS)".format(stats.instructions))

        # If so requested, log raw performance stats
        if args.stats_log:
            with open(args.stats_log, "at", encoding="utf8", newline="") as fd:
                writer = csv.writer(fd)
                writer.writerow([
                    info["author"],
                    args.module,
                    span,
                    stats.instructions,
                    stats.loads,
                    stats.load_misses,
                    stats.stores,
                    stats.store_misses])

        # If caching was enabled, print cache stats
        if args.cache:
            print("Loads: {0:,} of which {1:,} missed (miss rate: {2:.2}%)".format(
                stats.loads, stats.load_misses, (stats.load_misses / stats.loads) * 100))
            print("Stores: {0:,} of which {1:,} missed (miss rate: {2:.2}%)".format(
                stats.stores, stats.store_misses, (stats.store_misses / stats.stores) * 100))
        else:
            # Otherwise, just show load and store counts
            print("Loads: {0:,}".format(stats.loads))
            print("Stores: {0:,}".format(stats.stores))

    elif "mockup" in info:
        print("Attribute 'mockup' detected; running mockup sanity checks...")

        # Run the basic test suite many times (at least 2 to verify proper init, and more
        # to hopefully catch any silly huge-resource-allocation bugs...)
        for i in range(100):
            mockup_tests(ask)

        print("ALL SANITY CHECKS PASSED--WELL DONE")


if __name__ == "__main__":
    main(sys.argv[1:])
    shutdown()

