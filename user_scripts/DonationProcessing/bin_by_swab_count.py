#!/usr/bin/env python

__author__ = "Daniel McDonald"
__copyright__ = "Copyright 2009-2013, QIIME Web Analysis"
__credits__ = ["Daniel McDonald","Emily TerAvest"]
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = ["Daniel McDonald"]
__email__ = "mcdonadt@colorado.edu"
__status__ = "Development"

"""
This determines the number of kits we need from to make for each number of swabs
"""

script_info = {}
script_info['brief_description'] = "Separates the kits by number of swabs"
script_info['script_description'] = ""
script_info['script_usage'] = []
script_info['required_options'] = [
        make_option('--input', '-i', help="Input file, "),
        make_option('--starting_sample', help='Starting sample number', 
                    type='int')
        ]
script_info['optional_options'] = [
        make_option('--input', '-i', help="Input table"),
        make_option('--correct_us_states', action='store_true', default=False,
                    help="Abbreviate US states"),
        make_option('--pad_us_zipcodes', action='store_true', default=False,
                    help="Force US zip codes to be 5 digits"),
        make_option('--tag', help='prefix tag'),
        make_option('--swabs_per_kit', help="swabs per kit", type="str"),
        make_option('--number_of_kits', help="number of kits", type="str"),
        ]
script_info['version'] = __version__
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
