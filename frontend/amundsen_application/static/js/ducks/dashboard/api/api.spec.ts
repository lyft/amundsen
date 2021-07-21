import axios, { AxiosResponse } from 'axios';

import { dashboardMetadata } from 'fixtures/metadata/dashboard';

import * as API from './v0';

jest.mock('axios');

describe('getDashboard', () => {
  let axiosMockGet;
  it('resolves with object containing dashboard metadata and status code', async () => {
    const mockStatus = 200;
    const mockResponse = {
      data: {
        dashboard: dashboardMetadata,
        msg: 'success',
      },
      status: mockStatus,
    };
    axiosMockGet = jest
      .spyOn(axios, 'get')
      .mockImplementationOnce(() => Promise.resolve(mockResponse));
    expect.assertions(2);
    await API.getDashboard('testUri').then((processedResponse) => {
      expect(processedResponse).toEqual({
        dashboard: dashboardMetadata,
        statusCode: mockStatus,
      });
    });
    expect(axiosMockGet).toHaveBeenCalled();
  });

  it('catches error and resolves with object containing error information', async () => {
    const mockStatus = 500;
    const mockMessage = 'oops';
    const mockResponse = {
      response: {
        data: {
          msg: mockMessage,
        },
        status: mockStatus,
      },
    };
    axiosMockGet = jest
      .spyOn(axios, 'get')
      .mockImplementationOnce(() => Promise.reject(mockResponse));
    expect.assertions(2);
    await API.getDashboard('testUri').catch((processedResponse) => {
      expect(processedResponse).toEqual({
        statusMessage: mockMessage,
        statusCode: mockStatus,
      });
    });
    expect(axiosMockGet).toHaveBeenCalled();
  });
});
