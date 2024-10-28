import yagmail
import smtplib
import email
from email.header import decode_header
import imaplib

def main():
    user = "" #ADD CREDENTIALS
    password = "" 
    sender(user, password, "Smart Home System", "whatisiot1@gmail.com", "Sent with python")
    receiver(user, password)
    
def sender(sender_email, sender_pass, subject, receiver_email, body):
    
    try: 
        yag = yagmail.SMTP(sender_email, sender_pass)
        yag.send(to=receiver_email, subject=subject,contents=body)
        print("Sent Email: ")
    except Exception as e: 
        print(e)
        
def receiver(receiver_email, password):
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(receiver_email, password)
        mail.select('inbox') 
        
        status, data = mail.search(None, 'ALL')
        email_ids = data[0].split()
        
        if email_ids:  
            latest_email_id = email_ids[-1] 
            
            status, data = mail.fetch(latest_email_id, '(RFC822)')
            raw_email = data[0][1]
            
            msg = email.message_from_bytes(raw_email)
            
            subject, encoding = decode_header(msg.get("Subject", ""))[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding if encoding else "utf-8")
            else:
                subject = subject or "No Subject"
            
            from_ = msg.get("From", "Unknown Sender")
            
            print(f"Subject: {subject}")
            print(f"From: {from_}")
            print()
            
            body = None
            
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))
                    
                    if "attachment" not in content_disposition:
                        body = part.get_payload(decode=True)
                        if body:
                            try:
                                body = body.decode()
                            except UnicodeDecodeError:
                                body = "Cannot decode body content"
                            break
            else:
                body = msg.get_payload(decode=True)
                if body:
                    try:
                        body = body.decode()
                    except UnicodeDecodeError:
                        body = "Cannot decode body content"
            
            print(f"Body: {body}")
        
        else:
            print("No emails found.")
            
        mail.logout() 
    
    except Exception as e:
        print(f"An error occurred: {e}")
    
if __name__ == '__main__':
    main()