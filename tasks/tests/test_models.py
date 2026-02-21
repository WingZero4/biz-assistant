from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from onboarding.models import BusinessProfile
from tasks.models import ResourceTemplate, Task, TaskPlan, TaskResource


class TaskPlanTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'pass123')
        self.profile = BusinessProfile.objects.create(
            user=self.user, business_name='Test', business_type='Test', stage='IDEA',
        )
        today = timezone.now().date()
        self.plan = TaskPlan.objects.create(
            user=self.user, business_profile=self.profile,
            starts_on=today, ends_on=today + timedelta(days=30),
        )

    def test_str(self):
        self.assertIn('testuser', str(self.plan))

    def test_completion_pct_no_tasks(self):
        self.assertEqual(self.plan.completion_pct, 0)

    def test_completion_pct_with_tasks(self):
        today = timezone.now().date()
        Task.objects.create(
            plan=self.plan, title='T1', description='D', category='PLANNING',
            day_number=1, due_date=today, status='DONE',
        )
        Task.objects.create(
            plan=self.plan, title='T2', description='D', category='PLANNING',
            day_number=2, due_date=today, status='PENDING',
        )
        self.assertEqual(self.plan.completion_pct, 50)


class TaskTest(TestCase):

    def setUp(self):
        user = User.objects.create_user('testuser', 'test@example.com', 'pass123')
        profile = BusinessProfile.objects.create(
            user=user, business_name='Test', business_type='Test', stage='IDEA',
        )
        today = timezone.now().date()
        self.plan = TaskPlan.objects.create(
            user=user, business_profile=profile,
            starts_on=today, ends_on=today + timedelta(days=30),
        )

    def test_str(self):
        task = Task.objects.create(
            plan=self.plan, title='Do thing', description='D', category='PLANNING',
            day_number=1, due_date=timezone.now().date(),
        )
        self.assertIn('Do thing', str(task))
        self.assertIn('PENDING', str(task))

    def test_ordering(self):
        today = timezone.now().date()
        t2 = Task.objects.create(
            plan=self.plan, title='T2', description='D', category='PLANNING',
            day_number=1, due_date=today, sort_order=1,
        )
        t1 = Task.objects.create(
            plan=self.plan, title='T1', description='D', category='PLANNING',
            day_number=1, due_date=today, sort_order=0,
        )
        tasks = list(self.plan.tasks.all())
        self.assertEqual(tasks[0], t1)
        self.assertEqual(tasks[1], t2)


class ResourceTemplateTest(TestCase):

    def test_str(self):
        tmpl = ResourceTemplate.objects.create(
            title='LLC Registration Steps',
            resource_type='CHECKLIST',
            content='- [ ] Step 1\n- [ ] Step 2',
        )
        self.assertIn('Checklist', str(tmpl))
        self.assertIn('LLC Registration', str(tmpl))

    def test_default_status_is_draft(self):
        tmpl = ResourceTemplate.objects.create(
            title='Test', resource_type='GUIDE', content='Guide content',
        )
        self.assertEqual(tmpl.status, 'DRAFT')

    def test_ordering_by_times_used(self):
        t1 = ResourceTemplate.objects.create(
            title='Popular', resource_type='TEMPLATE', content='x', times_used=10,
        )
        t2 = ResourceTemplate.objects.create(
            title='Unpopular', resource_type='TEMPLATE', content='y', times_used=1,
        )
        templates = list(ResourceTemplate.objects.all())
        self.assertEqual(templates[0], t1)


class TaskResourceTest(TestCase):

    def setUp(self):
        user = User.objects.create_user('testuser', 'test@example.com', 'pass123')
        profile = BusinessProfile.objects.create(
            user=user, business_name='Test', business_type='Test', stage='IDEA',
        )
        today = timezone.now().date()
        plan = TaskPlan.objects.create(
            user=user, business_profile=profile,
            starts_on=today, ends_on=today + timedelta(days=30),
        )
        self.task = Task.objects.create(
            plan=plan, title='Test Task', description='D', category='PLANNING',
            day_number=1, due_date=today,
        )

    def test_create_resource_linked_to_task(self):
        resource = TaskResource.objects.create(
            task=self.task, title='Test Checklist',
            resource_type='CHECKLIST', content='- [ ] Do thing',
        )
        self.assertEqual(self.task.resources.count(), 1)
        self.assertFalse(resource.is_completed)

    def test_resource_with_template(self):
        tmpl = ResourceTemplate.objects.create(
            title='Standard Checklist', resource_type='CHECKLIST',
            content='- [ ] Step 1', status='REVIEWED', times_used=5,
        )
        resource = TaskResource.objects.create(
            task=self.task, template=tmpl,
            title=tmpl.title, resource_type=tmpl.resource_type,
            content=tmpl.content,
        )
        self.assertEqual(resource.template, tmpl)
        self.assertEqual(tmpl.usages.count(), 1)

    def test_resource_ordering(self):
        r2 = TaskResource.objects.create(
            task=self.task, title='Second', resource_type='GUIDE',
            content='Guide', sort_order=1,
        )
        r1 = TaskResource.objects.create(
            task=self.task, title='First', resource_type='CHECKLIST',
            content='Check', sort_order=0,
        )
        resources = list(self.task.resources.all())
        self.assertEqual(resources[0], r1)
        self.assertEqual(resources[1], r2)
