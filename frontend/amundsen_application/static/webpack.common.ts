// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as path from 'path';
import * as fs from 'fs';
import * as webpack from 'webpack';
import HtmlWebpackPlugin from 'html-webpack-plugin';
import MiniCssExtractPlugin from 'mini-css-extract-plugin';
// import {BundleAnalyzerPlugin} from 'webpack-bundle-analyzer';
import MomentLocalesPlugin from 'moment-locales-webpack-plugin';
import { CleanWebpackPlugin } from 'clean-webpack-plugin';

import appConfig from './js/config/config';

function resolve(dir) {
  return path.join(__dirname, dir);
}

const TSX_PATTERN = /\.ts|\.tsx$/;
const JSX_PATTERN = /\.jsx?$/;
const CSS_PATTERN = /\.(sa|sc|c)ss$/;
const IMAGE_PATTERN = /\.(png|svg|jpg|gif)$/;
const VENDORS_PATTERN = /[\\/]node_modules[\\/](react|react-dom)[\\/]/;
const FONT_PATTERN = /\.(ttf|woff2|otf)$/;
const RESOLVED_EXTENSIONS = ['.tsx', '.ts', '.js', '.jsx', '.css', '.scss'];

const PATHS = {
  dist: resolve('/dist'),
  pages: resolve('/js/pages'),
  components: resolve('/js/components'),
  features: resolve('/js/features'),
  config: resolve('/js/config'),
  ducks: resolve('/js/ducks'),
  interfaces: resolve('/js/interfaces'),
  utils: resolve('/js/utils'),
  css: resolve('/css/'),
};

// Process of Templates
const walkSync = (dir: string, filelist: string[] = []) => {
  fs.readdirSync(dir).forEach((file) => {
    filelist = fs.statSync(path.join(dir, file)).isDirectory()
      ? walkSync(path.join(dir, file), filelist)
      : filelist.concat(path.join(dir, file));
  });
  return filelist;
};
const templatesList = walkSync('templates');
const htmlWebpackPluginConfig = templatesList.map(
  (file) =>
    new HtmlWebpackPlugin({
      filename: file,
      template: file,
      config: appConfig,
      inject: false,
    })
);

const config: webpack.Configuration = {
  entry: {
    main: [resolve('/css/styles.scss'), resolve('/js/index.tsx')],
  },
  output: {
    publicPath: '/static/dist/',
    path: PATHS.dist,
    filename: '[name].[contenthash].js',
  },
  devtool: 'source-map',
  resolve: {
    alias: {
      pages: PATHS.pages,
      components: PATHS.components,
      features: PATHS.features,
      config: PATHS.config,
      ducks: PATHS.ducks,
      interfaces: PATHS.interfaces,
      utils: PATHS.utils,
    },
    extensions: RESOLVED_EXTENSIONS,
    fallback: {
      // Needed by react-markdown as of 5.0.2
      path: require.resolve('path-browserify'),
    },
  },
  module: {
    rules: [
      {
        test: TSX_PATTERN,
        loader: 'ts-loader',
      },
      {
        test: JSX_PATTERN,
        exclude: /node_modules/,
        use: 'babel-loader',
      },
      {
        test: CSS_PATTERN,
        use: [
          MiniCssExtractPlugin.loader,
          'css-loader',
          {
            loader: 'sass-loader',
            options: {
              sassOptions: {
                includePaths: [PATHS.css],
              },
            },
          },
        ],
      },
      {
        test: IMAGE_PATTERN,
        use: 'file-loader',
      },
      {
        test: FONT_PATTERN,
        use: 'file-loader',
      },
      // Hacky, required for react-bootstrap @ 0.33.1 - remove after upgrading,
      // see: https://github.com/webpack/webpack/issues/11467
      // Tracked at https://github.com/amundsen-io/amundsen/issues/818
      {
        test: /\.m?js$/,
        resolve: {
          fullySpecified: false,
        },
      },
    ],
  },
  plugins: [
    new CleanWebpackPlugin(),
    new MomentLocalesPlugin(), // To strip all locales except “en”
    ...htmlWebpackPluginConfig,
    // fix "process is not defined" error:
    new webpack.ProvidePlugin({
      process: 'process/browser',
    }),
  ],
  optimization: {
    moduleIds: 'deterministic',
    splitChunks: {
      cacheGroups: {
        default: false,
        major: {
          name: 'vendors',
          test: VENDORS_PATTERN,
          chunks: 'all',
        },
      },
    },
  },
};
export default config;
