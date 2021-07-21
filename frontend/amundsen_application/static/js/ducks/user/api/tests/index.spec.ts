import axios, { AxiosResponse } from 'axios';

import globalState from 'fixtures/globalState';

import { LoggedInUser, PeopleUser, Resource } from 'interfaces';

import * as API from '../v0';

jest.mock('axios');

describe('getLoggedInUser', () => {
  let axiosMock;
  let mockGetResponse: AxiosResponse<API.LoggedInUserAPI>;
  let testUser: LoggedInUser;
  beforeAll(() => {
    testUser = globalState.user.loggedInUser;
    mockGetResponse = {
      data: {
        user: testUser,
        msg: 'Success',
      },
      status: 200,
      statusText: '',
      headers: {},
      config: {},
    };
    axiosMock = jest
      .spyOn(axios, 'get')
      .mockImplementation(() => Promise.resolve(mockGetResponse));
  });

  it('calls axios with correct parameters', async () => {
    expect.assertions(1);
    await API.getLoggedInUser().then(() => {
      expect(axiosMock).toHaveBeenCalledWith(`/api/auth_user`);
    });
  });

  it('returns user from response data', async () => {
    expect.assertions(1);
    await API.getLoggedInUser().then((user) => {
      expect(user).toBe(testUser);
    });
  });

  afterAll(() => {
    axiosMock.mockClear();
  });
});

describe('getUser', () => {
  let axiosMock;
  let mockGetResponse: AxiosResponse<API.UserAPI>;
  let testId: string;
  let testUser: PeopleUser;
  beforeAll(() => {
    testId = 'testId';
    testUser = globalState.user.profile.user;
    mockGetResponse = {
      data: {
        user: testUser,
        msg: 'Success',
      },
      status: 200,
      statusText: '',
      headers: {},
      config: {},
    };
    axiosMock = jest
      .spyOn(axios, 'get')
      .mockImplementation(() => Promise.resolve(mockGetResponse));
  });

  it('calls axios with correct parameters', async () => {
    expect.assertions(1);
    await API.getUser(testId).then(() => {
      expect(axiosMock).toHaveBeenCalledWith(
        `/api/metadata/v0/user?user_id=${testId}`
      );
    });
  });

  it('returns user from response data', async () => {
    expect.assertions(1);
    await API.getUser(testId).then((user) => {
      expect(user).toBe(testUser);
    });
  });

  afterAll(() => {
    axiosMock.mockClear();
  });
});

describe('getUserOwn', () => {
  let axiosMock;
  let mockGetResponse: AxiosResponse<API.UserOwnAPI>;
  let testId: string;
  let testResources;
  beforeAll(() => {
    testId = 'testId';
    testResources = globalState.user.profile.own;
    mockGetResponse = {
      data: {
        own: testResources,
        msg: 'Success',
      },
      status: 200,
      statusText: '',
      headers: {},
      config: {},
    };
    axiosMock = jest
      .spyOn(axios, 'get')
      .mockImplementation(() => Promise.resolve(mockGetResponse));
  });

  it('calls axios with correct parameters', async () => {
    expect.assertions(1);
    await API.getUserOwn(testId).then(() => {
      expect(axiosMock).toHaveBeenCalledWith(
        `/api/metadata/v0/user/own?user_id=${testId}`
      );
    });
  });

  it('returns response data with owned resources', async () => {
    expect.assertions(1);
    await API.getUserOwn(testId).then((data) => {
      expect(data.own).toBe(testResources);
    });
  });

  afterAll(() => {
    axiosMock.mockClear();
  });
});

describe('getUserRead', () => {
  let axiosMock;
  let mockGetResponse: AxiosResponse<API.UserReadAPI>;
  let testId: string;
  let testResources: Resource[];
  beforeAll(() => {
    testId = 'testId';
    testResources = globalState.user.profile.read;
    mockGetResponse = {
      data: {
        read: testResources,
        msg: 'Success',
      },
      status: 200,
      statusText: '',
      headers: {},
      config: {},
    };
    axiosMock = jest
      .spyOn(axios, 'get')
      .mockImplementation(() => Promise.resolve(mockGetResponse));
  });

  it('calls axios with correct parameters', async () => {
    expect.assertions(1);
    await API.getUserRead(testId).then(() => {
      expect(axiosMock).toHaveBeenCalledWith(
        `/api/metadata/v0/user/read?user_id=${testId}`
      );
    });
  });

  it('returns response data with frequently read resources', async () => {
    expect.assertions(1);
    await API.getUserRead(testId).then((data) => {
      expect(data.read).toBe(testResources);
    });
  });

  afterAll(() => {
    axiosMock.mockClear();
  });
});
