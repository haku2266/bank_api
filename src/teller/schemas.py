from datetime import datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from pydantic import BaseModel, Field, field_validator, EmailStr, ConfigDict, Extra
import re
import phonenumbers

from src.auth.schemas import UserListSchema

