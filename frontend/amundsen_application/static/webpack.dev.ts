import merge from 'webpack-merge';
import MiniCssExtractPlugin from 'mini-css-extract-plugin';
// import { BundleAnalyzerPlugin } from 'webpack-bundle-analyzer';

import commonConfig from './webpack.common';

const webpack = require('webpack');

export default merge(commonConfig, {
  mode: 'development',
  devtool: 'inline-source-map',
  plugins: [
    new MiniCssExtractPlugin({
      filename: '[name].dev.css',
    }),
    // fix "process is not defined" error:
    new webpack.ProvidePlugin({
      process: 'process/browser',
    }),
    // new BundleAnalyzerPlugin()     // Uncomment to check the bundle size on dev
  ],
  output: {
    filename: '[name].dev.js',
  },
});
