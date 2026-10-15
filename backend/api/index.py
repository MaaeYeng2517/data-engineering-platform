"""Vercel serverless entry point for DataAir API.

On Vercel, the backend directory becomes the deployment root, so modules
like `config.py` and `app/` sit at /var/task/ rather than /var/task/backend/.
We create a `backend` package alias so all `backend.*` imports resolve.
"""
import os
import sys
import types

_deploy_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _deploy_root)

_backend = types.ModuleType("backend")
_backend.__path__ = [_deploy_root]
sys.modules["backend"] = _backend

from backend.main import app, lifespan  # noqa: E402

__all__ = ["app"]
