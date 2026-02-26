/**
 * Gmail client for Email MCP server
 *
 * Handles Gmail API authentication and email operations.
 */

import { google } from 'googleapis';
import fs from 'fs/promises';
import path from 'path';

export class GmailClient {
  constructor(credentialsPath, tokenPath) {
    this.credentialsPath = credentialsPath;
    this.tokenPath = tokenPath;
    this.gmail = null;
    this.auth = null;
  }

  /**
   * Initialize Gmail API client
   */
  async initialize() {
    try {
      // Load credentials
      const credentials = JSON.parse(
        await fs.readFile(this.credentialsPath, 'utf-8')
      );

      const { client_secret, client_id, redirect_uris } = credentials.installed || credentials.web;

      // Create OAuth2 client
      this.auth = new google.auth.OAuth2(
        client_id,
        client_secret,
        redirect_uris[0]
      );

      // Load token
      const token = JSON.parse(
        await fs.readFile(this.tokenPath, 'utf-8')
      );

      this.auth.setCredentials(token);

      // Create Gmail client
      this.gmail = google.gmail({ version: 'v1', auth: this.auth });

      console.log('Gmail client initialized successfully');
    } catch (error) {
      console.error('Failed to initialize Gmail client:', error);
      throw error;
    }
  }

  /**
   * Send an email
   *
   * @param {Object} params - Email parameters
   * @param {string} params.to - Recipient email address
   * @param {string} params.subject - Email subject
   * @param {string} params.body - Email body (plain text)
   * @param {string} [params.threadId] - Thread ID for replies
   * @returns {Promise<Object>} Sent message details
   */
  async sendEmail({ to, subject, body, threadId }) {
    try {
      // Create email message
      const message = this._createMessage(to, subject, body);

      // Send email
      const params = {
        userId: 'me',
        requestBody: {
          raw: message,
        },
      };

      // Add thread ID if replying
      if (threadId) {
        params.requestBody.threadId = threadId;
      }

      const response = await this.gmail.users.messages.send(params);

      console.log('Email sent successfully:', response.data.id);

      return {
        success: true,
        messageId: response.data.id,
        threadId: response.data.threadId,
      };
    } catch (error) {
      console.error('Failed to send email:', error);
      return {
        success: false,
        error: error.message,
      };
    }
  }

  /**
   * List emails
   *
   * @param {Object} params - List parameters
   * @param {string} [params.query] - Gmail search query
   * @param {number} [params.maxResults=10] - Maximum results
   * @returns {Promise<Array>} List of messages
   */
  async listEmails({ query = 'is:unread in:inbox', maxResults = 10 }) {
    try {
      const response = await this.gmail.users.messages.list({
        userId: 'me',
        q: query,
        maxResults,
      });

      const messages = response.data.messages || [];

      // Get full message details
      const fullMessages = await Promise.all(
        messages.map(async (msg) => {
          const fullMsg = await this.gmail.users.messages.get({
            userId: 'me',
            id: msg.id,
            format: 'full',
          });
          return fullMsg.data;
        })
      );

      return fullMessages;
    } catch (error) {
      console.error('Failed to list emails:', error);
      throw error;
    }
  }

  /**
   * Get email by ID
   *
   * @param {string} messageId - Message ID
   * @returns {Promise<Object>} Message details
   */
  async getEmail(messageId) {
    try {
      const response = await this.gmail.users.messages.get({
        userId: 'me',
        id: messageId,
        format: 'full',
      });

      return response.data;
    } catch (error) {
      console.error('Failed to get email:', error);
      throw error;
    }
  }

  /**
   * Create RFC 2822 formatted email message
   *
   * @private
   * @param {string} to - Recipient
   * @param {string} subject - Subject
   * @param {string} body - Body
   * @returns {string} Base64 encoded message
   */
  _createMessage(to, subject, body) {
    const message = [
      `To: ${to}`,
      `Subject: ${subject}`,
      'Content-Type: text/plain; charset=utf-8',
      '',
      body,
    ].join('\n');

    // Base64 encode (URL-safe)
    const encodedMessage = Buffer.from(message)
      .toString('base64')
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=+$/, '');

    return encodedMessage;
  }

  /**
   * Extract email headers
   *
   * @param {Object} message - Gmail message object
   * @returns {Object} Headers as key-value pairs
   */
  extractHeaders(message) {
    const headers = {};
    if (message.payload && message.payload.headers) {
      message.payload.headers.forEach((header) => {
        headers[header.name] = header.value;
      });
    }
    return headers;
  }

  /**
   * Extract email body
   *
   * @param {Object} message - Gmail message object
   * @returns {string} Email body text
   */
  extractBody(message) {
    let body = '';

    const payload = message.payload;

    if (payload.parts) {
      // Multipart message
      for (const part of payload.parts) {
        if (part.mimeType === 'text/plain' && part.body.data) {
          body = Buffer.from(part.body.data, 'base64').toString('utf-8');
          break;
        }
      }
    } else if (payload.body && payload.body.data) {
      // Simple message
      body = Buffer.from(payload.body.data, 'base64').toString('utf-8');
    }

    return body || '(No text content)';
  }
}
