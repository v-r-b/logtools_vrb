import logging
from time import sleep
from logtools_vrb import LogUtils, MailLogHandler

# file mail_credentials.json: fill in correct information first!
filePath = "tests/mail_credentials.json"
# use correct address for email receiver
receiver = "me@mydomain.com"

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
# create MailLogHandler
mlh = MailLogHandler(receiver, json_mail_info=filePath)
# register as additional log handler with logger
logger.addHandler(mlh)

# emit log message via e-mail
logger.info("Test")

sleep(3)
# Send mail in case of an exception
try:
    a = 10 / 0
except:
    logger.error(f"[{LogUtils.get_exc_info()}] when dividing a number by zero", exc_info=True)
