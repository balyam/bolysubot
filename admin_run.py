"""
Запуск веб-админки
"""
import uvicorn
from app.admin.app import create_admin_app

if __name__ == "__main__":
    app = create_admin_app()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )

