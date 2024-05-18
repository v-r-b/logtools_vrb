from __future__ import annotations
import logging, ssl, socket

from mailtools_vrb import EasySSLSendmail
from logtools_vrb import program_name, ExcInfo

from typing import TYPE_CHECKING 
if TYPE_CHECKING: 
    from _typeshed import FileDescriptorOrPath as FileDescriptorOrPath

# get fqdn and hostname of localhost
_fqdn = socket.getfqdn()
_hostname = _fqdn.split(".", 1)[0]
# get name of currently running program from command line parameter 0

class MailLogHandler(logging.Handler):
    """ Log handler which mails log messages to a given recipient.
    """    

    LOG_ALWAYS = logging.CRITICAL+1
    """ Log level to be used for messages that shall be sent in any case, even
    if logging has been disabled by calling logging.disable(), since the default 
    argument to logging.disable() is CRITICAL and LOG_ALWAYS is CRITICAL+1.
    Can be disabled by calling logging.disable(MailLogHandler.LOG_ALWAYS) """

    DEFLT_SUB_START_FMT: str = '[%(fqdn)s] %(program)s: '
    """ Default format string for start portion of the mail subject """

    def __init__(self, mail_to: str, *,
                 json_mail_info: dict|FileDescriptorOrPath|None = None,
                 host: str|None = None, port: int|None = None, 
                 ssl_context: ssl.SSLContext|None = None,
                 user: str|None = None, password: str|None = None, 
                 sender: str|None = None, minpause: int|None = None,
                 level: int|str = logging.NOTSET,
                 sub_start_fmt: str = DEFLT_SUB_START_FMT,
                 add_log_always_level: int = True) -> None:
        """ Constructor.

        Args:
            mail_to (str): receiver address for log mails
            level (int | str, optional): minimum level for log message output. Defaults to logging.NOTSET.
            sub_start_fmt (str, optional): Format string for start portion of the mail subject. This
                will be followed by a speficic message. Inside the format string, all LogRecord attributes,
                plus %(host)s, %(fqdn)s and %(program)s can be used. Defaults to DEFLT_SUB_START_FMT.
            add_log_always_level (bool, optional): Add level "LOG_ALWAYS" to logging. Defaults to True.
            any other: see EasySSLSendmail.make_credentials_dict()
            
            Specific arguments overwrite items from file or dict. Any combination of dict/file
            and arguments can be used and must provide mail_to, host, port, user, password.
            Optional arguments: sender, ssl_context, minpause, level.
        """
        # Evaluate arguments and store values in a dictionary
        self._credentials = EasySSLSendmail.make_credentials_dict(
                                    json_mail_info=json_mail_info,
                                    host=host, port=port, minpause=minpause,
                                    user=user, password=password, sender=sender)
        self._ssl_context = ssl_context
        self._mail_to = mail_to
        # Fill in additional fields program, host and fqdn.
        # Any other formatting will be done in emit() method
        self._sub_start_fmt = sub_start_fmt.replace("%(program)s", program_name).\
                              replace("%(host)s", _hostname).replace("%(fqdn)s", _fqdn)
        if add_log_always_level:
            logging.addLevelName(MailLogHandler.LOG_ALWAYS, "LOG_ALWAYS")
        super().__init__(level)

    def emit(self, lr: logging.LogRecord):
        """ Format subject and mail message.
        If lr.msg is of type BaseException or ExcInfo, the exception information
        contained will be included into the mail subject and body, regardless of
        the value of lr.exc_info (e.g. if log() was called without exc_info=True).

        Args:
            lr (logging.LogRecord): data to be formatted
        """
        # let Formatter format the message from the LogRecord
        formatted_msg = self.format(lr)

        # base versions of mail subject and body
        mail_subject = self._sub_start_fmt % lr.__dict__
        mail_msg = lr.msg

        # if we got a BaseException as mail_msg, get corresponding ExcInfo object:
        if isinstance(mail_msg, BaseException):
            mail_msg = ExcInfo(mail_msg)

        # format message, depending on the values of msg and exc_info
        if isinstance(mail_msg, ExcInfo):
            # Subject is program name, "[EXC] tag and exception info"
            mail_subject += f"[EXC] {mail_msg.to_str(1)}"
            # Mail body is full exception information incl. stack trace
            formatted_msg = mail_msg.to_str(4)
        else:
            if not lr.exc_info:
                # No exception -> subject == <start portion>: lr.message
                # lr.message contains the result of lr.msg % lr.args from log call,
                # but no formatting done by the Formatter
                mail_subject += lr.message
            else:
                # if exc_info is not None, the formatted message already includes the stack trace.
                #
                # Subject is program name: "[EXC]" tag, lr.message and exception info
                # lr.message contains the result of lr.msg % lr.args from log call,
                # but no formatting done by the Formatter
                ei = ExcInfo(lr.exc_info)
                mail_subject += f"[EXC] {lr.message} -- {ei.to_str(1)}"
                # Mail body is full exception information w/o stack trace
                # plus formatted message (incl. stack trace)
                formatted_msg = f"{ei.to_str(3)}\n\n{formatted_msg}"

        # Send mail using server and login information from the constructor
        with EasySSLSendmail(json_mail_info=self._credentials, 
                             ssl_context=self._ssl_context) as mailserver:
            mailserver.login()
            mailserver.send_mail_message(mail_subject, self._mail_to, formatted_msg)

#################################################
# Sample usage:
#################################################

if False:
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)
    mlh = MailLogHandler("webmaster@buerckel.de", "../sample_files/mail_credentials.json")
    logger.addHandler(mlh)
    logger.info("Test")
