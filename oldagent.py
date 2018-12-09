
import asyncio
import time
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from indy import crypto, did, wallet


async def prep(wallet_handle, my_vk, their_vk, msg):
    with open('plaintext.txt', 'w') as f:
        f.write(msg)
    with open('plaintext.txt', 'rb') as f:
        msg = f.read()
    print("wallet handle: ", wallet_handle)
    print("my_vk: ", my_vk)
    print("their vk: ", their_vk)
    print("msg: ", type(msg), msg)
    encrypted = await crypto.anon_crypt(their_vk, msg)
    # encrypted = await crypto.anon_crypt(their_vk, msg)
    print('encrypted = %s' % repr(encrypted))

    print("message sent")
    with open('encrypted.dat', 'wb') as f:
        f.write(bytes(encrypted))
    print('prepping %s' % msg)
    send(msg)


def send(msg):
    fromaddr="chondool@gmail.com"
    toaddr="ikhyeon.jeon@evernym.com"

    # instance of MIMEMultipart
    emailToSend = MIMEMultipart()

    # storing the senders email address
    emailToSend['From'] = fromaddr

    # storing the receivers email address
    emailToSend['To'] = toaddr

    # storing the subject
    emailToSend['Subject'] = "Subject of the Mail"

    msg = "Check the attached file"
    body = msg
    print(msg)

    # attach the body with the msg instance
    emailToSend.attach(MIMEText(body, 'plain'))

    # open the file to be sent
    filename = "encrypted.dat"
    attachment = open(filename, "rb")

    # instance of MIMEBase and named as p
    p = MIMEBase('application', 'octet-stream')

    # To change the payload into encoded form
    p.set_payload((attachment).read())

    # encode into base64
    encoders.encode_base64(p)

    p.add_header('Content-Disposition', "attachment; filename= %s" % filename)

    # attach the instance 'p' to instance 'msg'
    emailToSend.attach(p)

    # creates SMTP session
    s = smtplib.SMTP('smtp.gmail.com', 587)

    # start TLS for security
    s.starttls()

    # Authentication
    s.login(fromaddr, "use your own password")

    # Converts the Multipart msg into a string
    text = emailToSend.as_string()

    # sending the mail
    s.sendmail(fromaddr, toaddr, text)

    # terminating the session
    s.quit()


async def init():
    me = input('Who are you? ').strip()
    wallet_config = '{"id": "%s-wallet"}' % me
    wallet_credentials = '{"key": "%s-wallet-key"}' % me

    # 1. Create Wallet and Get Wallet Handle
    try:
        await wallet.create_wallet(wallet_config, wallet_credentials)
    except:
        pass
    wallet_handle = await wallet.open_wallet(wallet_config, wallet_credentials)
    print('wallet = %s' % wallet_handle)

    (my_did, my_vk) = await did.create_and_store_my_did(wallet_handle, "{}")
    print('my_did and verkey = %s %s' % (my_did, my_vk))

    their = input("Other party's DID and verkey? ").strip().split(' ')
    return wallet_handle, my_did, my_vk, their[0], their[1]


async def read(wallet_handle, my_vk):
    with open('encrypted.dat', 'rb') as f:
        encrypted = f.read()
    print("wallet handle: ", wallet_handle)
    print("my_vk: ", my_vk)
    print("encrypted: ", encrypted)
    # print("msg: ", msg)
    decrypted = await crypto.auth_decrypt(wallet_handle, my_vk, encrypted)
    # decrypted = await crypto.anon_decrypt(wallet_handle, my_vk, encrypted)
    print(decrypted)


async def demo():
    wallet_handle, my_did, my_vk, their_did, their_vk = await init()

    while True:
        argv = input('> ').strip().split(' ')
        cmd = argv[0].lower()
        rest = ' '.join(argv[1:])
        if re.match(cmd, 'prep'):
            await prep(wallet_handle, my_vk, their_vk, rest)
            # await send(rest)
        elif re.match(cmd, 'read'):
            await read(wallet_handle, my_vk)
        elif re.match(cmd, 'quit'):
            break
        else:
            print('Huh?')


if __name__ == '__main__':
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(demo())
        time.sleep(1)  # waiting for libindy thread complete
    except KeyboardInterrupt:
        print('')
