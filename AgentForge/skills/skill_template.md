---
name: skill-template
description: Template for creating new skills - copy and modify this file
tags: template,starter
---

# Skill Template

This is a template for creating new skills in AgentForge.

## How to Use This Template

1. **Copy this file** to the `skills/` directory with a new name
2. **Modify the frontmatter** (section between `---`):
   - `name`: Unique skill identifier
   - `description`: Brief description (shown in system prompt)
   - `tags`: Comma-separated categories

3. **Write the skill body** with:
   - Usage scenarios
   - Step-by-step instructions
   - Important notes and caveats

## Skill Body Structure

### Overview

Describe what this skill does and when to use it.

### Steps

1. First step
2. Second step
3. Third step

### Examples

Provide example usage if applicable.

### Notes

Important considerations, warnings, or tips.

---

## Two-Layer Loading Pattern

Skills use a two-layer loading pattern:

**Layer 1 (System Prompt):** The `description` from frontmatter is included in the system prompt, allowing the model to know what skills are available.

**Layer 2 (On-Demand):** The full skill content is loaded only when the model calls `load_skill`, saving tokens until the skill is actually needed.

This pattern ensures:
- Token efficiency (don't load unused skills)
- Complete information when needed
- Clean separation of concerns
