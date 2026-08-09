/* -----------------------------------------------------------------------
 * rngs.c - Multi-stream Lehmer RNG implementation
 * 256 streams, modulus 2^31-1, multiplier 48271
 * From: Leemis & Park, Discrete-Event Simulation - A First Course, 2006
 * ----------------------------------------------------------------------- */
#include <stdio.h>
#include <time.h>
#include "rngs.h"

#define MODULUS    2147483647L
#define MULTIPLIER 48271L
#define CHECK      399268537L
#define STREAMS    256
#define A256       22925L
#define DEFAULT    123456789L

static long seed[STREAMS] = {DEFAULT};
static int  stream        = 0;
static int  initialized   = 0;

double Random(void) {
    const long Q = MODULUS / MULTIPLIER;
    const long R = MODULUS % MULTIPLIER;
    long t;

    t = MULTIPLIER * (seed[stream] % Q) - R * (seed[stream] / Q);
    if (t > 0) seed[stream] = t;
    else       seed[stream] = t + MODULUS;
    return ((double) seed[stream] / MODULUS);
}

void PlantSeeds(long x) {
    const long Q = MODULUS / A256;
    const long R = MODULUS % A256;
    int j, s;

    initialized = 1;
    s = stream;
    SelectStream(0);
    PutSeed(x);
    stream = s;
    for (j = 1; j < STREAMS; j++) {
        x = A256 * (seed[j-1] % Q) - R * (seed[j-1] / Q);
        if (x > 0) seed[j] = x;
        else       seed[j] = x + MODULUS;
    }
}

void PutSeed(long x) {
    if (x > 0) x = x % MODULUS;
    else       x = ((unsigned long) time(NULL)) % MODULUS;
    seed[stream] = x;
}

void GetSeed(long *x) {
    *x = seed[stream];
}

void SelectStream(int index) {
    stream = ((index % STREAMS) + STREAMS) % STREAMS;
    if ((initialized == 0) && (stream != 0)) PlantSeeds(DEFAULT);
}

void TestRandom(void) {
    long i, x;
    double u;
    int ok;

    SelectStream(0);
    PutSeed(1);
    for (i = 0; i < 10000; i++) u = Random();
    GetSeed(&x);
    ok = (x == CHECK);
    SelectStream(1);
    PlantSeeds(1);
    GetSeed(&x);
    ok = ok && (x == A256);
    if (ok) printf("\n rngs.c OK (multi-stream Lehmer verified)\n");
    else    printf("\n rngs.c ERROR\n");
    (void)u;
}
