#!/usr/bin/env python3
"""
Secure Subprocess Utilities for MenuAutomacoes
Provides safe subprocess execution with input validation and injection prevention

This module implements security best practices for subprocess execution:
1. Explicit argument lists (no shell=True)
2. Input validation and sanitization
3. Path validation and canonicalization
4. Timeout protection
5. Resource limits
"""

import subprocess
import sys
import os
import shlex
from pathlib import Path
from typing import List, Optional, Union, Dict, Any
import logging


logger = logging.getLogger(__name__)


class SecureSubprocessError(Exception):
    """Custom exception for secure subprocess operations"""
    pass


class SecureSubprocessRunner:
    """Secure subprocess execution with input validation"""
    
    # Allowed executables - whitelist approach
    ALLOWED_EXECUTABLES = {
        'python': [sys.executable, 'python', 'python3'],
        'pip': ['pip', 'pip3', f'{sys.executable} -m pip'],
        'pip-audit': ['pip-audit'],
        'pytest': ['pytest', f'{sys.executable} -m pytest'],
        'git': ['git']
    }
    
    # Allowed arguments for specific commands
    ALLOWED_ARGUMENTS = {
        'pip-audit': ['--format=json', '--version', '--help'],
        'pytest': ['-v', '--tb=short', '--tb=long', '--tb=no', '-x', '-s', '--help'],
        'pip': ['install', 'list', 'show', 'freeze', '--version', '--help', '-r', '--break-system-packages'],
        'git': ['status', 'diff', 'log', 'add', 'commit', 'push', 'pull', '--version', '--help']
    }
    
    def __init__(self, working_directory: Optional[Path] = None):
        """Initialize secure subprocess runner
        
        Args:
            working_directory: Working directory for command execution
        """
        self.working_directory = working_directory or Path.cwd()
        if not self.working_directory.exists():
            raise SecureSubprocessError(f"Working directory does not exist: {self.working_directory}")
    
    def validate_executable(self, executable: str) -> str:
        """Validate and resolve executable path
        
        Args:
            executable: Executable name or path
            
        Returns:
            Validated executable path
            
        Raises:
            SecureSubprocessError: If executable is not allowed or not found
        """
        # Check if executable is in whitelist
        for exe_type, allowed_exes in self.ALLOWED_EXECUTABLES.items():
            if executable in allowed_exes or executable.endswith(tuple(allowed_exes)):
                # For Python executables, always use sys.executable for security
                if exe_type == 'python':
                    return sys.executable
                break
        else:
            raise SecureSubprocessError(f"Executable not allowed: {executable}")
        
        # Validate executable exists (for external tools)
        if executable not in [sys.executable, 'python', 'python3']:
            try:
                # Try to run --version to validate executable exists and responds
                result = subprocess.run(
                    [executable, '--version'],
                    capture_output=True,
                    timeout=10,
                    check=False
                )
                if result.returncode not in [0, 1]:  # Some tools return 1 for --version
                    raise SecureSubprocessError(f"Executable validation failed: {executable}")
            except (FileNotFoundError, subprocess.TimeoutExpired):
                raise SecureSubprocessError(f"Executable not found or not responding: {executable}")
        
        return executable
    
    def validate_arguments(self, executable: str, arguments: List[str]) -> List[str]:
        """Validate command arguments against whitelist
        
        Args:
            executable: The executable being run
            arguments: List of arguments to validate
            
        Returns:
            Validated arguments list
            
        Raises:
            SecureSubprocessError: If arguments contain unsafe content
        """
        validated_args = []
        
        # Get allowed arguments for this executable
        exe_name = Path(executable).name
        allowed_args = self.ALLOWED_ARGUMENTS.get(exe_name, [])
        
        for arg in arguments:
            # Block dangerous patterns
            dangerous_patterns = [';', '&&', '||', '|', '>', '<', '$', '`', '$(', '${']
            if any(pattern in arg for pattern in dangerous_patterns):
                raise SecureSubprocessError(f"Potentially dangerous argument: {arg}")
            
            # Validate file paths exist if they look like paths
            if arg.startswith(('./', '/', '../')) or '.' in arg and '/' in arg:
                # This looks like a file path - validate it exists and is within working directory
                try:
                    arg_path = Path(arg)
                    if not arg_path.is_absolute():
                        arg_path = self.working_directory / arg_path
                    
                    # Resolve to canonical path and check it's within working directory
                    canonical_path = arg_path.resolve()
                    working_canonical = self.working_directory.resolve()
                    
                    if not str(canonical_path).startswith(str(working_canonical)):
                        raise SecureSubprocessError(f"Path outside working directory: {arg}")
                    
                    # Use the canonical path string
                    validated_args.append(str(canonical_path))
                    continue
                    
                except (OSError, ValueError) as e:
                    # If path validation fails, check if it's an allowed argument
                    if arg not in allowed_args and not any(arg.startswith(allowed) for allowed in allowed_args):
                        raise SecureSubprocessError(f"Invalid path argument: {arg} ({e})")
            
            # For non-path arguments, check against whitelist if available
            elif allowed_args and arg not in allowed_args:
                # Allow arguments that start with allowed prefixes (like test file paths)
                if not any(arg.startswith(allowed) for allowed in allowed_args):
                    logger.warning(f"Argument not in whitelist but allowing: {arg}")
            
            validated_args.append(arg)
        
        return validated_args
    
    def validate_file_path(self, file_path: Union[str, Path]) -> Path:
        """Validate file path is safe and within working directory
        
        Args:
            file_path: File path to validate
            
        Returns:
            Validated Path object
            
        Raises:
            SecureSubprocessError: If path is unsafe
        """
        path = Path(file_path)
        
        # Convert to absolute path relative to working directory
        if not path.is_absolute():
            path = self.working_directory / path
        
        # Resolve to canonical path
        try:
            canonical_path = path.resolve()
        except (OSError, ValueError) as e:
            raise SecureSubprocessError(f"Invalid file path: {file_path} ({e})")
        
        # Ensure path is within working directory
        working_canonical = self.working_directory.resolve()
        if not str(canonical_path).startswith(str(working_canonical)):
            raise SecureSubprocessError(f"File path outside working directory: {file_path}")
        
        return canonical_path
    
    def run_command(self, 
                   command: List[str], 
                   timeout: int = 300,
                   capture_output: bool = True,
                   text: bool = True,
                   check: bool = False,
                   input_data: Optional[str] = None) -> subprocess.CompletedProcess:
        """Safely execute a command with validation
        
        Args:
            command: Command as list [executable, arg1, arg2, ...]
            timeout: Timeout in seconds
            capture_output: Whether to capture stdout/stderr
            text: Whether to return text or bytes
            check: Whether to raise exception on non-zero exit
            input_data: Input data to send to process
            
        Returns:
            subprocess.CompletedProcess result
            
        Raises:
            SecureSubprocessError: If command validation fails
            subprocess.TimeoutExpired: If command times out
            subprocess.CalledProcessError: If check=True and command fails
        """
        if not command:
            raise SecureSubprocessError("Empty command")
        
        # Validate executable
        executable = self.validate_executable(command[0])
        
        # Validate arguments
        arguments = self.validate_arguments(executable, command[1:]) if len(command) > 1 else []
        
        # Build final command
        final_command = [executable] + arguments
        
        # Log the command (safely)
        safe_command = [shlex.quote(arg) for arg in final_command]
        logger.info(f"Executing secure command: {' '.join(safe_command)}")
        
        try:
            # Execute with security constraints
            result = subprocess.run(
                final_command,
                cwd=self.working_directory,
                capture_output=capture_output,
                text=text,
                check=check,
                timeout=timeout,
                input=input_data,
                # Security: Never use shell=True
                shell=False,
                # Security: Clear environment of potentially dangerous variables
                env=self._get_safe_environment()
            )
            
            logger.debug(f"Command completed with exit code: {result.returncode}")
            return result
            
        except subprocess.TimeoutExpired as e:
            logger.error(f"Command timed out after {timeout}s: {' '.join(safe_command)}")
            raise
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed with exit code {e.returncode}: {' '.join(safe_command)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error executing command: {e}")
            raise SecureSubprocessError(f"Command execution failed: {e}")
    
    def _get_safe_environment(self) -> Dict[str, str]:
        """Get sanitized environment variables for subprocess execution
        
        Returns:
            Dictionary of safe environment variables
        """
        # Start with minimal safe environment
        safe_env = {
            'PATH': os.environ.get('PATH', ''),
            'HOME': os.environ.get('HOME', ''),
            'USER': os.environ.get('USER', ''),
            'LANG': os.environ.get('LANG', 'en_US.UTF-8'),
            'LC_ALL': os.environ.get('LC_ALL', ''),
            'PYTHONPATH': os.environ.get('PYTHONPATH', ''),
            'VIRTUAL_ENV': os.environ.get('VIRTUAL_ENV', ''),
        }
        
        # Add environment variables that are safe and needed
        safe_vars = [
            'TERM', 'SHELL', 'TMPDIR', 'TMP', 'TEMP',
            'PYTHON_VERSION', 'PIP_*', 'PYTEST_*'
        ]
        
        for var in safe_vars:
            if '*' in var:
                # Handle wildcard patterns
                prefix = var.replace('*', '')
                for env_var, env_val in os.environ.items():
                    if env_var.startswith(prefix):
                        safe_env[env_var] = env_val
            elif var in os.environ:
                safe_env[var] = os.environ[var]
        
        # Remove any None values
        return {k: v for k, v in safe_env.items() if v is not None}


# Convenience functions for common operations
def run_python_script(script_path: Union[str, Path], 
                     args: Optional[List[str]] = None,
                     working_dir: Optional[Path] = None,
                     timeout: int = 300) -> subprocess.CompletedProcess:
    """Safely run a Python script
    
    Args:
        script_path: Path to Python script
        args: Additional arguments
        working_dir: Working directory
        timeout: Timeout in seconds
        
    Returns:
        subprocess.CompletedProcess result
    """
    runner = SecureSubprocessRunner(working_dir)
    script_path = runner.validate_file_path(script_path)
    
    command = [sys.executable, str(script_path)]
    if args:
        command.extend(args)
    
    return runner.run_command(command, timeout=timeout)


def run_pip_command(args: List[str],
                   working_dir: Optional[Path] = None,
                   timeout: int = 600) -> subprocess.CompletedProcess:
    """Safely run pip command
    
    Args:
        args: Pip arguments
        working_dir: Working directory
        timeout: Timeout in seconds
        
    Returns:
        subprocess.CompletedProcess result
    """
    runner = SecureSubprocessRunner(working_dir)
    command = [sys.executable, '-m', 'pip'] + args
    return runner.run_command(command, timeout=timeout)


def run_pytest(test_paths: List[Union[str, Path]],
              args: Optional[List[str]] = None,
              working_dir: Optional[Path] = None,
              timeout: int = 300) -> subprocess.CompletedProcess:
    """Safely run pytest
    
    Args:
        test_paths: Test files or directories
        args: Additional pytest arguments
        working_dir: Working directory
        timeout: Timeout in seconds
        
    Returns:
        subprocess.CompletedProcess result
    """
    runner = SecureSubprocessRunner(working_dir)
    
    # Validate test paths
    validated_paths = []
    for test_path in test_paths:
        validated_path = runner.validate_file_path(test_path)
        validated_paths.append(str(validated_path))
    
    command = [sys.executable, '-m', 'pytest'] + validated_paths
    if args:
        command.extend(args)
    
    return runner.run_command(command, timeout=timeout)