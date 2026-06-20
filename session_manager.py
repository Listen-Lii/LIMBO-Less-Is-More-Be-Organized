#!/usr/bin/env python3
"""
Session Manager - MCP Server for unified LLM routing

Provides MCP tools for forwarding messages to AI agents and receiving
streaming responses. Works with any MCP-compatible agent.

Protocol: JSON-RPC over stdin/stdout (similar to wechat server.ts)

Usage:
    python3 session_manager.py

The MCP server communicates via stdin/stdout using JSON-RPC protocol.
No external MCP SDK required - implements protocol manually.
"""

import json
import sys
import asyncio
import os
from typing import Dict, Any, Optional

# Import OpenClaw LLM client for routing LLM calls through OpenClaw Gateway
try:
    from openclaw_llm import get_default_client
except ImportError:
    # Fallback if openclaw_llm not available
    def get_default_client():
        return None

# Global session manager instance
_session_manager: Optional['SessionManager'] = None


class SessionManager:
    """Manages persistent agent sessions for LLM routing."""

    def __init__(self):
        self.sessions: Dict[str, 'AgentSession'] = {}
        self.pending_responses: Dict[str, asyncio.Queue] = {}

    def get_or_create_session(self, session_id: str, working_dir: str = "") -> 'AgentSession':
        """Get or create a session for the given session_id."""
        if session_id not in self.sessions:
            self.sessions[session_id] = AgentSession(session_id, working_dir)
        return self.sessions[session_id]

    def on_agent_response(self, session_id: str, content: str, done: bool = False):
        """Handle agent response - called when agent sends response."""
        if session_id in self.pending_responses:
            self.pending_responses[session_id].put_nowait({'content': content, 'done': done})


class AgentSession:
    """Represents a single agent session."""

    def __init__(self, session_id: str, working_dir: str = ""):
        self.session_id = session_id
        self.working_dir = working_dir
        self.messages: list = []

    def add_message(self, message: str):
        """Add a message to the session history."""
        self.messages.append({'role': 'user', 'content': message})


# ============================================================================
# MCP Protocol Helpers
# ============================================================================

def send_response(req_id: Any, result: dict):
    """Send JSON-RPC response to stdout."""
    response = {'jsonrpc': '2.0', 'id': req_id, 'result': result}
    sys.stdout.write(json.dumps(response) + '\n')
    sys.stdout.flush()


def send_error(req_id: Any, code: int, message: str):
    """Send JSON-RPC error to stdout."""
    response = {'jsonrpc': '2.0', 'id': req_id, 'error': {'code': code, 'message': message}}
    sys.stdout.write(json.dumps(response) + '\n')
    sys.stdout.flush()


def send_notification(method: str, params: dict):
    """Send JSON-RPC notification to stdout."""
    notification = {'jsonrpc': '2.0', 'method': method, 'params': params}
    sys.stdout.write(json.dumps(notification) + '\n')
    sys.stdout.flush()


# ============================================================================
# MCP Handlers
# ============================================================================

def handle_initialize(params: dict) -> dict:
    """Handle MCP initialize request."""
    return {
        'protocolVersion': '2024-11-05',
        'capabilities': {
            'tools': {},
            'resources': {},
        },
        'serverInfo': {
            'name': 'session-manager',
            'version': '1.0.0',
        },
    }


def handle_list_tools() -> dict:
    """Handle MCP list_tools request."""
    return {
        'tools': [
            {
                'name': 'forward_message',
                'description': 'Forward a message from web UI to the agent session',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'session_id': {'type': 'string', 'description': 'Session identifier'},
                        'message': {'type': 'string', 'description': 'Message to forward'},
                        'working_dir': {'type': 'string', 'description': 'Working directory context'},
                    },
                    'required': ['session_id', 'message'],
                },
            },
        ],
    }


def handle_call_tool(params: dict, session_mgr: SessionManager) -> dict:
    """Handle MCP call_tool request."""
    tool_name = params.get('name')
    args = params.get('arguments', {})

    if tool_name == 'forward_message':
        session_id = args.get('session_id', 'default')
        message = args.get('message', '')
        working_dir = args.get('working_dir', '')

        session = session_mgr.get_or_create_session(session_id, working_dir)
        session.add_message(message)

        # Build prompt with history
        context = f"工作目录: {working_dir}\n\n" if working_dir else ""
        context += "\n".join([f"{m['role']}: {m['content']}" for m in session.messages])

        # Use OpenClaw Gateway for LLM call
        messages = [
            {"role": "user", "content": context}
        ]
        client = get_default_client()
        if client:
            llm_result = client.complete_raw(messages, max_tokens=4096, temperature=0.7)
            if llm_result.get("error"):
                return {'content': [{'type': 'text', 'text': f'OpenClaw LLM error: {llm_result["error"]}'}], 'isError': True}
            response_text = llm_result.get("text", "")
        else:
            response_text = '[Error: OpenClaw client not available. Make sure openclaw_llm.py is in the same directory.]'

        # Add response to session history
        session.messages.append({'role': 'assistant', 'content': response_text})

        return {'content': [{'type': 'text', 'text': response_text}]}

    return {'content': [{'type': 'text', 'text': f'Unknown tool: {tool_name}'}], 'isError': True}


# ============================================================================
# Main MCP Server Loop
# ============================================================================

def main():
    """Main MCP server loop - synchronous for Python 3.9 compatibility."""
    global _session_manager
    _session_manager = SessionManager()

    buffer = ""

    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break

            buffer += line
            try:
                request = json.loads(buffer)
                buffer = ""
            except json.JSONDecodeError:
                continue

            method = request.get('method')
            req_id = request.get('id')
            params = request.get('params', {})

            if method == 'initialize':
                result = handle_initialize(params)
                send_response(req_id, result)
                send_notification('initialized', {'capabilities': result['capabilities']})

            elif method == 'tools/list':
                result = handle_list_tools()
                send_response(req_id, result)

            elif method == 'tools/call':
                result = handle_call_tool(params, _session_manager)
                send_response(req_id, result)

            elif method == 'notifications/claude/channel':
                # Agent is sending a message to us
                content = params.get('content', '')
                meta = params.get('meta', {})
                session_id = meta.get('user_id', 'default')
                if _session_manager:
                    _session_manager.on_agent_response(session_id, content)

            elif method.startswith('notifications/'):
                # Ignore other notifications
                pass

            else:
                send_error(req_id, -32601, f'Unknown method: {method}')

        except Exception as e:
            sys.stderr.write(f'MCP server error: {e}\n')
            sys.stderr.flush()


if __name__ == '__main__':
    main()