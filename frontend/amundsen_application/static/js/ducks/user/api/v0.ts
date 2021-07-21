import axios, { AxiosResponse } from 'axios';
import * as qs from 'simple-query-string';

import { LoggedInUser, PeopleUser, Resource } from 'interfaces';

export type LoggedInUserAPI = { user: LoggedInUser; msg: string };
export type UserAPI = { user: PeopleUser; msg: string };
export type UserOwnAPI = { own: Resource[]; msg: string };
export type UserReadAPI = { read: Resource[]; msg: string };

export function getLoggedInUser() {
  return axios
    .get(`/api/auth_user`)
    .then((response: AxiosResponse<LoggedInUserAPI>) => response.data.user);
}

export function getUser(userId: string, index?: string, source?: string) {
  const queryParams = qs.stringify({ index, source, user_id: userId });

  return axios
    .get(`/api/metadata/v0/user?${queryParams}`)
    .then((response: AxiosResponse<UserAPI>) => response.data.user);
}

export function getUserOwn(userId: string) {
  return axios
    .get(`/api/metadata/v0/user/own?user_id=${userId}`)
    .then((response: AxiosResponse<UserOwnAPI>) => response.data);
}

export function getUserRead(userId: string) {
  return axios
    .get(`/api/metadata/v0/user/read?user_id=${userId}`)
    .then((response: AxiosResponse<UserReadAPI>) => response.data);
}
