"""Welcome email sent after successful registration."""

SUBJECT = "Welcome to {product_name} -- your documentation pipeline is ready"

HTML_BODY = """\
<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI',
  Roboto, sans-serif; color: #1a1a1a; max-width: 600px; margin: 0 auto;
  padding: 24px; line-height: 1.6;">

  <h2 style="color: #111; margin-bottom: 8px;">
    Welcome to {product_name}
  </h2>

  <p>Hi {user_name},</p>

  <p>Your {product_name} account is ready. Here is what you can do right
  now on the <strong>Free</strong> tier:</p>

  <table style="width: 100%; border-collapse: collapse; margin: 16px 0;">
    <tr style="background: #f8f9fa;">
      <td style="padding: 8px 12px; border: 1px solid #e9ecef;">
        AI requests</td>
      <td style="padding: 8px 12px; border: 1px solid #e9ecef;
        text-align: right;"><strong>50</strong> / period</td>
    </tr>
    <tr>
      <td style="padding: 8px 12px; border: 1px solid #e9ecef;">
        Documentation pages</td>
      <td style="padding: 8px 12px; border: 1px solid #e9ecef;
        text-align: right;"><strong>10</strong> pages</td>
    </tr>
    <tr style="background: #f8f9fa;">
      <td style="padding: 8px 12px; border: 1px solid #e9ecef;">
        API calls</td>
      <td style="padding: 8px 12px; border: 1px solid #e9ecef;
        text-align: right;"><strong>100</strong> / period</td>
    </tr>
  </table>

  <h3 style="color: #111; margin-top: 24px;">Get started in 3 steps</h3>

  <ol style="padding-left: 20px;">
    <li style="margin-bottom: 8px;">
      <strong>Upload your docs</strong> -- push Markdown files or connect
      your Confluence workspace.</li>
    <li style="margin-bottom: 8px;">
      <strong>Run the pipeline</strong> -- the 14-step pipeline normalizes,
      enhances, and optimizes your documentation automatically.</li>
    <li style="margin-bottom: 8px;">
      <strong>Review results</strong> -- check the generated reports and
      download your Stripe-quality documentation.</li>
  </ol>

  <p style="text-align: center; margin: 32px 0;">
    <a href="{app_url}/dashboard"
       style="background: #2563eb; color: #fff; padding: 12px 32px;
              border-radius: 6px; text-decoration: none;
              font-weight: 600;">
      Open dashboard
    </a>
  </p>

  <p>Need more capacity? <a href="{app_url}/billing"
     style="color: #2563eb;">Upgrade your plan</a> to unlock higher limits
     and AI-powered enhancements.</p>

  <p>Questions? Reply to this email or visit
     <a href="{app_url}/support" style="color: #2563eb;">support</a>.</p>

  <p style="color: #666; font-size: 13px; margin-top: 40px;
     border-top: 1px solid #e9ecef; padding-top: 16px;">
    {product_name} -- Automated documentation pipeline<br>
    <a href="{app_url}" style="color: #2563eb;">{app_url}</a>
  </p>

</body>
</html>"""
