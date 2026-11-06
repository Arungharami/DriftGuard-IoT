/**
 * Minimal, dependency-free parser for the CNT 6167 manuscript source (src/content/paper.md).
 *
 * It understands exactly the subset the manuscript uses: one H1 title, an author line, H2/H3
 * headings, paragraphs, ordered and bullet lists, pipe tables, ```latex display maths,
 * `{{figure:key|caption}}` and `{{widget:key}}` markers. Anything else is kept as a paragraph.
 */

export type PaperBlock =
  | { type: "h2"; id: string; text: string }
  | { type: "h3"; id: string; text: string }
  | { type: "p"; text: string }
  | { type: "caption"; text: string }
  | { type: "list"; ordered: boolean; items: string[] }
  | { type: "table"; head: string[]; rows: string[][] }
  | { type: "math"; tex: string; n: number }
  | { type: "figure"; key: string; caption: string }
  | { type: "widget"; key: string }
  | { type: "reference"; n: number; text: string };

export type PaperSection = { id: string; title: string; blocks: PaperBlock[] };

export type Paper = {
  title: string;
  authors: string;
  sections: PaperSection[];
  wordCount: number;
};

export function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/^[ivx]+\.\s+/, "")
    .replace(/^[a-h]\.\s+/, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

const splitRow = (line: string) =>
  line
    .trim()
    .replace(/^\||\|$/g, "")
    .split("|")
    .map((c) => c.trim());

export function parsePaper(source: string): Paper {
  const lines = source.replace(/\r\n/g, "\n").split("\n");
  let title = "";
  let authors = "";
  const sections: PaperSection[] = [];
  let current: PaperSection | null = null;
  let inReferences = false;
  let parentId = "";
  const push = (block: PaperBlock) => {
    if (!current) return;
    current.blocks.push(block);
  };

  const at = (k: number) => lines[k] ?? "";
  let equations = 0;
  let i = 0;
  while (i < lines.length) {
    const line = at(i);
    const trimmed = line.trim();
    if (trimmed === "") {
      i += 1;
      continue;
    }
    if (trimmed.startsWith("# ")) {
      title = trimmed.slice(2).trim();
      i += 1;
      continue;
    }
    if (trimmed.startsWith("## ")) {
      const text = trimmed.slice(3).trim();
      const id = slugify(text);
      current = { id, title: text, blocks: [] };
      sections.push(current);
      parentId = id;
      inReferences = /^references$/i.test(text);
      current.blocks.push({ type: "h2", id, text });
      i += 1;
      continue;
    }
    if (trimmed.startsWith("### ")) {
      const text = trimmed.slice(4).trim();
      push({ type: "h3", id: `${parentId}-${slugify(text)}`, text });
      i += 1;
      continue;
    }
    if (trimmed.startsWith("```")) {
      const body: string[] = [];
      i += 1;
      while (i < lines.length && !at(i).trim().startsWith("```")) {
        body.push(at(i));
        i += 1;
      }
      i += 1;
      equations += 1;
      push({ type: "math", tex: body.join("\n").trim(), n: equations });
      continue;
    }
    const figure = trimmed.match(/^\{\{figure:([\w-]+)\|(.+)\}\}$/);
    if (figure) {
      push({ type: "figure", key: figure[1] ?? "", caption: (figure[2] ?? "").trim() });
      i += 1;
      continue;
    }
    const widget = trimmed.match(/^\{\{widget:([\w-]+)\}\}$/);
    if (widget) {
      push({ type: "widget", key: widget[1] ?? "" });
      i += 1;
      continue;
    }
    if (trimmed.startsWith("|")) {
      const rows: string[][] = [];
      while (i < lines.length && at(i).trim().startsWith("|")) {
        rows.push(splitRow(at(i)));
        i += 1;
      }
      const [head, , ...body] = rows;
      push({ type: "table", head: head ?? [], rows: body });
      continue;
    }
    const ordered = /^\d+\.\s/.test(trimmed);
    if (ordered || /^[-*]\s/.test(trimmed)) {
      const items: string[] = [];
      while (i < lines.length) {
        const t = at(i).trim();
        const m = ordered ? t.match(/^\d+\.\s+(.*)$/) : t.match(/^[-*]\s+(.*)$/);
        if (!m) break;
        items.push(m[1] ?? "");
        i += 1;
      }
      push({ type: "list", ordered, items });
      continue;
    }
    // Paragraph: consecutive non-blank lines.
    const para: string[] = [];
    while (i < lines.length && at(i).trim() !== "" && !/^(#|```|\||\{\{)/.test(at(i).trim())) {
      para.push(at(i).trim());
      i += 1;
    }
    const text = para.join(" ");
    if (!current) {
      if (!authors) authors = text;
      continue;
    }
    const ref = inReferences ? text.match(/^\[(\d+)\]\s+(.*)$/) : null;
    if (ref) {
      push({ type: "reference", n: Number(ref[1]), text: ref[2] ?? "" });
    } else if (/^\*[^*].*[^*]\*$/.test(text) && !text.slice(1, -1).includes("*")) {
      push({ type: "caption", text: text.slice(1, -1) });
    } else {
      push({ type: "p", text });
    }
  }

  const wordCount = sections
    .filter((s) => !/^references$/i.test(s.title))
    .flatMap((s) => s.blocks)
    .map((b) => {
      if (b.type === "p" || b.type === "caption" || b.type === "h2" || b.type === "h3") return b.text;
      if (b.type === "list") return b.items.join(" ");
      if (b.type === "table") return [...b.head, ...b.rows.flat()].join(" ");
      if (b.type === "figure") return b.caption;
      return "";
    })
    .join(" ")
    .split(/\s+/)
    .filter(Boolean).length;

  return { title, authors, sections, wordCount };
}

export type InlineToken =
  | { kind: "text"; value: string }
  | { kind: "bold"; value: string }
  | { kind: "italic"; value: string }
  | { kind: "cite"; n: number }
  | { kind: "link"; href: string; value: string };

/** Splits inline markdown into tokens: **bold**, *italic*, [n] citations, [text](url) and bare URLs. */
export function tokenizeInline(text: string): InlineToken[] {
  const out: InlineToken[] = [];
  const re = /\*\*(.+?)\*\*|\*(.+?)\*|\[(\d+)\](?!\()|\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)|(https?:\/\/[^\s)]+[^\s).,])/g;
  let last = 0;
  for (let m = re.exec(text); m; m = re.exec(text)) {
    if (m.index > last) out.push({ kind: "text", value: text.slice(last, m.index) });
    if (m[1] !== undefined) out.push({ kind: "bold", value: m[1] });
    else if (m[2] !== undefined) out.push({ kind: "italic", value: m[2] });
    else if (m[3] !== undefined) out.push({ kind: "cite", n: Number(m[3]) });
    else if (m[4] !== undefined) out.push({ kind: "link", value: m[4], href: m[5] ?? "" });
    else if (m[6] !== undefined) out.push({ kind: "link", value: m[6], href: m[6] });
    last = re.lastIndex;
  }
  if (last < text.length) out.push({ kind: "text", value: text.slice(last) });
  return out;
}

/** Average current and battery life for a duty-cycled node (paper Section III-B, Eq. 3). */
export function batteryLife({
  periodS,
  activeS,
  activeMa = 121.5,
  sleepMa = 0.0326,
  capacityMah = 2600,
  usable = 0.8,
}: {
  periodS: number;
  activeS: number;
  activeMa?: number;
  sleepMa?: number;
  capacityMah?: number;
  usable?: number;
}): { avgMa: number; hours: number; days: number } {
  const on = Math.min(activeS, periodS);
  const avgMa = (activeMa * on + sleepMa * (periodS - on)) / periodS;
  const hours = (capacityMah * usable) / avgMa;
  return { avgMa, hours, days: hours / 24 };
}
