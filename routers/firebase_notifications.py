import firebase_admin
from firebase_admin import credentials, messaging

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