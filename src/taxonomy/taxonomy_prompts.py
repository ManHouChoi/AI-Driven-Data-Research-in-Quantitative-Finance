"""Prompt templates for dynamic risk-taxonomy construction."""

SYSTEM_MSG = "You are a Senior Risk Architect specializing in SEC 10-K filings and risk taxonomy."


def get_macro_prompt(samples):
    samples_block = "\n---\n".join(samples)
    return f"""Analyze these representative SEC Item 1A risk disclosures:
{samples_block}

TASK:
1. Name: Create a precise Macro Category name.
2. Definition: Write a formal 2-sentence definition.
3. Centroid_Summary: Write a 50-word synthesis of the core thematic DNA.

FORMAT YOUR RESPONSE EXACTLY LIKE THIS:
Name: [Name]
Definition: [Definition]
Centroid_Summary: [Summary]
"""


def get_meso_prompt(samples, parent_name):
    samples_block = "\n---\n".join(samples)
    return f"""The following risks belong to the broader '{parent_name}' category:
{samples_block}

TASK:
1. Name: Define a specific Meso-level subcategory name.
2. Definition: Write a formal 2-sentence definition.
3. Centroid_Summary: Write a 50-word synthesis.

FORMAT YOUR RESPONSE EXACTLY LIKE THIS:
Name: [Name]
Definition: [Definition]
Centroid_Summary: [Summary]
"""


def get_evolution_prompt(new_samples, closest_categories, taxonomy_summary):
    taxonomy_block = "\n".join(f"- {item}" for item in taxonomy_summary)
    closest_block = "\n".join(f"- {cat}" for cat in closest_categories)
    samples_block = "\n---\n".join(new_samples)

    return f"""
EXISTING TAXONOMY (category and its parent macro):
{taxonomy_block}

CLOSEST EXISTING CATEGORIES (failed similarity threshold):
{closest_block}

NEW RISK SAMPLES (representative of the deviation cluster):
{samples_block}

TASK: Determine how to evolve the taxonomy. Choose ONE of the following actions:
(A) ADD: This cluster represents a fundamentally new risk theme not covered by any existing category. Provide a new category name and a suitable parent macro.
(B) MERGE: This cluster is a variation of an existing category. Merge it into the closest matching category.
(C) REORGANIZE: This cluster belongs to an existing category, but that category should be moved under a different macro parent. Provide the existing category name and the new parent macro.

RESPONSE FORMAT (exactly):
Decision: [A/B/C]
Recommended_Name: [Name]
Parent_Macro: [Macro Parent Name]
Reasoning: [Brief explanation of why this decision is appropriate]
"""
