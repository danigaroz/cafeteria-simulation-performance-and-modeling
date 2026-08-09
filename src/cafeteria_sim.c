/* cafeteria_sim.c
 * Cafeteria simulator with C waiters and S chairs.
 * Two customer classes: CAFE and DESAYUNO.
 *
 * Performance Modeling of Computer Systems and Networks
 * Universita' degli Studi di Roma Tor Vergata
 */
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <float.h>
#include "rngs.h"

/* Default values; can be overridden with -DC=..., -DS=..., -DMEAN_IARRIVAL=... at compile time */
#ifndef C
#define C 2
#endif
#ifndef S
#define S 4
#endif
#ifndef MEAN_IARRIVAL
#define MEAN_IARRIVAL 3.0
#endif

#define LAST      10000L
#define INFTY     (DBL_MAX / 2.0)
#define SNAPSHOT_INTERVAL 60.0
#define WARMUP_TIME 3600.0    /* minutes (60 h) - from Welch's method */
#define CSV_FILENAME "transient.csv"

#define CAFE      0
#define DESAYUNO  1

/* means in minutes */
static const double mean_iarrival        = MEAN_IARRIVAL;
static const double mean_attention[2]    = {1.5, 4.0};
static const double mean_consumption[2]  = {5.0, 12.0};
static const double p_cafe               = 0.7;

/* chair states */
#define EMPTY        0
#define WAIT_WAITER  1
#define ATTENDED     2
#define CONSUMING    3

typedef enum { EV_ARRIVAL, EV_END_ATT, EV_END_CONS, EV_SNAPSHOT } EventType;

/* --- distributions --- */
static double Exponential(double m) { return -m * log(1.0 - Random()); }

/* --- stochastic generators (one stream per process) --- */
static double interarrival(void)        { SelectStream(0); return Exponential(mean_iarrival); }
static int    generate_class(void)      { SelectStream(1); if (Random() < p_cafe) return CAFE; else return DESAYUNO; }
static double attention_time(int cls)   { SelectStream(2 + cls); return Exponential(mean_attention[cls]); }
static double consumption_time(int cls) { SelectStream(4 + cls); return Exponential(mean_consumption[cls]); }

/* --- chair state arrays --- */
static double chair_t_arrival[S];
static double chair_t_sit[S];
static double chair_t_att[S];
static int    chair_class[S];
static int    chair_state[S];
static double t_end_consumption[S];

/* --- waiter state arrays --- */
static int    waiter_chair[C];        /* chair served, -1 if idle */
static double t_end_attention[C];

/* --- seated-waiting FIFO (chair indices), bounded by S --- */
static int    waiting_chairs[S];
static int    wq_head = 0, wq_tail = 0, wq_count = 0;

/* --- standing FIFO (linked list, unbounded) --- */
typedef struct StandingNode {
    double t_arrival;
    int    class;
    struct StandingNode *next;
} StandingNode;

static StandingNode *standing_head = NULL, *standing_tail = NULL;
static int n_standing = 0;

static double t_clock = 0.0;
static double t_next_arrival;
static double t_next_snapshot;
static FILE  *csv_file = NULL;

/* --- statistics --- */
static long   clients_arrived = 0;
static long   clients_served  = 0;     /* total served (drives the LAST loop) */
static long   valid_clients   = 0;     /* served AFTER warm-up (used for stats) */
static long   count_class[2]  = {0, 0};
static double sum_standing    = 0.0;
static double sum_seated_wait = 0.0;
static double sum_total       = 0.0;

static double t_last_change        = 0.0;
static double area_chairs_occupied = 0.0;
static double area_waiters_busy    = 0.0;
static double area_n_in_system     = 0.0;

/* --- queue helpers --- */
static void push_standing(double t, int cls) {
    StandingNode *n = malloc(sizeof(StandingNode));
    n->t_arrival = t; n->class = cls; n->next = NULL;
    if (standing_tail) standing_tail->next = n; else standing_head = n;
    standing_tail = n; n_standing++;
}
static int pop_standing(double *t, int *cls) {
    if (!standing_head) return 0;
    *t = standing_head->t_arrival; *cls = standing_head->class;
    StandingNode *tmp = standing_head;
    standing_head = standing_head->next;
    if (!standing_head) standing_tail = NULL;
    free(tmp); n_standing--;
    return 1;
}
static void push_waiting(int chair_idx) {
    waiting_chairs[wq_tail] = chair_idx;
    wq_tail = (wq_tail + 1) % S; wq_count++;
}
static int pop_waiting(void) {
    if (wq_count == 0) return -1;
    int idx = waiting_chairs[wq_head];
    wq_head = (wq_head + 1) % S; wq_count--;
    return idx;
}

/* --- slot lookups --- */
static int find_free_waiter(void) {
    for (int i = 0; i < C; i++) if (waiter_chair[i] < 0) return i;
    return -1;
}
static int find_free_chair(void) {
    for (int i = 0; i < S; i++) if (chair_state[i] == EMPTY) return i;
    return -1;
}
static int chairs_occupied(void) {
    int n = 0; for (int i = 0; i < S; i++) if (chair_state[i] != EMPTY) n++;
    return n;
}
static int waiters_busy(void) {
    int n = 0; for (int i = 0; i < C; i++) if (waiter_chair[i] >= 0) n++;
    return n;
}

/* --- time-integrated areas (only after warm-up) --- */
static void update_areas(void) {
    if (t_clock < WARMUP_TIME) {
        /* during warm-up: do not accumulate; just track time */
        t_last_change = t_clock;
        return;
    }
    /* first crossing of WARMUP: start counting from WARMUP, not from t_last_change */
    if (t_last_change < WARMUP_TIME) {
        t_last_change = WARMUP_TIME;
    }
    double dt = t_clock - t_last_change;
    if (dt < 0) dt = 0;
    area_chairs_occupied += chairs_occupied() * dt;
    area_waiters_busy    += waiters_busy()    * dt;
    area_n_in_system     += (n_standing + chairs_occupied()) * dt;
    t_last_change = t_clock;
}

/* --- action helpers --- */
static void seat_in_chair(int chair, double t_arr, int cls) {
    chair_t_arrival[chair] = t_arr;
    chair_t_sit[chair]     = t_clock;
    chair_class[chair]     = cls;
    chair_state[chair]     = WAIT_WAITER;
}
static void start_attention_at(int chair, int waiter) {
    chair_t_att[chair]      = t_clock;
    chair_state[chair]      = ATTENDED;
    waiter_chair[waiter]    = chair;
    t_end_attention[waiter] = t_clock + attention_time(chair_class[chair]);
}

/* --- event handlers --- */
static void handle_arrival(void) {
    update_areas();
    double t_arr = t_clock;
    int    cls   = generate_class();
    clients_arrived++;
    t_next_arrival = t_clock + interarrival();

    int chair = find_free_chair();
    if (chair < 0) { push_standing(t_arr, cls); return; }
    seat_in_chair(chair, t_arr, cls);

    int w = find_free_waiter();
    if (w < 0) { push_waiting(chair); return; }
    start_attention_at(chair, w);
}

static void handle_end_attention(int waiter) {
    update_areas();
    int chair = waiter_chair[waiter];
    chair_state[chair] = CONSUMING;
    t_end_consumption[chair] = t_clock + consumption_time(chair_class[chair]);
    waiter_chair[waiter] = -1;
    t_end_attention[waiter] = INFTY;

    int next_chair = pop_waiting();
    if (next_chair >= 0) start_attention_at(next_chair, waiter);
}

static void handle_end_consumption(int chair) {
    update_areas();

    /* statistics accumulated only for customers leaving AFTER warm-up */
    if (t_clock >= WARMUP_TIME) {
        sum_total       += t_clock - chair_t_arrival[chair];
        sum_standing    += chair_t_sit[chair] - chair_t_arrival[chair];
        sum_seated_wait += chair_t_att[chair] - chair_t_sit[chair];
        count_class[chair_class[chair]]++;
        valid_clients++;
    }
    clients_served++;   /* total counter (drives the LAST loop) */

    chair_state[chair] = EMPTY;
    t_end_consumption[chair] = INFTY;

    double t_arr_next; int cls_next;
    if (!pop_standing(&t_arr_next, &cls_next)) return;
    seat_in_chair(chair, t_arr_next, cls_next);
    int w = find_free_waiter();
    if (w < 0) { push_waiting(chair); return; }
    start_attention_at(chair, w);
}

static void handle_snapshot(void) {
    update_areas();
    double T = (t_clock > 0) ? t_clock : 1e-9;
    long served = (clients_served > 0) ? clients_served : 1;

    fprintf(csv_file,
        "%.2f,%d,%d,%d,%d,%ld,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f\n",
        t_clock,
        n_standing + chairs_occupied(),
        n_standing,
        chairs_occupied(),
        waiters_busy(),
        clients_served,
        sum_total/served,
        sum_standing/served,
        sum_seated_wait/served,
        area_chairs_occupied/(T*S),
        area_waiters_busy/(T*C),
        clients_served/T);

    t_next_snapshot = t_clock + SNAPSHOT_INTERVAL;
}

/* --- next-event scheduler --- */
static double find_next_event(EventType *type, int *slot) {
    double t_min = t_next_arrival;
    *type = EV_ARRIVAL; *slot = -1;
    for (int i = 0; i < C; i++)
        if (t_end_attention[i] < t_min) { t_min = t_end_attention[i]; *type = EV_END_ATT; *slot = i; }
    for (int i = 0; i < S; i++)
        if (t_end_consumption[i] < t_min) { t_min = t_end_consumption[i]; *type = EV_END_CONS; *slot = i; }
    if (t_next_snapshot < t_min) { t_min = t_next_snapshot; *type = EV_SNAPSHOT; *slot = -1; }
    return t_min;
}

static void init_state(void) {
    for (int i = 0; i < S; i++) { chair_state[i] = EMPTY; t_end_consumption[i] = INFTY; }
    for (int i = 0; i < C; i++) { waiter_chair[i] = -1; t_end_attention[i] = INFTY; }
}

static void print_stats(void) {
    double T_total = t_clock;
    double T_eff   = (T_total > WARMUP_TIME) ? (T_total - WARMUP_TIME) : 1e-9;
    long   n       = (valid_clients > 0) ? valid_clients : 1;

    printf("\n==================== RESULTS ====================\n");
    printf("Configuration: C=%d waiters, S=%d chairs\n", C, S);
    printf("Warm-up T_0:                  %.2f min  (%.2f h)\n", WARMUP_TIME, WARMUP_TIME/60.0);
    printf("Total simulated time:         %.2f min  (%.2f h)\n", T_total, T_total/60.0);
    printf("Effective time (post-warmup): %.2f min  (%.2f h)\n", T_eff, T_eff/60.0);
    printf("Total customers served:       %ld\n", clients_served);
    printf("Valid (post-warmup):          %ld\n", valid_clients);
    printf("  CAFE:                       %ld (%.1f%%)\n", count_class[CAFE], 100.0*count_class[CAFE]/n);
    printf("  DESAYUNO:                   %ld (%.1f%%)\n", count_class[DESAYUNO], 100.0*count_class[DESAYUNO]/n);
    printf("\n--- Mean times (min, post-warmup) ---\n");
    printf("  Standing wait:              %.4f\n", sum_standing/n);
    printf("  Seated wait for waiter:     %.4f\n", sum_seated_wait/n);
    printf("  Total time in system:       %.4f\n", sum_total/n);
    printf("\n--- Throughput (post-warmup) ---\n");
    printf("  Observed arrival rate:      %.4f cust/min  (expected %.4f)\n", clients_arrived/T_total, 1.0/mean_iarrival);
    printf("  Throughput:                 %.4f cust/min  (%.1f/h)\n", valid_clients/T_eff, valid_clients*60.0/T_eff);
    printf("\n--- Utilization (time-integrated, post-warmup) ---\n");
    printf("  Chairs:                     %.4f  (%.1f%%)\n", area_chairs_occupied/(T_eff*S), 100.0*area_chairs_occupied/(T_eff*S));
    printf("  Waiters:                    %.4f  (%.1f%%)\n", area_waiters_busy/(T_eff*C), 100.0*area_waiters_busy/(T_eff*C));
    printf("\n--- Mean number in system (post-warmup) ---\n");
    printf("  L (all):                    %.4f\n", area_n_in_system/T_eff);
    printf("\n--- Little check (L = lambda * T) ---\n");
    printf("  lambda * T_sys = %.4f, L = %.4f\n", (valid_clients/T_eff) * (sum_total/n), area_n_in_system/T_eff);
    printf("==================================================\n");
}

int main(int argc, char *argv[]) {
    long seed = 123456789;
    int  batch_mode = 0;
    if (argc > 1) seed = atol(argv[1]);
    if (argc > 2 && argv[2][0] == 'b') batch_mode = 1;

    PlantSeeds(seed);
    init_state();
    t_next_arrival  = interarrival();
    t_next_snapshot = SNAPSHOT_INTERVAL;

    /* CSV transient file: only in normal (non-batch) mode to avoid clobbering */
    if (!batch_mode) {
        csv_file = fopen(CSV_FILENAME, "w");
        if (!csv_file) { perror("fopen"); return 1; }
        fprintf(csv_file,
            "t,n_in_system,n_standing,chairs_occupied,waiters_busy,"
            "clients_served,avg_total,avg_standing,avg_seated,"
            "util_chairs,util_waiters,throughput\n");
    }

    while (clients_served < LAST) {
        EventType type; int slot;
        t_clock = find_next_event(&type, &slot);
        switch (type) {
            case EV_ARRIVAL:    handle_arrival();             break;
            case EV_END_ATT:    handle_end_attention(slot);   break;
            case EV_END_CONS:   handle_end_consumption(slot); break;
            case EV_SNAPSHOT:   if (csv_file) handle_snapshot(); else t_next_snapshot += SNAPSHOT_INTERVAL; break;
        }
    }
    update_areas();
    if (csv_file) fclose(csv_file);

    if (batch_mode) {
        /* Single-line CSV summary for orchestration scripts (post-warmup) */
        double T_total = t_clock;
        double T_eff   = (T_total > WARMUP_TIME) ? (T_total - WARMUP_TIME) : 1e-9;
        long   n       = (valid_clients > 0) ? valid_clients : 1;
        printf("RESULT,%ld,%d,%d,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.2f\n",
            seed, C, S,
            sum_total/n,
            sum_standing/n,
            sum_seated_wait/n,
            valid_clients*60.0/T_eff,
            area_chairs_occupied/(T_eff*S),
            area_waiters_busy/(T_eff*C),
            area_n_in_system/T_eff,
            T_eff);
    } else {
        print_stats();
        printf("\nTransient data written to: %s (1 row every %.0f min)\n", CSV_FILENAME, SNAPSHOT_INTERVAL);
    }
    return 0;
}
