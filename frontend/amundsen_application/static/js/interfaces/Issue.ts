export interface Issue {
  issue_key: string;
  title: string;
  url: string;
  status: string;
  priority_name: string;
  priority_display_name: string;
}

export interface CreateIssuePayload {
  key: string;
  title: string;
  description: string;
}
