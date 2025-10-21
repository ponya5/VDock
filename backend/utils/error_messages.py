"""User-friendly error messages and error codes for VDock."""

class ErrorCode:
    """Error codes for common failure scenarios."""
    
    # Action execution errors (1000-1999)
    ACTION_EXECUTION_FAILED = 1000
    ACTION_VALIDATION_FAILED = 1001
    ACTION_TIMEOUT = 1002
    ACTION_PERMISSION_DENIED = 1003
    
    # Hotkey errors (2000-2099)
    HOTKEY_INVALID_KEY = 2000
    HOTKEY_SEND_FAILED = 2001
    HOTKEY_LIBRARY_UNAVAILABLE = 2002
    
    # Program/Application errors (2100-2199)
    PROGRAM_NOT_FOUND = 2100
    PROGRAM_LAUNCH_FAILED = 2101
    PROGRAM_PERMISSION_DENIED = 2102
    
    # URL errors (2200-2299)
    URL_INVALID = 2200
    URL_OPEN_FAILED = 2201
    
    # System errors (2300-2399)
    SYSTEM_COMMAND_FAILED = 2300
    SYSTEM_PERMISSION_DENIED = 2301
    SYSTEM_NOT_SUPPORTED = 2302
    
    # File/Upload errors (2400-2499)
    FILE_NOT_FOUND = 2400
    FILE_TOO_LARGE = 2401
    FILE_INVALID_FORMAT = 2402
    FILE_UPLOAD_FAILED = 2403
    
    # Configuration errors (2500-2599)
    CONFIG_INVALID = 2500
    CONFIG_MISSING_FIELD = 2501
    CONFIG_SAVE_FAILED = 2502
    
    # Network errors (2600-2699)
    NETWORK_TIMEOUT = 2600
    NETWORK_UNAVAILABLE = 2601
    NETWORK_REQUEST_FAILED = 2602


ERROR_MESSAGES = {
    # Action execution errors
    ErrorCode.ACTION_EXECUTION_FAILED: {
        'title': 'Action Failed',
        'message': 'Failed to execute the button action.',
        'troubleshooting': 'Try the following:\n• Check if the application or file exists\n• Verify you have the necessary permissions\n• Restart VDock and try again'
    },
    ErrorCode.ACTION_VALIDATION_FAILED: {
        'title': 'Invalid Configuration',
        'message': 'The button action configuration is invalid.',
        'troubleshooting': 'Edit the button and check:\n• All required fields are filled\n• Values are in the correct format\n• No special characters causing issues'
    },
    ErrorCode.ACTION_TIMEOUT: {
        'title': 'Action Timeout',
        'message': 'The action took too long to complete.',
        'troubleshooting': 'Try:\n• Running the action again\n• Checking if the target application is responding\n• Increasing timeout in settings'
    },
    ErrorCode.ACTION_PERMISSION_DENIED: {
        'title': 'Permission Denied',
        'message': 'VDock doesn\'t have permission to perform this action.',
        'troubleshooting': 'Try:\n• Running VDock as administrator\n• Checking folder/file permissions\n• Disabling security software temporarily'
    },
    
    # Hotkey errors
    ErrorCode.HOTKEY_INVALID_KEY: {
        'title': 'Invalid Hotkey',
        'message': 'The specified key combination is invalid.',
        'troubleshooting': 'Edit the button and:\n• Use valid key names (Ctrl, Alt, Shift, etc.)\n• Check for typos in key names\n• Try recording the hotkey instead of typing it'
    },
    ErrorCode.HOTKEY_SEND_FAILED: {
        'title': 'Hotkey Failed',
        'message': 'Failed to send the keyboard shortcut.',
        'troubleshooting': 'Try:\n• Clicking on the target application first\n• Checking if the application accepts keyboard input\n• Restarting VDock'
    },
    ErrorCode.HOTKEY_LIBRARY_UNAVAILABLE: {
        'title': 'Keyboard Control Unavailable',
        'message': 'The keyboard control library is not available.',
        'troubleshooting': 'Try:\n• Reinstalling VDock\n• Installing the pynput library: pip install pynput\n• Checking Python installation'
    },
    
    # Program errors
    ErrorCode.PROGRAM_NOT_FOUND: {
        'title': 'Program Not Found',
        'message': 'The specified program or file could not be found.',
        'troubleshooting': 'Edit the button and:\n• Verify the file path is correct\n• Use "Browse" to select the file\n• Check if the program is installed'
    },
    ErrorCode.PROGRAM_LAUNCH_FAILED: {
        'title': 'Launch Failed',
        'message': 'Failed to launch the program.',
        'troubleshooting': 'Try:\n• Launching the program manually first\n• Checking if the program is already running\n• Running VDock as administrator'
    },
    ErrorCode.PROGRAM_PERMISSION_DENIED: {
        'title': 'Access Denied',
        'message': 'Permission denied when trying to launch the program.',
        'troubleshooting': 'Try:\n• Running VDock as administrator\n• Checking file permissions\n• Moving the program to a different location'
    },
    
    # URL errors
    ErrorCode.URL_INVALID: {
        'title': 'Invalid URL',
        'message': 'The URL format is invalid.',
        'troubleshooting': 'Edit the button and:\n• Start with http:// or https://\n• Check for typos in the URL\n• Test the URL in a browser'
    },
    ErrorCode.URL_OPEN_FAILED: {
        'title': 'Failed to Open URL',
        'message': 'Could not open the URL in your browser.',
        'troubleshooting': 'Try:\n• Opening the URL manually in a browser\n• Setting a default browser in Windows\n• Checking your internet connection'
    },
    
    # System errors
    ErrorCode.SYSTEM_COMMAND_FAILED: {
        'title': 'System Command Failed',
        'message': 'Failed to execute the system command.',
        'troubleshooting': 'Try:\n• Running VDock as administrator\n• Checking if the command is supported\n• Verifying system settings'
    },
    ErrorCode.SYSTEM_PERMISSION_DENIED: {
        'title': 'System Permission Denied',
        'message': 'VDock needs administrator privileges for this action.',
        'troubleshooting': 'Try:\n• Right-click VDock and select "Run as administrator"\n• Adjusting Windows UAC settings\n• Checking security software'
    },
    ErrorCode.SYSTEM_NOT_SUPPORTED: {
        'title': 'Not Supported',
        'message': 'This action is not supported on your system.',
        'troubleshooting': 'This action may:\n• Only work on Windows/macOS/Linux\n• Require specific hardware\n• Need additional software installed'
    },
    
    # File errors
    ErrorCode.FILE_NOT_FOUND: {
        'title': 'File Not Found',
        'message': 'The specified file does not exist.',
        'troubleshooting': 'Check:\n• The file path is correct\n• The file hasn\'t been moved or deleted\n• You have permission to access the folder'
    },
    ErrorCode.FILE_TOO_LARGE: {
        'title': 'File Too Large',
        'message': 'The file exceeds the maximum allowed size (50MB).',
        'troubleshooting': 'Try:\n• Using a smaller file\n• Compressing the file\n• Hosting the file externally and using a URL'
    },
    ErrorCode.FILE_INVALID_FORMAT: {
        'title': 'Invalid File Format',
        'message': 'The file format is not supported.',
        'troubleshooting': 'Check:\n• Supported formats: PNG, JPG, GIF, MP4, WEBM\n• File extension matches file type\n• File is not corrupted'
    },
    ErrorCode.FILE_UPLOAD_FAILED: {
        'title': 'Upload Failed',
        'message': 'Failed to upload the file to the server.',
        'troubleshooting': 'Try:\n• Checking your internet connection\n• Uploading a different file\n• Restarting VDock'
    },
    
    # Configuration errors
    ErrorCode.CONFIG_INVALID: {
        'title': 'Invalid Configuration',
        'message': 'The configuration format is invalid.',
        'troubleshooting': 'Try:\n• Resetting to default settings\n• Checking for corrupted config files\n• Reinstalling VDock'
    },
    ErrorCode.CONFIG_MISSING_FIELD: {
        'title': 'Missing Configuration',
        'message': 'Required configuration field is missing.',
        'troubleshooting': 'Try:\n• Filling in all required fields\n• Using the configuration wizard\n• Checking documentation for required fields'
    },
    ErrorCode.CONFIG_SAVE_FAILED: {
        'title': 'Save Failed',
        'message': 'Failed to save the configuration.',
        'troubleshooting': 'Check:\n• Disk space is available\n• File permissions in data folder\n• Antivirus isn\'t blocking writes'
    },
    
    # Network errors
    ErrorCode.NETWORK_TIMEOUT: {
        'title': 'Connection Timeout',
        'message': 'The network request timed out.',
        'troubleshooting': 'Try:\n• Checking your internet connection\n• Trying again in a moment\n• Increasing timeout in settings'
    },
    ErrorCode.NETWORK_UNAVAILABLE: {
        'title': 'Network Unavailable',
        'message': 'No internet connection available.',
        'troubleshooting': 'Check:\n• WiFi or ethernet connection\n• Firewall settings\n• Proxy configuration'
    },
    ErrorCode.NETWORK_REQUEST_FAILED: {
        'title': 'Request Failed',
        'message': 'The network request failed.',
        'troubleshooting': 'Try:\n• Checking the URL is correct\n• Verifying the service is available\n• Checking firewall/proxy settings'
    }
}


def get_error_message(error_code: int) -> dict:
    """Get user-friendly error message for an error code.
    
    Args:
        error_code: Error code from ErrorCode class
        
    Returns:
        Dictionary with title, message, and troubleshooting info
    """
    return ERROR_MESSAGES.get(error_code, {
        'title': 'Unknown Error',
        'message': 'An unexpected error occurred.',
        'troubleshooting': 'Try:\n• Restarting VDock\n• Checking the logs\n• Reporting this issue'
    })


def format_error_response(error_code: int, details: str = None) -> dict:
    """Format an error response for API endpoints.
    
    Args:
        error_code: Error code from ErrorCode class
        details: Optional additional technical details
        
    Returns:
        Dictionary with error information for API response
    """
    error_info = get_error_message(error_code)
    
    response = {
        'success': False,
        'error_code': error_code,
        'error': error_info['message'],
        'title': error_info['title'],
        'troubleshooting': error_info['troubleshooting']
    }
    
    if details:
        response['details'] = details
    
    return response

