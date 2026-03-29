"""Standalone email templates for VeriDoc customer communications.

Templates are plain HTML strings with {placeholders} for string formatting.
Each template module exposes a SUBJECT and HTML_BODY constant.

Usage:
    from gitspeak_core.email_templates import welcome
    subject = welcome.SUBJECT.format(product_name="VeriDoc")
    body = welcome.HTML_BODY.format(
        user_name="Jane",
        product_name="VeriDoc",
        app_url="https://veri-doc.app",
    )
"""
