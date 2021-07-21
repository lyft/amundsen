// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import { PreviewData } from 'interfaces/PreviewData';

export const previewDataSuccess: PreviewData = {
  columns: [
    {
      column_name: 'column_1',
      column_type: 'VARCHAR',
    },
    {
      column_name: 'column_2',
      column_type: 'VARCHAR',
    },
  ],
  data: [
    {
      column_1: 'test_data11',
      column_2: 'test_data21',
    },
    {
      column_1: 'test_data12',
      column_2: 'test_data22',
    },
    {
      column_1: 'test_data13',
      column_2: 'test_data23',
    },
  ],
  error_text: '',
};

export const previewDataError: PreviewData = {
  error_text: 'error has occured',
};
