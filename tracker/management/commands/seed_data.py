from datetime import timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from tracker.models import ApplicationNote, Company, InterviewRound, JobApplication, ResumeVersion

User = get_user_model()


class Command(BaseCommand):
    help = 'Idempotently seeds demo data (2 users, 10 companies, 4 resumes, 24 applications, 18 rounds).'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Starting idempotent demo data seeding...'))
        now = timezone.now()
        today = now.date()

        # ---------------------------------------------------------------------
        # 1. Users (2 Users)
        # ---------------------------------------------------------------------
        u1, created_u1 = User.objects.get_or_create(
            username='alex_dev',
            defaults={
                'email': 'alex@example.com',
                'first_name': 'Alex',
                'last_name': 'Rivera',
            }
        )
        if created_u1:
            u1.set_password('DemoPassword123!')
            u1.save()

        u2, created_u2 = User.objects.get_or_create(
            username='priya_swe',
            defaults={
                'email': 'priya@example.com',
                'first_name': 'Priya',
                'last_name': 'Sharma',
            }
        )
        if created_u2:
            u2.set_password('DemoPassword123!')
            u2.save()

        # ---------------------------------------------------------------------
        # 2. Target Companies (10 Companies total)
        # ---------------------------------------------------------------------
        companies_data_u1 = [
            {'name': 'Google', 'industry': 'Tech', 'location': 'Mountain View, CA', 'website': 'https://careers.google.com', 'notes': 'Tier-1 tech target, strong DSA focus.'},
            {'name': 'Microsoft', 'industry': 'Enterprise Cloud', 'location': 'Redmond, WA', 'website': 'https://careers.microsoft.com', 'notes': 'Azure infrastructure and developer tools team.'},
            {'name': 'Stripe', 'industry': 'FinTech', 'location': 'San Francisco, CA', 'website': 'https://stripe.com/jobs', 'notes': 'High coding bar, practical system design.'},
            {'name': 'Atlassian', 'industry': 'Collaboration SaaS', 'location': 'Bengaluru, India', 'website': 'https://www.atlassian.com/company/careers', 'notes': 'Values-based interview rounds and system architecture.'},
            {'name': 'Uber', 'industry': 'Mobility & Logistics', 'location': 'San Francisco, CA', 'website': 'https://uber.com/careers', 'notes': 'Real-time dispatch and backend concurrency focus.'},
            {'name': 'Swiggy', 'industry': 'FoodTech & Quick Commerce', 'location': 'Bengaluru, India', 'website': 'https://careers.swiggy.com', 'notes': 'High scale hyper-local logistics and catalog pipelines.'},
        ]
        companies_data_u2 = [
            {'name': 'Amazon', 'industry': 'Cloud & E-Commerce', 'location': 'Seattle, WA', 'website': 'https://amazon.jobs', 'notes': 'Strong focus on 16 Leadership Principles.'},
            {'name': 'Netflix', 'industry': 'Streaming Entertainment', 'location': 'Los Gatos, CA', 'website': 'https://jobs.netflix.com', 'notes': 'Senior engineer autonomous culture and performance.'},
            {'name': 'Adobe', 'industry': 'Creative Software', 'location': 'San Jose, CA', 'website': 'https://adobe.com/careers', 'notes': 'Document Cloud and Firefly generative AI team.'},
            {'name': 'Flipkart', 'industry': 'E-Commerce', 'location': 'Bengaluru, India', 'website': 'https://flipkartcareers.com', 'notes': 'Big Billion Days scale and microservices architecture.'},
        ]

        u1_companies = {}
        for c in companies_data_u1:
            comp_obj, _ = Company.objects.get_or_create(
                owner=u1,
                name=c['name'],
                defaults={'industry': c['industry'], 'location': c['location'], 'website': c['website'], 'notes': c['notes']}
            )
            u1_companies[c['name']] = comp_obj

        u2_companies = {}
        for c in companies_data_u2:
            comp_obj, _ = Company.objects.get_or_create(
                owner=u2,
                name=c['name'],
                defaults={'industry': c['industry'], 'location': c['location'], 'website': c['website'], 'notes': c['notes']}
            )
            u2_companies[c['name']] = comp_obj

        # ---------------------------------------------------------------------
        # 3. Resume Versions (4 Resumes total: 2 per user)
        # ---------------------------------------------------------------------
        r_u1_fullstack, _ = ResumeVersion.objects.get_or_create(
            owner=u1,
            label='Full Stack General v1',
            defaults={
                'target_role': 'Full Stack Software Engineer',
                'is_default': True,
                'plain_text': 'Full Stack Engineer with React, Django, PostgreSQL, and AWS experience.',
                'notes': 'Tailored for end-to-end product development roles.',
            }
        )
        r_u1_backend, _ = ResumeVersion.objects.get_or_create(
            owner=u1,
            label='Backend & Systems v2',
            defaults={
                'target_role': 'Backend Systems Engineer',
                'is_default': False,
                'plain_text': 'Backend Specialist with Python, Go, Distributed Systems, Redis, and Kafka.',
                'notes': 'High performance backend and distributed systems profile.',
            }
        )

        r_u2_devops, _ = ResumeVersion.objects.get_or_create(
            owner=u2,
            label='Cloud Infrastructure & DevOps v1',
            defaults={
                'target_role': 'Site Reliability Engineer',
                'is_default': True,
                'plain_text': 'Cloud Engineer with Kubernetes, Terraform, AWS, Prometheus, and CI/CD mastery.',
                'notes': 'DevOps and infrastructure focused resume version.',
            }
        )
        r_u2_backend, _ = ResumeVersion.objects.get_or_create(
            owner=u2,
            label='Distributed Systems SWE v2',
            defaults={
                'target_role': 'Software Engineer II',
                'is_default': False,
                'plain_text': 'Software Engineer with microservices, Java/Spring, and database sharding.',
                'notes': 'Enterprise microservices resume variant.',
            }
        )

        # ---------------------------------------------------------------------
        # 4. Job Applications (24 Applications total: 15 for u1, 9 for u2)
        # Realistic dates spanning past 45 days and upcoming next actions
        # ---------------------------------------------------------------------
        apps_data_u1 = [
            # 1. Google (Technical stage)
            {
                'company': u1_companies['Google'],
                'role': 'Software Engineer III (Core Search)',
                'resume': r_u1_backend,
                'status': JobApplication.StatusChoices.TECHNICAL,
                'source': JobApplication.SourceChoices.REFERRAL,
                'work_mode': JobApplication.WorkModeChoices.HYBRID,
                'ctc': Decimal('48.00'),
                'applied': today - timedelta(days=28),
                'next_action': today + timedelta(days=2),
                'desc': 'Core search ranking pipelines and distributed indexing.',
            },
            # 2. Google (Saved role)
            {
                'company': u1_companies['Google'],
                'role': 'Cloud Infrastructure Engineer',
                'resume': r_u1_backend,
                'status': JobApplication.StatusChoices.SAVED,
                'source': JobApplication.SourceChoices.CAREER_PORTAL,
                'work_mode': JobApplication.WorkModeChoices.HYBRID,
                'ctc': Decimal('42.00'),
                'applied': None,
                'next_action': today + timedelta(days=5),
                'desc': 'Google Cloud Platform storage layer infrastructure.',
            },
            # 3. Microsoft (Offer secured!)
            {
                'company': u1_companies['Microsoft'],
                'role': 'Software Engineer II (Azure Dev)',
                'resume': r_u1_fullstack,
                'status': JobApplication.StatusChoices.OFFER,
                'source': JobApplication.SourceChoices.CAMPUS,
                'work_mode': JobApplication.WorkModeChoices.HYBRID,
                'ctc': Decimal('36.00'),
                'applied': today - timedelta(days=42),
                'next_action': today + timedelta(days=3),
                'desc': 'Azure Portal experience and distributed frontend SDKs.',
            },
            # 4. Microsoft (OA stage)
            {
                'company': u1_companies['Microsoft'],
                'role': 'Systems Engineer (M365)',
                'resume': r_u1_backend,
                'status': JobApplication.StatusChoices.OA,
                'source': JobApplication.SourceChoices.CAREER_PORTAL,
                'work_mode': JobApplication.WorkModeChoices.ONSITE,
                'ctc': Decimal('32.00'),
                'applied': today - timedelta(days=12),
                'next_action': today + timedelta(days=3),
                'desc': 'Office 365 real-time collaboration backend services.',
            },
            # 5. Stripe (HR stage)
            {
                'company': u1_companies['Stripe'],
                'role': 'Backend Engineer (Billing & Invoicing)',
                'resume': r_u1_backend,
                'status': JobApplication.StatusChoices.HR,
                'source': JobApplication.SourceChoices.REFERRAL,
                'work_mode': JobApplication.WorkModeChoices.REMOTE,
                'ctc': Decimal('52.00'),
                'applied': today - timedelta(days=35),
                'next_action': today + timedelta(days=4),
                'desc': 'Global recurring payments and idempotent transactional APIs.',
            },
            # 6. Stripe (Saved)
            {
                'company': u1_companies['Stripe'],
                'role': 'Full Stack Engineer (Dashboard UI)',
                'resume': r_u1_fullstack,
                'status': JobApplication.StatusChoices.SAVED,
                'source': JobApplication.SourceChoices.LINKEDIN,
                'work_mode': JobApplication.WorkModeChoices.REMOTE,
                'ctc': Decimal('45.00'),
                'applied': None,
                'next_action': None,
                'desc': 'Financial analytics dashboard and developer tools.',
            },
            # 7. Atlassian (Technical stage)
            {
                'company': u1_companies['Atlassian'],
                'role': 'Senior Software Engineer (Jira Platform)',
                'resume': r_u1_backend,
                'status': JobApplication.StatusChoices.TECHNICAL,
                'source': JobApplication.SourceChoices.LINKEDIN,
                'work_mode': JobApplication.WorkModeChoices.REMOTE,
                'ctc': Decimal('40.00'),
                'applied': today - timedelta(days=22),
                'next_action': today + timedelta(days=6),
                'desc': 'Event-driven event routing for Jira enterprise cloud.',
            },
            # 8. Atlassian (Applied)
            {
                'company': u1_companies['Atlassian'],
                'role': 'Product Developer (Confluence Spaces)',
                'resume': r_u1_fullstack,
                'status': JobApplication.StatusChoices.APPLIED,
                'source': JobApplication.SourceChoices.CAREER_PORTAL,
                'work_mode': JobApplication.WorkModeChoices.REMOTE,
                'ctc': Decimal('34.00'),
                'applied': today - timedelta(days=8),
                'next_action': today + timedelta(days=8),
                'desc': 'Confluence collaborative real-time editor.',
            },
            # 9. Uber (OA stage)
            {
                'company': u1_companies['Uber'],
                'role': 'Backend Engineer (Marketplace Pricing)',
                'resume': r_u1_backend,
                'status': JobApplication.StatusChoices.OA,
                'source': JobApplication.SourceChoices.REFERRAL,
                'work_mode': JobApplication.WorkModeChoices.HYBRID,
                'ctc': Decimal('44.00'),
                'applied': today - timedelta(days=16),
                'next_action': today + timedelta(days=2),
                'desc': 'Surge pricing algorithm pipelines and geospatial data structures.',
            },
            # 10. Uber (Rejected)
            {
                'company': u1_companies['Uber'],
                'role': 'Android Engineer (Driver App)',
                'resume': r_u1_fullstack,
                'status': JobApplication.StatusChoices.REJECTED,
                'source': JobApplication.SourceChoices.CAREER_PORTAL,
                'work_mode': JobApplication.WorkModeChoices.ONSITE,
                'ctc': Decimal('38.00'),
                'applied': today - timedelta(days=44),
                'next_action': None,
                'desc': 'Driver turn-by-turn navigation UI.',
            },
            # 11. Uber (Withdrawn)
            {
                'company': u1_companies['Uber'],
                'role': 'Data Platform Engineer',
                'resume': r_u1_backend,
                'status': JobApplication.StatusChoices.WITHDRAWN,
                'source': JobApplication.SourceChoices.COLD_EMAIL,
                'work_mode': JobApplication.WorkModeChoices.HYBRID,
                'ctc': Decimal('35.00'),
                'applied': today - timedelta(days=30),
                'next_action': None,
                'desc': 'Apache Hudi lakehouse data streaming.',
            },
            # 12. Swiggy (Technical stage)
            {
                'company': u1_companies['Swiggy'],
                'role': 'SDE-2 (Instamart Logistics)',
                'resume': r_u1_backend,
                'status': JobApplication.StatusChoices.TECHNICAL,
                'source': JobApplication.SourceChoices.CAMPUS,
                'work_mode': JobApplication.WorkModeChoices.ONSITE,
                'ctc': Decimal('30.00'),
                'applied': today - timedelta(days=25),
                'next_action': today + timedelta(days=7),
                'desc': 'Dark store dispatch optimization algorithms.',
            },
            # 13. Swiggy (Applied)
            {
                'company': u1_companies['Swiggy'],
                'role': 'Full Stack Developer (Consumer Web)',
                'resume': r_u1_fullstack,
                'status': JobApplication.StatusChoices.APPLIED,
                'source': JobApplication.SourceChoices.LINKEDIN,
                'work_mode': JobApplication.WorkModeChoices.HYBRID,
                'ctc': Decimal('26.00'),
                'applied': today - timedelta(days=5),
                'next_action': None,
                'desc': 'Swiggy web checkout and payments integration.',
            },
            # 14. Swiggy (Saved)
            {
                'company': u1_companies['Swiggy'],
                'role': 'DevOps Engineer (Core Infrastructure)',
                'resume': r_u1_backend,
                'status': JobApplication.StatusChoices.SAVED,
                'source': JobApplication.SourceChoices.CAREER_PORTAL,
                'work_mode': JobApplication.WorkModeChoices.ONSITE,
                'ctc': Decimal('28.00'),
                'applied': None,
                'next_action': today + timedelta(days=1),
                'desc': 'Kubernetes cluster operations and auto-scaling.',
            },
            # 15. Google (Applied)
            {
                'company': u1_companies['Google'],
                'role': 'Tools & Infrastructure Engineer',
                'resume': r_u1_backend,
                'status': JobApplication.StatusChoices.APPLIED,
                'source': JobApplication.SourceChoices.COLD_EMAIL,
                'work_mode': JobApplication.WorkModeChoices.ONSITE,
                'ctc': Decimal('40.00'),
                'applied': today - timedelta(days=3),
                'next_action': today + timedelta(days=9),
                'desc': 'Internal developer productivity tooling and CI pipelines.',
            },
        ]

        apps_data_u2 = [
            # 16. Amazon (Offer!)
            {
                'company': u2_companies['Amazon'],
                'role': 'Cloud Support Engineer (AWS EC2)',
                'resume': r_u2_devops,
                'status': JobApplication.StatusChoices.OFFER,
                'source': JobApplication.SourceChoices.CAMPUS,
                'work_mode': JobApplication.WorkModeChoices.HYBRID,
                'ctc': Decimal('28.00'),
                'applied': today - timedelta(days=38),
                'next_action': None,
                'desc': 'Virtualization troubleshooting and Linux kernel tuning.',
            },
            # 17. Amazon (Technical stage)
            {
                'company': u2_companies['Amazon'],
                'role': 'SDE-1 (Fulfillment Technologies)',
                'resume': r_u2_backend,
                'status': JobApplication.StatusChoices.TECHNICAL,
                'source': JobApplication.SourceChoices.CAREER_PORTAL,
                'work_mode': JobApplication.WorkModeChoices.ONSITE,
                'ctc': Decimal('32.00'),
                'applied': today - timedelta(days=20),
                'next_action': today + timedelta(days=3),
                'desc': 'Warehouse robotics automated routing system.',
            },
            # 18. Netflix (Technical stage)
            {
                'company': u2_companies['Netflix'],
                'role': 'Site Reliability Engineer (Data Mesh)',
                'resume': r_u2_devops,
                'status': JobApplication.StatusChoices.TECHNICAL,
                'source': JobApplication.SourceChoices.REFERRAL,
                'work_mode': JobApplication.WorkModeChoices.REMOTE,
                'ctc': Decimal('60.00'),
                'applied': today - timedelta(days=18),
                'next_action': today + timedelta(days=5),
                'desc': 'Chaos engineering and multi-region failover resilience.',
            },
            # 19. Netflix (Rejected)
            {
                'company': u2_companies['Netflix'],
                'role': 'Core Platform Engineer',
                'resume': r_u2_backend,
                'status': JobApplication.StatusChoices.REJECTED,
                'source': JobApplication.SourceChoices.LINKEDIN,
                'work_mode': JobApplication.WorkModeChoices.REMOTE,
                'ctc': Decimal('55.00'),
                'applied': today - timedelta(days=40),
                'next_action': None,
                'desc': 'Telemetry collection infrastructure.',
            },
            # 20. Adobe (HR stage)
            {
                'company': u2_companies['Adobe'],
                'role': 'Infrastructure Automation Engineer',
                'resume': r_u2_devops,
                'status': JobApplication.StatusChoices.HR,
                'source': JobApplication.SourceChoices.REFERRAL,
                'work_mode': JobApplication.WorkModeChoices.HYBRID,
                'ctc': Decimal('35.00'),
                'applied': today - timedelta(days=32),
                'next_action': today + timedelta(days=4),
                'desc': 'Terraform GitOps deployment pipeline automation.',
            },
            # 21. Adobe (OA stage)
            {
                'company': u2_companies['Adobe'],
                'role': 'Software Development Engineer (Creative Cloud)',
                'resume': r_u2_backend,
                'status': JobApplication.StatusChoices.OA,
                'source': JobApplication.SourceChoices.CAREER_PORTAL,
                'work_mode': JobApplication.WorkModeChoices.HYBRID,
                'ctc': Decimal('30.00'),
                'applied': today - timedelta(days=10),
                'next_action': today + timedelta(days=2),
                'desc': 'Asset syncing engine for Photoshop and Illustrator.',
            },
            # 22. Flipkart (Technical stage)
            {
                'company': u2_companies['Flipkart'],
                'role': 'SDE-2 (Checkout & Payments)',
                'resume': r_u2_backend,
                'status': JobApplication.StatusChoices.TECHNICAL,
                'source': JobApplication.SourceChoices.CAMPUS,
                'work_mode': JobApplication.WorkModeChoices.ONSITE,
                'ctc': Decimal('27.00'),
                'applied': today - timedelta(days=24),
                'next_action': today + timedelta(days=6),
                'desc': 'High throughput UPI and card payment gateways.',
            },
            # 23. Flipkart (Saved)
            {
                'company': u2_companies['Flipkart'],
                'role': 'DevOps Architect',
                'resume': r_u2_devops,
                'status': JobApplication.StatusChoices.SAVED,
                'source': JobApplication.SourceChoices.LINKEDIN,
                'work_mode': JobApplication.WorkModeChoices.ONSITE,
                'ctc': Decimal('38.00'),
                'applied': None,
                'next_action': None,
                'desc': 'Private cloud virtualization infrastructure.',
            },
            # 24. Flipkart (Applied)
            {
                'company': u2_companies['Flipkart'],
                'role': 'Backend Engineer (Search & Recommendations)',
                'resume': r_u2_backend,
                'status': JobApplication.StatusChoices.APPLIED,
                'source': JobApplication.SourceChoices.COLD_EMAIL,
                'work_mode': JobApplication.WorkModeChoices.ONSITE,
                'ctc': Decimal('25.00'),
                'applied': today - timedelta(days=4),
                'next_action': today + timedelta(days=8),
                'desc': 'Personalized product feed microservice.',
            },
        ]

        u1_apps = []
        for app in apps_data_u1:
            app_obj, _ = JobApplication.objects.get_or_create(
                owner=u1,
                company=app['company'],
                role_title=app['role'],
                defaults={
                    'resume_version': app['resume'],
                    'status': app['status'],
                    'source': app['source'],
                    'work_mode': app['work_mode'],
                    'expected_ctc_lpa': app['ctc'],
                    'applied_date': app['applied'],
                    'next_action_date': app['next_action'],
                    'job_description': app['desc'],
                }
            )
            u1_apps.append(app_obj)

        u2_apps = []
        for app in apps_data_u2:
            app_obj, _ = JobApplication.objects.get_or_create(
                owner=u2,
                company=app['company'],
                role_title=app['role'],
                defaults={
                    'resume_version': app['resume'],
                    'status': app['status'],
                    'source': app['source'],
                    'work_mode': app['work_mode'],
                    'expected_ctc_lpa': app['ctc'],
                    'applied_date': app['applied'],
                    'next_action_date': app['next_action'],
                    'job_description': app['desc'],
                }
            )
            u2_apps.append(app_obj)

        # ---------------------------------------------------------------------
        # 5. Interview Rounds (18 Rounds total: 11 for u1, 7 for u2)
        # Spanning past 45 days and upcoming 10 days
        # ---------------------------------------------------------------------
        rounds_u1_data = [
            # Google SWE III (App 0): 1 cleared DSA round, 1 upcoming System Design in 2 days
            {
                'app': u1_apps[0],
                'num': 1,
                'type': InterviewRound.RoundTypeChoices.DSA,
                'time': now - timedelta(days=14),
                'status': InterviewRound.RoundStatusChoices.CLEARED,
                'interviewer': 'Danielle (L5 SWE)',
                'rating': 5,
                'notes': 'LRU Cache and Graph traversal problem. Solved in O(V+E) time.',
            },
            {
                'app': u1_apps[0],
                'num': 2,
                'type': InterviewRound.RoundTypeChoices.SYSTEM_DESIGN,
                'time': now + timedelta(days=2, hours=3),
                'status': InterviewRound.RoundStatusChoices.SCHEDULED,
                'interviewer': 'David (Principal SWE)',
                'rating': None,
                'notes': 'Distributed Web Crawler system design interview.',
            },
            # Microsoft (App 2, Offer): 3 completed rounds (DSA, System Design, HR)
            {
                'app': u1_apps[2],
                'num': 1,
                'type': InterviewRound.RoundTypeChoices.DSA,
                'time': now - timedelta(days=35),
                'status': InterviewRound.RoundStatusChoices.CLEARED,
                'interviewer': 'Vikram',
                'rating': 4,
                'notes': 'Tree reconstruction and Dynamic Programming string match.',
            },
            {
                'app': u1_apps[2],
                'num': 2,
                'type': InterviewRound.RoundTypeChoices.TECHNICAL,
                'time': now - timedelta(days=26),
                'status': InterviewRound.RoundStatusChoices.CLEARED,
                'interviewer': 'Ananya',
                'rating': 5,
                'notes': 'Deep dive into concurrency, memory management, and C# internals.',
            },
            {
                'app': u1_apps[2],
                'num': 3,
                'type': InterviewRound.RoundTypeChoices.HR,
                'time': now - timedelta(days=15),
                'status': InterviewRound.RoundStatusChoices.CLEARED,
                'interviewer': 'HR Partner Rachel',
                'rating': 5,
                'notes': 'Behavioral and compensation expectations discussed. Offer extended.',
            },
            # Microsoft M365 (App 3, OA): 1 Scheduled OA in 3 days
            {
                'app': u1_apps[3],
                'num': 1,
                'type': InterviewRound.RoundTypeChoices.OA,
                'time': now + timedelta(days=3, hours=4),
                'status': InterviewRound.RoundStatusChoices.SCHEDULED,
                'interviewer': 'Codility Online Assessment',
                'rating': None,
                'notes': '3 coding questions in 90 minutes.',
            },
            # Stripe Backend (App 4, HR stage): 2 cleared technical rounds, 1 upcoming HR in 4 days
            {
                'app': u1_apps[4],
                'num': 1,
                'type': InterviewRound.RoundTypeChoices.TECHNICAL,
                'time': now - timedelta(days=25),
                'status': InterviewRound.RoundStatusChoices.CLEARED,
                'interviewer': 'Marcus (Staff Eng)',
                'rating': 4,
                'notes': 'Live coding a rate limiter and idempotency key cache.',
            },
            {
                'app': u1_apps[4],
                'num': 2,
                'type': InterviewRound.RoundTypeChoices.SYSTEM_DESIGN,
                'time': now - timedelta(days=12),
                'status': InterviewRound.RoundStatusChoices.CLEARED,
                'interviewer': 'Elena (Eng Director)',
                'rating': 5,
                'notes': 'Led ledger reconciliation design and double-entry bookkeeping storage.',
            },
            {
                'app': u1_apps[4],
                'num': 3,
                'type': InterviewRound.RoundTypeChoices.HR,
                'time': now + timedelta(days=4, hours=1),
                'status': InterviewRound.RoundStatusChoices.SCHEDULED,
                'interviewer': 'Stripe People Ops',
                'rating': None,
                'notes': 'Culture fit and values alignment.',
            },
            # Atlassian (App 6, Technical stage): 1 upcoming round in 6 days
            {
                'app': u1_apps[6],
                'num': 1,
                'type': InterviewRound.RoundTypeChoices.TECHNICAL,
                'time': now + timedelta(days=6, hours=5),
                'status': InterviewRound.RoundStatusChoices.SCHEDULED,
                'interviewer': 'James',
                'rating': None,
                'notes': 'Pair programming on REST API and reactive event handling.',
            },
            # Uber Marketplace (App 8, OA stage): 1 Scheduled OA in 2 days
            {
                'app': u1_apps[8],
                'num': 1,
                'type': InterviewRound.RoundTypeChoices.OA,
                'time': now + timedelta(days=2, hours=1),
                'status': InterviewRound.RoundStatusChoices.SCHEDULED,
                'interviewer': 'HackerRank Automated',
                'rating': None,
                'notes': 'Algorithms and database query optimization tests.',
            },
        ]

        rounds_u2_data = [
            # Amazon Cloud Support (App 15, Offer): 2 cleared rounds
            {
                'app': u2_apps[0],
                'num': 1,
                'type': InterviewRound.RoundTypeChoices.TECHNICAL,
                'time': now - timedelta(days=30),
                'status': InterviewRound.RoundStatusChoices.CLEARED,
                'interviewer': 'Sanjay',
                'rating': 5,
                'notes': 'Linux kernel troubleshooting, tcpdump, and networking.',
            },
            {
                'app': u2_apps[0],
                'num': 2,
                'type': InterviewRound.RoundTypeChoices.MANAGERIAL,
                'time': now - timedelta(days=18),
                'status': InterviewRound.RoundStatusChoices.CLEARED,
                'interviewer': 'Bar Raiser Karen',
                'rating': 4,
                'notes': 'Customer obsession and Ownership leadership principles.',
            },
            # Amazon SDE-1 (App 16, Technical): 1 upcoming DSA in 3 days
            {
                'app': u2_apps[1],
                'num': 1,
                'type': InterviewRound.RoundTypeChoices.DSA,
                'time': now + timedelta(days=3, hours=2),
                'status': InterviewRound.RoundStatusChoices.SCHEDULED,
                'interviewer': 'Rahul',
                'rating': None,
                'notes': 'Binary trees, heaps, and Dijkstra path finding.',
            },
            # Netflix SRE (App 17, Technical): 1 upcoming in 5 days
            {
                'app': u2_apps[2],
                'num': 1,
                'type': InterviewRound.RoundTypeChoices.SYSTEM_DESIGN,
                'time': now + timedelta(days=5, hours=3),
                'status': InterviewRound.RoundStatusChoices.SCHEDULED,
                'interviewer': 'Chris (Cloud Reliability)',
                'rating': None,
                'notes': 'Telemetry aggregation pipeline at 10M events/second.',
            },
            # Adobe Automation (App 19, HR stage): 1 cleared technical, 1 upcoming HR in 4 days
            {
                'app': u2_apps[4],
                'num': 1,
                'type': InterviewRound.RoundTypeChoices.TECHNICAL,
                'time': now - timedelta(days=20),
                'status': InterviewRound.RoundStatusChoices.CLEARED,
                'interviewer': 'Amit',
                'rating': 4,
                'notes': 'Terraform module design and Kubernetes security policies.',
            },
            {
                'app': u2_apps[4],
                'num': 2,
                'type': InterviewRound.RoundTypeChoices.HR,
                'time': now + timedelta(days=4, hours=2),
                'status': InterviewRound.RoundStatusChoices.SCHEDULED,
                'interviewer': 'Adobe Talent Acquisition',
                'rating': None,
                'notes': 'Benefits, remote work flexibility, and salary structure.',
            },
            # Flipkart SDE-2 (App 21, Technical): 1 upcoming DSA in 6 days
            {
                'app': u2_apps[6],
                'num': 1,
                'type': InterviewRound.RoundTypeChoices.DSA,
                'time': now + timedelta(days=6, hours=4),
                'status': InterviewRound.RoundStatusChoices.SCHEDULED,
                'interviewer': 'Deepak',
                'rating': None,
                'notes': 'Dynamic programming on grid paths and Trie prefix matching.',
            },
        ]

        for r in rounds_u1_data:
            InterviewRound.objects.get_or_create(
                application=r['app'],
                round_number=r['num'],
                defaults={
                    'round_type': r['type'],
                    'scheduled_at': r['time'],
                    'status': r['status'],
                    'interviewer_name': r['interviewer'],
                    'notes': r['notes'],
                    'self_rating': r['rating'],
                }
            )

        for r in rounds_u2_data:
            InterviewRound.objects.get_or_create(
                application=r['app'],
                round_number=r['num'],
                defaults={
                    'round_type': r['type'],
                    'scheduled_at': r['time'],
                    'status': r['status'],
                    'interviewer_name': r['interviewer'],
                    'notes': r['notes'],
                    'self_rating': r['rating'],
                }
            )

        # ---------------------------------------------------------------------
        # 6. Sample Notes (Optional richness)
        # ---------------------------------------------------------------------
        ApplicationNote.objects.get_or_create(
            application=u1_apps[2],
            title='Offer Letter Breakdown',
            defaults={'body': 'Base CTC 24L + 8L stock grant + 4L performance bonus.'}
        )
        ApplicationNote.objects.get_or_create(
            application=u1_apps[0],
            title='DSA Round Reflection',
            defaults={'body': 'Interviewer seemed very happy with the BFS approach over DFS for shortest hop.'}
        )
        ApplicationNote.objects.get_or_create(
            application=u2_apps[0],
            title='Amazon Offer Received',
            defaults={'body': 'Joining date tentative for next month. Relocation package included.'}
        )

        # Output Summary
        user_count = User.objects.filter(username__in=['alex_dev', 'priya_swe']).count()
        comp_count = Company.objects.filter(owner__in=[u1, u2]).count()
        resume_count = ResumeVersion.objects.filter(owner__in=[u1, u2]).count()
        app_count = JobApplication.objects.filter(owner__in=[u1, u2]).count()
        round_count = InterviewRound.objects.filter(application__owner__in=[u1, u2]).count()

        self.stdout.write(self.style.SUCCESS(
            f'Successfully seeded demo database!\n'
            f'- Users: {user_count} (alex_dev, priya_swe | password: DemoPassword123!)\n'
            f'- Companies: {comp_count}\n'
            f'- Resumes: {resume_count}\n'
            f'- Applications: {app_count}\n'
            f'- Interview Rounds: {round_count}\n'
            f'Seeding is 100% idempotent.'
        ))
