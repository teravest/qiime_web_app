#!/usr/bin/env python

__author__ = "Emily TerAvest"
__copyright__ = "Copyright 2009-2013, QIIME Web Analysis"
__credits__ = ["Emily TerAvest", "Daniel McDonald"]
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = ["Emily TerAvest"]
__email__ = "emily.teravest@colorado.edu"
__status__ = "Development"

from random import choice
from cx_Oracle import connect
from credentials import Credentials
from cogent.util.misc import parse_command_line_parameters
from optparse import make_option

script_info = {}
script_info['brief_description'] = """Insert handout kits from a list of fundrazr\
donners"""
script_info['script_description'] = ""
script_info['script_usage'] = []
script_info['required_options'] = [
        make_option('--output', '-o', help="Output table"),
        make_option('--starting_sample', help='Starting sample number',
                    type='int'),

        ]
script_info['optional_options'] = [
        make_option('--swabs_to_kits', help="dict of swabs to kits",
                     type="str"),
        make_option('--input', '-i', help="input file of partipants"),
        make_option('--tag', help='prefix tag')
        ]
script_info['version'] = __version__


def write_unassigned(l, output_unassigned):
    """writes a file with unassigned donations

    """
    print '\t'.join(l)
    output_unassigned.write('\t'.join(l))
    output_unassigned.write('\n')


def determine_swabs(donationfile):
    """determines the number of kits with each nubmer of swab in the
       dontation file.

       """
    lines = [l.strip().split('\t') for l in open(donationfile,'U')]

    header = lines[0][:]
    header[0] = "swabs_per_kit"
    country_idx = header.index('Country')
    output_unassigned = open(donationfile.split('.')[0] + '_noswabs.txt','w')
    output_unassigned.write('\t'.join(lines[0]))
    output_unassigned.write('\n')

    amount_map = [(0.0, 0.1, 1),
                  (98.9, 129.1, 1),
                  (179.9, 230.1, 2),
                  (259.9, 260.1, 3),
                  (319.9, 320.1, 4),
                  (499.9, 500.1, 7)]

    us_amount_map = {1:99.0,
                     2:180.0,
                     3:260.0,
                     4:320.0,
                     7:500.0}

    num_swab_to_kits = { 1: 0, 2:0, 3:0, 4:0, 7:0}



    import string
    amount_idx = map(string.lower, lines[0]).index('amount')
    for l in lines[1:]:
        amount = float(l[amount_idx].replace(",",""))

        num_swabs = None
        for low,high,swabs in amount_map:
            if low <= amount <= high:
                num_swabs = swabs
                break

        if num_swabs is None:
            write_unassigned(l, output_unassigned)
        elif l[country_idx] != 'US' \
             and num_swabs in us_amount_map \
             and amount == us_amount_map[num_swabs]:
            #print l
            print "bad ammount, country does not equal US"
            write_unassigned(l, output_unassigned)
        elif num_swabs == 1 \
                and amount < 98.9:
             #and not l[currency_idx].startswith('KNIGHT_'):
            write_unassigned(l, output_unassigned)
        else:
          #return a dictionary with the number of kits with each number of swabs
          num_swab_to_kits[num_swabs] = num_swab_to_kits[num_swabs] + 1

    output_unassigned.close()
    return num_swab_to_kits

# character sets for kit id, passwords and verification codes
KIT_ALPHA = "abcdefghijklmnopqrstuvwxyz"
KIT_PASSWD = '1234567890'
KIT_VERCODE = KIT_PASSWD


BASE_PRINTOUT_TEXT = """Thank you for participating in the American Gut Project! Below you will find your sample barcodes (the numbers that anonymously link your samples to you) and your login credentials. It is very important that you login before you begin any sample collection.

Please login at: http://www.microbio.me/AmericanGut

Thanks,
The American Gut Project
"""

def verify_unique_sample_id(cursor, sample_id):
    """Verify that a sample ID does not already exist
    """
    cursor.execute("select barcode from ag_kit_barcodes where barcode='%s'" % \
                sample_id)
    results = cursor.fetchall()

    if len(results) != 0:
        return False

    cursor.execute("select barcode from ag_handout_kits where barcode='%s'" % \
                sample_id)
    results = cursor.fetchall()

    if len(results) != 0:
        return False

    return True

def get_used_kit_ids(cursor):
    """Grab in use kit IDs, return set of them
    """
    cursor.execute("select supplied_kit_id from ag_kit")

    return set([i[0] for i in cursor.fetchall()])

def make_kit_id(obs_kit_ids, kit_id_length=5, tag=None):
    """Generate a new unique kit id
    """
    if tag is None:
        kit_id = ''.join([choice(KIT_ALPHA) for i in range(kit_id_length)])
    else:
        if kit_id_length + len(tag) + 1 >9:
            #we have a 9 char limit for kit ids reduce the kit_id_length
            kit_id_lenght = 8 - len(tag)
        kit_id = '_'.join([tag, ''.join([choice(KIT_ALPHA)
                                         for i in range(kit_id_length)])])
    while kit_id in obs_kit_ids:
        if tag is None:
            kit_id = ''.join([choice(KIT_ALPHA) for i in range(kit_id_length)])
        else:
            if kit_id_length + len(tag) + 1 >9:
                #we have a 9 char limit for kit ids reduce the kit_id_length
                kit_id_lenght = 8 - len(tag)
            kit_id = '_'.join([tag, ''.join([choice(KIT_ALPHA)
                                             for i in range(kit_id_length)])])

    obs_kit_ids.add(kit_id)

    return (obs_kit_ids, kit_id)

KIT_PASSWD_NOZEROS = KIT_PASSWD[0:-1]
def make_passwd(passwd_length=8):
    """Generate a new password
    """
    x = ''.join([choice(KIT_PASSWD) for i in range(passwd_length-1)])
    return choice(KIT_PASSWD_NOZEROS) + x

KIT_VERCODE_NOZEROS = KIT_PASSWD_NOZEROS
def make_verification_code(vercode_length=5):
    """Generate a verification code
    """
    x = ''.join([choice(KIT_VERCODE) for i in range(vercode_length-1)])
    return choice(KIT_VERCODE_NOZEROS) + x

def get_printout_data(kit_passwd_map, kit_barcode_map):
    """Produce the text for paper slips with kit credentials
    """
    text = []
    for kit_id,passwd in kit_passwd_map:
        text.append(BASE_PRINTOUT_TEXT)
        barcodes = kit_barcode_map[kit_id]

        padding_lines = 5

        if len(barcodes) > 5:
            text.append("Sample Barcodes:\t%s" % ', '.join(barcodes[:5]))
            for i in range(len(barcodes))[5::5]:
                padding_lines -= 1
                text.append("\t\t\t%s" % ', '.join(barcodes[i:i+5]))
        else:
            text.append("Sample Barcodes:\t%s" % ', '.join(barcodes))

        text.append("Kit ID:\t\t%s" % kit_id)
        text.append("Password:\t\t%s" % passwd)

        # padding between sheets so they print pretty
        for i in range(padding_lines):
            text.append('')

    return text

def unassigned_kits(starting_sample, cursor, existing_kit_ids, output,
                    swabs_per_kit, tag=None):
    """Creates handout kits based on number of kits need for each swab count
    """
    header = ["barcode","swabs_per_kit","KIT_ID","KIT_PASSWORD",
              "KIT_VERIFICATION_CODE","SAMPLE_BARCODE_FILE"]

    outlines = [header[:]]

    kit_barcode_map = {}
    kit_passwd_map = []
    current_sample_id = starting_sample

    for swab_count in swabs_per_kit:
        kit_count = swabs_per_kit[swab_count]
        for kit in range(kit_count):
            existing_kit_ids, kit_id = make_kit_id(existing_kit_ids, tag=tag)
            passwd = make_passwd()
            vercode = make_verification_code()

            kit_barcode_map[kit_id] = []
            kit_passwd_map.append((kit_id, passwd))

            # add on the samples per kit
            for sample in range(swab_count):
                sample_id = "%0.9d" % current_sample_id

                if not verify_unique_sample_id(cursor, sample_id):
                    raise ValueError, "%s is not unique!" % sample_id

                outlines.append([sample_id, swab_count, kit_id, passwd,
                                 vercode, "%s.jpg" % sample_id])
                kit_barcode_map[kit_id].append(sample_id)

                current_sample_id += 1

    f = open(output,'w')
    f.write('\n'.join(['\t'.join(map(str, l)) for l in outlines]))
    f.write('\n')
    f.close()

    return kit_passwd_map, kit_barcode_map, outlines

def make_printouts(kit_passwd_map, kit_barcode_map, output):
    """Makes a file with the kit creditinal infomration
    """
    f = open(output + '.printouts', 'w')
    f.write('\n'.join(get_printout_data(kit_passwd_map, kit_barcode_map)))
    f.write('\n')
    f.close()

def insert_kits(kits, proj_id, cursor):
    """inserts the handout kits into the test database and the
       prodction database.
    """
    #skip the header line
    for line in kits[1:]:
        #line continuations are on lines below to prevent newlines being in the
        #output files. 
        #first insert handout kits
        kitinsertstmt = """insert into ag_handout_kits ('barcode',\
'swabs_per_kit','KIT_ID','KIT_PASSWORD','KIT_VERIFICATION_CODE',\
'SAMPLE_BARCODE_FILE') values ('%s','%s', '%s', '%s', '%s', '%s')""" \
                           %(tuple(line[0:6]))
        barcodeinsertstmt = """insert into barcode ('barcode', 'obsolete') \
values ('%s', 'N')""" %line[0]
        #this statment will need updated when group info is on live
        barcodeprojinsertstmt = """insert into barcode_project ('barcode',\
'project') values ('%s', '%s')""" %(line[0], proj_id)
        print kitinsertstmt + ';'
        print barcodeinsertstmt + ';'
        print barcodeprojinsertstmt + ';'

        #cursor.execute(kitinsertstmt)
        #cursor.execute(barcodeinsertstmt)
        #cursor.execute(barcdoeprojinsertstmt)



def main():
    option_parser, opts, args = parse_command_line_parameters(**script_info)


    # setup DB connection
    cred = Credentials()
    con = connect(cred.liveMetadataDatabaseConnectionString)
    cursor = con.cursor()
    existing_kit_ids = get_used_kit_ids(cursor)
    starting_sample = opts.starting_sample
    output = opts.output
    tag = opts.tag
    if opts.input is not None:
        swabs_to_kits = determine_swabs(opts.input)
    elif opts.swabs_to_kits is not None:
        swabs_to_kits = eval(opts.swabs_to_kits)
    else:
        print "Must specify either input file or swabs to kits dictionary"
        exit()

    kit_passwd_map, kit_barcode_map, outlines = unassigned_kits(starting_sample,
                                                      cursor,
                                                      existing_kit_ids, output,
                                                      swabs_to_kits, tag)
    make_printouts (kit_passwd_map, kit_barcode_map, output)
    testcon = connect(cred.testMetadataDatabaseConnectionString)
    testcursor = testcon.cursor()
    try:
        insert_kits(outlines, '1', testcursor)
        testcursor.close()
    except e:
        #if anything happens raise and exit
        testcursor.close()
        print "error when uploading to test database"
        raise e

    try:
        insert_kits(outlines, '1', cursor)
    except e:
        print "error while uploading to production database"
        cursor.close()
        raise e
    cursor.close()



if __name__ == '__main__':
    main()
