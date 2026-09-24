/* Generated bounded arithmetic subject; MIT license, see repository LICENSE. */
#include <stdint.h>
#include <inttypes.h>
#include <stdio.h>
static int64_t subject(int64_t x,int64_t y,int fault,int mutant) {
  int64_t a=(x+(0)); /* logical location 0 */
  if (fault==0) a+=(1);
  if (mutant==0) a=(a+1); /* increment */
  if (mutant==1) a=(a-1); /* decrement */
  int64_t b=(y-(1)); /* logical location 1 */
  if (fault==1) b+=(1);
  if (mutant==2) b=(b-1); /* decrement */
  if (mutant==3) b=(-b); /* negation */
  if (mutant==4) b=(0); /* zero */
  int64_t c=(2*a+b); /* logical location 2 */
  if (fault==2) c+=(1);
  if (mutant==5) c=(c-1); /* decrement */
  if (mutant==6) c=(-c); /* negation */
  int64_t d=(c>2?c-(2):c+(2)); /* logical location 3 */
  if (fault==3) d+=(1);
  if (mutant==7) d=(d+1); /* increment */
  if (mutant==8) d=(d-1); /* decrement */
  if (mutant==9) d=(0); /* zero */
  int64_t e=(3*d+a); /* logical location 4 */
  if (fault==4) e+=(1);
  if (mutant==10) e=(e+1); /* increment */
  if (mutant==11) e=(0); /* zero */
  int64_t r=(e-b); /* logical location 5 */
  if (fault==5) r+=(1);
  if (mutant==12) r=(r+1); /* increment */
  if (mutant==13) r=(r-1); /* decrement */
  if (mutant==14) r=(0); /* zero */
  return r;
}
int main(void) {
  for (int x=-3;x<=3;x++) for(int y=-3;y<=3;y++) {
    printf("%d,%d,%" PRId64 ",%" PRId64,x,y,subject(x,y,-1,-1),subject(x,y,0,-1));
    for (int m=0;m<15;m++) printf(",%" PRId64,subject(x,y,0,m));
    putchar('\n');
  }
  return 0;
}
