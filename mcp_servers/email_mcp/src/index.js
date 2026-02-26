/**
 * Email MCP Server
 *
 * Provides email operations via Model Context Protocol (MCP).
 * Integrates with Gmail API for sending and reading emails.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import { GmailClient } from './gmail_client.js';
import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';

// Load environment variables
dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Configuration
const CREDENTIALS_PATH = process.env.GMAIL_CREDENTIALS_PATH || 'credentials/gmail_credentials.json';
const TOKEN_PATH = process.env.GMAIL_TOKEN_PATH || 'credentials/gmail_token.json';

/**
 * Email MCP Server
 */
class EmailMCPServer {
  constructor() {
    this.server = new Server(
      {
        name: 'email-mcp',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
          resources: {},
        },
      }
    );

    this.gmailClient = new GmailClient(CREDENTIALS_PATH, TOKEN_PATH);
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
          name: 'send_email',
          description: 'Send an email via Gmail',
          inputSchema: {
            type: 'object',
            properties: {
              to: {
                type: 'string',
                description: 'Recipient email address',
              },
              subject: {
                type: 'string',
                description: 'Email subject',
              },
              body: {
                type: 'string',
                description: 'Email body (plain text)',
              },
              threadId: {
                type: 'string',
                description: 'Thread ID for replies (optional)',
              },
            },
            required: ['to', 'subject', 'body'],
          },
        },
        {
          name: 'list_emails',
          description: 'List emails from Gmail inbox',
          inputSchema: {
            type: 'object',
            properties: {
              query: {
                type: 'string',
                description: 'Gmail search query (default: "is:unread in:inbox")',
              },
              maxResults: {
                type: 'number',
                description: 'Maximum number of results (default: 10)',
              },
            },
          },
        },
        {
          name: 'get_email',
          description: 'Get email details by ID',
          inputSchema: {
            type: 'object',
            properties: {
              messageId: {
                type: 'string',
                description: 'Gmail message ID',
              },
            },
            required: ['messageId'],
          },
        },
      ],
    }));

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'send_email':
            return await this.handleSendEmail(args);

          case 'list_emails':
            return await this.handleListEmails(args);

          case 'get_email':
            return await this.handleGetEmail(args);

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

    // List available resources
    this.server.setRequestHandler(ListResourcesRequestSchema, async () => ({
      resources: [
        {
          uri: 'gmail://inbox',
          name: 'Gmail Inbox',
          description: 'Access to Gmail inbox messages',
          mimeType: 'application/json',
        },
      ],
    }));

    // Read resource
    this.server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
      const { uri } = request.params;

      if (uri === 'gmail://inbox') {
        const messages = await this.gmailClient.listEmails({
          query: 'is:unread in:inbox',
          maxResults: 10,
        });

        return {
          contents: [
            {
              uri,
              mimeType: 'application/json',
              text: JSON.stringify(messages, null, 2),
            },
          ],
        };
      }

      throw new Error(`Unknown resource: ${uri}`);
    });
  }

  /**
   * Handle send_email tool call
   */
  async handleSendEmail(args) {
    const { to, subject, body, threadId } = args;

    const result = await this.gmailClient.sendEmail({
      to,
      subject,
      body,
      threadId,
    });

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2),
        },
      ],
    };
  }

  /**
   * Handle list_emails tool call
   */
  async handleListEmails(args) {
    const { query, maxResults } = args;

    const messages = await this.gmailClient.listEmails({
      query,
      maxResults,
    });

    // Extract key information
    const simplified = messages.map((msg) => {
      const headers = this.gmailClient.extractHeaders(msg);
      return {
        id: msg.id,
        threadId: msg.threadId,
        from: headers.From,
        subject: headers.Subject,
        date: headers.Date,
        snippet: msg.snippet,
      };
    });

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(simplified, null, 2),
        },
      ],
    };
  }

  /**
   * Handle get_email tool call
   */
  async handleGetEmail(args) {
    const { messageId } = args;

    const message = await this.gmailClient.getEmail(messageId);

    const headers = this.gmailClient.extractHeaders(message);
    const body = this.gmailClient.extractBody(message);

    const result = {
      id: message.id,
      threadId: message.threadId,
      headers,
      body,
      snippet: message.snippet,
    };

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2),
        },
      ],
    };
  }

  /**
   * Start the MCP server
   */
  async start() {
    try {
      // Initialize Gmail client
      await this.gmailClient.initialize();

      // Start server with stdio transport
      const transport = new StdioServerTransport();
      await this.server.connect(transport);

      console.error('Email MCP server started successfully');
    } catch (error) {
      console.error('Failed to start Email MCP server:', error);
      process.exit(1);
    }
  }
}

// Start server
const server = new EmailMCPServer();
server.start();
