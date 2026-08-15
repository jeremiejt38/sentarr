export type Status = 'pending' | 'in_progress' | 'completed' | 'error' | 'not_applicable';
export type AcquisitionStatus =
  | 'queued'
  | 'downloading'
  | 'completed'
  | 'imported'
  | 'failed'
  | 'unmatched';

export interface ArrItem {
  id: number;
  title: string;
  profileLabel?: string;
  status: AcquisitionStatus;
  progress?: number;
}

export interface TimelineStep {
  key: string;
  label: string;
  status: Status | AcquisitionStatus;
  startedAt?: string;
  completedAt?: string;
  errorMessage?: string | null;
}

export interface TreeNode {
  id: number;
  label: string;
  status: Status | AcquisitionStatus;
  progress?: number;
  children?: TreeNode[];
}
