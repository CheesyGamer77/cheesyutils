import aiosqlite
from typing import Any, Iterable, List, Optional, Union
from enum import Enum


class DataType(Enum):
    integer = "INTEGER"
    real = "REAL"
    blob = "BLOB"
    text = "TEXT"
    null = "NULL"


class Table:
    """Helper class to construct sql queries for tables"""

    def __init__(self, name: str):
        self._name = name
        self._columns = []
        self._has_primary_key = False

    @property
    def sql(self) -> Optional[str]:    
        return """CREATE TABLE IF NOT EXISTS {} {}""".format(self._name, "(" + (", ".join([column for column in self._columns])) + ")")
    
    def add_column(
        self,
        name: str,
        datatype: DataType,
        primary_key: Optional[bool] = False,
        unique: Optional[bool] = False,
        default: Optional[Any] = None,
        not_null: Optional[bool] = False
    ):
        sql = f"""{name} {datatype.value}"""

        if primary_key:
            if self._has_primary_key:
                raise ValueError("Primary key already exists in table")
            else:
                sql += """ PRIMARY KEY"""

        if not_null:
            sql += """ NOT NULL"""
        
        if unique:
            sql += """ UNIQUE"""
        
        if default:
            # add redundant quotes on strings
            if isinstance(default, str):
                default = f"\"{default}\""

            sql += f""" DEFAULT {default}"""


        self._columns.append(sql)
    

class Database:
    def __init__(self, fp: str):
        self.fp = fp

    async def create_table(self, table: Table):
        await self.execute(table.sql)

    async def query_first(self, sql: str, as_dict: Optional[bool] = True, parameters: Iterable[Any] = None) -> Optional[Union[dict, list]]:
        res = await self.execute(sql, auto_commit=False, as_dict=as_dict, parameters=parameters)
        if isinstance(res, (list, tuple)):
            return res[0] if res else None
        return res
    
    async def query_all(self, sql: str, as_dict: Optional[bool] = True, parameters: Iterable[Any] = None) -> Optional[Union[list, dict]]:
        return await self.execute(sql, auto_commit=False, as_dict=as_dict, parameters=parameters)

    async def execute(self, sql: str, auto_commit: Optional[bool] = True, as_dict: Optional[bool] = False, parameters: Iterable[Any] = None) -> List[dict]:
        async with aiosqlite.connect(self.fp) as db:
            if as_dict:
                db.row_factory = aiosqlite.Row

            async with db.execute_fetchall(sql, parameters=parameters) as result:
                if auto_commit:
                    await db.commit()

                return result
