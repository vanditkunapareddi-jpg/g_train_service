"""NextStop — application package.

This package holds the backend logic for the project:

- ``config``        : feed URLs and small app-wide settings
- ``models``        : Pydantic data models (custom lines + stations)
- ``storage``       : local JSON file storage for custom lines
- ``mta``           : GTFS-realtime feed fetching and parsing
- ``routes``        : FastAPI routers (arrivals + custom lines)
"""

__version__ = "1.0.0"
