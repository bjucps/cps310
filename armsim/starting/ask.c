/* TODO: provide your name and project information here */
#include <stddef.h>

/* ArmSim Kernel/Shell Interface definition */
#include "askapi.h"

char **ask_info(void) {
    // TODO
    return NULL;
}

void ask_init(const struct ask_host_services *host) {
    // TODO
}

void ask_config_set(ask_config_t flags) {
    // TODO
}

ask_config_t ask_config_get(void) {
    // TODO
    return 0;
}

void ask_stats_report(struct ask_stats *stats) {
    // TODO
}

word ask_reg_get(ask_mode_t bank, int index) {
    // TODO
    return 0;
}

void ask_reg_set(ask_mode_t bank, int index, word value) {
    // TODO
}

word ask_cpsr_get(void) {
    // TODO
    return 0;
}

void ask_cpsr_set(word value) {
    // TODO
}

int	ask_cpu_running(void) {
    // TODO
    return 0;
}

void ask_cpu_signal(ask_signal_t signal) {
    // TODO
}

int	ask_cpu_run(int cycles) {
    // TODO
}

 
