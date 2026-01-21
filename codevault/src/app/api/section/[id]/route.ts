import { NextRequest } from "next/server";
import {
  getNodeById,
  getChildNodes,
  getTablesByNodeId,
  DbNode,
  DbTable,
} from "@/lib/db";

interface SectionResponse {
  node: DbNode;
  children: DbNode[];
  tables: DbTable[];
  breadcrumb: DbNode[];
}

// breadcrumb 생성 (상위 노드들)
function getBreadcrumb(nodeId: string): DbNode[] {
  const breadcrumb: DbNode[] = [];
  let current = getNodeById(nodeId);

  while (current) {
    breadcrumb.unshift(current);
    if (current.parent_id) {
      current = getNodeById(current.parent_id);
    } else {
      break;
    }
  }

  return breadcrumb;
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

  try {
    const node = getNodeById(id);

    if (!node) {
      return Response.json({ error: "Section not found" }, { status: 404 });
    }

    const children = getChildNodes(id);
    const tables = getTablesByNodeId(id);
    const breadcrumb = getBreadcrumb(id);

    const response: SectionResponse = {
      node,
      children,
      tables,
      breadcrumb,
    };

    return Response.json(response);
  } catch (error) {
    console.error("Section fetch error:", error);
    const errorMessage = error instanceof Error ? error.message : String(error);
    return Response.json(
      { error: "Failed to fetch section", message: errorMessage },
      { status: 500 }
    );
  }
}
