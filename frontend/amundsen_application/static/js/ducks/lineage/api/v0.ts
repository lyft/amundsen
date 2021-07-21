import axios, { AxiosError, AxiosResponse } from 'axios';
import { Lineage } from 'interfaces/Lineage';
import { getQueryParams } from 'ducks/utilMethods';

export const API_PATH = '/api/metadata/v0';

export type LineageAPI = { lineage: Lineage };

export function getTableLineage(
  key: string,
  depth: number = 1,
  direction: string = 'both'
) {
  const tableQueryParams = getQueryParams({ key, depth, direction });
  return axios
    .get(`${API_PATH}/get_table_lineage?${tableQueryParams}`)
    .then((response: AxiosResponse<LineageAPI>) => ({
      data: response.data,
      statusCode: response.status,
    }))
    .catch((e: AxiosError<LineageAPI>) => {
      const { response } = e;
      const statusCode = response?.status;
      return Promise.reject({ statusCode });
    });
}

export function getFeatureLineage(
  key: string,
  depth: number = 1,
  direction: string = 'upstream'
) {
  const tableQueryParams = getQueryParams({ key, depth, direction });
  return axios
    .get(`${API_PATH}/get_feature_lineage?${tableQueryParams}`)
    .then((response: AxiosResponse<LineageAPI>) => ({
      data: response.data,
      statusCode: response.status,
    }))
    .catch((e: AxiosError<LineageAPI>) => {
      const { response } = e;
      const status = response ? response.status : null;
      return Promise.reject({ status });
    });
}

export function getColumnLineage(
  key: string,
  columnName: string,
  depth: number,
  direction: string
) {
  const tableQueryParams = getQueryParams({
    key,
    depth,
    direction,
    column_name: columnName,
  });
  return axios
    .get(`${API_PATH}/get_column_lineage?${tableQueryParams}`)
    .then((response: AxiosResponse<LineageAPI>) => ({
      data: response.data,
      statusCode: response.status,
    }))
    .catch((e: AxiosError<LineageAPI>) => {
      const { response } = e;
      const statusCode = response?.status;
      return Promise.reject({ statusCode });
    });
}
