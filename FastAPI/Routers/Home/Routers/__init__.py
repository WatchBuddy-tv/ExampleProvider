# This tool was written by @keyiflerolsun | for @KekikAkademi

from FastAPI import APIRouter

home_router = APIRouter(prefix="")

from . import home
