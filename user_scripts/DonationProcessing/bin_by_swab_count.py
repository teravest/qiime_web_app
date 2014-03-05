#!/usr/bin/env python

from sys import argv

def write_stuff(header, data, fname):
    f = open(fname, 'w')
    f.write('\t'.join(header))
    f.write('\n')
    f.write('\n'.join(['\t'.join(i) for i in buf]))
    f.write('\n')
    f.close()

lines = [l.strip().split('\t') for l in open(argv[1])]
header = lines[0]

data = sorted(lines[1:], key=lambda x: int(x[0]))

basename = argv[1].split('_')[0] # e.g., January1
basename += '_numswabs_%s.txt'

last_swab = data[0][0]
buf = []
for l in data:
    num_swab = l[0]

    if num_swab != last_swab:
        write_stuff(header, buf, basename % last_swab)
        buf = []
        last_swab = num_swab
    buf.append(l)

if buf:
    write_stuff(header, buf, basename % last_swab)
