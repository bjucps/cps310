#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
#include <dlfcn.h>
#include <time.h>

#include "askapi.h"

struct libask_api {
    char          **(*info)(void);
    void            (*disasm)(word address, word instruction, char *buff, size_t size);
    void            (*init)(const struct ask_host_services *);
    void            (*config_set)(ask_config_t flags);
    ask_config_t    (*config_get)(void);
    void	        (*stats_report)(struct ask_stats *);
    word	        (*reg_get)(ask_mode_t bank, int index);
    void            (*reg_set)(ask_mode_t bank, int index, word value);
    word            (*cpsr_get)(void);
    void            (*cpsr_set)(word value);
    int             (*cpu_running)(void);
    void            (*cpu_signal)(ask_signal_t signal);
    int             (*cpu_run)(int cycles);
};

#define LIBASK_API_NAMES \
    X(info)\
    X(disasm)\
    X(init)\
    X(config_set)\
    X(config_get)\
    X(stats_report)\
    X(reg_set)\
    X(reg_get)\
    X(cpsr_set)\
    X(cpsr_get)\
    X(cpu_running)\
    X(cpu_signal)\
    X(cpu_run)


// use search data in api->info() for string `prefix`, optionally extracting the rest of the string into `*suffix`
bool kernel_has(struct libask_api *api, char *prefix, char **suffix);

// run one round of mockup tests (return 0 on success, non-0 on failure)
int mockup_tests(struct libask_api *api);

int main(int argc, char **argv) {
    int ret = EXIT_FAILURE;

    void *libask_so = NULL;
    struct libask_api libask;

    if (argc != 2) {
        printf("usage: %s LIBASK_SO\n", argv[0]);
        goto cleanup;
    }

    if ((libask_so = dlopen(argv[1], RTLD_NOW)) == NULL) {
        printf("error: unable to load '%s' (%s)\n", argv[1], dlerror());
        goto cleanup;
    }

    memset(&libask, 0, sizeof libask);
#define X(stem)\
    if ((libask.stem = dlsym(libask_so, "ask_" #stem)) == NULL) {\
        printf("error: unable to load function '" #stem "' (%s)\n", dlerror());\
        goto cleanup;\
    }
    LIBASK_API_NAMES
#undef X

    if (kernel_has(&libask, "mockup", NULL)) {
        printf("Running 'mockup' tests on '%s'...\n", argv[1]);
        for (int i = 0; i < 100; ++i) {
            if (mockup_tests(&libask)) {
                printf("error: mockup tests failed at iteration %d\n", i);
                goto cleanup;
            }
        }
        printf("PASSED\n");
    } else {
        printf("'%s' is not a 'mockup' kernel; nothing to do...\n", argv[1]);
    }

    ret = EXIT_SUCCESS;
cleanup:
    memset(&libask, 0, sizeof libask);
    if (libask_so) dlclose(libask_so);
    return ret;
}

bool kernel_has(struct libask_api *api, char *prefix, char **suffix) {
	size_t prefix_len = strlen(prefix);
	bool has_suffix = prefix[prefix_len - 1] == '=';
	if (has_suffix && !suffix) return false;

	for (char **ip = api->info(); *ip; ++ip) {
		if (strncmp(*ip, prefix, prefix_len) == 0) {
			if (has_suffix) {
				*suffix = *ip + prefix_len;
				return true;
			} else if ((*ip)[prefix_len] == '\0') {
				return true;
			}
		}
	}	
	return false;
}

static FILE *mock_log = NULL;

static word mock_mem_load(word address) {
    return 0u;
}

static void mock_mem_store(word address, word value) {
    // NOP
}

static void mock_log_trace(unsigned step, word pc, word cpsr, word r0, word r1, word r2, word r3,
    word r4, word r5, word r6, word r7, word r8, word r9,
    word r10, word r11, word r12, word sp, word lr
) {
    // NOP
}

static void mock_log_msg(const char *msg) {
    fprintf(mock_log, "%s\n", msg);
}

static void mock_panic(const char *msg) {
    printf("panic: %s\n", msg);
    exit(1);
}

#define MOCKFAIL(msg) do { printf("mock: %s\n", msg); goto cleanup; } while (0);
#define MOCKFAILF(fmt, ...) do { printf("mock: " fmt "\n", __VA_ARGS__); goto cleanup; } while (0);

int mockup_tests(struct libask_api *api) {
    int ret = 1;
    
    unsigned int seed = (unsigned int)time(NULL);
    srandom(seed);

    ask_host_services_t host = {
        .mem_load = mock_mem_load,
        .mem_store = mock_mem_store,
        .log_trace = mock_log_trace,
        .log_msg = mock_log_msg,
        .panic = mock_panic,
    };
    ask_stat_t stats = { 0 };

    char *logbuf = NULL;
    size_t loglen = 0u;
    mock_log = open_memstream(&logbuf, &loglen);
    if (!mock_log) MOCKFAIL("unable to allocate memory stream for mock-log");

    api->init(&host);

    if (api->config_get() != 0) MOCKFAIL("Config flags not zero'd by ask_init...");
    for (int i = 0; i < 16; ++i) {
        if (api->reg_get(am_nil, 0) != 0) MOCKFAILF("Register %d not zero'd by ask_init...", i);
    }
    api->stats_report(&stats);
    if (stats.instructions != 0) MOCKFAIL("Instruction count not reset to 0 by CPU initialization...");

    fflush(mock_log);
    if (strcmp(logbuf, "CPU initialized\n") != 0) MOCKFAIL("Stipulated 'CPU initialized' log message not detected");

    ret = 0;
cleanup:
    if (mock_log) { fclose(mock_log); mock_log = NULL; }
    free(logbuf);
    return ret;
}

