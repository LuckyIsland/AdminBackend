from flask_mail import Mail
from flask_mail import Message

from configs import MailConfig


def singleton(class_):
    class class_w(class_):
        _instance = None
        def __new__(class_, *args, **kwargs):
            if class_w._instance is None:
                class_w._instance = super(class_w,
                                    class_).__new__(class_,
                                                    *args,
                                                    **kwargs)
                class_w._instance._sealed = False
            return class_w._instance
        def __init__(self, *args, **kwargs):
            if self._sealed:
                return
            super(class_w, self).__init__(*args, **kwargs)
            self._sealed = True
    class_w.__name__ = class_.__name__
    return class_w

@singleton
class MailHelper(object):
    def __init__(self, application):
        self.application = application
        self.mail = Mail(application)

    def send_code(self, to, code):
        subject = 'Code to authorize.'
        sender = 'LuckyIsland'
        body = 'Your code is {0}'.format(code)
        msg = Message(subject, sender=sender, recipients=[to], body=body)
        with self.application.app_context():
            self.mail.send(msg)

    def send_email(self, subject, sender, text_body, recipients, html_body = None):
        msg = Message(subject, sender=sender, recipients=recipients)
        msg.body = text_body
        msg.html = html_body
        with self.application.app_context():
            self.mail.send(msg)

def init_mail(application):
    application.config = dict(MailConfig, **application.config)
    mail_helper = MailHelper(application)
#    mh.send_email('Test subj', 'LuckyIsland', 'Test body', ['ya.super.vladik@gmail.com'])
