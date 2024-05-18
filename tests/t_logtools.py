import logging
from logtools_vrb import ExcInfo, LogUtils

def print_heading(s): 
    print(f"\n#### {s}: ######################## \n")

# Get Logger instance and set log level
logger=logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

######################################
# SAMPLE USAGE: ExcInfo
######################################

try:
    1/0
except:
    print_heading("ExcInfo demo")
    logger.error(f"{ExcInfo(comment='oh-oh!')}")
    logger.error(f"{ExcInfo(verbosity=2)}")

######################################
# SAMPLE USAGE: LogUtils
######################################

# Make log record for the calling line without
# log level, message and stack trace, just to
# get position information
lr = LogUtils.make_log_record()
# Get info from log record
caller = LogUtils.get_caller(lr)
print_heading("Caller record (var 1)")
print(caller)
# caller record now contains information about the line
# in which make_log_record was called.

# simpler variant, if no log record is needed:
caller = LogUtils.find_caller()
# caller record now contains information about the line
# in which find_caller was called.
print_heading("Caller record (var 2)")
print(caller)

# Make log record for use with logger
lr = LogUtils.make_log_record(logging.INFO, "Message")
# print formatted message to stdout using lf (see above)
print_heading("Log selfmade record")
logger.handle(lr)

# Use get_exc_info() in case of an exception
try:
    a = 10 / 0
except:
    print_heading("Embed exception information using get_exc_info")
    logger.error(f"[{LogUtils.get_exc_info()}] when dividing a number by zero", exc_info=True)

# Use make_log_record in case of an exception
try:
    a = 1 / 0
except:
    print_heading("Embed exception information using make_log_record (var 1)")
    lr = LogUtils.make_log_record(logging.ERROR, "Exception caught!", extra={"comment": "I knew that!"}, exc_info=True)
    print("LogRecord: ", lr.__dict__)
    # print error log message
    logger.handle(lr)
    # get exception object from log record for exception
    # in line "a = 1 / 0"
    ei = LogUtils.get_exc_info(lr)
    print(f"Exception: {str(ei)}")

# other variant:
divident = 2
divisor = 0
operation = "divide %i by %i"
try:
    a = 2 / 0
except BaseException as exc:
    print_heading("Embed exception information using make_log_record with arguments")
    a_str = "caught!"
    an_int = 42
    lr = LogUtils.make_log_record(logging.ERROR, "Exception in: " + operation, divident, divisor, exc_info=exc)
    logger.handle(lr)