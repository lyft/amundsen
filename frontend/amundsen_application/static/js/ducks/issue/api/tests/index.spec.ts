import axios from 'axios';
import { NotificationType } from 'interfaces';
import AppConfig from 'config/config';
import * as API from '../v0';

jest.mock('axios');

describe('getIssues', () => {
  let mockGetResponse;
  let axiosMock;
  beforeAll(() => {
    mockGetResponse = {
      data: {
        issues: [],
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

  it('calls axios with correct parameters if tableKey provided', async () => {
    expect.assertions(1);
    await API.getIssues('tableKey').then(() => {
      expect(axiosMock).toHaveBeenCalledWith(
        `${API.API_PATH}/issues?key=tableKey`
      );
    });
  });

  it('returns response data', async () => {
    expect.assertions(1);

    await API.getIssues('tableKey').then((data) => {
      expect(data).toEqual(mockGetResponse.data.issues);
    });
  });

  afterAll(() => {
    axiosMock.mockClear();
  });
});

describe('createIssue', () => {
  let mockGetResponse;
  let axiosMock;
  const issueResult = { issue_key: 'key', data_issue_url: 'url' };
  let createIssuePayload;
  let sendNotificationPayload;
  beforeAll(() => {
    mockGetResponse = {
      data: {
        issue: issueResult,
        msg: 'Success',
      },
      status: 200,
      statusText: '',
      headers: {},
      config: {},
    };
    createIssuePayload = {
      key: 'key',
      title: 'title',
      description: 'description',
    };
    sendNotificationPayload = {
      owners: ['owner1'],
      sender: 'sender',
      notificationType: NotificationType.DATA_ISSUE_REPORTED,
      options: {
        resource_name: 'resource_name',
        resource_path: 'resource_path',
        data_issue_url: 'url',
      },
    };
    axiosMock = jest
      .spyOn(axios, 'post')
      .mockImplementation(() => Promise.resolve(mockGetResponse));
  });

  it('returns response data', async () => {
    AppConfig.mailClientFeatures.notificationsEnabled = false;
    expect.assertions(3);
    await API.createIssue(createIssuePayload, sendNotificationPayload).then(
      (data) => {
        expect(data).toEqual(issueResult);
        expect(axiosMock).toHaveBeenCalledWith(
          `${API.API_PATH}/issue`,
          createIssuePayload
        );
        expect(axiosMock).toHaveBeenCalledTimes(1);
      }
    );
  });

  it('submits a notification if notifications are enabled', async () => {
    AppConfig.mailClientFeatures.notificationsEnabled = true;
    expect.assertions(3);
    await API.createIssue(createIssuePayload, sendNotificationPayload).then(
      (data) => {
        expect(data).toEqual(issueResult);
        expect(axiosMock).toHaveBeenCalledWith(
          `${API.API_PATH}/issue`,
          createIssuePayload
        );
        expect(axiosMock).toHaveBeenCalledWith(
          API.NOTIFICATION_API_PATH,
          sendNotificationPayload
        );
      }
    );
  });

  afterAll(() => {
    axiosMock.mockClear();
  });
});
