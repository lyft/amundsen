import axios, { AxiosResponse } from 'axios';

import { AnnouncementPost } from 'interfaces';

export type AnnouncementsAPI = {
  msg: string;
  posts: AnnouncementPost[];
};

const SERVER_ERROR_CODE = 500;

export function getAnnouncements() {
  return axios({
    method: 'get',
    url: '/api/announcements/v0/',
  })
    .then((response: AxiosResponse<AnnouncementsAPI>) => {
      const { data, status } = response;

      return {
        posts: data.posts,
        statusCode: status,
      };
    })
    .catch((e) => {
      const { response } = e;
      const statusCode = response
        ? response.status || SERVER_ERROR_CODE
        : SERVER_ERROR_CODE;

      return Promise.reject({
        posts: [],
        statusCode,
      });
    });
}
