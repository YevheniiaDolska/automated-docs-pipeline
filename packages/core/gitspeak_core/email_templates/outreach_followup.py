"""Follow-up email sent 5 days after the initial audit outreach."""

SUBJECT = "Re: Your {company_name} documentation audit"

HTML_BODY = """\
<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI',
  Roboto, sans-serif; color: #1a1a1a; max-width: 600px; margin: 0 auto;
  padding: 24px; line-height: 1.6;">

  <p>Hi {recipient_name},</p>

  <p>Following up on the documentation audit I shared last week. Since
  then, I noticed a couple of additional items in {company_name}'s docs
  that are worth highlighting:</p>

  <ul style="padding-left: 20px;">
    <li style="margin-bottom: 6px;">
      <strong>SEO gaps:</strong> {seo_gap_detail}</li>
    <li style="margin-bottom: 6px;">
      <strong>API reference drift:</strong> {drift_detail}</li>
  </ul>

  <p>These are common issues we see in developer documentation at scale.
  The VeriDoc pipeline addresses them automatically with:</p>

  <ol style="padding-left: 20px;">
    <li style="margin-bottom: 6px;">24-check SEO/GEO optimization
      (search engines and AI assistants)</li>
    <li style="margin-bottom: 6px;">Automatic API-to-docs drift
      detection</li>
    <li style="margin-bottom: 6px;">LLM-powered quality enhancement
      with Stripe-level standards</li>
  </ol>

  <p>Happy to walk through these in a quick 15-minute call -- or if you
  prefer, I can send a more detailed scorecard for specific sections of
  your docs.</p>

  <p style="text-align: center; margin: 32px 0;">
    <a href="{calendar_url}"
       style="background: #2563eb; color: #fff; padding: 12px 32px;
              border-radius: 6px; text-decoration: none;
              font-weight: 600;">
      Schedule 15 minutes
    </a>
  </p>

  <p>Best,<br>
  {sender_name}<br>
  <span style="color: #666;">{sender_title}, VeriDoc</span></p>

  <p style="color: #666; font-size: 13px; margin-top: 40px;
     border-top: 1px solid #e9ecef; padding-top: 16px;">
    VeriDoc -- Automated documentation pipeline<br>
    <a href="https://veri-doc.app" style="color: #2563eb;">veri-doc.app</a>
  </p>

</body>
</html>"""
