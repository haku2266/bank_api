from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import fastapi.openapi.utils as fu
from src.auth import routers as auth_routers
from src.bank import routers as bank_routers
from src.account import routers as account_routers
from src.teller import routers as teller_routers
from src.loan import routers as loan_routers

from sqladmin import Admin, ModelView

from src.database import async_engine


# Admin panel
from src.auth.models import User
from src.bank.models import Bank
from src.account.models import Account, Deposit, Withdraw
from src.teller.models import Teller
from src.loan.models import Loan, LoanType, LoanCompensation

app = FastAPI()
admin = Admin(app, async_engine)


class BankAdmin(ModelView, model=Bank):
    column_list = [Bank.id, Bank.name]


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.name]


class AccountAdmin(ModelView, model=Account):
    column_list = [Account.id]


class DepositsAdmin(ModelView, model=Deposit):
    column_list = [Deposit.id, Deposit.account_id]


class WithdrawsAdmin(ModelView, model=Withdraw):
    column_list = [Withdraw.id, Withdraw.account_id]


class TellerAdmin(ModelView, model=Teller):
    column_list = [Teller.id, Teller.user_id]


class LoanAdmin(ModelView, model=Loan):
    column_list = [Loan.id, Loan.account_id]


class LoanTypeAdmin(ModelView, model=LoanType):
    column_list = [LoanType.id, LoanType.name]


class LoanCompensationAdmin(ModelView, model=LoanCompensation):
    column_list = [LoanCompensation.id, LoanCompensation.loan_id]


admin.add_view(UserAdmin)
admin.add_view(AccountAdmin)
admin.add_view(DepositsAdmin)
admin.add_view(WithdrawsAdmin)
admin.add_view(TellerAdmin)
admin.add_view(LoanAdmin)
admin.add_view(LoanCompensationAdmin)
admin.add_view(LoanTypeAdmin)
admin.add_view(BankAdmin)


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
