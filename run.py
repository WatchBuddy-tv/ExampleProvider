# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from Kekik.cli import cikis_yap, hata_yakala
from FastAPI   import HOST, PORT
import uvicorn, subprocess

def run_uvicorn():
    uvicorn.run("FastAPI:app", host=HOST, port=PORT, proxy_headers=True, forwarded_allow_ips="*", workers=1, log_level="info")

def run_gunicorn():
    subprocess.run([
        "gunicorn",
        "-k", "uvicorn.workers.UvicornWorker",
        "FastAPI:app",
        "--log-level", "info",
        "--bind", f"{HOST}:{PORT}",
        "--workers", "2",
        "--keep-alive", "5",
        "--worker-tmp-dir", "/dev/shm",
        "--max-requests", "10000", "--max-requests-jitter", "1000"
    ], check=True)

if __name__ == "__main__":
    try:
        run_uvicorn()
        cikis_yap(False)
    except Exception as error:
        hata_yakala(error)
