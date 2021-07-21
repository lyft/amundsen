// Copyright Contributors to the Amundsen project.
// SPDX-License-Identifier: Apache-2.0

import * as React from 'react';
import { CopyBlock, atomOneLight } from 'react-code-blocks';
import './styles.scss';

const LANGUAGE = 'sql';

type CodeBlockProps = {
  text: string;
  children?: JSX.Element;
};

const CodeBlock: React.FC<CodeBlockProps> = ({
  text,
  children,
}: CodeBlockProps) => (
  <div className="code-block-container">
    {children}
    <CopyBlock
      text={text}
      language={LANGUAGE}
      theme={atomOneLight}
      showLineNumbers={false}
      wrapLines
      codeBlock
    />
  </div>
);

export default CodeBlock;
