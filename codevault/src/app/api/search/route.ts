import { NextRequest } from "next/server";
import { searchCode } from "@/lib/search";
import type { SearchItem } from "@/lib/types";
import indexData from "../../../../public/data/part9-index.json";

// 서버에서만 인덱스 데이터를 로드
const searchIndex = indexData as SearchItem[];

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const query = searchParams.get("q") || "";
  const limit = parseInt(searchParams.get("limit") || "50", 10);

  if (!query.trim()) {
    return Response.json({ results: [], query: "" });
  }

  const results = searchCode(searchIndex, query, limit);

  return Response.json({
    results,
    query,
    total: results.length,
  });
}
