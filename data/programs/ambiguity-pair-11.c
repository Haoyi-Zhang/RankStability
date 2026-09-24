/* MIT license. Two correction origins; equal reference outputs. */
#include <stdint.h>
#include <inttypes.h>
#include <stdio.h>
static int64_t faulty(int64_t x,int m) { int64_t a=x+12;
if(m==0) a=(a+1);
if(m==1) a=(a-1);
if(m==2) a=(-a);
if(m==3) a=(0);
int64_t b=a+12;
if(m==4) b=(b+1);
if(m==5) b=(b-1);
if(m==6) b=(-b);
if(m==7) b=(0);
return b;}
static int64_t correction0(int64_t x) { int64_t a=x; int64_t b=a+12; return b; }
static int64_t correction1(int64_t x) { int64_t a=x+12; int64_t b=a; return b; }
int main(void) { for(int x=-9;x<=9;x++) {
printf("%d,%" PRId64 ",%" PRId64 ",%" PRId64,x,correction0(x),correction1(x),faulty(x,-1));
for(int m=0;m<8;m++) printf(",%" PRId64,faulty(x,m));
putchar('\n'); } return 0; }
