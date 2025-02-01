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
            "input": 'DEBUG: {"access_token": "eyJhbGciOiJIUzI1NiIs..."}',
            "expected": 'DEBUG: {"access_token": "[REDACTED]"}'
        },
        # Multiple tokens
        {
            "input": '{"access_token": "eyJ123...", "refresh_token": "eyJ456..."}',
            "expected": '{"access_token": "[REDACTED]", "refresh_token": "[REDACTED]"}'
        },
        # Single quotes
        {
            "input": "{'access_token': 'eyJ789...'}",
            "expected": '{"access_token": "[REDACTED]"}'
        },
        # Mixed quotes
        {
            "input": "{'access_token': 'eyJ123...', \"refresh_token\": \"eyJ456...\"}",
            "expected": '{"access_token": "[REDACTED]", "refresh_token": "[REDACTED]"}'
        },
        # Make sure non-token messages pass through unchanged
        {
            "input": "Normal log message without any tokens",
            "expected": "Normal log message without any tokens"
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
            test_message = '{"access_token": "eyJ123...", "refresh_token": "eyJ456..."}'
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
            assert "eyJ123" not in record.msg
            assert "eyJ456" not in record.msg

def test_real_logging(app):
    """Test that actual logging calls get filtered"""
    with app.app_context():
        # Test a variety of log messages
        test_messages = [
            ('{"access_token": "eyJ123..."}', '[REDACTED]'),
            ('{"refresh_token": "eyJ456..."}', '[REDACTED]'),
            ('Normal message', 'Normal message'),  # Should pass through unchanged
            ('Mixed message with {"access_token": "eyJ789..."}', '[REDACTED]')
        ]
        
        for test_msg, expected in test_messages:
            app.logger.info(test_msg)
