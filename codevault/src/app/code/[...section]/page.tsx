import { notFound } from "next/navigation";
import SectionView from "@/components/code/SectionView";
import { getNodeById, getChildNodes, getTablesByNodeId, getPartFullContent } from "@/lib/db";

interface PageProps {
  params: Promise<{ section: string[] }>;
  searchParams: Promise<{ highlight?: string }>;
}

export default async function CodePage({ params, searchParams }: PageProps) {
  const { section } = await params;
  const { highlight } = await searchParams;
  const sectionId = section.join(".");

  // Part 번호만 있는 경우 (예: /code/10, /code/11)
  if (section.length === 1 && /^\d+$/.test(section[0])) {
    const partNum = section[0];
    const { sections, allContent } = getPartFullContent(partNum);

    if (sections.length === 0) {
      notFound();
    }

    const partNames: Record<string, string> = {
      "2": "Objectives",
      "6": "Heating, Ventilating and Air-Conditioning",
      "7": "Plumbing",
      "8": "Sewage Systems",
      "9": "Housing and Small Buildings",
      "10": "Change of Use",
      "11": "Renovation",
      "12": "Resource Conservation and Environmental Integrity",
    };

    const isMarkdown = parseInt(partNum, 10) >= 10;

    return (
      <div className="p-8">
        <SectionView
          id={partNum}
          title={partNames[partNum] || `Part ${partNum}`}
          content={allContent}
          highlight={highlight}
          tables={{}}
          content_format={isMarkdown ? "markdown" : undefined}
        />
      </div>
    );
  }

  // DB에서 노드 조회
  const node = getNodeById(sectionId);

  if (!node) {
    notFound();
  }

  // 자식 노드와 테이블 조회
  const children = getChildNodes(sectionId);
  const tables = getTablesByNodeId(sectionId);

  // 하위 노드 content 합치기 (재귀적)
  let content = node.content || "";

  // Part 번호 확인 (Part 10 이상은 markdown 형식)
  const partNum = parseInt(sectionId.split(".")[0], 10);
  const isMarkdown = partNum >= 10;

  // Section/Subsection/Alt Subsection인 경우: 하위 Article까지 content 수집
  if ((node.type === "section" || node.type === "subsection" || node.type === "alt_subsection") && children.length > 0) {
    const childContents: string[] = [];

    for (const child of children) {
      // Subsection/Alt Subsection인 경우 헤딩 먼저 추가
      if (child.type === "subsection" || child.type === "alt_subsection") {
        childContents.push(`[SUBSECTION:${child.id}:${child.title || ""}]`);
      }

      if (child.content) {
        // Part 10+는 마커 없이 content만 추가
        if (isMarkdown) {
          childContents.push(child.content);
        } else {
          // Subsection은 이미 [SUBSECTION:...] 마커가 추가됨, content만 추가
          // Article인 경우만 [ARTICLE:...] 마커 추가
          if (child.type === "subsection" || child.type === "alt_subsection") {
            childContents.push(child.content);
          } else {
            // Part 9 Article: ID와 Title을 특수 마커로
            childContents.push(`[ARTICLE:${child.id}:${child.title || ""}]\n${child.content}`);
          }
        }
      } else {
        // 자식에 content가 없으면 손자(Article) 조회
        const grandChildren = getChildNodes(child.id);

        for (const grandChild of grandChildren) {
          if (grandChild.content) {
            if (isMarkdown) {
              childContents.push(grandChild.content);
            } else {
              childContents.push(`[ARTICLE:${grandChild.id}:${grandChild.title || ""}]\n${grandChild.content}`);
            }
          }
        }
      }
    }

    content = childContents.join("\n\n");
  }

  // 테이블 HTML을 content에 포함 (테이블 ID 기준으로 삽입 위치 결정)
  // 일단은 단순히 테이블 목록으로 전달
  const tableHtmlMap: Record<string, string> = {};
  for (const table of tables) {
    tableHtmlMap[table.id] = table.html;
  }

  // Part 10 이상은 markdown 형식
  const content_format = isMarkdown ? "markdown" : undefined;

  return (
    <div className="p-8">
      <SectionView
        id={node.id}
        title={node.title || ""}
        content={content}
        highlight={highlight}
        tables={tableHtmlMap}
        content_format={content_format}
      />
    </div>
  );
}

// 동적 생성 (SSG 비활성화)
export const dynamic = "force-dynamic";
