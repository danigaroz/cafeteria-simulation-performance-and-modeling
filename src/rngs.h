/* -----------------------------------------------------------------------
 * rngs.h - Multi-stream Lehmer random number generator
 * From: Leemis & Park, Discrete-Event Simulation - A First Course, 2006
 * ----------------------------------------------------------------------- */
#ifndef RNGS_H
#define RNGS_H

double Random(void);
void   PlantSeeds(long x);
void   GetSeed(long *x);
void   PutSeed(long x);
void   SelectStream(int index);
void   TestRandom(void);

#endif
