// Ontario Building Code Data Types

export interface TocItem {
  id: string;
  title: string;
  children: TocItem[];
}

export interface Subsection {
  id: string;
  title: string;
  page: number;
  content: string;
  articles: Article[];
}

export interface Article {
  id: string;
  title: string;
  content: string;
}

export interface Section {
  id: string;
  title: string;
  page: number;
  subsections: Subsection[];
}

export interface Part {
  id: string;
  title: string;
  sections: Section[];
}

export interface SearchItem {
  id: string;
  title: string;
  section: string;
  sectionId: string;
  content: string;
  page: number;
  path: string;
}
