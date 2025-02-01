import logging
from unittest.mock import Mock
from remote_assist_display import TokenMaskingFilter

def test_token_masking_filter():
    # This test doesn't need the app, just tests the filter directly
    record = Mock(spec=logging.LogRecord)
    token_filter = TokenMaskingFilter()

    test_cases = [
        # Single token
        {
            "input": 'DEBUG: {"access_token": "ey1hbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"}',
            "expected": 'DEBUG: {"access_token": "[REDACTED]"}'
        },
        # Multiple tokens
        {
            "input": '{"access_token": "ey2hbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c", "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5ODc2NTQzMjEwIiwibmFtZSI6IkphbmUgRG9lIn0.yRQYnWzskCZUxPwaQupWkiUzKELZ49eM7oWxAQK_ZXw"}',
            "expected": '{"access_token": "[REDACTED]", "refresh_token": "[REDACTED]"}'
        },
        # Single quotes
        {
            "input": "{'access_token': 'ey3hbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c'}",
            "expected": "{'access_token': '[REDACTED]'}"
        },
        # Mixed quotes
        {
            "input": "{'access_token': 'ey4hbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c', \"refresh_token\": \"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5ODc2NTQzMjEwIiwibmFtZSI6IkphbmUgRG9lIn0.yRQYnWzskCZUxPwaQupWkiUzKELZ49eM7oWxAQK_ZXw\"}",
            "expected": "{'access_token': '[REDACTED]', \"refresh_token\": \"[REDACTED]\"}"
        },
        # Make sure non-token messages pass through unchanged
        {
            "input": "Normal log message without any tokens",
            "expected": "Normal log message without any tokens"
        },
        # Test cases for escaped quotes
        {
            "input": '[2025-02-01 15:04:36,173] DEBUG in auth: Token: "{\\"access_token\\":\\"ey5hbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c\\"}"',
            "expected": '[2025-02-01 15:04:36,173] DEBUG in auth: Token: "{\\"access_token\\":\\"[REDACTED]\\"}"'
        },
        {
            "input": 'Token response: "{\\"access_token\\":\\"ey6hbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c\\", \\"refresh_token\\":\\"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5ODc2NTQzMjEwIiwibmFtZSI6IkphbmUgRG9lIn0.yRQYnWzskCZUxPwaQupWkiUzKELZ49eM7oWxAQK_ZXw\\"}"',
            "expected": 'Token response: "{\\"access_token\\":\\"[REDACTED]\\", \\"refresh_token\\":\\"[REDACTED]\\"}"'
        },
        {
            "input": 'Mixed content with token "{\\"access_token\\":\\"ey7hbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c\\"}" in the middle',
            "expected": 'Mixed content with token "{\\"access_token\\":\\"[REDACTED]\\"}" in the middle'
        }
    ]

    for case in test_cases:
        record.msg = case["input"]
        token_filter.filter(record)
        assert record.msg == case["expected"], f"Failed on input: {case['input']}"

def test_app_logger_filtering(app):
    """Test that the filter is properly attached to the app logger"""
    # Test both file and console handlers
    for handler in app.logger.handlers:
        # Verify the TokenMaskingFilter is attached
        filter_types = [type(f) for f in handler.filters]
        assert TokenMaskingFilter in filter_types, f"TokenMaskingFilter not found in {handler}"
        
        # Test actual filtering through the handler
        with app.app_context():
            test_message = '{"access_token": "ey7hbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c", "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5ODc2NTQzMjEwIiwibmFtZSI6IkphbmUgRG9lIn0.yRQYnWzskCZUxPwaQupWkiUzKELZ49eM7oWxAQK_ZXw"}'
            # Create a new record (this is how logging internally works)
            record = logging.LogRecord(
                name="test",
                level=logging.DEBUG,
                pathname="test.py",
                lineno=1,
                msg=test_message,
                args=(),
                exc_info=None
            )
            
            # Process the record through the handler's filters
            for filter in handler.filters:
                filter.filter(record)
            
            assert '"access_token": "[REDACTED]"' in record.msg
            assert '"refresh_token": "[REDACTED]"' in record.msg
            assert "ey" not in record.msg
            assert "ey" not in record.msg

def test_real_logging(app):
    """Test that actual logging calls get filtered"""
    with app.app_context():
        # Test a variety of log messages
        test_messages = [
            ('{"access_token": "ey7hbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"}', '[REDACTED]'),
            ('{"refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5ODc2NTQzMjEwIiwibmFtZSI6IkphbmUgRG9lIn0.yRQYnWzskCZUxPwaQupWkiUzKELZ49eM7oWxAQK_ZXw"}', '[REDACTED]'),
            ('Normal message', 'Normal message'),  # Should pass through unchanged
            ('Mixed message with {"access_token": "ey7hbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"}', '[REDACTED]')
        ]
        
        for test_msg, expected in test_messages:
            app.logger.info(test_msg)
