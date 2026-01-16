import { notFound } from "next/navigation";
import SectionView from "@/components/code/SectionView";
import part9Data from "../../../../public/data/part9.json";
import type { Part, Section, Subsection } from "@/lib/types";

interface PageProps {
  params: Promise<{ section: string[] }>;
}

function findContent(sectionPath: string[]): { id: string; title: string; content: string } | null {
  const data = part9Data as Part;
  const fullId = sectionPath.join(".");

  // Look for section (e.g., "9.1")
  for (const section of data.sections) {
    if (section.id === fullId) {
      // Return first subsection content if section has subsections
      if (section.subsections.length > 0) {
        const firstSub = section.subsections[0];
        return {
          id: section.id,
          title: section.title,
          content: section.subsections.map(s => s.content).join("\n\n"),
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
        };
      }
    }
  }

  return null;
}

export default async function CodePage({ params }: PageProps) {
  const { section } = await params;
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
