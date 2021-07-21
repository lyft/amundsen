import axios, { AxiosResponse } from 'axios';

import { Tag } from 'interfaces';

import * as API from '../v0';

describe('getAllTags', () => {
  it('resolves with array of sorted result of response.data.tags on success', async () => {
    const rawTags: Tag[] = [
      { tag_count: 2, tag_name: 'test' },
      { tag_count: 1, tag_name: 'atest' },
    ];
    const expectedTags: Tag[] = [
      { tag_count: 1, tag_name: 'atest' },
      { tag_count: 2, tag_name: 'test' },
    ];
    const mockResponse: AxiosResponse<API.AllTagsAPI> = {
      data: {
        tags: rawTags,
        msg: 'Success',
      },
      status: 200,
      statusText: '',
      headers: {},
      config: {},
    };

    jest
      .spyOn(axios, 'get')
      .mockImplementation(() => Promise.resolve(mockResponse));

    expect.assertions(1);

    await API.getAllTags().then((sortedTags) => {
      expect(sortedTags).toEqual(expectedTags);
    });
  });
});
