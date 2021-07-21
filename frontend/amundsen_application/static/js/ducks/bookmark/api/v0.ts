import axios, { AxiosResponse } from 'axios';

import { ResourceType } from 'interfaces';

export const API_PATH = '/api/metadata/v0';
// TODO - Consider moving 'Bookmarks' under 'User'
// TODO: Define types for the AxiosResponse data

export function addBookmark(resourceKey: string, resourceType: ResourceType) {
  return axios
    .put(`${API_PATH}/user/bookmark`, { type: resourceType, key: resourceKey })
    .then((response: AxiosResponse) => response.data);
}

export function removeBookmark(
  resourceKey: string,
  resourceType: ResourceType
) {
  return axios
    .delete(`${API_PATH}/user/bookmark`, {
      data: { type: resourceType, key: resourceKey },
    })
    .then((response: AxiosResponse) => response.data);
}

export function getBookmarks(userId?: string) {
  return axios
    .get(`${API_PATH}/user/bookmark` + (userId ? `?user_id=${userId}` : ''))
    .then((response: AxiosResponse) => response.data);
}
