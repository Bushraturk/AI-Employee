"""Social media drafter for cloud agent.

Generates draft social media posts based on business goals and strategic themes.
Writes drafts to Pending_Approval/social/ for human review.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pathlib import Path

from shared.models.approval_request import ApprovalRequest, ApprovalType, ApprovalStatus, RiskLevel
from shared.utils.vault_manager import VaultManager
from shared.utils.logger import VaultLogger, LogCategory
from shared.risk_assessor import RiskAssessor
from cloud_agent.src.utils.business_goals_parser import BusinessGoalsParser


logger = logging.getLogger(__name__)


class SocialDrafter:
    """Drafts social media posts based on business goals.

    Analyzes business goals and generates appropriate social media content
    aligned with strategic themes and success indicators.
    """

    def __init__(
        self,
        agent_id: str,
        vault_manager: VaultManager,
        vault_logger: VaultLogger,
        claude_api_key: str,
        business_goals_path: str,
    ):
        """Initialize social drafter.

        Args:
            agent_id: Agent ID
            vault_manager: Vault manager instance
            vault_logger: Vault logger instance
            claude_api_key: Claude API key
            business_goals_path: Path to Business_Goals.md
        """
        self.agent_id = agent_id
        self.vault_manager = vault_manager
        self.vault_logger = vault_logger
        self.claude_api_key = claude_api_key
        self.business_goals_path = business_goals_path

        # Initialize risk assessor
        self.risk_assessor = RiskAssessor()

        # Initialize business goals parser
        vault_path = Path(business_goals_path).parent
        self.goals_parser = BusinessGoalsParser(vault_path)

        logger.info("Social drafter initialized")

    def draft_post(
        self,
        platform: str = "linkedin",
        content_type: str = "update",
    ) -> Optional[ApprovalRequest]:
        """Draft a social media post.

        Args:
            platform: Target platform (linkedin, twitter, facebook, instagram)
            content_type: Type of content (update, announcement, tip, insight)

        Returns:
            ApprovalRequest instance or None if drafting failed
        """
        try:
            self.vault_logger.info(
                LogCategory.AGENT,
                f"Drafting {content_type} post for {platform}",
                details={"platform": platform, "content_type": content_type}
            )

            # Get business goals context
            social_focus = self.goals_parser.get_social_media_focus()

            # Generate post content
            post_content = self._generate_post_content(
                platform=platform,
                content_type=content_type,
                social_focus=social_focus,
            )

            if not post_content:
                logger.error(f"Failed to generate post content for {platform}")
                return None

            # Assess risk
            risk_level, risk_factors = self.risk_assessor.assess_social_post(
                platform=platform,
                content=post_content,
            )

            # Create approval request
            approval_id = f"social_approval_{platform}_{datetime.now().strftime('%Y%m%dT%H%M%SZ')}"

            approval = ApprovalRequest(
                approval_id=approval_id,
                approval_type=ApprovalType.SOCIAL_POST,
                target_id=platform,
                timestamp=datetime.now(),
                status=ApprovalStatus.PENDING,
                risk_level=risk_level,
                risk_factors=risk_factors,
                title=f"Social post for {platform.title()}: {content_type}",
                summary=f"Draft {content_type} post for {platform}",
                body=post_content,
                metadata={
                    "platform": platform,
                    "content_type": content_type,
                    "scheduled_time": None,  # Can be set by user during approval
                },
                created_by=self.agent_id,
                action_file_id=f"social_{platform}_{datetime.now().strftime('%Y%m%d')}",
                expires_at=datetime.now() + timedelta(hours=48),
            )

            # Write approval request to vault
            approval_folder = "Pending_Approval/social"
            approval_path = self.vault_manager.get_folder_path(approval_folder) / approval.get_filename()
            approval.to_file(str(approval_path))

            self.vault_logger.info(
                LogCategory.AGENT,
                f"Created social post approval request: {approval_id}",
                details={
                    "approval_id": approval_id,
                    "platform": platform,
                    "risk_level": risk_level.value,
                }
            )

            # Write update for dashboard
            self._write_dashboard_update(approval, platform, content_type)

            return approval

        except Exception as e:
            self.vault_logger.error(
                LogCategory.AGENT,
                f"Failed to draft social post: {e}",
                error_type=type(e).__name__,
                stack_trace=str(e),
            )
            return None

    def _generate_post_content(
        self,
        platform: str,
        content_type: str,
        social_focus: Dict[str, Any],
    ) -> Optional[str]:
        """Generate post content using business goals context.

        Args:
            platform: Target platform
            content_type: Type of content
            social_focus: Social media focus from business goals

        Returns:
            Post content or None if generation failed
        """
        try:
            # For MVP, use template-based generation
            # TODO: Integrate with Claude API via MCP for dynamic content

            themes = social_focus.get("themes", [])
            projects = social_focus.get("projects", [])

            # Select theme for this post
            theme = themes[0] if themes else "Business automation and efficiency"

            # Generate content based on platform and type
            if platform == "linkedin":
                content = self._generate_linkedin_post(content_type, theme, projects)
            elif platform == "twitter":
                content = self._generate_twitter_post(content_type, theme)
            elif platform == "facebook":
                content = self._generate_facebook_post(content_type, theme, projects)
            elif platform == "instagram":
                content = self._generate_instagram_post(content_type, theme)
            else:
                content = self._generate_generic_post(content_type, theme)

            return content

        except Exception as e:
            logger.error(f"Failed to generate post content: {e}")
            return None

    def _generate_linkedin_post(
        self,
        content_type: str,
        theme: str,
        projects: List[Dict[str, str]],
    ) -> str:
        """Generate LinkedIn post content.

        Args:
            content_type: Type of content
            theme: Strategic theme
            projects: Active projects

        Returns:
            LinkedIn post content
        """
        if content_type == "update":
            return f"""🚀 Exciting progress on our automation journey!

We're focused on {theme.lower()}, and the results are already showing.

Key highlights:
• Streamlined workflows reducing manual tasks
• Improved response times for better client experience
• Real-time visibility into business operations

The future of work is here, and it's automated. 💡

#Automation #BusinessEfficiency #DigitalTransformation

---
[DRAFT - Requires Approval]
"""
        elif content_type == "insight":
            return f"""💡 Business Insight: {theme}

In today's fast-paced business environment, automation isn't just a luxury—it's a necessity.

Here's what we've learned:
✓ Automation frees up time for strategic work
✓ Consistent processes lead to better outcomes
✓ Technology should enhance, not replace, human judgment

What's your experience with business automation? Share in the comments! 👇

#BusinessStrategy #Automation #Productivity

---
[DRAFT - Requires Approval]
"""
        else:
            return f"""📢 {theme}

We're committed to leveraging technology to deliver exceptional results.

Stay tuned for more updates!

#Business #Innovation

---
[DRAFT - Requires Approval]
"""

    def _generate_twitter_post(self, content_type: str, theme: str) -> str:
        """Generate Twitter post content.

        Args:
            content_type: Type of content
            theme: Strategic theme

        Returns:
            Twitter post content (280 chars max)
        """
        if content_type == "update":
            return f"""🚀 Making progress on {theme.split(':')[0].lower()}!

Automation is transforming how we work. The results speak for themselves.

#Automation #BusinessEfficiency

[DRAFT - Requires Approval]
"""
        else:
            return f"""💡 {theme.split(':')[0]}

The future of work is automated, efficient, and human-centered.

#Business #Innovation

[DRAFT - Requires Approval]
"""

    def _generate_facebook_post(
        self,
        content_type: str,
        theme: str,
        projects: List[Dict[str, str]],
    ) -> str:
        """Generate Facebook post content.

        Args:
            content_type: Type of content
            theme: Strategic theme
            projects: Active projects

        Returns:
            Facebook post content
        """
        return f"""🎯 {theme}

We're excited to share our progress in business automation and efficiency!

Our focus areas:
• Reducing manual tasks through smart automation
• Improving client communication and response times
• Building real-time visibility into operations

Technology is enabling us to work smarter, not harder. 💪

What automation tools are you using in your business? Let us know in the comments!

#BusinessAutomation #Efficiency #SmallBusiness

---
[DRAFT - Requires Approval]
"""

    def _generate_instagram_post(self, content_type: str, theme: str) -> str:
        """Generate Instagram post content.

        Args:
            content_type: Type of content
            theme: Strategic theme

        Returns:
            Instagram post content
        """
        return f"""✨ {theme.split(':')[0]} ✨

Transforming the way we work, one automation at a time.

🤖 Smart workflows
⚡ Faster response times
📊 Real-time insights

The future is automated. Are you ready?

#BusinessAutomation #Productivity #Innovation #SmallBusiness #Entrepreneur

---
[DRAFT - Requires Approval]
"""

    def _generate_generic_post(self, content_type: str, theme: str) -> str:
        """Generate generic post content.

        Args:
            content_type: Type of content
            theme: Strategic theme

        Returns:
            Generic post content
        """
        return f"""{theme}

We're leveraging automation to improve efficiency and deliver better results.

Stay tuned for updates!

---
[DRAFT - Requires Approval]
"""

    def _write_dashboard_update(
        self,
        approval: ApprovalRequest,
        platform: str,
        content_type: str,
    ) -> None:
        """Write update for dashboard merger.

        Args:
            approval: Created approval request
            platform: Target platform
            content_type: Content type
        """
        try:
            update_folder = "Updates"
            update_filename = f"social_draft_{datetime.now().strftime('%Y%m%dT%H%M%SZ')}.md"
            update_path = self.vault_manager.get_folder_path(update_folder) / update_filename

            update_content = f"""---
type: social_draft
timestamp: {datetime.now().isoformat()}
approval_id: {approval.approval_id}
platform: {platform}
content_type: {content_type}
---

# Social Media Draft Created

**Platform**: {platform.title()}
**Content Type**: {content_type}
**Risk Level**: {approval.risk_level.value}

Draft social media post created and awaiting approval in `Pending_Approval/social/`.
"""

            with open(update_path, "w", encoding="utf-8") as f:
                f.write(update_content)

        except Exception as e:
            logger.error(f"Failed to write dashboard update: {e}")
