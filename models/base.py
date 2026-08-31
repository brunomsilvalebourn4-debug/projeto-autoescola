from dataclasses import fields


class RowModel:
    @classmethod
    def from_row(cls, row):
        if row is None:
            return None
        available = set(row.keys())
        values = {field.name: row[field.name] for field in fields(cls) if field.name in available}
        return cls(**values)
