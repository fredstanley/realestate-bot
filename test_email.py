import unittest
from unittest.mock import MagicMock, patch
from email_utils import send_email_with_pdf

class TestEmailUtils(unittest.TestCase):
    @patch('email_utils.smtplib.SMTP')
    def test_send_email_success(self, mock_smtp):
        # Setup mock
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        pdf_bytes = b"%PDF-1.4..."
        recipient = "test@example.com"
        sender = "sender@gmail.com"
        password = "password"
        address = "123 Main St"
        
        success, msg = send_email_with_pdf(pdf_bytes, recipient, sender, password, address)
        
        self.assertTrue(success)
        self.assertIsNone(msg)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_with(sender, password)
        mock_server.send_message.assert_called_once()

    @patch('email_utils.smtplib.SMTP')
    def test_send_email_failure(self, mock_smtp):
        # Setup mock to raise exception
        mock_smtp.return_value.__enter__.side_effect = Exception("SMTP Connection Failed")
        
        pdf_bytes = b"data"
        success, msg = send_email_with_pdf(pdf_bytes, "to", "from", "pass", "addr")
        
        self.assertFalse(success)
        self.assertIn("SMTP Connection Failed", msg)

if __name__ == '__main__':
    unittest.main()
