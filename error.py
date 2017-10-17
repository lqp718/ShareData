import StringIO, logging, traceback

def trace_log():
    fp = StringIO.StringIO()
    traceback.print_exc(file=fp)
    logging.error(fp.getvalue())


def trace_msg():
    fp = StringIO.StringIO()
    traceback.print_exc(file=fp)
    return fp.getvalue()
