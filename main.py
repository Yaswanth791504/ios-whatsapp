from fastapi import FastAPI, HTTPException
from routers.userRoute import router as userRouter
from routers.messageRoutes import router as messageRouter
from routers.statusRoutes import router as statusRouter
from routers.callRoutes import router as callRouter
from routers.groupRoutes import router as groupRouter
import subprocess
import os
from sockets import sio_app
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json

app = FastAPI()

@app.post("/migrate")
def migrate_db():
    local_conn_details = {
        'dbname': 'postgres',
        'user': 'postgres',
        'password': 'yaswanth',
        'host': 'localhost',
        'port': '5432'
    }

    render_conn_details = {
        'dbname': 'whatsapp_ga3f',
        'user': 'whatsapp_ga3f_user',
        'password': 'F6jkr9CTaO2ojq9ADns8BlnJdC4frTqX',
        'host': 'dpg-cps6gqg8fa8c7392fjc0-a.oregon-postgres.render.com',
        'port': '5432'
    }

    local_backup_file = 'local_backup.dump'

    try:
        # Dump the local database without ownership information
        dump_command = [
            'C:\\Program Files\\PostgreSQL\\16\\bin\\pg_dump',
            '-h', local_conn_details['host'],
            '-p', local_conn_details['port'],
            '-U', local_conn_details['user'],
            '-d', local_conn_details['dbname'],
            '-F', 'c',
            '--no-owner',  # Exclude ownership information
            '-b',
            '-f', local_backup_file
        ]

        env = os.environ.copy()
        env['PGPASSWORD'] = local_conn_details['password']

        result = subprocess.run(dump_command, check=True, capture_output=True, env=env)
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"pg_dump error: {result.stderr.decode()}")

        # Restore the dump to the Render database, dropping objects if they exist
        restore_command = [
            'C:\\Program Files\\PostgreSQL\\16\\bin\\pg_restore',
            '-h', render_conn_details['host'],
            '-p', render_conn_details['port'],
            '-U', render_conn_details['user'],
            '-d', render_conn_details['dbname'],
            '--clean',         # Drop objects before creating them
            '--if-exists',     # Only drop if they exist
            '--no-owner',      # Ignore ownership during restore
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

# Include routers for various routes
app.include_router(router=userRouter)
app.include_router(router=messageRouter)
app.include_router(router=statusRouter)
app.include_router(router=callRouter)
app.include_router(router=groupRouter)

# Mount the socket.io application
app.mount("/", app=sio_app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)





if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    # uvicorn.run('main:app', host="0.0.0.0",port=port, reload=True)
    uvicorn.run('main:app', port=port, reload=True)
