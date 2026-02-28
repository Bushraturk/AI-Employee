/**
 * Social Media MCP Server
 *
 * Provides social media posting operations via Model Context Protocol (MCP).
 * Supports Facebook, Instagram, Twitter, and LinkedIn.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import axios from 'axios';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

/**
 * Social Media MCP Server
 */
class SocialMCPServer {
  constructor() {
    this.server = new Server(
      {
        name: 'social-mcp',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    // Platform credentials
    this.credentials = {
      facebook: {
        accessToken: process.env.FACEBOOK_ACCESS_TOKEN,
        pageId: process.env.FACEBOOK_PAGE_ID,
      },
      instagram: {
        accessToken: process.env.INSTAGRAM_ACCESS_TOKEN,
        accountId: process.env.INSTAGRAM_ACCOUNT_ID,
      },
      twitter: {
        apiKey: process.env.TWITTER_API_KEY,
        apiSecret: process.env.TWITTER_API_SECRET,
        accessToken: process.env.TWITTER_ACCESS_TOKEN,
        accessSecret: process.env.TWITTER_ACCESS_SECRET,
      },
      linkedin: {
        accessToken: process.env.LINKEDIN_ACCESS_TOKEN,
        organizationId: process.env.LINKEDIN_ORGANIZATION_ID,
      },
    };

    this.setupHandlers();
  }

  /**
   * Setup MCP request handlers
   */
  setupHandlers() {
    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'post_to_facebook',
          description: 'Post content to Facebook page',
          inputSchema: {
            type: 'object',
            properties: {
              message: {
                type: 'string',
                description: 'Post message/content',
              },
              link: {
                type: 'string',
                description: 'Optional link to share',
              },
            },
            required: ['message'],
          },
        },
        {
          name: 'post_to_instagram',
          description: 'Post image to Instagram',
          inputSchema: {
            type: 'object',
            properties: {
              imageUrl: {
                type: 'string',
                description: 'URL of image to post',
              },
              caption: {
                type: 'string',
                description: 'Post caption',
              },
            },
            required: ['imageUrl', 'caption'],
          },
        },
        {
          name: 'post_to_twitter',
          description: 'Post tweet to Twitter',
          inputSchema: {
            type: 'object',
            properties: {
              text: {
                type: 'string',
                description: 'Tweet text (max 280 characters)',
              },
            },
            required: ['text'],
          },
        },
        {
          name: 'post_to_linkedin',
          description: 'Post content to LinkedIn organization page',
          inputSchema: {
            type: 'object',
            properties: {
              text: {
                type: 'string',
                description: 'Post text/content',
              },
              link: {
                type: 'string',
                description: 'Optional link to share',
              },
            },
            required: ['text'],
          },
        },
      ],
    }));

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'post_to_facebook':
            return await this.postToFacebook(args);

          case 'post_to_instagram':
            return await this.postToInstagram(args);

          case 'post_to_twitter':
            return await this.postToTwitter(args);

          case 'post_to_linkedin':
            return await this.postToLinkedIn(args);

          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error) {
        return {
          content: [
            {
              type: 'text',
              text: `Error: ${error.message}`,
            },
          ],
          isError: true,
        };
      }
    });
  }

  /**
   * Post to Facebook
   */
  async postToFacebook(args) {
    const { message, link } = args;
    const { accessToken, pageId } = this.credentials.facebook;

    if (!accessToken || !pageId) {
      throw new Error('Facebook credentials not configured');
    }

    const url = `https://graph.facebook.com/v18.0/${pageId}/feed`;
    const data = {
      message,
      access_token: accessToken,
    };

    if (link) {
      data.link = link;
    }

    const response = await axios.post(url, data);

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            success: true,
            platform: 'facebook',
            postId: response.data.id,
            message: 'Posted to Facebook successfully',
          }),
        },
      ],
    };
  }

  /**
   * Post to Instagram
   */
  async postToInstagram(args) {
    const { imageUrl, caption } = args;
    const { accessToken, accountId } = this.credentials.instagram;

    if (!accessToken || !accountId) {
      throw new Error('Instagram credentials not configured');
    }

    // Step 1: Create media container
    const containerUrl = `https://graph.facebook.com/v18.0/${accountId}/media`;
    const containerData = {
      image_url: imageUrl,
      caption,
      access_token: accessToken,
    };

    const containerResponse = await axios.post(containerUrl, containerData);
    const containerId = containerResponse.data.id;

    // Step 2: Publish media container
    const publishUrl = `https://graph.facebook.com/v18.0/${accountId}/media_publish`;
    const publishData = {
      creation_id: containerId,
      access_token: accessToken,
    };

    const publishResponse = await axios.post(publishUrl, publishData);

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            success: true,
            platform: 'instagram',
            postId: publishResponse.data.id,
            message: 'Posted to Instagram successfully',
          }),
        },
      ],
    };
  }

  /**
   * Post to Twitter
   */
  async postToTwitter(args) {
    const { text } = args;
    const { apiKey, apiSecret, accessToken, accessSecret } = this.credentials.twitter;

    if (!apiKey || !apiSecret || !accessToken || !accessSecret) {
      throw new Error('Twitter credentials not configured');
    }

    // Twitter API v2 requires OAuth 1.0a
    // For simplicity, using a basic implementation
    // In production, use a proper OAuth library like 'twitter-api-v2'

    const url = 'https://api.twitter.com/2/tweets';
    const data = { text };

    // Note: This is a simplified version
    // Real implementation needs proper OAuth 1.0a signing
    const response = await axios.post(url, data, {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
    });

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            success: true,
            platform: 'twitter',
            tweetId: response.data.data.id,
            message: 'Posted to Twitter successfully',
          }),
        },
      ],
    };
  }

  /**
   * Post to LinkedIn
   */
  async postToLinkedIn(args) {
    const { text, link } = args;
    const { accessToken, organizationId } = this.credentials.linkedin;

    if (!accessToken || !organizationId) {
      throw new Error('LinkedIn credentials not configured');
    }

    const url = 'https://api.linkedin.com/v2/ugcPosts';
    const data = {
      author: `urn:li:organization:${organizationId}`,
      lifecycleState: 'PUBLISHED',
      specificContent: {
        'com.linkedin.ugc.ShareContent': {
          shareCommentary: {
            text,
          },
          shareMediaCategory: 'NONE',
        },
      },
      visibility: {
        'com.linkedin.ugc.MemberNetworkVisibility': 'PUBLIC',
      },
    };

    if (link) {
      data.specificContent['com.linkedin.ugc.ShareContent'].shareMediaCategory = 'ARTICLE';
      data.specificContent['com.linkedin.ugc.ShareContent'].media = [
        {
          status: 'READY',
          originalUrl: link,
        },
      ];
    }

    const response = await axios.post(url, data, {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
        'X-Restli-Protocol-Version': '2.0.0',
      },
    });

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            success: true,
            platform: 'linkedin',
            postId: response.data.id,
            message: 'Posted to LinkedIn successfully',
          }),
        },
      ],
    };
  }

  /**
   * Start the server
   */
  async start() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Social MCP Server running on stdio');
  }
}

// Start server
const server = new SocialMCPServer();
server.start().catch(console.error);
