"""Day-3 onboarding email with tips for getting the most out of the pipeline."""

SUBJECT = "3 tips to get the most from {product_name}"

HTML_BODY = """\
<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI',
  Roboto, sans-serif; color: #1a1a1a; max-width: 600px; margin: 0 auto;
  padding: 24px; line-height: 1.6;">

  <h2 style="color: #111; margin-bottom: 8px;">
    Getting the most from {product_name}
  </h2>

  <p>Hi {user_name},</p>

  <p>You signed up 3 days ago. Here are the features that teams find most
  valuable in their first week:</p>

  <h3 style="color: #111; margin-top: 24px;">
    1. Enable AI-powered enhancements
  </h3>

  <p>Add <code>--use-llm</code> to your pipeline run to activate
  Stripe-quality improvements: realistic code examples, missing section
  detection, and code block verification.</p>

  <div style="background: #f8f9fa; padding: 12px 16px; border-radius: 6px;
    font-family: 'SF Mono', Monaco, monospace; font-size: 14px;
    margin: 12px 0;">
    veridoc run --use-llm --docs-dir ./docs
  </div>

  <h3 style="color: #111; margin-top: 24px;">
    2. Import from Confluence
  </h3>

  <p>Migrate existing documentation from Confluence with a single command.
  The pipeline handles HTML-to-Markdown conversion, frontmatter generation,
  and quality enhancement automatically.</p>

  <div style="background: #f8f9fa; padding: 12px 16px; border-radius: 6px;
    font-family: 'SF Mono', Monaco, monospace; font-size: 14px;
    margin: 12px 0;">
    veridoc migrate --confluence-url https://your-company.atlassian.net
  </div>

  <h3 style="color: #111; margin-top: 24px;">
    3. Review the executive audit
  </h3>

  <p>Every pipeline run generates an executive audit PDF with quality scores,
  risk analysis, and actionable recommendations. Share it with your team to
  build the case for documentation investment.</p>

  <p style="text-align: center; margin: 32px 0;">
    <a href="{app_url}/dashboard"
       style="background: #2563eb; color: #fff; padding: 12px 32px;
              border-radius: 6px; text-decoration: none;
              font-weight: 600;">
      Open dashboard
    </a>
  </p>

  <p>Need help? Reply to this email -- we respond within 24 hours.</p>

  <p style="color: #666; font-size: 13px; margin-top: 40px;
     border-top: 1px solid #e9ecef; padding-top: 16px;">
    {product_name} -- Automated documentation pipeline<br>
    <a href="{app_url}" style="color: #2563eb;">{app_url}</a><br>
    <a href="{app_url}/settings/notifications"
       style="color: #999; font-size: 12px;">Manage email preferences</a>
  </p>

</body>
</html>"""
