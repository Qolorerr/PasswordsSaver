from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib


def send_password(email, site, password):
    message = "PasswordsSaver\r\nSITE: {}\r\nPASSWORD: {}\r\nIf it’s not you, then it’s worth considering".format(site,
                                                                                                                  password)
    subject = "Access to password"
    send_mail(email, subject, message)


def send_mail(email, subject, message):
    msg = MIMEMultipart()
    password = "dankurmihiva"
    msg['From'] = "ps.access54@gmail.com"
    msg['To'] = email
    msg['Subject'] = subject
    msg.attach(MIMEText(message, 'plain'))
    server = smtplib.SMTP('smtp.gmail.com: 587')
    server.starttls()
    server.login(msg['From'], password)
    server.sendmail(msg['From'], msg['To'], msg.as_string())
    server.quit()
    print("successfully sent email to %s:" % (msg['To']))
