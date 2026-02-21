"""
LinkedIn Post Generator

Generates engaging LinkedIn posts based on business context from Company Handbook.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, time
import json
import random

logger = logging.getLogger(__name__)


class LinkedInPostGenerator:
    """Generate LinkedIn posts for business development"""

    def __init__(self, vault_path: str, config: Dict[str, Any] = None):
        """
        Initialize LinkedIn post generator

        Args:
            vault_path: Path to vault directory
            config: Configuration with:
                - company_handbook_path: Path to Company_Handbook folder (default: 'Company_Handbook')
                - post_frequency: Posts per week (default: 2-3)
                - optimal_times: List of optimal posting times (default: business hours)
                - hashtag_strategy: Hashtag strategy (default: 'moderate')
        """
        self.vault_path = Path(vault_path)
        self.config = config or {}

        # Configuration
        self.company_handbook_path = self.vault_path / self.config.get('company_handbook_path', 'Company_Handbook')
        self.post_frequency = self.config.get('post_frequency', 2.5)  # 2-3 per week
        self.optimal_times = self.config.get('optimal_times', [
            time(9, 0),   # 9 AM
            time(12, 0),  # 12 PM
            time(15, 0),  # 3 PM
            time(17, 0)   # 5 PM
        ])
        self.hashtag_strategy = self.config.get('hashtag_strategy', 'moderate')

        # Post storage
        self.posts_path = self.vault_path / 'LinkedIn_Posts'
        self.posts_path.mkdir(parents=True, exist_ok=True)

        # Business context cache
        self.business_context = None

    def load_business_context(self) -> Dict[str, Any]:
        """
        Load business context from Company Handbook

        Returns:
            Dictionary with business context
        """
        if self.business_context:
            return self.business_context

        context = {
            'company_name': 'Unknown',
            'products': [],
            'services': [],
            'values': [],
            'target_audience': [],
            'key_messages': []
        }

        # Load from Company_Handbook if exists
        if self.company_handbook_path.exists():
            try:
                # Look for key files
                about_file = self.company_handbook_path / 'about.md'
                products_file = self.company_handbook_path / 'products.md'
                values_file = self.company_handbook_path / 'values.md'

                if about_file.exists():
                    content = about_file.read_text(encoding='utf-8')
                    context['company_name'] = self._extract_company_name(content)
                    context['key_messages'] = self._extract_key_messages(content)

                if products_file.exists():
                    content = products_file.read_text(encoding='utf-8')
                    context['products'] = self._extract_products(content)
                    context['services'] = self._extract_services(content)

                if values_file.exists():
                    content = values_file.read_text(encoding='utf-8')
                    context['values'] = self._extract_values(content)

            except Exception as e:
                logger.error(f"Error loading business context: {e}")

        self.business_context = context
        return context

    def generate_post(self, post_type: str = 'product', topic: str = None) -> Dict[str, Any]:
        """
        Generate LinkedIn post

        Args:
            post_type: Type of post (product, service, value, insight, announcement)
            topic: Optional specific topic

        Returns:
            Dictionary with post content and metadata
        """
        context = self.load_business_context()

        # Generate post based on type
        if post_type == 'product':
            post_content = self._generate_product_post(context, topic)
        elif post_type == 'service':
            post_content = self._generate_service_post(context, topic)
        elif post_type == 'value':
            post_content = self._generate_value_post(context, topic)
        elif post_type == 'insight':
            post_content = self._generate_insight_post(context, topic)
        elif post_type == 'announcement':
            post_content = self._generate_announcement_post(context, topic)
        else:
            post_content = self._generate_generic_post(context, topic)

        # Add hashtags
        hashtags = self._generate_hashtags(post_type, context)
        post_content += f"\n\n{' '.join(hashtags)}"

        # Create post metadata
        post_data = {
            'content': post_content,
            'post_type': post_type,
            'topic': topic,
            'hashtags': hashtags,
            'generated_at': datetime.now().isoformat(),
            'status': 'draft',
            'scheduled_time': self._get_next_optimal_time(),
            'requires_approval': True
        }

        return post_data

    def save_post(self, post_data: Dict[str, Any]) -> str:
        """
        Save post to LinkedIn_Posts folder

        Args:
            post_data: Post data dictionary

        Returns:
            Post ID
        """
        # Use existing post_id if present, otherwise generate new one
        if 'post_id' in post_data:
            post_id = post_data['post_id']
        else:
            # Generate post ID with microseconds to avoid collisions
            post_id = f"linkedin-post-{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}"
            post_data['post_id'] = post_id

        # Save post file
        post_file = self.posts_path / f"{post_id}.json"

        try:
            with open(post_file, 'w', encoding='utf-8') as f:
                json.dump(post_data, f, indent=2)

            logger.info(f"Saved LinkedIn post: {post_id}")
            return post_id

        except Exception as e:
            logger.error(f"Error saving post: {e}")
            return None

    def get_post(self, post_id: str) -> Optional[Dict[str, Any]]:
        """
        Get post by ID

        Args:
            post_id: Post ID

        Returns:
            Post data dictionary or None
        """
        post_file = self.posts_path / f"{post_id}.json"

        if not post_file.exists():
            return None

        try:
            with open(post_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading post: {e}")
            return None

    def list_posts(self, status: str = None) -> List[Dict[str, Any]]:
        """
        List all posts

        Args:
            status: Filter by status (draft, approved, posted, rejected)

        Returns:
            List of post data dictionaries
        """
        posts = []

        for post_file in self.posts_path.glob('*.json'):
            try:
                with open(post_file, 'r', encoding='utf-8') as f:
                    post_data = json.load(f)

                    # Filter by status if specified
                    if status and post_data.get('status') != status:
                        continue

                    posts.append(post_data)

            except Exception as e:
                logger.error(f"Error loading post {post_file}: {e}")

        # Sort by generated_at (newest first)
        posts.sort(key=lambda p: p.get('generated_at', ''), reverse=True)

        return posts

    def update_post_status(self, post_id: str, status: str, notes: str = None) -> bool:
        """
        Update post status

        Args:
            post_id: Post ID
            status: New status (draft, approved, posted, rejected)
            notes: Optional notes

        Returns:
            True if successful
        """
        post_data = self.get_post(post_id)

        if not post_data:
            return False

        post_data['status'] = status
        post_data['updated_at'] = datetime.now().isoformat()

        if notes:
            post_data['notes'] = notes

        # Save updated post
        post_file = self.posts_path / f"{post_id}.json"

        try:
            with open(post_file, 'w', encoding='utf-8') as f:
                json.dump(post_data, f, indent=2)

            return True

        except Exception as e:
            logger.error(f"Error updating post: {e}")
            return False

    def _generate_product_post(self, context: Dict[str, Any], topic: str = None) -> str:
        """Generate product-focused post"""
        products = context.get('products', [])

        if not products:
            return self._generate_generic_post(context, topic)

        product = topic if topic else random.choice(products)

        templates = [
            f"🚀 Excited to share how {product} is transforming the way businesses operate.\n\nOur solution helps teams achieve more with less effort. Here's what makes it special:\n\n✅ Streamlined workflows\n✅ Increased productivity\n✅ Better outcomes\n\nInterested in learning more? Let's connect!",

            f"💡 Innovation spotlight: {product}\n\nWe built {product} to solve a real problem. Today, it's helping businesses like yours succeed.\n\nKey benefits:\n• Save time on repetitive tasks\n• Focus on what matters most\n• Scale with confidence\n\nReady to see it in action?",

            f"🎯 {product} is designed for teams that want to do more.\n\nWhether you're scaling up or optimizing operations, our solution adapts to your needs.\n\nWhat challenges are you facing? Let's discuss how we can help."
        ]

        return random.choice(templates)

    def _generate_service_post(self, context: Dict[str, Any], topic: str = None) -> str:
        """Generate service-focused post"""
        services = context.get('services', [])

        if not services:
            return self._generate_generic_post(context, topic)

        service = topic if topic else random.choice(services)

        templates = [
            f"🤝 Our {service} service is built on one principle: your success is our success.\n\nWe partner with businesses to deliver results that matter. From strategy to execution, we're with you every step.\n\nLet's talk about your goals.",

            f"💼 {service}: More than just a service, it's a partnership.\n\nWe bring expertise, dedication, and a commitment to excellence. Our clients choose us because we deliver.\n\nWhat can we help you achieve?",

            f"🌟 Introducing {service} - tailored solutions for modern businesses.\n\nEvery organization is unique. That's why we customize our approach to fit your specific needs.\n\nReady to explore possibilities?"
        ]

        return random.choice(templates)

    def _generate_value_post(self, context: Dict[str, Any], topic: str = None) -> str:
        """Generate value-focused post"""
        values = context.get('values', [])

        if not values:
            return self._generate_generic_post(context, topic)

        value = topic if topic else random.choice(values)

        templates = [
            f"💭 Reflection: {value}\n\nThis value guides everything we do. It shapes our decisions, our culture, and our relationships with clients.\n\nWhat values drive your organization?",

            f"🌱 At our core, we believe in {value}.\n\nIt's not just a statement on our website. It's how we show up every day, in every interaction.\n\nValues matter. What are yours?",

            f"✨ {value} - more than a buzzword, it's our commitment.\n\nWe hold ourselves accountable to this principle because it creates better outcomes for everyone.\n\nHow do you live your values?"
        ]

        return random.choice(templates)

    def _generate_insight_post(self, context: Dict[str, Any], topic: str = None) -> str:
        """Generate insight/thought leadership post"""
        templates = [
            f"📊 Industry insight: {topic or 'The future of work is changing'}\n\nWe're seeing a shift in how businesses operate. The companies that adapt quickly will thrive.\n\nKey trends to watch:\n• Remote-first operations\n• AI-powered automation\n• Data-driven decisions\n\nWhat trends are you seeing?",

            f"🔍 Observation: {topic or 'Success leaves clues'}\n\nAfter working with dozens of businesses, we've noticed patterns. The most successful organizations share common traits.\n\nThey:\n✓ Embrace change\n✓ Invest in their people\n✓ Focus on outcomes\n\nWhat would you add to this list?",

            f"💡 Thought: {topic or 'Efficiency vs. effectiveness'}\n\nDoing things right vs. doing the right things. Both matter, but one creates more value.\n\nHow do you balance efficiency and effectiveness in your work?"
        ]

        return random.choice(templates)

    def _generate_announcement_post(self, context: Dict[str, Any], topic: str = None) -> str:
        """Generate announcement post"""
        company_name = context.get('company_name', 'Our company')

        templates = [
            f"📢 Exciting news from {company_name}!\n\n{topic or 'We have something special to share.'}\n\nThis is just the beginning. Stay tuned for more updates.\n\nThank you for being part of our journey!",

            f"🎉 Big announcement: {topic or 'New milestone achieved!'}\n\nWe're thrilled to share this with our community. Your support makes moments like this possible.\n\nHere's to what's next!",

            f"🚀 {company_name} update: {topic or 'Something new is coming'}\n\nWe've been working hard behind the scenes. Can't wait to show you what we've built.\n\nMore details coming soon!"
        ]

        return random.choice(templates)

    def _generate_generic_post(self, context: Dict[str, Any], topic: str = None) -> str:
        """Generate generic business post"""
        company_name = context.get('company_name', 'Our company')

        templates = [
            f"👋 Quick update from {company_name}\n\n{topic or 'We are here to help businesses succeed.'}\n\nWhether you are scaling, optimizing, or transforming, we are ready to support your journey.\n\nLet's connect!",

            f"💼 {company_name} is committed to delivering value.\n\n{topic or 'Every day, we work with businesses like yours to achieve more.'}\n\nWhat challenges can we help you solve?",

            f"🌟 At {company_name}, we believe in {topic or 'making a difference'}.\n\nOur mission is simple: help businesses thrive in a changing world.\n\nReady to grow together?"
        ]

        return random.choice(templates)

    def _generate_hashtags(self, post_type: str, context: Dict[str, Any]) -> List[str]:
        """Generate relevant hashtags"""
        # Base hashtags
        base_hashtags = ['#Business', '#Growth', '#Innovation']

        # Type-specific hashtags
        type_hashtags = {
            'product': ['#ProductDevelopment', '#Technology', '#Solutions'],
            'service': ['#Services', '#Consulting', '#Partnership'],
            'value': ['#Leadership', '#Culture', '#Values'],
            'insight': ['#ThoughtLeadership', '#Insights', '#Trends'],
            'announcement': ['#News', '#Announcement', '#Update']
        }

        hashtags = base_hashtags + type_hashtags.get(post_type, [])

        # Limit based on strategy
        if self.hashtag_strategy == 'minimal':
            return hashtags[:3]
        elif self.hashtag_strategy == 'moderate':
            return hashtags[:5]
        else:  # aggressive
            return hashtags[:8]

    def _get_next_optimal_time(self) -> str:
        """Get next optimal posting time"""
        now = datetime.now()

        # Find next optimal time
        for optimal_time in self.optimal_times:
            scheduled = datetime.combine(now.date(), optimal_time)

            if scheduled > now:
                return scheduled.isoformat()

        # If no time today, use first time tomorrow
        tomorrow = now.date().replace(day=now.day + 1)
        scheduled = datetime.combine(tomorrow, self.optimal_times[0])
        return scheduled.isoformat()

    def _extract_company_name(self, content: str) -> str:
        """Extract company name from content"""
        # Simple extraction - look for first heading or "Company:" line
        lines = content.split('\n')
        for line in lines:
            if line.startswith('# '):
                return line.replace('# ', '').strip()
            if line.startswith('Company:'):
                return line.replace('Company:', '').strip()

        return 'Our Company'

    def _extract_products(self, content: str) -> List[str]:
        """Extract products from content"""
        products = []
        lines = content.split('\n')

        for line in lines:
            if line.startswith('- ') or line.startswith('* '):
                product = line.replace('- ', '').replace('* ', '').strip()
                if product:
                    products.append(product)

        return products[:5]  # Limit to 5

    def _extract_services(self, content: str) -> List[str]:
        """Extract services from content"""
        return self._extract_products(content)  # Same logic

    def _extract_values(self, content: str) -> List[str]:
        """Extract values from content"""
        return self._extract_products(content)  # Same logic

    def _extract_key_messages(self, content: str) -> List[str]:
        """Extract key messages from content"""
        return self._extract_products(content)  # Same logic
