#!/usr/bin/env python3
"""
MCP (Model Context Protocol) Server Access Test
This script checks if MCP servers are accessible and configured.
"""

import subprocess
import json
import sys
import os
from pathlib import Path


def check_mcp_config_file():
    """
    Check if MCP configuration file exists.
    Returns True if config file exists and has servers configured.
    """
    # Common MCP config file locations
    config_paths = [
        Path.home() / ".claude" / "mcp.json",
        Path.home() / ".config" / "claude" / "mcp.json",
        Path.home() / "AppData" / "Roaming" / "Claude" / "mcp.json",  # Windows
    ]

    for config_path in config_paths:
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    # Check if there are any servers configured
                    if config.get("mcpServers") and len(config["mcpServers"]) > 0:
                        return True
            except (json.JSONDecodeError, PermissionError, KeyError):
                continue

    # Check for project-level configuration in .claude.json
    claude_json_path = Path.cwd() / ".claude.json"
    if claude_json_path.exists():
        try:
            with open(claude_json_path, 'r') as f:
                config = json.load(f)
                # Check if there are any servers configured in the current project
                current_project_path = str(Path.cwd().resolve())
                if config.get("projects", {}).get(current_project_path, {}).get("mcpServers"):
                    project_servers = config["projects"][current_project_path]["mcpServers"]
                    if len(project_servers) > 0:
                        return True
        except (json.JSONDecodeError, PermissionError, KeyError):
            pass

    return False


def check_mcp_access():
    """
    Check if MCP servers are accessible.
    Returns True if MCP servers are configured and accessible, False otherwise.
    """
    # First, check for config file
    if check_mcp_config_file():
        return True

    # Try to run the claude mcp list command
    try:
        result = subprocess.run(
            ["claude", "mcp", "list"],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Check if the command executed successfully
        if result.returncode == 0:
            output = result.stdout.strip()

            # Check if "No MCP servers configured" is in the output
            if "No MCP servers configured" in output:
                return False

            # If we get here, MCP servers are likely configured
            return True
        else:
            # Command failed
            return False

    except subprocess.TimeoutExpired:
        return False
    except FileNotFoundError:
        return False
    except Exception:
        return False


def main():
    """Main function to run the MCP access test."""
    has_mcp_access = check_mcp_access()

    # Print the result
    print(has_mcp_access)

    # Exit with appropriate status code
    sys.exit(0 if has_mcp_access else 1)


if __name__ == "__main__":
    main()
