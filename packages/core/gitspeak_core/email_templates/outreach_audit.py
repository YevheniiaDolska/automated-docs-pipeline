"""Outreach email for offering a free documentation audit to prospects."""

SUBJECT = "Your {company_name} documentation: free quality audit"

HTML_BODY = """\
<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI',
  Roboto, sans-serif; color: #1a1a1a; max-width: 600px; margin: 0 auto;
  padding: 24px; line-height: 1.6;">

  <p>Hi {recipient_name},</p>

  <p>I ran a quick audit on <strong>{company_name}</strong>'s public
  documentation at <a href="{docs_url}" style="color: #2563eb;">
  {docs_url}</a> and found some opportunities to improve:</p>

  <table style="width: 100%; border-collapse: collapse; margin: 16px 0;">
    <tr style="background: #f8f9fa;">
      <td style="padding: 8px 12px; border: 1px solid #e9ecef;">
        Overall quality score</td>
      <td style="padding: 8px 12px; border: 1px solid #e9ecef;
        text-align: right; font-weight: 600;">{quality_score}/100</td>
    </tr>
    <tr>
      <td style="padding: 8px 12px; border: 1px solid #e9ecef;">
        Pages analyzed</td>
      <td style="padding: 8px 12px; border: 1px solid #e9ecef;
        text-align: right;">{pages_analyzed}</td>
    </tr>
    <tr style="background: #f8f9fa;">
      <td style="padding: 8px 12px; border: 1px solid #e9ecef;">
        Issues found</td>
      <td style="padding: 8px 12px; border: 1px solid #e9ecef;
        text-align: right;">{issues_found}</td>
    </tr>
    <tr>
      <td style="padding: 8px 12px; border: 1px solid #e9ecef;">
        Top issue category</td>
      <td style="padding: 8px 12px; border: 1px solid #e9ecef;
        text-align: right;">{top_issue}</td>
    </tr>
  </table>

  <p>The full audit report is attached as a PDF. Key findings include:</p>

  <ul style="padding-left: 20px;">
    <li style="margin-bottom: 6px;">{finding_1}</li>
    <li style="margin-bottom: 6px;">{finding_2}</li>
    <li style="margin-bottom: 6px;">{finding_3}</li>
  </ul>

  <p>These issues directly impact developer experience and search
  discoverability. Our automated pipeline fixes them at scale -- we
  have helped companies like Confluent and LaunchDarkly improve their
  documentation quality by 30-50 points.</p>

  <p>Would a 20-minute walkthrough of the audit results be useful? I can
  show you exactly what the pipeline does and how it maps to your docs.</p>

  <p style="text-align: center; margin: 32px 0;">
    <a href="{calendar_url}"
       style="background: #2563eb; color: #fff; padding: 12px 32px;
              border-radius: 6px; text-decoration: none;
              font-weight: 600;">
      Book a walkthrough
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
