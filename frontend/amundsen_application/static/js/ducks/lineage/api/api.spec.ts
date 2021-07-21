import axios from 'axios';

import { tableLineage } from 'fixtures/metadata/table';

import * as API from './v0';

jest.mock('axios');

describe('getLineage', () => {
  let axiosMockGet;
  it('resolves with object containing table lineage and status code', async () => {
    const mockStatus = 200;
    const mockResponse = {
      data: tableLineage,
      status: mockStatus,
    };
    axiosMockGet = jest
      .spyOn(axios, 'get')
      .mockImplementationOnce(() => Promise.resolve(mockResponse));
    expect.assertions(2);
    await API.getTableLineage(
      'database://cluster.schema/table_name',
      1,
      'both'
    ).then((processedResponse) => {
      expect(processedResponse).toEqual({
        data: tableLineage,
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
    await API.getTableLineage('testUri', 1, 'both').catch(
      (processedResponse) => {
        expect(processedResponse).toEqual({
          statusCode: mockStatus,
        });
      }
    );
    expect(axiosMockGet).toHaveBeenCalled();
  });
});
