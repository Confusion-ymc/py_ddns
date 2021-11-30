import pathlib
from email.header import Header
import smtplib
from email.mime.text import MIMEText
import configparser

from logger import log

from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr

import smtplib


def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr((Header(name, 'utf-8').encode(), addr))


def send(content):
    config_path = 'config'

    conf = configparser.ConfigParser()
    conf.read(pathlib.Path().cwd() / config_path)
    address = conf.get('EMAIL', 'address', fallback=None)
    secret_code = conf.get('EMAIL', 'secret_code', fallback=None)
    if not (address and secret_code):
        return

    from_addr = address
    password = secret_code
    to_addr = address
    smtp_server = 'smtp.qq.com'

    msg = MIMEText(content, 'plain', 'utf-8')
    msg['From'] = _format_addr('我多透明 <%s>' % from_addr)
    msg['To'] = _format_addr('我多透明 <%s>' % to_addr)
    msg['Subject'] = Header('DDNS通知', 'utf-8').encode()

    server = smtplib.SMTP_SSL(smtp_server, 465)
    try:
        server.login(from_addr, password)
        server.sendmail(from_addr, [to_addr], msg.as_string())
        log.info("邮件发送成功")
    except Exception as e:
        print(f"邮件发送失败 {e}")
    finally:
        server.quit()
