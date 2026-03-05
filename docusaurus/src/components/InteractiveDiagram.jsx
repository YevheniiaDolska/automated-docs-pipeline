import React from 'react';

/**
 * Embeds an interactive HTML diagram via iframe.
 * Works with diagram files from docs/diagrams/ or templates/interactive-diagram.html.
 *
 * Usage in MDX:
 *   import InteractiveDiagram from '@site/src/components/InteractiveDiagram';
 *   <InteractiveDiagram src="/diagrams/cloud-architecture.html" title="Cloud architecture" />
 */
export default function InteractiveDiagram({ src, title, height = 650 }) {
  return (
    <figure style={{
      margin: '1.5rem 0',
      borderRadius: '12px',
      overflow: 'hidden',
      boxShadow: '0 4px 20px rgba(0, 0, 0, 0.15)',
    }}>
      <iframe
        src={src}
        title={title || 'Interactive diagram'}
        width="100%"
        height={height}
        style={{ border: 'none', display: 'block' }}
        loading="lazy"
      />
      {title && (
        <figcaption style={{
          background: 'var(--ifm-code-background, #f5f5f5)',
          padding: '0.5rem 1rem',
          fontSize: '0.8rem',
          color: 'var(--ifm-color-emphasis-600, #666)',
          textAlign: 'center',
        }}>
          {title}
        </figcaption>
      )}
    </figure>
  );
}
