/**
 * Struct Markdown Renderer
 *
 * This module provides TypeScript types and functions to render Struct elements
 * to Markdown, matching the backend pushikoo-interface's asmarkdown() behavior.
 */

// ============================================================================
// Type Definitions (matching backend pushikoo-interface)
// ============================================================================

export interface StructText {
  type: "text";
  text: string;
  bold?: boolean;
  italic?: boolean;
}

export interface StructTitle {
  type: "title";
  text: string;
  heading?: number;
  bold?: boolean;
  italic?: boolean;
}

export interface StructImage {
  type: "image";
  source: string;
  alt?: string;
}

export interface StructURL {
  type: "url";
  source: string;
  title: StructText;
}

export type StructElement = StructText | StructTitle | StructImage | StructURL;

export interface Struct {
  content: StructElement[];
}

// ============================================================================
// Markdown Rendering Functions
// ============================================================================

/**
 * Render StructText to markdown.
 * Matches backend behavior:
 * - Replace newlines with "  \n" (markdown line break)
 * - Wrap with ** for bold
 * - Wrap with * for italic
 */
function structTextAsMarkdown(element: StructText | StructTitle): string {
  let result = element.text.replace(/\n/g, "  \n");

  if (element.bold) {
    result = `**${result}**`;
  }
  if (element.italic) {
    result = `*${result}*`;
  }

  return result;
}

/**
 * Render StructTitle to markdown.
 * Matches backend behavior:
 * - Prefix with "#" * heading level
 * - Suffix with "  \n"
 */
function structTitleAsMarkdown(element: StructTitle): string {
  const heading = element.heading ?? 1;
  const content = structTextAsMarkdown(element);
  return "#".repeat(heading) + " " + content + "  \n";
}

/**
 * Render StructImage to markdown.
 * Matches backend behavior:
 * - Format: ![alt](source)  \n
 */
function structImageAsMarkdown(element: StructImage): string {
  const alt = element.alt ?? "";
  return `![${alt}](${element.source})  \n`;
}

/**
 * Render StructURL to markdown.
 * Matches backend behavior:
 * - Format: [title.asmarkdown()](source)
 */
function structURLAsMarkdown(element: StructURL): string {
  const titleMd = structTextAsMarkdown(element.title);
  return `[${titleMd}](${element.source})`;
}

/**
 * Render a single StructElement to markdown.
 */
function elementAsMarkdown(element: StructElement): string {
  switch (element.type) {
    case "title":
      return structTitleAsMarkdown(element as StructTitle);
    case "text":
      return structTextAsMarkdown(element as StructText);
    case "image":
      return structImageAsMarkdown(element as StructImage);
    case "url":
      return structURLAsMarkdown(element as StructURL);
    default:
      // Handle unknown types gracefully
      return "";
  }
}

/**
 * Render a Struct to markdown.
 * Matches backend behavior: concatenate all element markdown outputs.
 */
export function structAsMarkdown(struct: Struct): string {
  if (!struct?.content) return "";
  return struct.content.map(elementAsMarkdown).join("");
}

/**
 * Get plain text preview from Struct (for table display).
 * Extracts text from text/title elements only.
 */
export function structAsPlainText(struct: Struct): string {
  if (!struct?.content) return "";
  return struct.content
    .filter(
      (e): e is StructText | StructTitle =>
        e.type === "text" || e.type === "title"
    )
    .map((e) => e.text)
    .join(" ");
}
