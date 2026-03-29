"""Upgrade prompt email sent when a user approaches their tier limits."""

SUBJECT = "You have used {usage_percent}% of your {product_name} {tier} limits"

HTML_BODY = """\
<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI',
  Roboto, sans-serif; color: #1a1a1a; max-width: 600px; margin: 0 auto;
  padding: 24px; line-height: 1.6;">

  <h2 style="color: #111; margin-bottom: 8px;">
    You are approaching your {tier} limits
  </h2>

  <p>Hi {user_name},</p>

  <p>You have used <strong>{usage_percent}%</strong> of your
  <strong>{tier}</strong> plan limits this billing period:</p>

  <table style="width: 100%; border-collapse: collapse; margin: 16px 0;">
    <tr style="background: #f8f9fa;">
      <td style="padding: 8px 12px; border: 1px solid #e9ecef;">
        AI requests</td>
      <td style="padding: 8px 12px; border: 1px solid #e9ecef;
        text-align: right;">{ai_used} / {ai_limit}</td>
    </tr>
    <tr>
      <td style="padding: 8px 12px; border: 1px solid #e9ecef;">
        Pages</td>
      <td style="padding: 8px 12px; border: 1px solid #e9ecef;
        text-align: right;">{pages_used} / {pages_limit}</td>
    </tr>
    <tr style="background: #f8f9fa;">
      <td style="padding: 8px 12px; border: 1px solid #e9ecef;">
        API calls</td>
      <td style="padding: 8px 12px; border: 1px solid #e9ecef;
        text-align: right;">{api_used} / {api_limit}</td>
    </tr>
  </table>

  <p>When you reach the limit, pipeline runs are paused until the next
  billing period. Upgrade to {next_tier} to get higher limits and continue
  without interruption.</p>

  <h3 style="color: #111; margin-top: 24px;">
    {next_tier} includes
  </h3>

  <ul style="padding-left: 20px;">
    <li style="margin-bottom: 6px;">{next_tier_ai_limit} AI requests
      per period</li>
    <li style="margin-bottom: 6px;">{next_tier_pages_limit} documentation
      pages</li>
    <li style="margin-bottom: 6px;">{next_tier_api_limit} API calls
      per period</li>
  </ul>

  <p style="text-align: center; margin: 32px 0;">
    <a href="{app_url}/billing/checkout?tier={next_tier_slug}"
       style="background: #2563eb; color: #fff; padding: 12px 32px;
              border-radius: 6px; text-decoration: none;
              font-weight: 600;">
      Upgrade to {next_tier}
    </a>
  </p>

  <p style="color: #666; font-size: 13px;">
    Annual plans save 20%. <a href="{app_url}/billing"
    style="color: #2563eb;">Compare plans</a></p>

  <p style="color: #666; font-size: 13px; margin-top: 40px;
     border-top: 1px solid #e9ecef; padding-top: 16px;">
    {product_name} -- Automated documentation pipeline<br>
    <a href="{app_url}" style="color: #2563eb;">{app_url}</a><br>
    <a href="{app_url}/settings/notifications"
       style="color: #999; font-size: 12px;">Manage email preferences</a>
  </p>

</body>
</html>"""
