import axios from 'axios';

import * as API from '../v0';

jest.mock('axios');

describe('postActionLog', () => {
  let axiosMock;
  let params: API.ActionLogParams;
  beforeAll(() => {
    axiosMock = jest
      .spyOn(axios, 'post')
      .mockImplementation(() => Promise.resolve());
    params = {
      command: 'test',
    };
    API.postActionLog(params);
  });

  it('calls axios with expected parameters', () => {
    expect(axiosMock).toHaveBeenCalledWith(API.BASE_URL, params);
  });

  afterAll(() => {
    axiosMock.mockClear();
  });
});
