#ifndef _STDDEF_H
#define _STDDEF_H

typedef long size_t;
typedef long ptrdiff_t;
typedef long ssize_t;

#define NULL ((void*)0)

typedef struct {
    long long __max_align_ll;
    long double __max_align_ld;
} max_align_t;

#endif