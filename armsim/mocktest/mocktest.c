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
    void            (*stats_report)(struct ask_stats *);
    word            (*reg_get)(ask_mode_t bank, int index);
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

struct libask {
    void *_handle;
    struct libask_api api;
};

// dynamically load kernel shared object and resolve names
bool load_kernel(char *soname, struct libask *);

// free/release a loaded kernel shared object
void unload_kernel(struct libask *);

// use search data in api->info() for string `prefix`, optionally extracting the rest of the string into `*suffix`
bool kernel_has(struct libask *, char *prefix, char **suffix);

// run one round of mockup tests (return 0 on success, non-0 on failure)
int mockup_tests(struct libask_api *api);

int main(int argc, char **argv) {
    int ret = EXIT_FAILURE;
    struct libask ask = { 0 };

    if (argc != 2) {
        printf("usage: %s LIBASK_SO\n", argv[0]);
        goto cleanup;
    }
    if (!load_kernel(argv[1], &ask)) goto cleanup;

    char *author = NULL;
    if (kernel_has(&ask, "author=", &author)) {
        printf("Hello, %s!\n", author);
    } else {
        printf("Naughty author, not including an 'author=...' tag in ask_info()'s output!\n");
    }

    if (kernel_has(&ask, "mockup", NULL)) {
        printf("Running 'mockup' tests on '%s'...\n", argv[1]);
        for (int i = 0; i < 100; ++i) {
            if (mockup_tests(&ask.api)) {
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
    unload_kernel(&ask);
    return ret;
}

void unload_kernel(struct libask *ask) {
    if (ask && ask->_handle) dlclose(ask->_handle);
    memset(ask, 0, sizeof *ask);
}

bool load_kernel(char *soname, struct libask *ask) {
    bool    ret = false;
    void    *handle = NULL;

    if ((handle = dlopen(soname, RTLD_NOW)) == NULL) {
        printf("error: unable to load '%s' (%s)\n", soname, dlerror());
        goto cleanup;
    }

    memset(ask, 0, sizeof *ask);
#define X(stem)\
    if ((ask->api.stem = dlsym(handle, "ask_" #stem)) == NULL) {\
        printf("error: unable to load function '" #stem "' (%s)\n", dlerror());\
        goto cleanup;\
    }
    LIBASK_API_NAMES
#undef X
    ask->_handle = handle;
    handle = NULL;
    ret = true;
cleanup:
    if (handle) dlclose(handle);
    return ret;
}

bool kernel_has(struct libask *ask, char *prefix, char **suffix) {
    size_t prefix_len = strlen(prefix);
    bool has_suffix = prefix[prefix_len - 1] == '=';
    if (has_suffix && !suffix) return false;

    for (char **ip = ask->api.info(); *ip; ++ip) {
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
   
    // set up mock hosting environment 
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

    // test initial state after "init" function call
    api->init(&host);
    if (api->config_get() != 0) MOCKFAIL("Config flags not zero'd by ask_init...");
    for (int i = 0; i < 16; ++i) {
        if (api->reg_get(am_nil, 0) != 0) MOCKFAILF("Register %d not zero'd by ask_init...", i);
    }
    api->stats_report(&stats);
    if (stats.instructions != 0) MOCKFAIL("Instruction count not reset to 0 by CPU initialization...");
    fflush(mock_log);
    if (strcmp(logbuf, "CPU initialized\n") != 0) MOCKFAIL("Stipulated 'CPU initialized' log message not detected");

    // test config setting/getting
    api->config_set(ac_trace_log);
    if (!(api->config_get() & ac_trace_log)) MOCKFAIL("Unable to verify that ask_config_set/ask_config_get work...");

    // test register setting/getting (with random values to inhibit cheating/accidental passes)
    unsigned int seed = (unsigned int)time(NULL);
    srandom(seed);
    word reg_vals[16] = { 0 };
    for (int i = 0; i < 16; ++i) {
        reg_vals[i] = (word)random(); 
        api->reg_set(am_nil, i, reg_vals[i]);
    }
    for (int i = 0; i < 16; ++i) {
        if (api->reg_get(am_nil, i) != reg_vals[i]) MOCKFAIL("Unable to verify that ask_reg_set/ask_reg_get work...");
    }

    // test instruction step counts
    api->cpu_run(1);
    api->stats_report(&stats);
    if (stats.instructions != 1) MOCKFAIL("Unable to verify that ask_cpu_run can increment instruction count by 1...");
    int steps = (int)random() % 97 + 3;
    api->cpu_run(steps);
    api->stats_report(&stats);
    if (stats.instructions != (steps + 1)) MOCKFAIL("Unable to verify that ask_cpu_run can increment instruction count by more than 1...");

    ret = 0;
cleanup:
    if (mock_log) { fclose(mock_log); mock_log = NULL; }
    free(logbuf);
    return ret;
}

