// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

const defaultConfig = {
  stats: [],
};

/**
 * Generates test data for the table data
 * @example
 * let testData = new TestDataBuilder()
 *                         .withEightStats()
 *                         .build();
 */
function TestDataBuilder(config = {}) {
  this.Klass = TestDataBuilder;
  this.config = {
    ...defaultConfig,
    ...config,
  };

  this.withSevenUniqueValues = () => {
    const attr = {
      uniqueValues: [
        {
          value: '2020-11-28',
          count: 2418200,
        },
        {
          value: '2020-11-26',
          count: 2265000,
        },
        {
          value: '2020-12-01',
          count: 1983000,
        },
        {
          value: '2020-11-27',
          count: 1903500,
        },
        {
          value: '2020-11-30',
          count: 1520800,
        },
        {
          value: '2020-11-29',
          count: 1286900,
        },
        {
          value: '2020-11-25',
          count: 281100,
        },
      ],
    };

    return new this.Klass(attr);
  };

  this.withVariableNumberOfUniqueValues = (numberOfValues) => {
    const dummyValue = {
      value: '2020-11-28',
      count: 2418200,
    };
    const attr = {
      uniqueValues: Array(numberOfValues)
        .fill(dummyValue)
        .map(({ value, count }, i) => ({ value: value + i, count })),
    };

    return new this.Klass(attr);
  };

  this.withOneUniqueValue = () => {
    const attr = {
      uniqueValues: [
        {
          value: '2020-11-28',
          count: 2418200,
        },
      ],
    };

    return new this.Klass(attr);
  };

  this.withEmptyUniqueValues = () => {
    const attr = { uniqueValues: [] };

    return new this.Klass(attr);
  };

  this.build = () => this.config;
}

export default TestDataBuilder;
