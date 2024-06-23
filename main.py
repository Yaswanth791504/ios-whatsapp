from fastapi import FastAPI, HTTPException # type: ignore
from routers.userRoute import router as userRouter
from routers.messageRoutes import router as messageRouter
from routers.statusRoutes import router as statusRouter
from routers.callRoutes import router as callRouter
from routers.groupRoutes import router as groupRouter
import psycopg2
import uvicorn
import os 
import subprocess
from sockets import sio_app
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

@app.post("/migrate")
def migrate_db():
    local_conn_details = {
        'dbname': 'WhatsappDatabase',
        'user': 'postgres',
        'password': 'yaswanth',
        'host': 'localhost',
        'port': '5432'
    }

    render_conn_details = {
        'dbname': 'ios_whatsapp',
        'user': 'ios_whatsapp_user',
        'password': 'RCRvGbKKe8Z9G1Y8rm5rYGkZfGF9aFJf',
        'host': 'dpg-cporqtqju9rs738v5000-a.oregon-postgres.render.com',
        'port': '5432'
    }

    local_backup_file = 'local_backup.dump'

    try:
        dump_command = [
            'pg_dump',
            '-h', local_conn_details['host'],
            '-p', local_conn_details['port'],
            '-U', local_conn_details['user'],
            '-d', local_conn_details['dbname'],
            '-F', 'c',
            '-b',
            '-f', local_backup_file
        ]
        
        env = os.environ.copy()
        env['PGPASSWORD'] = local_conn_details['password']
        
        result = subprocess.run(dump_command, check=True, capture_output=True, env=env)
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"pg_dump error: {result.stderr.decode()}")

        restore_command = [
            'pg_restore',
            '-h', render_conn_details['host'],
            '-p', render_conn_details['port'],
            '-U', render_conn_details['user'],
            '-d', render_conn_details['dbname'],
            '-F', 'c',
            local_backup_file
        ]
        
        env['PGPASSWORD'] = render_conn_details['password']
        
        result = subprocess.run(restore_command, check=True, capture_output=True, env=env)
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"pg_restore error: {result.stderr.decode()}")

    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Error during migration: {e.stderr.decode()}")
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"Executable not found: {e}")

    return {"status": "migration completed"}



app.include_router(router=userRouter)
app.include_router(router=messageRouter)
app.include_router(router=statusRouter)
app.include_router(router=callRouter)
app.include_router(router=groupRouter)

app.mount("/", app=sio_app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run('main:app',port=port, reload=True)
    # uvicorn.run('main:app', host="0.0.0.0", port=port, reload=True)