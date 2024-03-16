from fastapi import FastAPI
from src.auth import routers as auth_routers
from src.bank import routers as bank_routers

app = FastAPI()

app.include_router(auth_routers.router)
app.include_router(bank_routers.router)
