/**
 * OBC Part 9 주요 정의어 목록
 * 출처: Ontario Building Code, Division A, Article 1.4.1.2
 */

export interface Definition {
  term: string;
  definition: string;
  aliases?: string[]; // 대체 표기
}

export const definitions: Definition[] = [
  {
    term: "loadbearing",
    definition: "Subjected to or designed to carry loads in addition to its own weight.",
    aliases: ["load-bearing", "load bearing"],
  },
  {
    term: "fire separation",
    definition: "A construction assembly that acts as a barrier against the spread of fire.",
  },
  {
    term: "dwelling unit",
    definition: "A suite used or intended to be used by one or more persons as a residence.",
  },
  {
    term: "storey",
    definition: "The portion of a building between the top of any floor and the top of the floor next above it, or the space between any floor and the ceiling above it if there is no floor above.",
    aliases: ["story"],
  },
  {
    term: "occupancy",
    definition: "The use or intended use of a building or part thereof for the shelter or support of persons, animals or property.",
  },
  {
    term: "fire-resistance rating",
    definition: "The time in hours or minutes that a material or assembly of materials will withstand the passage of flame and the transmission of heat when exposed to fire.",
    aliases: ["fire resistance rating"],
  },
  {
    term: "combustible",
    definition: "A material that fails to meet the acceptance criteria of CAN/ULC-S114, 'Standard Method of Test for Determination of Non-Combustibility in Building Materials'.",
  },
  {
    term: "noncombustible",
    definition: "A material that meets the acceptance criteria of CAN/ULC-S114, 'Standard Method of Test for Determination of Non-Combustibility in Building Materials'.",
    aliases: ["non-combustible"],
  },
  {
    term: "firewall",
    definition: "A type of fire separation of noncombustible construction that subdivides a building or separates adjoining buildings to resist the spread of fire.",
  },
  {
    term: "fire compartment",
    definition: "An enclosed space in a building that is separated from all other parts of the building by enclosing construction that provides a fire separation.",
  },
  {
    term: "building height",
    definition: "The number of storeys contained between the roof and the floor of the first storey.",
  },
  {
    term: "grade",
    definition: "The lowest of the average levels of finished ground adjoining each exterior wall of a building.",
  },
  {
    term: "means of egress",
    definition: "A continuous path of travel provided for the escape of persons from any point in a building or contained open space to a public thoroughfare or other acceptable open space.",
  },
  {
    term: "exit",
    definition: "That part of a means of egress that leads from the floor area it serves to a public thoroughfare or an open exterior area.",
  },
  {
    term: "suite",
    definition: "A single room or series of rooms of complementary use, operated under a single tenancy.",
  },
  {
    term: "secondary suite",
    definition: "A dwelling unit that is ancillary to a principal dwelling unit on the same property.",
  },
  {
    term: "habitable room",
    definition: "A room intended for human occupancy that is equipped with a window.",
  },
  {
    term: "service room",
    definition: "A room provided in a building to contain equipment associated with building services.",
  },
  {
    term: "vapour barrier",
    definition: "A membrane or material that restricts the passage of water vapour.",
    aliases: ["vapor barrier"],
  },
  {
    term: "air barrier",
    definition: "A material or system designed and installed to provide a continuous barrier to the movement of air.",
  },
  {
    term: "thermal resistance",
    definition: "The resistance to heat flow (RSI) of a material or component of construction.",
  },
  {
    term: "crawl space",
    definition: "A space between the ground and the underside of the lowest floor assembly not exceeding 1.8 m in height.",
  },
  {
    term: "attic",
    definition: "The space between the roof and the ceiling of the top storey or between a dwarf wall and a sloping roof.",
  },
  {
    term: "basement",
    definition: "A storey or storeys below the first storey.",
  },
  {
    term: "joist",
    definition: "A horizontal structural member used to support a floor or ceiling.",
  },
  {
    term: "rafter",
    definition: "A structural member used to support a roof.",
  },
  {
    term: "stud",
    definition: "A vertical structural member used in walls and partitions.",
  },
  {
    term: "sheathing",
    definition: "Boards or sheet material fastened to joists, rafters or studs as a base for roofing, flooring or siding.",
  },
  {
    term: "cladding",
    definition: "Components of a building which form a part of the exterior wall but are non-loadbearing.",
  },
  {
    term: "flashing",
    definition: "A component used to direct water away from building elements.",
  },
];

// 정의어 검색용 맵 생성
export const definitionMap: Map<string, Definition> = new Map();

definitions.forEach((def) => {
  // 메인 용어 추가 (소문자)
  definitionMap.set(def.term.toLowerCase(), def);

  // aliases 추가
  if (def.aliases) {
    def.aliases.forEach((alias) => {
      definitionMap.set(alias.toLowerCase(), def);
    });
  }
});

// 정의어 패턴 생성 (정규식용)
export function getDefinitionPattern(): RegExp {
  const allTerms: string[] = [];

  definitions.forEach((def) => {
    allTerms.push(def.term);
    if (def.aliases) {
      allTerms.push(...def.aliases);
    }
  });

  // 긴 용어부터 매칭하도록 정렬
  allTerms.sort((a, b) => b.length - a.length);

  // 정규식 특수문자 이스케이프
  const escaped = allTerms.map((term) =>
    term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
  );

  // 단어 경계로 매칭 (대소문자 무시)
  return new RegExp(`\\b(${escaped.join("|")})\\b`, "gi");
}
