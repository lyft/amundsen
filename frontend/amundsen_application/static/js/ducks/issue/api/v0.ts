import axios, { AxiosResponse } from 'axios';
import { Issue, CreateIssuePayload, NotificationPayload } from 'interfaces';
import { notificationsEnabled } from 'config/config-utils';

export const API_PATH = '/api/issue';
export const NOTIFICATION_API_PATH = '/api/mail/v0/notification';

export type IssuesAPI = {
  issues: {
    issues: Issue[];
    total: number;
    all_issues_url: string;
  };
};

export type IssueApi = {
  issue: Issue;
};

export function getIssues(tableKey: string) {
  return axios
    .get(`${API_PATH}/issues?key=${tableKey}`)
    .then((response: AxiosResponse<IssuesAPI>) => response.data.issues);
}

export function createIssue(
  payload: CreateIssuePayload,
  notificationPayload: NotificationPayload
) {
  return axios
    .post(`${API_PATH}/issue`, {
      key: payload.key,
      title: payload.title,
      description: payload.description,
    })
    .then((response: AxiosResponse<IssueApi>) => {
      if (notificationsEnabled()) {
        notificationPayload.options.data_issue_url = response.data.issue.url;
        axios.post(NOTIFICATION_API_PATH, notificationPayload);
      }
      return response.data.issue;
    });
}
