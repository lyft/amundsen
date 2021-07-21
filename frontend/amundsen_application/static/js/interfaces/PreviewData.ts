// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

interface PreviewColumnItem {
  column_name: string;
  column_type: string;
}

interface PreviewDataItem {
  [columnName: string]: string;
}

export interface PreviewData {
  columns?: PreviewColumnItem[];
  data?: PreviewDataItem[];
  error_text?: string;
}
