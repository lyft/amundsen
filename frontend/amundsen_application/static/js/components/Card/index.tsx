// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { Link } from 'react-router-dom';

import './styles.scss';

export interface CardProps {
  title?: string;
  subtitle?: string;
  copy?: string | JSX.Element;
  isLoading?: boolean;
  href?: string;
  onClick?: (e: React.SyntheticEvent) => void;
}

const CardShimmerLoader: React.FC = () => (
  <div className="card-shimmer-loader">
    <div className="card-shimmer-row shimmer-row-line--1 is-shimmer-animated" />
    <div className="card-shimmer-row shimmer-row-line--2 is-shimmer-animated" />
    <div className="card-shimmer-row shimmer-row-line--3 is-shimmer-animated" />

    <div className="card-shimmer-loader-body">
      <div className="card-shimmer-row shimmer-row-line--4 is-shimmer-animated" />
      <div className="card-shimmer-row shimmer-row-line--5 is-shimmer-animated" />
    </div>
  </div>
);

const Card: React.FC<CardProps> = ({
  href,
  title,
  subtitle,
  copy,
  onClick = undefined,
  isLoading = false,
}: CardProps) => {
  let card;
  let cardContent = (
    <>
      <header className="card-header">
        {title && <h2 className="card-title">{title}</h2>}
        {subtitle && <h3 className="card-subtitle">{subtitle}</h3>}
      </header>
      <div className="card-body">
        {copy && <div className="card-copy">{copy}</div>}
      </div>
    </>
  );

  if (isLoading) {
    cardContent = <CardShimmerLoader />;
  }

  if (href) {
    card = (
      <Link
        className={`card is-link ${isLoading ? 'is-loading' : ''}`}
        to={href}
        onClick={onClick}
      >
        {cardContent}
      </Link>
    );
  } else {
    card = (
      <article className={`card ${isLoading ? 'is-loading' : ''}`}>
        {cardContent}
      </article>
    );
  }

  return <>{card}</>;
};

export default Card;
