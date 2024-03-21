from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import fastapi.openapi.utils as fu
from src.auth import routers as auth_routers
from src.bank import routers as bank_routers
from src.account import routers as account_routers
from src.teller import routers as teller_routers
from src.loan import routers as loan_routers

app = FastAPI()

app.include_router(auth_routers.router)
app.include_router(bank_routers.router)
app.include_router(account_routers.router)
app.include_router(teller_routers.router)
app.include_router(loan_routers.router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    detail = {str(error["loc"][1]): error["msg"].lower() for error in exc.errors()}
    return JSONResponse(
        status_code=422,
        content={"detail": detail},
    )


fu.validation_error_response_definition = {
    "title": "HTTPValidationError",
    "type": "object",
    "properties": {
        "detail": {
            "title": "Message",
            "type": "object",
            "properties": {
                "error1_location": {"type": "string"},
                "error2_location": {"type": "string"},
            },
        }
    },
}
