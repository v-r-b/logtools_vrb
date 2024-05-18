from __future__ import annotations

from datetime import datetime
import typing
if typing.TYPE_CHECKING:
    from logging import _SysExcInfoType, _ArgsType

from collections.abc import Mapping
from dataclasses import dataclass
import sys
import logging
from logging import LogRecord, Logger, _srcfile
from types import TracebackType
import traceback

from logtools_vrb import program_name, program_pid

@dataclass
class CallerRecord:
    """ information regarding current position in program """
    
    prog_name: str
    """ name of the running script """
    pid: int|None
    """ process id """
    filename: str
    """ filename currently being executed """
    line_number: int
    """ current line number in <filename> """
    context_name: str
    """ current method or function name """
    stack_info: str|None
    """ stack info as string """

class ExcInfo:
    """ Enhanced handling of exception information in logging etc. """
    def __init__(self, exc_info: BaseException|_SysExcInfoType|None = None,
                 comment: str = "", verbosity: int = 1) -> None:
        """ Extract exception information such as type, text, traceback, filename,
        line number, function and codeline (or a subset of this information) from
        the exc_info object passed in. If None is passed in as an argument,
        sys.exc_info() ist used as an information source.

        Args:
            exc_info (BaseException | _SysExcInfoType | None, optional): exception information object. Defaults to None.
            comment (str, optional): additional text used in to_str(), __str__() and __format__() methods. Defaults to "".
            verbosity (int, optional): verbosity level for __str__() function. See to_str() for details. Defaults to 1.
        """
        # If no info has been given, use sys.exc_info()
        if exc_info is None:
            exc_info = sys.exc_info()

        # Create members with default values. 
        # These can be used in __format__() method.
        self.prog_name: str = program_name
        self.pid: int = program_pid
        self.exc: BaseException|None = None
        self.tb: TracebackType|None = None
        self.filename: str = ""
        self.linenum: int = -1
        self.codeline: str = ""
        self.context: str = ""
        self.comment: str = comment
        self.verbosity = verbosity

        if isinstance(exc_info, BaseException):
            # then we only have an exception object
            self.exc = exc_info
            # get traceback from exception:
            self.tb = self.exc.__traceback__
        elif isinstance(exc_info, tuple) and (len(exc_info) > 1):
            # then we have an exception object ...
            self.exc = exc_info[1]
            if self.exc is not None:
                # ... plus probably traceback information
                self.tb = exc_info[2] if len(exc_info) > 2 else None
        if self.tb is not None:
            self.linenum = self.tb.tb_lineno
            stack = traceback.extract_tb(self.tb, 1)
            self.filename = stack[0].filename
            self.context = stack[0].name
            self.codeline = stack[0].line if stack[0].line else ""

    def to_str(self, verbosity: int|None = None) -> str:
        """ Return a preformatted string

        Args:
            verbosity (int | None, optional): verbosity level of the output. Defaults to None which
            means that self.verbosity is used (see constructor)
                0: output of __repr__(), 
                1: exc classname + text + comment, 
                2: level 1 plus position information (file, function, line number), 
                3: level 2 plus codeline being executed when the exception occurred,
                4: level 3 plus stacktrace.
        Returns:
            str: string representation 
        """
        if verbosity is None:
            verbosity = self.verbosity
        if verbosity == 0:
            return self.__repr__()
        else:
            s = repr(self.exc)
            if self.comment:
                s += f" [{self.comment}]"
            if verbosity > 1:
                if self.filename:
                    s += f" in file {self.filename}"
                if self.linenum >= 0:
                    s += f", line {self.linenum}"
                if self.context:
                    s += f", function {self.context}"
                if (verbosity > 2) and self.codeline:
                    s += f", executing '{self.codeline}'"
                if verbosity > 3: # include multiline stack trace
                    s += "\n\n" + "".join(traceback.format_exception(self.exc))
            return s

    def __format__(self, __format_spec: str) -> str:
        """ Format exception information. The format string may either be
        a number between "0" and "4" or it may contain keys ({}-formatting).

        Using a number results in a call to self.to_str(int(__format_spec)).
        For details concerning the return value see there.

        An empty __format_spec results in a call to self.to_str() without arguments.

        Valid keys are 'prog_name', 'pid', 'exc', 'exc_type', 'exc_text', 
        'tb', 'filename', 'linenum', 'codeline' , 'context' and 'comment'.
        See __init__ for the corresponding value types. 
        Note:
        'exc' yields <exc.__class__.__name__>('<exc>') (type name plus text)
        'exc_type' yields <exc.__class__.__name__>, 'exc_text' yields <exc>. 

        Examples:
            ei = ExcInfo()
            format(ei, "")
            format(ei, "1")
            format(ei, "Exc {exc} in line {linenum}. {comment}")

        Args:
            __format_spec (str): format string as described above

        Returns:
            str: formatted information as described above
        
        Raises:
            KeyError: if used with an invalid key.
        """
        if not __format_spec:
            # return default representation
            return self.to_str()
        if __format_spec in ("0", "1", "2", "3", "4"):
            # return representation according to verbosity level
            return self.to_str(int(__format_spec))
        else:
            # Make "{exc}" return exception type and ('exception text')
            __format_spec = __format_spec.replace("{exc}", "{exc.__class__.__name__}('{exc}')")
            # Allow accessing the exception type only via "{exc_type}"
            __format_spec = __format_spec.replace("{exc_type}", "{exc.__class__.__name__}")
            # Allow accessing the exception type only via "{exc_text}"
            __format_spec = __format_spec.replace("{exc_text}", "{exc}")
            return __format_spec.format(**self.__dict__)

    def __str__(self) -> str:
        return self.to_str()         
           
class LogUtils:
    """ Misc Utils concerning logging and exceptions """

    @classmethod
    def now(cls, datefmt: str="%Y-%m-%d %H:%M:%S") -> str:
        return datetime.now().strftime(datefmt)
    
    @classmethod
    def clear_log_handlers(cls, logger: Logger|None = None) -> Logger:
        """ Remove all log handlers from the given logger.
        If logger is None, user root logger.

        Args:
            logger (Logger | None, optional): logger to use. Defaults to None.

        Returns:
            Logger: the logger used
        """
        if logger is None:
            logger = logging.getLogger() # root logger
        for h in logger.handlers:
            logger.removeHandler(h)
        return logger

    
    @classmethod
    def make_log_record(cls, level: int = logging.NOTSET, 
                        msg: str = "", *args: object,
                        logger: Logger|None = None, 
                        exc_info: BaseException|_SysExcInfoType|bool = False, 
                        extra: Mapping[str, object]|None = None, 
                        stack_info: bool = False,
                        stacklevel: int = 1) -> LogRecord:
        """ Make log record from the given information. The record can either
        be used directly or information can be extracted using the get...(, LogRecord)
        class methods.

        Args:
            level (int): logging level (INFO, DEBUG, ...)
            msg (str): log message
            args: Used together with msg to create the message field of the record (using msg % args)
            logger (Logger, optional): logger to use. Defaults to None (means root logger).
            exc_info (BaseException|_SysExcInfoType|bool, optional): include given exception info 
                (if exc_info is of type BaseException or _SysExcInfoType) or get it 
                from sys.exc_info() (if exc_info == True). Defaults to False.
            extra (Mapping[str, object], optional): additional key-value pairs for the record's __dict__. Defaults to None.
            stack_info (bool, optional): include stack_info?. Defaults to False.
            stacklevel (int, optional): stack level to use. Defaults to 1.

        Returns:
            LogRecord: Record containing information about the current position
            in the program's run, inluding stack and exception information, if wanted
        """
        return cls._make_log_record(level, msg, *args, 
                                    logger=logger, 
                                    exc_info=exc_info, 
                                    extra=extra, 
                                    stack_info=stack_info, 
                                    stacklevel=stacklevel)

    @classmethod
    def get_exc_info(cls, exc_info: LogRecord|BaseException|_SysExcInfoType|None = None) -> ExcInfo:
        """ Get ExcInfo object from information passed in as an argument.
        If no exc_info object is passed in, the function uses sys.exc_info().
        If a LogRecord is passed in which contains a field "comment" (set via
        the "extra" parameter in make_log_record) it is taken as "comment" parameter
        when constructing the ExcInfo object.

        Args:
            exc_info LogRecord|BaseException|sys._OptExcInfo|None, optional): exception information. Defaults to None.

        Returns:
            ExcInfo exception information object
        """
        if isinstance(exc_info, LogRecord):
            if "comment" in exc_info.__dict__:
                return ExcInfo(exc_info.exc_info, exc_info.__dict__["comment"])
            else:
                return ExcInfo(exc_info.exc_info)
        else:
            return ExcInfo(exc_info)

    @classmethod
    def get_caller(cls, lr: LogRecord) -> CallerRecord:
        """ Extract information about the position in the program from 
        the given LogRecord instance.

        Args:
            lr (LogRecord): LogRecord with position information.

        Returns:
            CallerRecord: position information
        """
        return CallerRecord(program_name, lr.process, lr.pathname, 
                            lr.lineno, lr.funcName, lr.stack_info)

    @classmethod
    def find_caller(cls, stack_info: bool=False, stacklevel: int=1) -> CallerRecord:
        """ Return information about the current position in the program's run.

        Args:
            stack_info (bool, optional): include stack info?. Defaults to False.
            stacklevel (int, optional): stack level to use. Defaults to 1.

        Returns:
            CallerRecord: position information
        """
        return cls._find_caller(stack_info, stacklevel)

    @classmethod
    def _make_log_record(cls, level: int, msg: object, *args: object,
                         logger: Logger|None = None, 
                         exc_info: BaseException|_SysExcInfoType|bool = False, 
                         extra: Mapping[str, object]|None = None, 
                         stack_info: bool = False,
                         stacklevel: int = 1):
        """
        Construct LogRecord. The implementaion is taken from logging._log.
        See make_log_record() for details on parameters.
        """
        if logger is None:
            logger = logging.getLogger() # root logger
        sinfo = None
        if _srcfile:
            #IronPython doesn't track Python frames, so findCaller raises an
            #exception on some versions of IronPython. We trap it here so that
            #IronPython can use logging.
            try:
                fn, lno, func, sinfo = logger.findCaller(stack_info, stacklevel)
            except ValueError: # pragma: no cover
                fn, lno, func = "(unknown file)", 0, "(unknown function)"
        else: # pragma: no cover
            fn, lno, func = "(unknown file)", 0, "(unknown function)"
        exc: _SysExcInfoType|None = None
        if exc_info:
            if isinstance(exc_info, BaseException):
                exc = (type(exc_info), exc_info, exc_info.__traceback__)
            elif not isinstance(exc_info, tuple):
                exc = sys.exc_info()
        record = logger.makeRecord(logger.name, level, fn, lno, msg, args,
                                 exc, func, extra, sinfo)
        return record

    @classmethod
    def _find_caller(cls, stack_info=False, stacklevel=1) -> CallerRecord:
        """
        Return caller information. The indirection is necessary to get the
        correct program position. See make_log_record() for details on parameters.
        """
        sinfo = None
        if _srcfile:
            #IronPython doesn't track Python frames, so findCaller raises an
            #exception on some versions of IronPython. We trap it here so that
            #IronPython can use logging.
            try:
                fn, lno, func, sinfo = logging.getLogger().findCaller(stack_info, stacklevel)
            except ValueError: # pragma: no cover
                fn, lno, func = "(unknown file)", 0, "(unknown function)"
        else: # pragma: no cover
            fn, lno, func = "(unknown file)", 0, "(unknown function)"
        return CallerRecord(program_name, program_pid, fn, lno, func, sinfo)


