## Notes

### `__init__.py`

Python 3.3+ supports namespace packages, so `__init__.py` is no longer required in every directory. In this project, `__init__.py` will only be added to directories that need to expose package-level imports or package initialization logic. This keeps the project cleaner while preserving flexibility.

### `favicon.ico` 404

When a browser opens the API URL, it automatically requests `/favicon.ico` for the tab icon. Since the backend currently does not serve a favicon, FastAPI correctly returns `404 Not Found`. This is expected behavior and does not indicate an application error. The favicon will be provided later by the frontend or a static file server.

