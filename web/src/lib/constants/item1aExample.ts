export const item1aHierarchyExample = {
  heading: "Macroeconomic and Industry Risks",
  subheading:
    "The Company’s operations and performance depend significantly on global and regional economic conditions...",
  rawText:
    "The Company has international operations with sales outside the U.S. representing a majority of the Company’s total net sales. In addition, the Company’s global supply chain is large and complex...",
  inputExcerpt:
    "The Company’s operations and performance depend significantly on global and regional economic conditions and adverse economic conditions can materially adversely affect the Company’s business, results of operations, financial condition and stock price.\nThe Company has international operations with sales outside the U.S. representing a majority of the Company’s total net sales. In addition, the Company’s global supply chain is large and complex..."
} as const;

export const item1aParagraphRecordJson = `{
  "section_anchor": "ITEM 1A. RISK FACTORS",
  "Heading": "${item1aHierarchyExample.heading}",
  "Subheading": "${item1aHierarchyExample.subheading}",
  "RawText": "${item1aHierarchyExample.rawText}"
}`;
