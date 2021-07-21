// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

export enum CaseType {
  LOWER_CASE = 'lowerCase',
  SENTENCE_CASE = 'sentenceCase',
  UPPER_CASE = 'upperCase',
  TITLE_CASE = 'titleCase',
}

export function convertText(str = '', caseType: CaseType | null): string {
  switch (caseType) {
    case CaseType.LOWER_CASE:
      return str.toLowerCase();
    case CaseType.SENTENCE_CASE:
      return `${str.charAt(0).toUpperCase()}${str.slice(1).toLowerCase()}`;
    case CaseType.UPPER_CASE:
      return str.toUpperCase();
    case CaseType.TITLE_CASE:
      const splitStr = str.toLowerCase().split(' ');
      for (let i = 0; i < splitStr.length; i++) {
        splitStr[i] =
          splitStr[i].charAt(0).toUpperCase() + splitStr[i].substring(1);
      }
      return splitStr.join(' ');
    default:
      return str;
  }
}
