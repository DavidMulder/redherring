#!/usr/bin/python

import difflib, sys, os.path, argparse
from dateutil.parser import parse as date_parse

def similarity(a, b):
    return difflib.SequenceMatcher(None, a, b)

def discover(filename):
    discoveries = {}

    with open(sys.argv[1], 'r') as f:
        ln = 1
        for line in f:
            if not line.strip():
                continue
            try:
                stamp, line = line.strip().split(': ', 1) # The seperator between date stamp and the message
            except:
                continue # ignore lines that wont parse
            data = stamp.split()
            date = date_parse(' '.join(data[:3]))
            module = data[-1].split('[')[0]
            line_found = False
            for other in discoveries.keys():
                s = similarity(line, other)
                diff = s.ratio()
                if diff > .85: # These lines are similar
                    discoveries[other][0] = (discoveries[other][0]+diff)/2.0
                    discoveries[other][1].append((date, line))

                    # Scratch out the uncommon sequences
                    new_line = '-'*len(line)
                    for block in s.get_matching_blocks():
                        if block.size > 0:
                            new_line = new_line[:block.a] + line[block.a:block.a+block.size] + new_line[block.a+block.size:]
                    discoveries[new_line] = discoveries.pop(other)

                    line_found = True
                    break
            if not line_found:
                discoveries[line] = [1.0, [(date, line)], module]
            ln += 1

    return discoveries

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Red Herring: Sorts through syslog debug and determines what is common (un-interesting) and what is unusual.", formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("syslog", help="File where syslog messages are stored")
    parser.add_argument("--print-messages", help="Print all the messages that were matched", action="store_true")
    parser.add_argument("--only-uncommon", help="Only print the uncommon messages", action="store_true")
    parser.add_argument("--uncommon-frequency", help="Frequency at which message is considered uncommon, default is 1", type=int, default=1)
    parser.add_argument("--unique-messages", help="Print the number of unique messages", action="store_true")
    parser.add_argument("--one-liner", help="Print only a one line summary for each message", action="store_true")

    args = parser.parse_args()

    if not os.path.exists(args.syslog):
        sys.stderr.write('The specified syslog file "%s" does not exist\n' % args.syslog)
        exit(1)

    if args.one_liner and args.print_messages:
        sys.stderr.write('You can\'t specify --one-liner and --print-messages together\n')
        exit(2)

    discoveries = discover(args.syslog)

    for line in discoveries.keys():
        data = discoveries[line]
        if args.only_uncommon and len(data[1]) > args.uncommon_frequency:
            continue
        data[1].sort(key=lambda things: things[0])
        if not args.one_liner:
            print '\n\nMessage: %s' % line
            print 'Module: %s' % data[2]
            print 'Frequency: %d' % len(data[1])
            print 'Similarity: %d%%' % (100.0*data[0])
            print 'Range: %s through %s' % (data[1][0][0].strftime('%d %b %H:%M:%S'), data[1][-1][0].strftime('%d %b %H:%M:%S'))
            if args.print_messages:
                for i in data[1]:
                    print '%s: %s' % (i[0].strftime('%d %b %H:%M:%S'), i[1])
        else:
            if args.only_uncommon and args.uncommon_frequency == 1:
                print '%s: %s' % (data[1][0][0].strftime('%d %b %H:%M:%S'), line)
            else:
                print 'freq %.2d sim %.3d%% range %s - %s msg: %s' % (len(data[1]), (100.0*data[0]), data[1][0][0].strftime('%m/%d %H:%M:%S'), data[1][-1][0].strftime('%m/%d %H:%M:%S'), line)

    if args.unique_messages:
        print '\n\nUnique Messages: %d\n' % len(discoveries.keys())

