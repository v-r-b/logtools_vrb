from __future__ import annotations

import typing
import logging
from logging import LogRecord, Logger, Handler, Formatter

from logtools_vrb import program_name

class LevelAwareFormatter(Formatter):
    """ Formatter for use with the logging module supporting
    different format strings depending on the log level.

    For log attributes, see here:
    https://docs.python.org/3/library/logging.html
    """
    SIMPLE_FMT = program_name + '[%(process)d]: %(name)s - %(message)s'
    """ Format string for simple debug output (for use with % style formatting) """
    QUALIFIED_FMT = program_name + '[%(process)d]: [%(levelname)s] %(name)s - %(message)s ' \
                    + 'in %(funcName)s, line %(lineno)d (file %(pathname)s)'
    """ Format string for output including position information (for use with % style formatting) """

    DEFAULT_LEVEL_FORMATS = {
                    logging.NOTSET: SIMPLE_FMT,
                    logging.DEBUG: SIMPLE_FMT,
                    logging.INFO: SIMPLE_FMT,
                    logging.WARNING: QUALIFIED_FMT,
                    logging.ERROR: QUALIFIED_FMT,
                    logging.CRITICAL: QUALIFIED_FMT
                }
    """ Default format strings for known log levels (for use with % style formatting)"""

    def __init__(self,  default_fmt: str|None=SIMPLE_FMT, datefmt: str|None=None, 
                        style: typing.Literal['%', '{', '$']='%', validate: bool=True, *,
                        level_fmts: dict|None=None, defaults: dict|None=None):
        """ Constructor. For details on arguments see logging.Formatter class.
        Pass different format strings depending on the log level as a dictionary, e.g.: 
        {
            logging.INFO: "%(name)s - %(message)s",
            logging.WARNING: "%(processName)s[%(process)d]: %(name)s - %(message)s"
        }. The formatting style is determined by the style parameter. Additional format
        strings may be added later by using set_level_format()

        Args:
            fmt (str, optional): default format string. Defaults to SIMPLE_FMT.
            datefmt (str, optional): time format string. Defaults to None.
            style (str, optional): use '%', '{' or '$' to specify the formatting style. Defaults to '%'
            validate (bool, optional): If True (the default), incorrect or mismatched fmt and style will raise a ValueError
            level_fmts (dict, optional): level specific format strings. If not
                given (is None), and if style is "%", then use DEFAULT_LEVEL_FORMATS.
            defaults (dict[str, Any], optional) – a dictionary with default values to use in custom 
                fields. For example, LevelFormatter('%(ip)s %(message)s', defaults={"ip": None})

        Raises:
            ValueError (see validate parameter)
        """
        self._default_mappings: dict|None = defaults
        self._formatters: dict[int, Formatter] = {}

        # If no format dict ist passed, use defaults in case of % style formatting
        if level_fmts is None and style == "%":
            level_fmts = LevelAwareFormatter.DEFAULT_LEVEL_FORMATS.copy()
        # For each level and corresponding format string, 
        # create a Formatter object and store it in _formatters[lvl]
        if level_fmts is not None:
            for lvl, fmt in level_fmts.items():
                self._formatters[lvl] = Formatter(fmt, datefmt, style, validate, 
                                                  defaults=self._default_mappings)
        # default_fmt will be used, if theres no level specific formatter
        super().__init__(default_fmt, datefmt, style, validate, defaults=self._default_mappings)

    def set_level_formatter(self, level: int, fmt: str, datefmt: str|None=None, 
                            style: typing.Literal['%', '{', '$']='%', validate: bool=True):
        """ Set format string for a specific level. Default values for
        custom mappings are taken from the constructor's "defaults" argument.

        Args:
            level (int): log level (logging.INFO, logging.DEBUG etc.)
            fmt (str): format string (fmt argument for Formatter)
            datefmt (str, optional): date format (datefmt argument for Formatter). Defaults to None.
            style (str, optional): use '%', '{' or '$' to specify the formatting style. Defaults to '%'
            validate (bool, optional): If True (the default), incorrect or mismatched fmt and style will raise a ValueError
        """
        # create a new Formatter object and store it in _formatters[level]
        self._formatters[level] = logging.Formatter(
                                fmt, datefmt, style, validate, 
                                defaults=self._default_mappings)

    def remove_level_formatter(self, level: int):
        """ Remove formater for a specific level. As a result of this operation, messages
        of the specified format will then be formatted with the default formatter.

        Args:
            level (int): log level (logging.INFO, logging.DEBUG etc.)
        """
        # remove Formatter object from _formatters[level]. 
        if level in self._formatters:
            self._formatters.pop(level)

    def apply_to(self, handler: Handler, *,
                 logger: Logger|None = None) -> LevelAwareFormatter:
        """ Sets self as the formatter for the given handler.
        If a logger is given as well, the handler is added to the logger.

        Args:
            handler (Handler): handler for which to set the formatter.
            logger (Logger, optional): logger to which the handler shall be added. Defaults to None.

        Returns:
            LevelAwareFormatter: self
        """
        handler.setFormatter(self)
        if logger is not None:
            logger.addHandler(handler)
        return self
        
    def format(self, record: LogRecord) -> str:
        """ Call log level specific formatter or, if there's
        none, use the default formatter by calling super().format().

        For more details see Formatter.format() """
        if record.levelno in self._formatters:
            return self._formatters[record.levelno].format(record)
        else:
            return super().format(record)
