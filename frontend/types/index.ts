export interface BookMetadata {
  id: string;
  title: string;
  author: string;
  language: string;
  subject: string[];
  release_date: string;
  downloads: number;
  cover_url: string;
}

export interface BookData {
  metadata: BookMetadata;
  content_preview: string;
  content_length: number;
}

export interface Relationship {
  character: string;
  type: string;
  strength?: number;
}

export interface Character {
  name: string;
  aliases?: string[];
  role: string;
  description: string;
  relationships?: Relationship[];
}

export interface GraphNode {
  id: string;
  size: number;
  role: string;
  description?: string;
}

export interface GraphLink {
  source: string;
  target: string;
  value: number;
  type: string;
}

export interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

export interface Theme {
  name: string;
  description: string;
}

export interface Sentiment {
  overall: string;
  analysis: string;
}

export interface Quote {
  quote: string;
  speaker?: string;
  context: string;
  significance: string;
}

export interface AnalysisData {
  characters: Character[];
  graph: GraphData;
  themes: Theme[];
  sentiment: Sentiment;
  key_quotes: Quote[];
}

export interface AnalysisStatus {
  status: "processing" | "complete" | "error" | "not_found";
  message?: string;
  progress?: number;
  stage?: string;
  partial_results?: Partial<AnalysisData>;
}

export interface BookFetchStatus {
  status: "processing" | "complete" | "error" | "not_found";
  message?: string;
  progress?: number;
  stage?: string;
}

export interface PartialAnalysisData {
  characters?: Character[];
  graph?: GraphData;
  themes?: Theme[];
  sentiment?: Sentiment;
  key_quotes?: Quote[];
}
