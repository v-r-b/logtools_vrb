"""
# logtools_vrb

Logging tools.

  - On PyPI: https://pypi.org/project/logtools-vrb/
  - On GitHub: https://github.com/v-r-b/logtools_vrb 

## \_\_init__.py

```program_name, program_pid```

Name and process ID of currently running program

## logtools.py

```class CallerRecord:```

Information regarding current position in program

```class ExcInfo```

Enhanced handling of exception information in logging etc.

```class LogUtils```

Misc Utils concerning logging and exceptions

## formatting.py

```class LevelAwareFormatter```

Formatter for use with the logging module supporting
different format strings depending on the log level.

## mailloghandler.py

```class MailLogHandler```

Log handler which mails log messages to a given recipient.
"""

import sys, os

program_name: str = os.path.basename(sys.argv[0]) \
    if sys.argv is not None and \
       sys.argv[0] is not None \
    else "(unknown program)"
""" name of currently running program """

program_pid = os.getpid()
""" process ID of currently running program """

__all__ = (
    "CallerRecord", 
    "ExcInfo", 
    "LogUtils",
    "LevelAwareFormatter",
    "MailLogHandler"
)

from logtools_vrb.logtools import CallerRecord, ExcInfo, LogUtils
from logtools_vrb.formatting import LevelAwareFormatter
from logtools_vrb.mailloghandler import MailLogHandler
