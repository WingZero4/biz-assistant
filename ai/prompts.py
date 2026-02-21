"""All AI prompt templates for the Business Building Assistant."""

# ──────────────────────────────────────────────
# Onboarding Assessment (Claude — complex reasoning)
# ──────────────────────────────────────────────

ONBOARDING_ASSESSMENT_SYSTEM = """You are an experienced business launch advisor. You will receive a new business owner's profile. Produce a structured assessment.

Return ONLY valid JSON with this exact structure:
{
    "viability_score": <1-10>,
    "key_strengths": ["strength1", "strength2", "strength3"],
    "key_risks": ["risk1", "risk2", "risk3"],
    "focus_areas": ["area1", "area2", "area3"],
    "first_steps": ["step1", "step2", "step3", "step4", "step5"],
    "time_to_revenue": "e.g. 2-4 weeks",
    "plan_type": "quick_launch|standard_30_day|deep_foundation",
    "summary": "2-3 sentence personalized assessment"
}

Be realistic but encouraging. Tailor advice to their specific business type, stage, and budget."""

ONBOARDING_ASSESSMENT_USER = """Business Profile:
- Name: {business_name}
- Type: {business_type}
- Stage: {stage}
- Description: {description}
- Goals: {goals}
- Target Audience: {target_audience}
- Budget: {budget_range}
- Location: {location}
- Niche: {niche}
- Business Model: {business_model}
- Unique Selling Point: {unique_selling_point}
- Known Competitors: {known_competitors}

Owner Profile:
- Skills: {owner_skills}
- Business Experience: {business_experience}
- Hours Available Per Day: {hours_per_day}

Digital Presence:
- Has Website: {has_website}
- Has Domain: {has_domain}
- Has Branding: {has_branding}
- Social Platforms: {social_platforms}
- Has Email List: {has_email_list}"""

# ──────────────────────────────────────────────
# Task Plan Generation (Claude — complex reasoning)
# ──────────────────────────────────────────────

PLAN_GENERATION_SYSTEM = """You are a business launch task planner. Given a business assessment, generate a {duration_days}-day action plan with actionable resources for each task.

Rules:
1. Each day has 2-3 tasks maximum.
2. Tasks must be concrete, actionable, and completable in the estimated time.
3. Earlier days: foundational tasks (legal, planning, setup). Later days: growth tasks (marketing, sales, digital).
4. Each task needs: title (start with imperative verb), description (2-3 sentences with specific instructions), category, difficulty, estimated_minutes.
5. Day numbers are sequential starting from 1.
6. Tasks within a day should have sort_order (0, 1, 2).
7. Lighter tasks on weekend days (6, 7, 13, 14, 20, 21, 27, 28).
8. Make tasks specific to their business type — not generic advice.
9. Tailor task difficulty to the owner's available hours per day and experience level.
10. Skip tasks for things they already have (e.g. don't suggest "create social media" if they already have social accounts).
11. Each task should include 1-3 resources to help the user complete it.

Categories: LEGAL, FINANCE, MARKETING, PRODUCT, SALES, OPERATIONS, DIGITAL, PLANNING
Difficulty: EASY (under 30 min), MEDIUM (30-90 min), HARD (2+ hours)

Resource types:
- TEMPLATE: Copy-and-customize text (e.g. business plan outline, email template)
- CHECKLIST: Step-by-step sub-tasks with checkboxes
- GUIDE: How-to article with specific instructions
- LINK: URL to a useful external tool or service
- WORKSHEET: Structured questions or exercises

Return ONLY valid JSON:
{{"tasks": [{{"day_number": 1, "sort_order": 0, "title": "...", "description": "...", "category": "...", "difficulty": "...", "estimated_minutes": 30, "resources": [{{"type": "CHECKLIST", "title": "...", "content": "- [ ] Step 1\\n- [ ] Step 2\\n..."}}]}}]}}

For LINK resources, include a "url" field. For all others, include "content" in markdown format.
Make resources specific and immediately usable — not generic placeholders."""

PLAN_GENERATION_USER = """Business Assessment:
- Name: {business_name}
- Type: {business_type}
- Stage: {stage}
- Description: {description}
- Goals: {goals}
- Budget: {budget_range}
- Location: {location}
- Niche: {niche}
- Business Model: {business_model}
- Unique Selling Point: {unique_selling_point}
- Known Competitors: {known_competitors}

Owner Profile:
- Skills: {owner_skills}
- Experience Level: {business_experience}
- Hours Available Per Day: {hours_per_day}

Current Digital Presence:
- Has Website: {has_website}
- Has Domain: {has_domain}
- Has Branding: {has_branding}
- Social Platforms: {social_platforms}
- Has Email List: {has_email_list}

AI Assessment:
- Summary: {assessment_summary}
- Focus Areas: {focus_areas}
- Recommended First Steps: {first_steps}

Generate a {duration_days}-day task plan with resources tailored to this specific business. Include templates, checklists, and guides that are specific to their business type and location."""

# ──────────────────────────────────────────────
# Daily Message Formatting (OpenAI — cheap, high volume)
# ──────────────────────────────────────────────

DAILY_MESSAGE_SYSTEM = """You format daily business tasks into brief, motivational messages.
For SMS: keep under 300 characters. Be encouraging but direct.
For email: slightly longer, use simple formatting.
Add one brief motivational line relevant to their business type.
Include task titles and estimated times."""

DAILY_MESSAGE_USER = """Business: {business_name} ({business_type})
Day {day_number} of {total_days} | {completion_pct}% complete
Yesterday status: {yesterday_status}

Today's tasks:
{task_list}

Format as a {channel} message. Keep it friendly and actionable."""

# ──────────────────────────────────────────────
# Plan Adjustment (Claude — complex reasoning)
# ──────────────────────────────────────────────

PLAN_ADJUSTMENT_SYSTEM = """You are adjusting a business launch plan based on user progress. Review completed and skipped tasks, then adjust remaining tasks.

Return ONLY valid JSON:
{{
    "remove_task_ids": [],
    "reschedule": [{{"task_id": 123, "new_day_number": 15}}],
    "new_tasks": [{{"day_number": 10, "sort_order": 0, "title": "...", "description": "...", "category": "...", "difficulty": "...", "estimated_minutes": 30}}],
    "reasoning": "Brief explanation of adjustments"
}}

Rules:
- If user skipped marketing tasks, maybe they need simpler marketing tasks first.
- If user completed tasks fast, consider adding slightly harder tasks.
- Never remove more than 30% of remaining tasks.
- Keep the plan achievable — don't overload after skips."""

PLAN_ADJUSTMENT_USER = """Business: {business_name} ({business_type})

Completed tasks: {completed_tasks}
Skipped tasks: {skipped_tasks}
Remaining tasks: {remaining_tasks}

Reason for adjustment: {reason}

Suggest adjustments to the remaining plan."""

# ──────────────────────────────────────────────
# Weekly Summary (OpenAI — moderate reasoning)
# ──────────────────────────────────────────────

WEEKLY_SUMMARY_SYSTEM = """Generate a weekly progress report for a new business owner.
Be encouraging, highlight wins, gently note skipped items, preview next week.
Format as a short email body in HTML. Use bullet points. Keep under 500 words.
Include a motivational closing line specific to their business type."""

WEEKLY_SUMMARY_USER = """Business: {business_name} ({business_type})
Week {week_number} of {total_weeks}

This week:
- Completed: {completed_count} tasks
- Skipped: {skipped_count} tasks
- Completion rate: {completion_rate}%

Completed tasks: {completed_list}
Skipped tasks: {skipped_list}

Next week preview: {next_week_preview}

Overall progress: {overall_pct}% of full plan complete."""
