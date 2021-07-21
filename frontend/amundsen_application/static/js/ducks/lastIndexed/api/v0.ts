import axios, { AxiosResponse } from 'axios';

export const API_PATH = '/api/metadata/v0';

type MessageAPI = { msg: string };

export type LastIndexedAPI = { timestamp: string } & MessageAPI;

export function getLastIndexed() {
  return axios
    .get(`${API_PATH}/get_last_indexed`)
    .then((response: AxiosResponse<LastIndexedAPI>) => {
      const { data } = response;

      return data.timestamp;
    })
    .catch(() => {
      const timestamp = null;
      return Promise.reject({
        timestamp,
      });
    });
}
