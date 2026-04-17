from typing import TYPE_CHECKING

import gunicorn.app.base
from werkzeug.middleware.proxy_fix import ProxyFix

from .app import app

if TYPE_CHECKING:
    from flask import Flask


app.wsgi_app = ProxyFix(app.wsgi_app)

class Application(gunicorn.app.base.BaseApplication):
    def load_config(self) -> None:
        self.cfg.set('bind', '0')
    def load(self) -> Flask:
        return app


application = Application()
