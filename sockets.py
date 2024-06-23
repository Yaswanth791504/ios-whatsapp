import socketio

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
sio_app = socketio.ASGIApp(sio)


connected_users = {}

@sio.event
async def connect(sid, environ):
    print(f'User connected: {sid}')
    # print(environ)
    user_id = environ.get('HTTP_USER_ID')

    connected_users[user_id] = sid
    print(connected_users)

@sio.event
async def disconnect(sid):
    print(f'User disconnected: {sid}')
    
    user_id = next((k for k, v in connected_users.items() if v == sid), None)
    if user_id:
        del connected_users[user_id]

    print(connected_users)

@sio.event
async def send_message(sid, data):
    print(f'Received message from {sid}: {data}')
    recipient_id = data['recipient_id']
    message = data['message']
    print(recipient_id)

    
    recipient_sid = connected_users.get(recipient_id)
    if recipient_sid:
        await sio.emit('receive_message', data, room=recipient_sid)
    else:
        print(f'Recipient {recipient_id} not connected')


