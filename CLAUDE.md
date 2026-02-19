# AI Business Building Assistant

## Overview
AI-driven business coaching assistant that onboards new business owners, assesses their needs, generates a personalized 30-day launch plan, and sends daily actionable tasks via SMS + email. Users reply DONE/SKIP via SMS to track progress; the AI adapts the plan based on engagement.

## Stack
- **Python 3.14**, **Django 6.0.2**, **SQLite**
- **Claude API** (Sonnet) — onboarding assessment, plan generation, plan adjustment
- **OpenAI API** (GPT-4.1-nano/mini) — daily message formatting, weekly summaries
- **Twilio** — SMS outbound + inbound webhook
- **SendGrid** — Email outbound + event webhook
- **django-axes** — rate limiting
- **PythonAnywhere** — hosting (scheduled tasks instead of Celery)

## Project Structure
```
biz-assistant/
├── config/          # Django settings, URLs, WSGI
├── accounts/        # User auth + UserProfile (phone, timezone, channel prefs)
├── onboarding/      # BusinessProfile, Conversation, 4-step wizard
├── tasks/           # TaskPlan, Task, generation/progress services
├── notifications/   # MessageLog, SMS/email services, webhooks
├── ai/              # Shared AI client wrappers (not a Django app)
├── templates/       # Django templates (Bootstrap 5)
└── static/          # CSS, JS
```

## Key Design Decisions
- **Service layer pattern**: All mutations go through services (OnboardingService, TaskGenerationService, TaskProgressService, NotificationService)
- **AI routing**: Claude for complex reasoning (assessment, planning), OpenAI for high-volume cheap tasks (daily messages, summaries)
- **PythonAnywhere scheduled tasks** instead of Celery (management commands run on cron)
- **SQLite** for MVP simplicity — migrate to PostgreSQL when needed

## Models
- **UserProfile**: extends auth.User with phone, timezone, preferred_channel, daily_send_hour
- **BusinessProfile**: business info + AI-generated assessment (JSONField)
- **Conversation**: onboarding chat history for context continuity
- **TaskPlan**: 30-day plan linked to business profile (ACTIVE/COMPLETED/PAUSED/REPLACED)
- **Task**: individual tasks with status lifecycle (PENDING → SENT → DONE/SKIPPED/RESCHEDULED)
- **MessageLog**: SMS/email delivery tracking with Twilio/SendGrid IDs

## Run Commands
```bash
python manage.py runserver          # Dev server
python manage.py test               # Run all tests
python manage.py makemigrations     # After model changes
python manage.py migrate            # Apply migrations
python manage.py check              # System checks
python manage.py send_daily_tasks   # Send daily tasks (scheduled task)
python manage.py send_weekly_summaries  # Weekly progress emails
python manage.py adjust_stale_plans    # Adjust plans for inactive users
```

## Environment Variables
```
DJANGO_SECRET_KEY, DJANGO_DEBUG, DJANGO_ALLOWED_HOSTS
ANTHROPIC_API_KEY, OPENAI_API_KEY
TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER
SENDGRID_API_KEY, SENDGRID_FROM_EMAIL
```

## Task Status Lifecycle
`PENDING → SENT → DONE | SKIPPED | RESCHEDULED`

## Known Issues
- axes W006 warning silenced by including ip_address in lockout params
