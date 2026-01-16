import Link from "next/link";
import tocData from "../../public/data/toc.json";

export default function Home() {
  return (
    <div className="p-8 max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Ontario Building Code 2024
        </h1>
        <p className="text-gray-600">
          Part 9 - Housing and Small Buildings
        </p>
      </div>

      <div className="grid gap-3">
        {tocData.map((section) => (
          <Link
            key={section.id}
            href={`/code/${section.id}`}
            className="block p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50/50 transition-colors"
          >
            <div className="flex items-start gap-3">
              <span className="font-mono text-sm text-blue-600 font-medium shrink-0">
                {section.id}
              </span>
              <div>
                <h2 className="font-medium text-gray-900">{section.title}</h2>
                {section.children.length > 0 && (
                  <p className="text-sm text-gray-500 mt-1">
                    {section.children.length} subsection{section.children.length > 1 ? "s" : ""}
                  </p>
                )}
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
