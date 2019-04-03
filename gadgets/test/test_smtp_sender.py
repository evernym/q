import asyncio
import pytest
from unittest.mock import patch, call

import helpers
import smtp_sender


@pytest.mark.asyncio
async def test_smtp_send():
    # Mock the class that imap_receiver creates when it builds an imap session.
    with patch('smtp_sender.smtplib.SMTP', autospec=True) as patched:
        # patched.return_value = the mock that's returned from the constructor
        # of the class.
        mock = patched.return_value
        sender = smtp_sender.Sender(smtp_sender.EXAMPLE)
        await sender.send(b'hello')
        mock.starttls.assert_called_once()
        mock.login.assert_called_once()
        mock.sendmail.assert_called_once()
        mock.quit.assert_called_once()


if __name__ == '__main__':
    asyncio.get_event_loop().set_debug(True)
    pytest.main(['-k', 'smtp'])