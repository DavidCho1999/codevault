import type { SearchItem } from "./types";

export function searchCode(
  index: SearchItem[],
  query: string,
  limit: number = 50
): SearchItem[] {
  if (!query.trim()) return [];

  const terms = query.toLowerCase().split(/\s+/).filter(Boolean);

  const results = index
    .map((item) => {
      const searchText = `${item.id} ${item.title} ${item.content}`.toLowerCase();
      let score = 0;

      for (const term of terms) {
        // Exact ID match gets highest score
        if (item.id.toLowerCase() === term) {
          score += 100;
        }
        // ID contains term
        else if (item.id.toLowerCase().includes(term)) {
          score += 50;
        }
        // Title match
        if (item.title.toLowerCase().includes(term)) {
          score += 30;
        }
        // Content match
        if (item.content.toLowerCase().includes(term)) {
          score += 10;
          // Bonus for multiple occurrences
          const occurrences = (
            item.content.toLowerCase().match(new RegExp(term, "g")) || []
          ).length;
          score += Math.min(occurrences, 5) * 2;
        }
      }

      return { item, score };
    })
    .filter((r) => r.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, limit)
    .map((r) => r.item);

  return results;
}

export function highlightText(text: string, query: string): string {
  if (!query.trim()) return text;

  const terms = query.split(/\s+/).filter(Boolean);
  let result = text;

  for (const term of terms) {
    const regex = new RegExp(`(${escapeRegex(term)})`, "gi");
    result = result.replace(regex, "**$1**");
  }

  return result;
}

function escapeRegex(string: string): string {
  return string.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

export function getSnippet(content: string, query: string, maxLength: number = 200): string {
  if (!content) return "";

  const terms = query.toLowerCase().split(/\s+/).filter(Boolean);
  const lowerContent = content.toLowerCase();

  // Find the first match position
  let matchIndex = -1;
  for (const term of terms) {
    const idx = lowerContent.indexOf(term);
    if (idx !== -1 && (matchIndex === -1 || idx < matchIndex)) {
      matchIndex = idx;
    }
  }

  if (matchIndex === -1) {
    // No match found, return start of content
    return content.slice(0, maxLength) + (content.length > maxLength ? "..." : "");
  }

  // Get snippet around the match
  const start = Math.max(0, matchIndex - 50);
  const end = Math.min(content.length, matchIndex + maxLength - 50);

  let snippet = content.slice(start, end);
  if (start > 0) snippet = "..." + snippet;
  if (end < content.length) snippet = snippet + "...";

  return snippet;
}
