from typing import Iterator

from databuilder.models.graph_serializable import GraphSerializable


class QueryBase(GraphSerializable):
    @staticmethod
    def _normalize(sql: str) -> str:
        """
        Normalizes a SQL query or SQL expression.

        No checks are made to ensure that the input is valid SQL.
        This is not a full normalization.  The following operations are preformed:

        - Any run of whitespace characters outside of a quoted region is replaces by a single ' ' character.
        - Characters outside of quoted regions are made lower case.
        - If present, a trailing ';' is removed from the query.

        Note:
        Making characters outside quoted regions lower case does not in general result in an equivalent SQL statement.
        For example, with MySQL the case sensitivity of table names is operating system dependant.
        In practice, modern systems rarely rely on case sensitivity, and since making the non-quoted regions of the
        query lowercase is very helpful in identifying queries, we go ahead and do so.

        Also, this method fails to identify expressions such as `1 + 2` and `1+2`.
        There are likely too many special cases in this area to make much progress without doing a proper parse.
        """
        text = sql.strip()
        it = iter(text)
        sb = []
        for c in it:
            if c.isspace():
                c = QueryBase._process_whitespace(it)
                sb.append(' ')
            sb.append(c.lower())
            if c in ('`', '"', "'"):
                for d in QueryBase._process_quoted(it, c):
                    sb.append(d)
        if sb[-1] == ';':
            sb.pop()
        return ''.join(sb)

    @staticmethod
    def _process_quoted(it: Iterator[str], quote: str) -> Iterator[str]:
        """
        Yields characters up to and including the first occurrence of the (non-escaped) character `quote`.

        Allows `quote` to be escaped with '\\'.
        """
        p = ''
        for c in it:
            yield c
            if c == quote and p != '\\':
                break
            p = c

    @staticmethod
    def _process_whitespace(it: Iterator[str]) -> str:
        """
        Returns the first non-whitespace character encountered.

        This should never return `None` since the query text is striped before being processed.
        That is, if the current character is a whitespace character, then there remains at least one non-whitespace
        character in the stream.
        """
        for c in it:
            if not c.isspace():
                return c
        raise ValueError("Input string was not stripped!")
