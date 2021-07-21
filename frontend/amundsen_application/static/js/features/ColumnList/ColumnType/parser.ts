// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

export type ParsedType = string | NestedType;

export interface NestedType {
  head: string;
  tail: string;
  children: ParsedType[];
}
enum DatabaseId {
  Hive = 'hive',
  Presto = 'presto',
  Delta = 'delta',
}
const SUPPORTED_TYPES = {
  // https://cwiki.apache.org/confluence/display/Hive/LanguageManual+Types#LanguageManualTypes-ComplexTypes
  [DatabaseId.Hive]: ['array', 'map', 'struct', 'uniontype'],
  // https://prestosql.io/docs/current/language/types.html#structural
  [DatabaseId.Presto]: ['array', 'map', 'row'],
  // https://docs.databricks.com/spark/latest/spark-sql/language-manual/sql-ref-datatypes.html#data-types
  [DatabaseId.Delta]: ['array', 'map', 'struct'],
};
const OPEN_DELIMETERS = {
  '(': ')',
  '<': '>',
  '[': ']',
};
const CLOSE_DELIMETERS = {
  ')': '(',
  '>': '<',
  ']': '[',
};
const SEPARATOR_DELIMETER = ',';

/*
 * Iterates through the columnType string and recursively creates a NestedType
 */
function parseNestedTypeHelper(
  columnType: string,
  startIndex: number = 0,
  currentIndex: number = 0
): { nextStartIndex: number; results: ParsedType[] } {
  const children: ParsedType[] = [];

  while (currentIndex < columnType.length) {
    const currentChar = columnType.charAt(currentIndex);

    if (currentChar === SEPARATOR_DELIMETER) {
      /* Case 1: End of non-nested item */
      children.push(columnType.substring(startIndex, currentIndex + 1).trim());
      startIndex = currentIndex + 1;
      currentIndex = startIndex;
    } else if (currentChar in CLOSE_DELIMETERS) {
      /* Case 2: End of a nested item  */
      if (startIndex !== currentIndex) {
        children.push(columnType.substring(startIndex, currentIndex).trim());
      }
      return {
        nextStartIndex: currentIndex + 1,
        results: children,
      };
    } else if (currentChar in OPEN_DELIMETERS) {
      /* Case 3: Beginning of a nested item */
      if (
        columnType.substring(startIndex, currentIndex).endsWith('timestamp')
      ) {
        /*
          Case 3.1: A non-supported item like timestamp() in Presto
          Advance until we reach the closing character for this item.
          On the next iteration Case 1 will apply.
        */
        while (
          columnType.charAt(currentIndex) !== OPEN_DELIMETERS[currentChar]
        ) {
          currentIndex++;
        }
        currentIndex++;
      } else {
        /* Case 3.2: A supported nested item */
        const parsedResults = parseNestedTypeHelper(
          columnType,
          currentIndex + 1,
          currentIndex + 1
        );
        let isLast: boolean = true;
        let { nextStartIndex } = parsedResults;

        if (columnType.charAt(nextStartIndex) === SEPARATOR_DELIMETER) {
          isLast = false;
          nextStartIndex++;
        }

        children.push({
          head: columnType.substring(startIndex, currentIndex + 1),
          tail: `${OPEN_DELIMETERS[currentChar]}${
            isLast ? '' : SEPARATOR_DELIMETER
          }`,
          children: parsedResults.results,
        });

        startIndex = nextStartIndex;
        currentIndex = startIndex;
      }
    } else {
      currentIndex++;
    }
  }

  return {
    nextStartIndex: currentIndex + 1,
    results: children,
  };
}

/*
 * Returns whether or not a columnType string represents a complex type for the given database
 */
export function isNestedType(columnType: string, databaseId: string): boolean {
  const supportedTypes = SUPPORTED_TYPES[databaseId];
  let isNested = false;
  if (supportedTypes) {
    supportedTypes.forEach((supportedType) => {
      if (
        columnType.startsWith(supportedType) &&
        columnType !== supportedType
      ) {
        isNested = true;
      }
    });
  }
  return isNested;
}

/**
 * Returns a NestedType object for supported complex types, else returns null
 */
export function parseNestedType(
  columnType: string,
  databaseId: string
): NestedType | null {
  // Presto includes un-needed "" characters
  if (databaseId === DatabaseId.Presto) {
    columnType = columnType.replace(/"/g, '');
  }

  if (isNestedType(columnType, databaseId)) {
    return parseNestedTypeHelper(columnType).results[0] as NestedType;
  }
  return null;
}

/*
 * Returns the truncated string representation for a NestedType
 */
export function getTruncatedText(nestedType: NestedType): string {
  const { head, tail } = nestedType;
  return `${head}...${tail.replace(SEPARATOR_DELIMETER, '')}`;
}
