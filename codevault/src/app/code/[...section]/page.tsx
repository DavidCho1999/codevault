import { notFound } from "next/navigation";
import SectionView from "@/components/code/SectionView";
import part9Data from "../../../../public/data/part9.json";
import type { Part, Section, Subsection, EquationData } from "@/lib/types";

interface PageProps {
  params: Promise<{ section: string[] }>;
  searchParams: Promise<{ highlight?: string }>;
}

function findContent(sectionPath: string[]): { id: string; title: string; content: string; equations?: Record<string, EquationData> } | null {
  const data = part9Data as Part;
  const fullId = sectionPath.join(".");

  // Look for section (e.g., "9.1")
  for (const section of data.sections) {
    if (section.id === fullId) {
      // Return first subsection content if section has subsections
      if (section.subsections.length > 0) {
        // Merge all equations from subsections
        const allEquations: Record<string, EquationData> = {};
        for (const sub of section.subsections) {
          if (sub.equations) {
            Object.assign(allEquations, sub.equations);
          }
        }
        return {
          id: section.id,
          title: section.title,
          content: section.subsections.map(s => s.content).join("\n\n"),
          equations: Object.keys(allEquations).length > 0 ? allEquations : undefined,
        };
      }
      return { id: section.id, title: section.title, content: "" };
    }

    // Look for subsection (e.g., "9.1.1")
    for (const subsection of section.subsections) {
      if (subsection.id === fullId) {
        return {
          id: subsection.id,
          title: subsection.title,
          content: subsection.content,
          equations: subsection.equations,
        };
      }
    }
  }

  return null;
}

export default async function CodePage({ params, searchParams }: PageProps) {
  const { section } = await params;
  const { highlight } = await searchParams;
  const content = findContent(section);

  if (!content) {
    notFound();
  }

  return (
    <div className="p-8">
      <SectionView
        id={content.id}
        title={content.title}
        content={content.content}
        highlight={highlight}
        equations={content.equations}
      />
    </div>
  );
}

export async function generateStaticParams() {
  const data = part9Data as Part;
  const paths: { section: string[] }[] = [];

  for (const section of data.sections) {
    paths.push({ section: section.id.split(".") });
    for (const subsection of section.subsections) {
      paths.push({ section: subsection.id.split(".") });
    }
  }

  return paths;
}
