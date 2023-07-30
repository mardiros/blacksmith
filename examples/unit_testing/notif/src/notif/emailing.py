import abc
import email as emaillib
import smtplib
from email.message import Message
from textwrap import dedent
from typing import Tuple

from notif.resources.user import User

from blacksmith.sd._async.adapters.consul import AsyncConsulDiscovery


class AbstractEmailSender(abc.ABC):
    async def __call__(self, user: User, message: str):
        email_content = dedent(
            f"""\
            Subject: notification
            From: notification@localhost
            To: "{user.firstname} {user.lastname}" <{user.email}>

            {message}
            """
        )
        message = emaillib.message_from_string(email_content)
        addr, port = await self.get_endpoint()
        await self.sendmail(addr, port, message)

    async def sendmail(self, addr: str, port: int, message: Message):

        # XXX Synchronous socket here, OK for the example
        # real code should use aiosmtplib
        s = smtplib.SMTP(addr, port)
        s.send_message(message)
        s.quit()

    @abc.abstractmethod
    async def get_endpoint(self) -> Tuple[str, int]:
        pass


class EmailSender(AbstractEmailSender):
    def __init__(self, sd: AsyncConsulDiscovery):
        self.sd = sd

    async def get_endpoint(self) -> Tuple[str, int]:
        endpoint = await self.sd.resolve("smtp", None)
        return endpoint.address, endpoint.port
