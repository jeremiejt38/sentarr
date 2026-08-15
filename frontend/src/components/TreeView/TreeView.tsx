import { useState } from 'react';
import { ProgressBar } from '../ProgressBar/ProgressBar';
import { StatusBadge } from '../StatusBadge/StatusBadge';
import type { TreeNode } from '../../lib/arr.types';
import './tree-view.css';

interface TreeViewProps {
  nodes: TreeNode[];
}

function TreeNodeItem({ node, depth = 0 }: { node: TreeNode; depth?: number }) {
  const [expanded, setExpanded] = useState(true);
  const hasChildren = node.children && node.children.length > 0;

  return (
    <li className="tree-view__node">
      <div
        className="tree-view__row"
        style={{ paddingLeft: `${depth * 20}px` }}
        onClick={() => hasChildren && setExpanded(!expanded)}
        role={hasChildren ? 'button' : undefined}
        aria-expanded={hasChildren ? expanded : undefined}
      >
        {hasChildren ? (
          <span className="tree-view__toggle">{expanded ? '−' : '+'}</span>
        ) : (
          <span className="tree-view__toggle tree-view__toggle--leaf" />
        )}
        <span className="tree-view__label">{node.label}</span>
        <StatusBadge status={node.status} />
        {typeof node.progress === 'number' ? (
          <ProgressBar value={node.progress} />
        ) : null}
      </div>
      {hasChildren && expanded ? (
        <ul className="tree-view__children">
          {node.children!.map((child) => (
            <TreeNodeItem key={child.id} node={child} depth={depth + 1} />
          ))}
        </ul>
      ) : null}
    </li>
  );
}

export function TreeView({ nodes }: TreeViewProps) {
  return (
    <ul className="tree-view">
      {nodes.map((node) => (
        <TreeNodeItem key={node.id} node={node} />
      ))}
    </ul>
  );
}
