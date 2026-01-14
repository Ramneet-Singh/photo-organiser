from __future__ import annotations

from types import ModuleType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from photo_organiser.config.settings import Settings

AppFixture = tuple["Settings", ModuleType, ModuleType]


def test_database_create_and_connect(app: AppFixture) -> None:
    _settings, db_mod, _service_mod = app

    db_mod.create_database()

    assert db_mod.db_manager.check_connection() is True
