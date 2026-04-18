import sys
from difflib import unified_diff
from typing import TYPE_CHECKING

from sqlalchemy.schema import CreateTable, MetaData, Table

from .app import app, db
from .models import Base

if TYPE_CHECKING:
    from collections.abc import Sequence


def main() -> None:
    with app.app_context():
        database = MetaData()
        database.reflect(db.engine)

        models = Base.metadata

        database, models = (get_ddl_lines(i) for i in (database, models))
    sys.stdout.writelines(unified_diff(database, models, 'database', 'models', n=16))


def get_ddl_lines(metadata: MetaData) -> Sequence[str]:
    def get_ddl_lines(table: Table) -> Sequence[str]:
        ddl = str(CreateTable(table).compile(db.engine))
        lines = ddl.splitlines(keepends=True)
        middle = lines[2:-2]

        # insert trailing comma on the last line
        last = middle[-1]
        last = last[0:-1] + ', ' + last[-1]

        middle[-1] = last
        middle.sort()
        return lines[0:2] + middle + lines[-2:]

    return tuple(i for table in metadata.sorted_tables for i in get_ddl_lines(table))


if __name__ == '__main__':
    main()
