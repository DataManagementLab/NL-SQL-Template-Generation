#!/usr/bin/env python3
"""
Many SQL queries may be semantically equivalent without being
identical. For our evaluation, we will treat as equivalent any pair of
queries <A, B> such that the tables in the FROM clause of A are the
same as the tables in the FROM clause of B (in any order) and the sub
clauses in the WHERE clause of A and B are the same (in any order,
provided parentheses are respected).
"""

import re
import string

LOGGING = False
#  Alterations:
#
#  1. add_semicolon(query)
#  Adds a semicolon at the end of the SQL statement if it is missing.
#
#  2. standardise_blank_spaces(query):
#  Ensures there is one blank space between each special character and word.
#
#  3. capitalise(query, variables):
#  Converts all non-quoted sections of the query to uppercase.
#
#  4. standardise_aliases(query):
#  Standardises the format of table aliases to be "table_name + count".
#  If a table does not have an alias, it adds an alias for the table.
#
#  5. order_query(query):
#  Identifies the select, from and where clauses and orders the clause
#  components alphabetically using Python's sort() function.
#
#  Limitations
#  - We do not handle quoted table names (a way to allow all sorts of crazy
#    names). We do not handle table names that are using keywords from mySQL
#  - We assume AND and OR are not mixed without brackets to indicate
#    precedence (it is legal SQL to do so, though a bad idea anyway).

SQL_RESERVED_WORDS = {w for w in """ACCOUNT ACTION ADD AFTER AGAINST AGGREGATE
ALGORITHM ALL ALTER ALWAYS ANALYSE ANALYZE AND ANY AS ASC ASCII ASENSITIVE AT
AUTOEXTEND_SIZE AUTO_INCREMENT AVG AVG_ROW_LENGTH BACKUP BEFORE BEGIN BETWEEN
BIGINT BINARY BINLOG BIT BLOB BLOCK BOOL BOOLEAN BOTH BTREE BY BYTE CACHE CALL
CASCADE CASCADED CASE CATALOG_NAME CESSIBLE CHAIN CHANGE CHANGED CHANNEL CHAR
CHARACTER CHARSET CHECK CHECKSUM CIPHER CLASS_ORIGIN CLIENT CLOSE COALESCE CODE
COLLATE COLLATION COLUMN COLUMNS COLUMN_FORMAT COLUMN_NAME COMMENT COMMIT
COMMITTED COMPACT COMPLETION COMPRESSED COMPRESSION CONCURRENT CONDITION
CONNECTION CONSISTENT CONSTRAINT CONSTRAINT_CATALOG CONSTRAINT_NAME
CONSTRAINT_SCHEMA CONTAINS CONTEXT CONTINUE CONVERT CPU CREATE CROSS CUBE
CURRENT CURRENT_DATE CURRENT_TIME CURRENT_TIMESTAMP CURRENT_USER CURSOR
CURSOR_NAME DATA DATABASE DATABASES DATAFILE DATE DATETIME DAY DAY_HOUR
DAY_MICROSECOND DAY_MINUTE DAY_SECOND DEALLOCATE DEC DECIMAL DECLARE DEFAULT
DEFAULT_AUTH DEFINER DELAYED DELAY_KEY_WRITE DELETE DESC DESCRIBE DES_KEY_FILE
DETERMINISTIC DIAGNOSTICS DIRECTORY DISABLE DISCARD DISK DISTINCT DISTINCTROW
DIV DO DOUBLE DROP DUAL DUMPFILE DUPLICATE DYNAMIC EACH ELSE ELSEIF ENABLE
ENCLOSED ENCRYPTION END ENDS ENGINE ENGINES ENUM ERROR ERRORS ESCAPE ESCAPED
EVENT EVENTS EVERY EXCHANGE EXECUTE EXISTS EXIT EXPANSION EXPIRE EXPLAIN EXPORT
EXTENDED EXTENT_SIZE FALSE FAST FAULTS FETCH FIELDS FILE FILE_BLOCK_SIZE FILTER
FIRST FIXED FLOAT FLOAT4 FLOAT8 FLUSH FOLLOWS FOR FORCE FOREIGN FORMAT FOUND
FROM FULL FULLTEXT FUNCTION GENERAL GENERATED GEOMETRY GEOMETRYCOLLECTION GET
GET_FORMAT GLOBAL GRANT GRANTS GROUP GROUP_REPLICATION HANDLER HASH HAVING HELP
HIGH_PRIORITY HOST HOSTS HOUR HOUR_MICROSECOND HOUR_MINUTE HOUR_SECOND
IDENTIFIED IF IGNORE IGNORE_SERVER_IDS IMPORT IN INDEX INDEXES INFILE
INITIAL_SIZE INNER INOUT INSENSITIVE INSERT INSERT_METHOD INSTALL INSTANCE INT
INT1 INT2 INT3 INT4 INT8 INTEGER INTERVAL INTO INVOKER IO IO_AFTER_GTIDS
IO_BEFORE_GTIDS IO_THREAD IPC IS ISOLATION ISSUER ITERATE JOIN JSON KEY KEYS
KEY_BLOCK_SIZE KILL LANGUAGE LAST LEADING LEAVE LEAVES LEFT LESS LEVEL LIKE
LIMIT LINEAR LINES LINESTRING LIST LOAD LOCAL LOCALTIME LOCALTIMESTAMP LOCK
LOCKS LOGFILE LOGS LONG LONGBLOB LONGTEXT LOOP LOW_PRIORITY MASTER
MASTER_AUTO_POSITION MASTER_BIND MASTER_CONNECT_RETRY MASTER_DELAY
MASTER_HEARTBEAT_PERIOD MASTER_HOST MASTER_LOG_FILE MASTER_LOG_POS
MASTER_PASSWORD MASTER_PORT MASTER_RETRY_COUNT MASTER_SERVER_ID MASTER_SSL
MASTER_SSL_CA MASTER_SSL_CAPATH MASTER_SSL_CERT MASTER_SSL_CIPHER
MASTER_SSL_CRL MASTER_SSL_CRLPATH MASTER_SSL_KEY MASTER_SSL_VERIFY_SERVER_CERT
MASTER_TLS_VERSION MASTER_USER MATCH MAXVALUE MAX_CONNECTIONS_PER_HOUR
MAX_QUERIES_PER_HOUR MAX_ROWS MAX_SIZE MAX_STATEMENT_TIME MAX_UPDATES_PER_HOUR
MAX_USER_CONNECTIONS MEDIUM MEDIUMBLOB MEDIUMINT MEDIUMTEXT MEMORY MERGE
MESSAGE_TEXT MICROSECOND MIDDLEINT MIGRATE MINUTE MINUTE_MICROSECOND
MINUTE_SECOND MIN_ROWS MOD MODE MODIFIES MODIFY MONTH MULTILINESTRING
MULTIPOINT MULTIPOLYGON MUTEX MYSQL_ERRNO NAME NAMES NATIONAL NATURAL NCHAR NDB
NDBCLUSTER NEVER NEW NEXT NO NODEGROUP NONBLOCKING NONE NOT NO_WAIT
NO_WRITE_TO_BINLOG NULL NUMBER NUMERIC NVARCHAR OFFSET OLD_PASSWORD ON ONE ONLY
OPEN OPTIMIZE OPTIMIZER_COSTS OPTION OPTIONALLY OPTIONS OR ORDER OUT OUTER
OUTFILE OWNER PACK_KEYS PAGE PARSER PARSE_GCOL_EXPR PARTIAL PARTITION
PARTITIONING PARTITIONS PASSWORD PHASE PLUGIN PLUGINS PLUGIN_DIR POINT POLYGON
PORT PRECEDES PRECISION PREPARE PRESERVE PREV PRIMARY PRIVILEGES PROCEDURE
PROCESSLIST PROFILE PROFILES PROXY PURGE QUARTER QUERY QUICK RANGE READ READS
READ_ONLY READ_WRITE REAL REBUILD RECOVER REDOFILE REDO_BUFFER_SIZE REDUNDANT
REFERENCES REGEXP RELAY RELAYLOG RELAY_LOG_FILE RELAY_LOG_POS RELAY_THREAD
RELEASE RELOAD REMOVE RENAME REORGANIZE REPAIR REPEAT REPEATABLE REPLACE
REPLICATE_DO_DB REPLICATE_DO_TABLE REPLICATE_IGNORE_DB REPLICATE_IGNORE_TABLE
REPLICATE_REWRITE_DB REPLICATE_WILD_DO_TABLE REPLICATE_WILD_IGNORE_TABLE
REPLICATION REQUIRE RESET RESIGNAL RESTORE RESTRICT RESUME RETURN
RETURNED_SQLSTATE RETURNS REVERSE REVOKE RIGHT RLIKE ROLLBACK ROLLUP ROTATE
ROUTINE ROW ROWS ROW_COUNT ROW_FORMAT RTREE SAVEPOINT SCHEDULE SCHEMA SCHEMAS
SCHEMA_NAME SECOND SECOND_MICROSECOND SECURITY SELECT SENSITIVE SEPARATOR
SERIAL SERIALIZABLE SERVER SESSION SET SHARE SHOW SHUTDOWN SIGNAL SIGNED SIMPLE
SLAVE SLOW SMALLINT SNAPSHOT SOCKET SOME SONAME SOUNDS SOURCE SPATIAL SPECIFIC
SQL SQLEXCEPTION SQLSTATE SQLWARNING SQL_AFTER_GTIDS SQL_AFTER_MTS_GAPS
SQL_BEFORE_GTIDS SQL_BIG_RESULT SQL_BUFFER_RESULT SQL_CACHE SQL_CALC_FOUND_ROWS
SQL_NO_CACHE SQL_SMALL_RESULT SQL_THREAD SQL_TSI_DAY SQL_TSI_HOUR
SQL_TSI_MINUTE SQL_TSI_MONTH SQL_TSI_QUARTER SQL_TSI_SECOND SQL_TSI_WEEK
SQL_TSI_YEAR SSL STACKED START STARTING STARTS STATS_AUTO_RECALC
STATS_PERSISTENT STATS_SAMPLE_PAGES STATUS STOP STORAGE STORED STRAIGHT_JOIN
STRING SUBCLASS_ORIGIN SUBJECT SUBPARTITION SUBPARTITIONS SUPER SUSPEND SWAPS
SWITCHES TABLE TABLES TABLESPACE TABLE_CHECKSUM TABLE_NAME TEMPORARY TEMPTABLE
TERMINATED TEXT THAN THEN TIME TIMESTAMP TIMESTAMPADD TIMESTAMPDIFF TINYBLOB
TINYINT TINYTEXT TO TRAILING TRANSACTION TRIGGER TRIGGERS TRUE TRUNCATE TYPE
TYPES UNCOMMITTED UNDEFINED UNDO UNDOFILE UNDO_BUFFER_SIZE UNICODE UNINSTALL
UNION UNIQUE UNKNOWN UNLOCK UNSIGNED UNTIL UPDATE UPGRADE USAGE USE USER
USER_RESOURCES USE_FRM USING UTC_DATE UTC_TIME UTC_TIMESTAMP VALIDATION VALUE
VALUES VARBINARY VARCHAR VARCHARACTER VARIABLES VARYING VIEW VIRTUAL WAIT
WARNINGS WEEK WEIGHT_STRING WHEN WHERE WHILE WITH WITHOUT WORK WRAPPER WRITE
X509 XA XID XML XOR YEAR YEAR_MONTH ZEROFILL""".split()}


def add_semicolon(query):
    """

    :param query:
    :return:
    """
    query = query.strip()
    if len(query) > 0 and query[-1] != ';':
        return query + ';'
    return query


def update_quotes(char, in_single, in_double):
    """

    :param char:
    :param in_single:
    :param in_double:
    :return:
    """
    if char == '"' and not in_single:
        in_double = not in_double
    elif char == "'" and not in_double:
        in_single = not in_single
    return in_single, in_double


def standardise_blank_spaces(query):
    """

    :param query:
    :return:
    """
    # split on special characters except _.:-
    in_squote, in_dquote = False, False
    tmp_query = []
    pos = 0
    while pos < len(query):
        char = query[pos]
        pos += 1
        # Handle whether we are in quotes
        if char in ["'", '"']:
            if not (in_squote or in_dquote):
                tmp_query.append(" ")
            in_squote, in_dquote = update_quotes(char, in_squote, in_dquote)
            tmp_query.append(char)
            if not (in_squote or in_dquote):
                tmp_query.append(" ")
        elif in_squote or in_dquote:
            tmp_query.append(char)
        elif char in "!=<>,;()[]{}+*/\\#":
            tmp_query.append(" ")
            tmp_query.append(char)
            while pos < len(query) and query[pos] in "!=<>+*" and char in "!=<>+*":
                tmp_query.append(query[pos])
                pos += 1
            tmp_query.append(" ")
        else:
            tmp_query.append(char)
    new_query = ''.join(tmp_query)

    # Remove blank spaces just inside quotes:
    tmp_query = []
    in_squote, in_dquote = False, False
    prev = None
    prev2 = None
    for char in new_query:
        skip = False
        for quote, symbol in [(in_squote, "'"), (in_dquote, '"')]:
            if quote:
                if char in " \n" and prev == symbol:
                    skip = True
                    break
                if char in " \n" and prev == "%" and prev2 == symbol:
                    skip = True
                    break
                elif char == symbol and prev in " \n":
                    tmp_query.pop()
                elif char == symbol and prev == "%" and prev2 in " \n":
                    tmp_query.pop(len(tmp_query) - 2)
        if skip:
            continue

        in_squote, in_dquote = update_quotes(char, in_squote, in_dquote)
        tmp_query.append(char)
        prev2 = prev
        prev = char
    new_query = ''.join(tmp_query)

    # Replace single quotes with double quotes where possible
    tmp_query = []
    in_squote, in_dquote = False, False
    pos = 0
    while pos < len(new_query):
        char = new_query[pos]
        if (not in_dquote) and char == "'":
            to_add = [char]
            pos += 1
            saw_double = False
            while pos < len(new_query):
                tchar = new_query[pos]
                if tchar == '"':
                    saw_double = True
                to_add.append(tchar)
                if tchar == "'":
                    break
                pos += 1
            if not saw_double:
                to_add[0] = '"'
                to_add[-1] = '"'
            tmp_query.append(''.join(to_add))
        else:
            tmp_query.append(char)

        in_squote, in_dquote = update_quotes(char, in_squote, in_dquote)

        pos += 1
    new_query = ''.join(tmp_query)

    # remove repeated blank spaces
    new_query = ' '.join(new_query.split())

    # Remove spaces that would break SQL functions
    new_query = "COUNT(".join(new_query.split("count ("))
    new_query = "LOWER(".join(new_query.split("lower ("))
    new_query = "MAX(".join(new_query.split("max ("))
    new_query = "MIN(".join(new_query.split("min ("))
    new_query = "SUM(".join(new_query.split("sum ("))
    new_query = "COUNT(".join(new_query.split("COUNT ("))
    new_query = "LOWER(".join(new_query.split("LOWER ("))
    new_query = "MAX(".join(new_query.split("MAX ("))
    new_query = "MIN(".join(new_query.split("MIN ("))
    new_query = "SUM(".join(new_query.split("SUM ("))
    new_query = "COUNT( *".join(new_query.split("COUNT(*"))
    new_query = "YEAR(CURDATE())".join(new_query.split("YEAR ( CURDATE ( ) )"))

    return new_query


def capitalise(query, variables):
    """

    :param query:
    :param variables:
    :return:
    """
    ntokens = []
    in_squote, in_dquote = False, False
    for token in query.split():
        if token in variables or token in ["credit0", "level0", "level1", "number0", "number1", "year0",
                                           "business_rating0", 'value']:
            ntokens.append(token)
        else:
            modified = []
            for char in token:
                # Record the modified character
                if in_squote or in_dquote:
                    modified.append(char)
                else:
                    modified.append(char.upper())

                # Handle whether we are in quotes
                in_squote, in_dquote = update_quotes(char, in_squote, in_dquote)
            ntokens.append(''.join(modified))

    return ' '.join(ntokens)


def subquery_range(current, pos, tokens, in_quote=False):
    """

    :param current:
    :param pos:
    :param tokens:
    :param in_quote:
    :return:
    """
    if tokens[pos] == '(' and (not in_quote):
        start = pos
        end = pos + 1
        depth = 1
        in_squote, in_dquote = False, False
        while depth > 0:
            for char in tokens[end]:
                in_squote, in_dquote = update_quotes(char, in_squote, in_dquote)
            if not (in_squote or in_dquote):
                if '(' in tokens[end]:
                    depth += 1
                elif ')' in tokens[end]:
                    depth -= 1
            end += 1
        return (start, end)
    elif current is not None and pos == current[1]:
        start = pos
        end = pos + 1
        depth = 1
        in_squote, in_dquote = False, False
        while depth > 0 and start > 0:
            for char in tokens[start]:
                in_squote, in_dquote = update_quotes(char, in_squote, in_dquote)
            if not (in_squote or in_dquote):
                if '(' in tokens[start]:
                    depth -= 1
                elif ')' in tokens[start]:
                    depth += 1
            start -= 1
        if start != 0:
            start += 1

        while end < len(tokens) and tokens[end] != ')':
            end += 1
        if end != len(tokens):
            end += 1
        return (start, end)
    else:
        return current


ALIAS_PATTERN = re.compile("[A-Za-z0-9_]*")


def standardise_aliases(query, schema):
    """

    :param query:
    :param schema:
    :return:
    """
    count = {}  # dictionary storing how many times each table has been used
    aliases = {}  # dictionary mapping old aliases to standardised aliases
    field_aliases = {}
    tokens = query.split()

    # insert AS and replace old alias name with new alias name
    current_subquery = (0, -1)
    seen_from = {}
    seen_where = {}
    in_quote = False
    for i, word in enumerate(tokens):
        for part in word.split('"'):
            in_quote = not in_quote
        in_quote = not in_quote
        current_subquery = subquery_range(current_subquery, i, tokens, in_quote)
        if word == "FROM":
            if LOGGING: print("Seen from", current_subquery[0], i)
            seen_from[current_subquery[0]] = i
        elif current_subquery[0] not in seen_from:
            seen_from[current_subquery[0]] = None

        if word == "WHERE":
            seen_where[current_subquery[0]] = i
        elif current_subquery[0] not in seen_where:
            seen_where[current_subquery[0]] = None

        if word in schema[0] and not seen_where[current_subquery[0]] and seen_from[current_subquery[0]]:
            count[word] = count.get(word, -1) + 1
            if len(tokens) < i + 2 or tokens[i + 1] != 'AS':
                tokens.insert(i + 1, 'AS')
            alias = word + "alias" + str(count[word])

            # Check if there is an alias there now
            has_alias = False
            if len(tokens) > i + 2:
                if tokens[i + 2] not in SQL_RESERVED_WORDS:
                    if re.fullmatch(ALIAS_PATTERN, tokens[i + 2]) is not None:
                        has_alias = True

            # Update this occurrence and our mapping
            if has_alias:
                aliases[current_subquery[0], tokens[i + 2]] = alias
                tokens[i + 2] = alias
            else:
                aliases[current_subquery[0], word] = alias
                tokens.insert(i + 2, alias)
        elif i > 2 and tokens[i - 1] == 'AS':
            if tokens[i - 2] not in schema[0]:
                if LOGGING: print("Considering", tokens[i - 2:i + 1], current_subquery, seen_from[current_subquery[0]])
                word = "DERIVED_TABLE"
                if seen_from[current_subquery[0]] is None:
                    word = "DERIVED_FIELD"
                count[word] = count.get(word, -1) + 1
                alias = word + "alias" + str(count[word])
                if seen_from[current_subquery[0]] is None:
                    # print("New field alias", current_subquery[0], tokens[i], alias)
                    field_aliases[tokens[i]] = alias
                else:
                    # print("New alias", current_subquery[0], tokens[i], alias)
                    aliases[current_subquery[0], tokens[i]] = alias
                tokens[i] = alias

    # replace old alias names for the columns with new alias names
    current_subquery = (0, -1)
    if LOGGING:
        for alias in aliases:
            print(alias, aliases[alias])
        for field_alias in field_aliases:
            print(field_alias, field_aliases[field_alias])
    in_quote = False
    for i, word in enumerate(tokens):
        for part in word.split('"'):
            in_quote = not in_quote
        in_quote = not in_quote
        current_subquery = subquery_range(current_subquery, i, tokens, in_quote)
        if (current_subquery[0], word) in aliases:
            if len(tokens) > i + 1 and tokens[i + 1] != "AS":
                tokens[i] = aliases[current_subquery[0], word]
        if word in SQL_RESERVED_WORDS and word not in schema[1]:
            continue
        parts = word.split('.')
        if len(parts) == 2:
            if LOGGING: print(current_subquery, parts[0], word)
            if (current_subquery[0], parts[0]) in aliases:
                table = aliases[current_subquery[0], parts[0]]
                field = parts[1]
                if field in field_aliases and 'DERIVED' in table:
                    field = field_aliases[parts[1]]
                tokens[i] = table + "." + field
            else:
                for alias in aliases:
                    other = subquery_range((0, -1), alias[0], tokens)
                    if LOGGING: print("   ", alias, alias[1], parts[0], other[0], current_subquery[0], other[1], i)
                    if alias[1] == parts[0] and other[0] < current_subquery[0] and (other[1] == -1 or other[1] > i):
                        tokens[i] = aliases[alias] + '.' + parts[1]
        elif len(parts) == 1:
            # if no alias is specified, find the table name in the schema. We
            # assume that no field name is used ambiguously.
            options = []
            sf = seen_from.get(current_subquery[0], None)
            sw = seen_where.get(current_subquery[0], None)
            done = False
            if sf is None or i < sf or (sw is not None and i > sw):
                for table in schema[0]:
                    # print(table, schema[0][table])
                    if word in schema[0][table]:
                        # print("Found", i, word, table, current_subquery)
                        for pair in aliases:
                            alias = aliases[pair]
                            start = alias.split("alias")[0]
                            if pair[0] == current_subquery[0] and start == table:
                                tokens[i] = alias + '.' + word
                                done = True
                                break
                        if done:
                            break
            if (not done) and word in field_aliases:
                tokens[i] = field_aliases[word]

    return ' '.join(tokens)


def tokens_for_chunk(tokens, chunk):
    """

    :param tokens:
    :param chunk:
    :return:
    """
    return tokens[chunk[0]:chunk[1] + 1]


def get_matching_chunk(tokens, chunks, pos, target, default=None):
    """

    :param tokens:
    :param chunks:
    :param pos:
    :param target:
    :param default:
    :return:
    """
    saw_between = False
    while pos < len(chunks):
        chunk = chunks[pos]
        if tokens[chunk[0]].upper() == "BETWEEN":
            saw_between = True
        if chunk[0] == chunk[1] and tokens[chunk[0]] == target:
            if target != "AND" or (not saw_between):
                return pos
        if saw_between and tokens[chunk[0]].upper() == 'AND':
            saw_between = False
        pos += 1
    return default


def sort_chunk_list(start, end, chunks, tokens, separator=","):
    """

    :param start:
    :param end:
    :param chunks:
    :param tokens:
    :param separator:
    :return:
    """
    to_rearrange = []
    pos = start
    while pos < end:
        npos = get_matching_chunk(tokens, chunks, pos + 1, separator)
        if npos is None or npos > end:
            npos = end - 1
        left = chunks[pos][0]
        right = chunks[npos][1]
        to_rearrange.append((' '.join(tokens[left:right + 1]), pos, npos))
        pos = npos + 1

    if len(to_rearrange) > 0:
        to_rearrange.sort()
        min_pos = min([chunks[v[1]][0] for v in to_rearrange])
        max_pos = max([chunks[v[2]][1] for v in to_rearrange])
        ctokens = tokens[min_pos:max_pos + 1]
        cpos = min_pos
        for info in to_rearrange:
            saw_between = False
            for i in range(info[1], info[2] + 1):
                for j in range(chunks[i][0], chunks[i][1] + 1):
                    token = ctokens[j - min_pos]
                    advance = False
                    if (chunks[i][1] - chunks[i][0]) > 1:
                        advance = True
                    if token != separator or (saw_between and separator == 'AND'):
                        advance = True
                    if advance:
                        tokens[cpos] = ctokens[j - min_pos]
                        cpos += 1
                    if token == 'BETWEEN':
                        saw_between = True
                    if saw_between and token == 'AND':
                        saw_between = False
            if cpos <= max_pos:
                tokens[cpos] = separator
            cpos += 1


def order_sequence(tokens, start, end, variables):
    """

    :param tokens:
    :param start:
    :param end:
    :param variables:
    :return:
    """
    # Note - using https://ronsavage.github.io/SQL/sql-92.bnf.html to assist in
    # this construction.

    # First, recurse to subqueries
    cpos = start + 1
    chunks = [(start, start)]
    in_quote = False
    while cpos < end:
        for part in tokens[cpos].split('"'):
            in_quote = not in_quote
        in_quote = not in_quote
        sub = subquery_range(None, cpos, tokens, in_quote)
        if sub is None:
            chunks.append((cpos, cpos))
            cpos += 1
        else:
            chunks.append((cpos, sub[1] - 1))
            order_sequence(tokens, sub[0], sub[1] - 1, variables)
            cpos = sub[1]

    # Handle SELECT
    cur_chunk = 0
    while cur_chunk < len(chunks):
        next_select = get_matching_chunk(tokens, chunks, cur_chunk, "SELECT")
        if next_select is None: break

        next_distinct = get_matching_chunk(tokens, chunks, next_select, "DISTINCT")
        next_all = get_matching_chunk(tokens, chunks, next_select, "ALL")
        if next_distinct == next_select + 1 or next_all == next_select + 1:
            next_select += 1

        next_from = get_matching_chunk(tokens, chunks, next_select, "FROM", len(chunks))

        sort_chunk_list(next_select + 1, next_from, chunks, tokens)

        cur_chunk = next_from

    # Handle = and !=
    for symbol in ["=", "!="]:
        cur_chunk = 0
        while cur_chunk < len(chunks):
            next_equals = get_matching_chunk(tokens, chunks, cur_chunk, symbol)
            if next_equals is None:
                break
            left = tokens_for_chunk(tokens, chunks[next_equals - 1])
            right = tokens_for_chunk(tokens, chunks[next_equals + 1])
            left_text = ' '.join(left)
            right_text = ' '.join(right)

            swap = \
                left_text < right_text or \
                left_text in variables or \
                left_text[0] in string.digits or \
                left_text[0] in ['"', "'", "("] or \
                ' ' in left_text or \
                '.' not in left_text

            if right_text in variables or right_text[0] in string.digits or right_text[0] in ['"', "'",
                                                                                              "("] or ' ' in right_text or '.' not in right_text:
                swap = False

            if swap:
                cpos = chunks[next_equals - 1][0]
                for token in right:
                    tokens[cpos] = token
                    cpos += 1
                tokens[cpos] = symbol
                cpos += 1
                for token in left:
                    tokens[cpos] = token
                    cpos += 1

            cur_chunk = next_equals + 2

    #  - Table names in 'from'
    cur_chunk = 0
    while cur_chunk < len(chunks):
        next_from = get_matching_chunk(tokens, chunks, cur_chunk, "FROM")
        if next_from is None: break

        next_item = min(
            get_matching_chunk(tokens, chunks, next_from, "WHERE", len(chunks)),
            get_matching_chunk(tokens, chunks, next_from, "JOIN", len(chunks)),
            get_matching_chunk(tokens, chunks, next_from, "GROUP", len(chunks)),
            get_matching_chunk(tokens, chunks, next_from, "HAVING", len(chunks)),
            get_matching_chunk(tokens, chunks, next_from, "LIMIT", len(chunks)),
            get_matching_chunk(tokens, chunks, next_from, "ORDER", len(chunks)),
            get_matching_chunk(tokens, chunks, next_from, ";", len(chunks))
        )
        sort_chunk_list(next_from + 1, next_item, chunks, tokens)
        cur_chunk = next_item

    #  - Comparisons in 'where'
    cur_chunk = 0
    while cur_chunk < len(chunks):
        next_where = get_matching_chunk(tokens, chunks, cur_chunk, "WHERE")
        if next_where is None:
            if tokens[chunks[0][0]] != "SELECT" and tokens[chunks[1][1]] != "SELECT":
                next_where = 0
            else:
                break

        next_item = min(
            get_matching_chunk(tokens, chunks, next_where, "GROUP", len(chunks)),
            get_matching_chunk(tokens, chunks, next_where, "HAVING", len(chunks)),
            get_matching_chunk(tokens, chunks, next_where, "LIMIT", len(chunks)),
            get_matching_chunk(tokens, chunks, next_where, "ORDER", len(chunks)),
            get_matching_chunk(tokens, chunks, next_where, ";", len(chunks))
        )
        has_and = False
        has_or = False
        saw_between = False
        for v in range(next_where + 1, next_item):
            chunk = chunks[v]
            if tokens[chunk[0]] == "BETWEEN":
                saw_between = True
            if chunk[0] == chunk[1] and tokens[chunk[0]] == "AND":
                if not saw_between:
                    has_and = True
                else:
                    saw_between = False
            if chunk[0] == chunk[1] and tokens[chunk[0]] == "OR":
                has_or = True

        if not (has_and and has_or):
            min_pos = min([chunks[v][0] for v in range(next_where + 1, next_item)])
            max_pos = max([chunks[v][1] for v in range(next_where + 1, next_item)])
            ctokens = tokens[min_pos:max_pos + 1]
            sort_chunk_list(next_where + 1, next_item, chunks, tokens, "AND")
            sort_chunk_list(next_where + 1, next_item, chunks, tokens, "OR")
        cur_chunk = next_item


def order_query(query, variables):
    """

    :param query:
    :param variables:
    :return:
    """
    tokens = query.split()
    order_sequence(tokens, 0, len(tokens) - 1, variables)
    return ' '.join(tokens)


def make_canonical(query, schema, variables, skip=set()):
    """

    :param query:
    :param schema:
    :param variables:
    :param skip:
    :return:
    """
    if 'add_semicolon' not in skip:
        query = add_semicolon(query)
    if 'standardise_blank_spaces' not in skip:
        query = standardise_blank_spaces(query)
    if 'capitalise' not in skip:
        query = capitalise(query, variables)
    if 'standardise_aliases' not in skip:
        query = standardise_aliases(query, schema)
    if 'order_query' not in skip:
        query = order_query(query, variables)
    return query


if __name__ == "__main__":
    schema = ({'MOUNTAIN': {'NAME', 'RANGE', 'MOUNTAIN_ID', 'COUNTRY', 'HEIGHT', 'PROMINENCE'},
               'CLIMBER': {'NAME', 'TIME', 'POINTS', 'MOUNTAIN_ID', 'COUNTRY', 'CLIMBER_ID'}},
              {'NAME', 'TIME', 'POINTS', 'RANGE', 'MOUNTAIN_ID', 'CLIMBER_ID', 'CLIMBER', 'PROMINENCE', 'COUNTRY',
               'HEIGHT', 'MOUNTAIN'})
    sql = 'SELECT * FROM climber where climber.Mountain_ID = \
        ( SELECT mountain.Mountain_ID FROM mountain WHERE mountain.Name \
        = "Mount Kenya (Batian)" OR mountain.Range = "Rwenzori" GROUP BY \
        mountain.Mountain_ID ORDER BY count ( * ) desc limit 1 )'
    variables = {'var0': 'Mount Kenya (Batian)', 'var1': 'Rwenzori'}
    make_canonical(sql, schema, variables)
