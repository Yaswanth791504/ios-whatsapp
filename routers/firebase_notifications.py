import firebase_admin
from firebase_admin import credentials, messaging
import json
import os

dictionary = {
    "project_id": os.environ.get("FIREBASE_PROJECT_ID"),
    "private_key_id": os.environ.get("FIREBASE_PRIVATE_KEY_ID"),
    "private_key": os.environ.get("FIREBASE_PRIVATE_KEY").replace('\\n', '\n'),
    "client_email": os.environ.get("FIREBASE_CLIENT_EMAIL"),
    "client_id": os.environ.get("FIREBASE_CLIENT_ID"),
    "client_x509_cert_url": os.environ.get("FIREBASE_CLIENT_X509_CERT_URL"),
}

# Fetch the service account key JSON file contents
with open('./firebase-key.json') as f:
    dicti = json.load(f)
    dictionary.update(dicti)

# Initialize the app with a service account, granting admin privileges
with open('./firebase-key.json', 'w') as f:
    json.dump(dictionary, f)









cred = credentials.Certificate("./firebase-key.json")
firebase_admin.initialize_app(cred)

def send_call_ring(token, title, body, photo, call_id, type):
    print(call_id)
    print("=====================================")
    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        token=token,
        android=messaging.AndroidConfig(
            notification=messaging.AndroidNotification(
                icon='stock_ticker_update',
                color='#f45342',
                click_action='FLUTTER_NOTIFICATION_CLICK',
                image=photo
            )
        ),
        apns=messaging.APNSConfig(
            payload=messaging.APNSPayload(
                aps=messaging.Aps(
                    badge=42,
                ),
            ),
        ),
        data={
            'call_id': call_id,
            "type": type
        }
    )

    response = messaging.send(message)
    print('Successfully sent call:', response)

def send_message_notificaiton(token, title, body, photo):
    try :
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            token=token,
            android=messaging.AndroidConfig(
                notification=messaging.AndroidNotification(
                    icon='stock_ticker_update',
                    color='#f45342',
                    click_action='FLUTTER_NOTIFICATION_CLICK',
                    image=photo
                )
            ),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        badge=42,
                    ),
                ),
            ),
            data={
                'type': 'message'
            }
        )

        response = messaging.send(message)
        print('Successfully sent message:', response)
    except Exception as e:
        print(e)
        print('Failed to send message')