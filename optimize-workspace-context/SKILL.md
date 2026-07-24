---
name: optimize-workspace-context
description: Optimize CLAUDE.md or AGENTS.md files for AI consumption. Focus on quality improvements — inconsistencies, duplicates, unnecessary content, content that should be moved elsewhere. Use when asked to optimize, review, or clean up an AI config file.
---

# Optimize CLAUDE.md / AGENTS.md for AI Consumption

**Purpose**: Optimize `CLAUDE.md` or `AGENTS.md` files for AI agent/machine consumption. Focus on quality improvements: inconsistencies, duplicates, unnecessary content, and content that should be moved elsewhere. Preserve all essential actionable guidance.

**Target**: Any `CLAUDE.md` or `AGENTS.md` file in doc workspaces or code repositories. Size reduction is a byproduct, not the primary goal.

---

## Optimization Process

### Step 1: Analyze Current State

1. Count total lines in `AGENTS.md` (for context only, not a target)
2. Identify verbose sections (paragraphs, long explanations, multiple examples)
3. Find duplicate content across sections
4. Identify specific examples that could be genericized
5. Check for content that duplicates instruction files
6. Identify content that should be moved to instruction files or other locations
7. Find content that isn't needed for AI agents (human-only notes, historical context, etc.)

### Step 1.5: Identify Inconsistencies

**Format Inconsistencies:**
- Inconsistent heading levels (H2 vs H3 for similar content)
- Mixed list formats (bullets vs numbered vs dashes)
- Inconsistent code block formatting (language tags, indentation)
- Inconsistent link formats (markdown vs wiki-style vs plain text)
- Inconsistent checkbox syntax (`- [ ]` vs `- [x]` vs `* [ ]`)
- Inconsistent spacing (blank lines, indentation)
- Inconsistent emphasis (bold vs italic vs code formatting)

**Content Inconsistencies:**
- Same concept described differently in multiple sections
- Conflicting file naming conventions (different formats for same file type)
- Conflicting directory structure guidance
- Different workflow descriptions for same process
- Inconsistent terminology (same concept with different names)
- Conflicting formatting rules (e.g., "use bullets" vs "use paragraphs")

**Contradictory Instructions:**
- One section says "do X" while another says "don't do X"
- Conflicting rules about when to use certain formats
- Contradictory guidance on file organization
- One workflow contradicts another workflow
- Different sections give opposite advice for same scenario
- Conflicting examples showing different approaches

**Resolution Strategy:**
1. **Identify all instances** of each inconsistency pattern
2. **Determine authoritative source** (most specific, most recent, or most referenced)
3. **Resolve contradictions** by:
   - Keeping the more specific/complete guidance
   - Removing the less accurate version
   - Merging complementary guidance when both are valid
   - Adding clarifying notes if context-dependent
4. **Standardize format** across all sections
5. **Update all references** to use consistent terminology
6. **Document resolution** in comments if needed (remove after verification)

**Common Contradiction Patterns:**
- File naming: Multiple formats for same file type → Standardize to one format
- Workflow steps: Different step counts/orders → Consolidate to authoritative version
- Formatting rules: "Use X" vs "Use Y" → Choose one, document exception if needed
- Organization: Different folder structures → Standardize to one structure
- Terminology: Same concept, different names → Use consistent term throughout

### Step 2: Remove Redundancy

**Consolidate:**
- Duplicate guidance appearing in multiple sections → Single consolidated section
- Similar checklists → Merge into one
- Repeated principles → Single location with cross-reference
- Same content in DO/DON'T, Principles, and Common Issues → One section only

**Use cross-references instead of repeating content:**
- If instruction file exists: Replace detailed steps with 1-3 line summary + reference
- If content appears elsewhere: Reference it, don't duplicate

### Step 3: Condense Content

**Convert:**
- Paragraphs → Bullet points
- Explanations → Actionable steps
- Multiple examples → Single generic template
- Detailed descriptions → Concise requirements
- Verbose workflows → Step-by-step lists
- Multi-line bullet lists → Single-line comma-separated formats
- Numbered lists with explanations → Concise bullet points
- Verbose section headers → Condensed inline descriptions

**Specific patterns:**
- Content Filters: Multi-line bullets → Single-line comma-separated
- Workflow descriptions: Numbered lists with explanations → Concise bullets
- Workspace structure: Nested descriptions → Single-line comma-separated lists
- Instruction file lists: Shorten descriptions, remove redundant phrases

### Step 4: Remove Unnecessary Content

**Remove (AI-agent-irrelevant only):**
- Content that isn't needed for AI agents (human-only notes, historical context, evolution notes)
- Redundant descriptions repeating earlier content (after consolidation)
- Multiple examples of the same concept (keep one generic template)
- Generic productivity advice (not workspace-specific)
- Notes sections repeating earlier guidance (after consolidation)
- Integration workflow details (keep references only)

**Do NOT remove:**
- Essential actionable guidance
- Critical checklists
- Structure templates
- Core principles
- Workflow references
- File naming conventions

**Keep:**
- Essential structure templates
- Actionable workflow steps
- Core principles (DO/DON'T lists)
- Critical checklists
- Common issues and fixes
- File naming conventions
- Related instruction references

### Step 5: Move Content to Appropriate Locations

**Move to instruction files:**
- Detailed step-by-step workflows → Instruction files (keep only reference in AGENTS.md)
- Verbose examples → Instruction files (keep generic template in AGENTS.md)
- Detailed templates → Instruction files (keep structure reference in AGENTS.md)

**Move to other locations:**
- Project-specific details → Project documentation
- Historical context → Archive or historical notes
- Human-only notes → Separate documentation

**Genericize examples (if keeping in AGENTS.md):**
- Specific examples → Generic placeholders (`[Team]`, `[Component]`, `[Process]`, `[Repository]`, `[Workspace]`)
- Specific tool names → Generic terms (platform-agnostic where possible)
- Implementation-specific details → Generic patterns
- Person/team names → Placeholders or generic references
- Real-world scenarios → Generic templates

**Keep examples only if they illustrate unique concepts** (make them generic templates with placeholders)

### Step 6: Verify Preservation

**Ensure:**
- All essential actionable guidance remains
- Critical checklists are complete
- Structure templates are intact
- Core principles are actionable
- No critical content lost

### Step 7: Verify Quality Improvements

1. Verify all inconsistencies resolved (format + content)
2. Confirm duplicates removed or consolidated
3. Check content moved to appropriate locations
4. Verify unnecessary content removed (only AI-agent-irrelevant content)
5. Confirm all essential actionable guidance preserved
6. Count lines after optimization (for reference only, not a target)

---

## Common Patterns to Optimize

- **Verbose Workflow Sections**: Multi-paragraph → Condensed step-by-step lists
- **Multiple Similar Examples**: 3-4 detailed → Single generic template
- **Repeated Principles**: Same guidance in multiple sections → Single consolidated section
- **Explanatory Notes**: "Notes" section repeating earlier guidance → Remove
- **Integration Details**: Detailed workflow → Brief reference only
- **Specific Examples**: Real-world with names → Generic templates with placeholders
- **Duplicate Guidance**: Same content in DO/DON'T, Principles, and Common Issues → Consolidate
- **Platform-Specific Details**: Tool-specific → Generic platform-agnostic patterns
- **Implementation-Specific Examples**: Specific details → Generic patterns with placeholders
- **Format Inconsistencies**: Mixed formatting styles → Standardized format throughout
- **Content Contradictions**: Conflicting instructions → Resolved to single authoritative guidance
- **Terminology Inconsistencies**: Same concept, different names → Consistent terminology

---

## AGENTS.md Structure Rules

**Navigation Layer Only:**
- Workflows with instruction files: 1-3 lines + reference (max 3 lines total)
- Workflows without files: Core principles only (<10 bullets)
- Never duplicate step-by-step instructions from instruction files
- Navigation, not detail (tells WHERE to find info, not WHAT the info is)

**Critical Rules:**
- If instruction file exists: Only summary + reference (3 lines max)
- If no instruction file: Core principles only (<10 bullets)
- Never duplicate step-by-step instructions
- Focus on repeatable patterns, not one-offs

---

## Quality Checklist

**After Optimization:**
- [ ] All essential actionable guidance preserved
- [ ] No critical checklists removed
- [ ] Structure templates intact
- [ ] Core principles actionable
- [ ] No duplicate content across sections
- [ ] All inconsistencies resolved (format + content)
- [ ] Examples genericized (placeholders, not specifics)
- [ ] Content is concise and AI-consumable
- [ ] Steps are actionable, not theoretical
- [ ] Formatting consistent throughout (headings, lists, code blocks, links)
- [ ] Navigation layer maintained (references, not details)
- [ ] No contradictory instructions (all conflicts resolved)
- [ ] Consistent terminology used throughout
- [ ] File naming conventions standardized
- [ ] Workflow descriptions consistent (no conflicting steps)
- [ ] Formatting rules consistent (no "do X" vs "do Y" conflicts)
- [ ] Content moved to appropriate locations (instruction files, project docs, etc.)
- [ ] AI-agent-irrelevant content removed (only unnecessary content)

---

## Usage

Run this command when:
- Format inconsistencies detected (mixed styles, inconsistent structure)
- Content contradictions found (conflicting instructions, contradictory rules)
- Terminology inconsistencies identified (same concept with different names)
- Duplicate content found across sections
- Content that should be moved to instruction files or other locations
- AI-agent-irrelevant content present (human-only notes, historical context)
- AGENTS.md entries duplicate instruction file content
- Multiple sections repeat same guidance
- Examples are verbose or specific (should be genericized or moved)

**Don't optimize:**
- Files already optimized and consistent
- Files with essential detailed templates/examples that must remain specific
- Files where all content is needed for AI agents

---

## Output

Optimized `AGENTS.md` file with:
- All essential guidance preserved
- All inconsistencies resolved (format + content)
- Duplicate content consolidated or removed
- Content moved to appropriate locations (instruction files, project docs, etc.)
- AI-agent-irrelevant content removed
- Generic placeholders instead of specific examples (where appropriate)
- Concise, AI-consumable format
- Navigation layer maintained (references to instruction files)
- Consistent formatting throughout (standardized headings, lists, links, code blocks)
- All contradictions resolved (single authoritative guidance)
- Consistent terminology and naming conventions

**Note**: Size reduction is a byproduct of quality improvements, not the primary goal. Focus on consistency, removing duplicates, and optimizing for AI agent consumption.
