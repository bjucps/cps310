/* ArmSim Kernel API: Defines interface between ArmSim kernels (CPUs) and hosts (systems).
 (c) 2016-2023, Bob Jones University */
#ifndef ARMSIM_KERNEL_API
#define ARMSIM_KERNEL_API

#include <stdint.h>

/* The ASKAPI functions must be exported with "C" linkage, even if implemented in C++ */
#ifdef __cplusplus
extern "C" {
#endif

/* Fundamental unit typedefs */
typedef uint8_t		byte;
typedef int8_t		sbyte;
typedef uint16_t	hword;
typedef int16_t		shword;
typedef uint32_t	word;
typedef int32_t		sword;

/* Which mode/register bank are we talking about? */
typedef enum ask_mode {
	am_nil = -1,		/* The invalid mode (or, if you are asking for a register from a given bank, the current mode) */
	am_usr = 0,		/* USR mode register bank) */
	am_fiq,			/* FIQ mode/bank (triggered by FIQ signal to CPU) */
	am_irq,			/* IRQ mode/bank (triggered by IRQ signal to CPU) */
	am_svc,			/* SVC mode/bank (triggered by SWI) */
	am_sys,			/* SYS mode (uses the same bank as USR) */
	am_max
} ask_mode_t;

/* What sort of signal are we giving the CPU?
  (used to control concurrent simulation on a background thread)
*/
typedef enum ask_signal {
	as_halt,
	as_irq,
	as_fiq
} ask_signal_t;

/* Configuration bit flags */
typedef enum ask_config {
	ac_nothing		= 0x00000000,	/* nothing special enabled (default) */
	ac_trace_log		= 0x00000001,	/* required; if set, the kernel MUST emit a trace-log call after EVERY instruction */
	ac_mpu_on		= 0x00000002,	/* optional (with feature "mpu"); if set, the kernel must enforce memory protections when in "usr" mode */
	ac_cache_on		= 0x00000004,	/* optional (with feature "cache"); if cleared, the kernel must bypass its caching support and directly call host-load/store for all memory ops */
} ask_config_t;

/* Structure of function pointers: services provided by the hosting system */
typedef struct ask_host_services {
	/* Load a word from memory (or MMIO) <address>, which must be word-aligned */
	word (*mem_load)(word address);

	/* Store <value> to memory (or MMIO) <address>, which must be word-aligned */
	void (*mem_store)(word address, word value);
	
	/* Signal the host that <code> was just fetched from <address> and executed (yes, it takes a lot of parameters...) */
	void (*log_trace)(unsigned step, word pc, word cpsr, word r0, word r1, word r2, word r3,
						word r4, word r5, word r6, word r7, word r8, word r9,
						word r10, word r11, word r12, word sp, word lr);

	/* Log a debugging/informational message to the debug log */
	void (*log_msg)(const char *msg);

	/* Log a fatal error message and terminate simulation */
	void (*panic)(const char *msg);
} ask_host_services_t;

/* Structure of event counters maintained/published by the kernel */
typedef struct ask_stats {
	unsigned int instructions;		/* Number of instructions executed so far */
	unsigned int loads;			/* Total number of memory loads (including instruction fetches) */
	unsigned int stores;			/* Total number of memory stores */
	unsigned int load_misses;		/* Total number of loads that were cache misses (for cache-implementing kernels) */
	unsigned int store_misses;		/* Total number of stores that were cache misses (ditto) */
	/* more TBD */
} ask_stat_t;

/* Kernel API (what the host can call in your library */
/*----------------------------------------------------*/

/* Return a pointer to a NULL-terminated list of NUL-terminated C-strings describing the kernel's features */
char**	ask_info(void);

/* Disassemble a given 32-bit ARM <instruction> into the string buffer provided;
   <address> is the address where this instruction is found in memory; it is
   technically optional but required to accurately calculate branch targets.
   (To be called only if ask_info includes "disasm" in the feature list.) */
void	ask_disasm(word address, word instruction, char *buff, size_t size);

/* Reset/initialize the simulated CPU, binding it to the environment provided by the host services functions */
void	ask_init(const struct ask_host_services *);

/* Set/get the current configuration flags */
void		ask_config_set(ask_config_t flags);
ask_config_t	ask_config_get(void);

/* Populate a stats-counter struct with the current CPU performance statistics */
void	ask_stats_report(struct ask_stats *);

/* Get/set GPR values for a given mode's bank (am_nil == current mode's bank) */
word	ask_reg_get(ask_mode_t bank, int index);
void	ask_reg_set(ask_mode_t bank, int index, word value);

/* Get/set CPSR value (setting can cause mode changes!) */
word	ask_cpsr_get(void);
void	ask_cpsr_set(word value);

/* Query: is the simulated CPU running at the moment (e.g., on a background thread)? */
int	ask_cpu_running(void);

/* Signal a [running] CPU of an external event (forced halt, IRQ, or FIQ) */
void	ask_cpu_signal(ask_signal_t signal);

/* Start the CPU running (for <cycles> instructions, or until SWI 0 if <cycles> == 0) */
int	ask_cpu_run(int cycles);

#ifdef __cplusplus
}
#endif

#endif
