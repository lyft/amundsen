// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { mocked } from 'ts-jest/utils';

import { indexUsersEnabled } from 'config/config-utils';

import { GlobalState } from 'ducks/rootReducer';

import globalState from 'fixtures/globalState';
import { dashboardMetadata } from 'fixtures/metadata/dashboard';
import { activeUser0 } from 'fixtures/metadata/users';
import { mapStateToProps, DASHBOARD_OWNER_SOURCE } from '.';

jest.mock('config/config-utils', () => ({
  indexUsersEnabled: jest.fn(),
}));

describe('mapStateToProps', () => {
  let result;
  let expectedItemProps;
  let mockState: GlobalState;
  beforeAll(() => {
    mockState = {
      ...globalState,
      dashboard: {
        dashboard: {
          ...dashboardMetadata,
          owners: [activeUser0],
        },
        isLoading: false,
        statusCode: 200,
      },
    };
  });

  it('returns expected itemProps when indexUsersEnabled()', () => {
    mocked(indexUsersEnabled).mockImplementation(() => true);
    result = mapStateToProps(mockState);
    const id = activeUser0.user_id;
    expectedItemProps = {
      [id]: {
        label: activeUser0.display_name,
        link: `/user/${id}?source=${DASHBOARD_OWNER_SOURCE}`,
        isExternal: false,
      },
    };
    expect(result.itemProps).toEqual(expectedItemProps);
  });

  it('returns expected itemProps when !indexUsersEnabled()', () => {
    mocked(indexUsersEnabled).mockImplementation(() => false);
    result = mapStateToProps(mockState);
    expectedItemProps = {
      [activeUser0.user_id]: {
        label: activeUser0.display_name,
        link: activeUser0.profile_url,
        isExternal: true,
      },
    };
    expect(result.itemProps).toEqual(expectedItemProps);
  });
});
