import sys

def trace(frame, event, arg):
    if event == 'line':
        print (frame.f_code.co_filename, frame.f_lineno)
    return trace

sys.settrace(trace)

import mymod
