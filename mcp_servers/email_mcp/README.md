# Email MCP Server

**Version**: 1.0.0
**Protocol**: Model Context Protocol (MCP)
**Integration**: Gmail API

## Overview

The Email MCP server provides email operations for the AI Employee system via the Model Context Protocol. It integrates with Gmail API to send and read emails.

## Features

- **Send Email**: Send emails via Gmail with optional thread support
- **List Emails**: Query Gmail inbox with custom search queries
- **Get Email**: Retrieve full email details by message ID
- **Resources**: Access Gmail inbox as an MCP resource

## Installation

```bash
cd mcp_servers/email_mcp
npm install
```

## Configuration

### Environment Variables

Create a `.env` file or set environment variables:

```bash
GMAIL_CREDENTIALS_PATH=credentials/gmail_credentials.json
GMAIL_TOKEN_PATH=credentials/gmail_token.json
```

### Gmail API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Gmail API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download credentials as `gmail_credentials.json`
6. Run authentication flow to generate `gmail_token.json`

## Usage

### Start Server

```bash
npm start
```

### Development Mode

```bash
npm run dev
```

## MCP Tools

### send_email

Send an email via Gmail.

**Parameters:**
- `to` (string, required): Recipient email address
- `subject` (string, required): Email subject
- `body` (string, required): Email body (plain text)
- `threadId` (string, optional): Thread ID for replies

**Example:**
```json
{
  "to": "recipient@example.com",
  "subject": "Hello from AI Employee",
  "body": "This is a test email sent via MCP.",
  "threadId": "thread_123"
}
```

**Response:**
```json
{
  "success": true,
  "messageId": "msg_456",
  "threadId": "thread_123"
}
```

### list_emails

List emails from Gmail inbox.

**Parameters:**
- `query` (string, optional): Gmail search query (default: "is:unread in:inbox")
- `maxResults` (number, optional): Maximum results (default: 10)

**Example:**
```json
{
  "query": "is:unread in:inbox",
  "maxResults": 5
}
```

**Response:**
```json
[
  {
    "id": "msg_123",
    "threadId": "thread_456",
    "from": "sender@example.com",
    "subject": "Important Message",
    "date": "Mon, 25 Feb 2026 10:00:00 +0000",
    "snippet": "This is a preview of the email..."
  }
]
```

### get_email

Get full email details by message ID.

**Parameters:**
- `messageId` (string, required): Gmail message ID

**Example:**
```json
{
  "messageId": "msg_123"
}
```

**Response:**
```json
{
  "id": "msg_123",
  "threadId": "thread_456",
  "headers": {
    "From": "sender@example.com",
    "Subject": "Important Message",
    "Date": "Mon, 25 Feb 2026 10:00:00 +0000"
  },
  "body": "Full email body text...",
  "snippet": "This is a preview..."
}
```

## MCP Resources

### gmail://inbox

Access Gmail inbox messages as an MCP resource.

**URI**: `gmail://inbox`
**MIME Type**: `application/json`

Returns list of unread inbox messages (max 10).

## Integration with AI Employee

The Email MCP server is used by the Local Agent's EmailExecutor to send approved emails.

**Flow:**
1. Local Agent detects approved email in `Approved/` folder
2. EmailExecutor calls `send_email` tool via MCP
3. Email MCP server sends email via Gmail API
4. Result logged to audit trail

## Error Handling

All errors are returned in MCP format:

```json
{
  "content": [
    {
      "type": "text",
      "text": "Error: Failed to send email - Invalid recipient"
    }
  ],
  "isError": true
}
```

## Security

- **Credentials**: Gmail credentials stored locally, never synced to vault
- **OAuth 2.0**: Uses OAuth 2.0 for Gmail API authentication
- **Token Refresh**: Automatically refreshes expired tokens
- **Local Only**: MCP server runs locally, not on cloud VM

## Troubleshooting

### Authentication Failed

```bash
# Delete token and re-authenticate
rm credentials/gmail_token.json
npm start
```

### Gmail API Quota Exceeded

Gmail API has rate limits:
- 250 quota units per user per second
- 1 billion quota units per day

Sending an email costs 100 quota units.

### Connection Refused

Ensure the MCP server is running and the local agent can connect via stdio transport.

## Development

### Project Structure

```
email_mcp/
├── src/
│   ├── index.js          # MCP server entry point
│   └── gmail_client.js   # Gmail API client
├── package.json          # Dependencies
└── README.md            # This file
```

### Dependencies

- `@modelcontextprotocol/sdk`: MCP protocol implementation
- `googleapis`: Google APIs client library
- `dotenv`: Environment variable management

## License

Private - All Rights Reserved
