#!/usr/bin/env python

"""make a minimal sheet for printing address labels"""

from sys import argv, exit

lines = [l.strip().split('\t') for l in open(argv[1],'U')]

name_idx = map(lambda x: x.lower(), lines[0]).index('name')
email_idx = map(lambda x: x.lower(), lines[0]).index('name')

if name_idx == -1:
    print "can't get name index!"
    exit(1)
if email_idx == -1:
    print "can't get email index!"
    exit(1)

output = open(argv[1].split('.')[0] + '_minimal.txt', 'w')
output.write('\t'.join(lines[0]))
output.write('\n')

seen = set([])
for l in lines[1:]:
    name = l[name_idx]
    email = l[email_idx]

    if (name,email) in seen:
        continue
    else:
        seen.add((name,email))

    output.write('\t'.join(l))
    output.write('\n')
output.close()
