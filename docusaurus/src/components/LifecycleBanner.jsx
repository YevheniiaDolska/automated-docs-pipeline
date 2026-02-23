import React from 'react';

/**
 * LifecycleBanner -- displays a lifecycle status banner at the top of a page.
 *
 * Usage in MDX:
 *   import LifecycleBanner from '@site/src/components/LifecycleBanner';
 *   <LifecycleBanner status="deprecated" since="2024-01-15" replacement="/docs/new-page" />
 *
 * Props:
 *   status       - 'preview' | 'beta' | 'deprecated' | 'removed'
 *   since        - date string (for deprecated/removed)
 *   replacement  - URL to replacement doc (optional)
 *   sunset       - planned removal date (optional, for deprecated)
 */

const MESSAGES = {
  preview: {
    emoji: '🔬',
    label: 'Preview',
    text: 'This feature is in preview and may change without notice.',
  },
  beta: {
    emoji: '🧪',
    label: 'Beta',
    text: 'This feature is in beta. The API is stable but details may change.',
  },
  deprecated: {
    emoji: '⚠️',
    label: 'Deprecated',
    text: 'This feature is deprecated',
  },
  removed: {
    emoji: '🚫',
    label: 'Removed',
    text: 'This feature has been removed',
  },
};

export default function LifecycleBanner({ status, since, replacement, sunset }) {
  const info = MESSAGES[status];
  if (!info) return null;

  let message = info.text;

  if (status === 'deprecated' && since) {
    message += ` since ${since}`;
    if (sunset) {
      message += ` and will be removed on ${sunset}`;
    }
    message += '.';
  } else if (status === 'removed' && since) {
    message += ` on ${since}.`;
  } else {
    message += '.';
  }

  return (
    <div className={`lifecycle-banner lifecycle-banner--${status}`}>
      <strong>
        {info.emoji} {info.label}
      </strong>
      {': '}
      {message}
      {replacement && (
        <>
          {' '}
          See the <a href={replacement}>replacement documentation</a>.
        </>
      )}
    </div>
  );
}
