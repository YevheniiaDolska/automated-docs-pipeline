/**
 * Check PRs and post reminders if needed
 * Used by .github/workflows/pr-reminder.yml
 */

module.exports = async ({github, context}) => {
  const owner = context.repo.owner;
  const repo = context.repo.repo;

  // Get all open PRs
  const { data: prs } = await github.rest.pulls.list({
    owner,
    repo,
    state: 'open'
  });

  const now = new Date();

  for (const pr of prs) {
    // Skip draft PRs
    if (pr.draft) continue;

    // Calculate PR age in hours
    const prAge = Math.floor((now - new Date(pr.created_at)) / (1000 * 60 * 60));

    // Get reviews for this PR
    const { data: reviews } = await github.rest.pulls.listReviews({
      owner,
      repo,
      pull_number: pr.number
    });

    // Check existing comments to avoid duplicates
    const { data: comments } = await github.rest.issues.listComments({
      owner,
      repo,
      issue_number: pr.number
    });

    const hasReminderToday = comments.some(comment => {
      const commentAge = (now - new Date(comment.created_at)) / (1000 * 60 * 60);
      return comment.user.login === 'github-actions[bot]' &&
             comment.body.includes('reminder') &&
             commentAge < 24;
    });

    if (hasReminderToday) continue;

    let message = null;

    if (reviews.length === 0) {
      // No reviews yet
      if (prAge > 48) {
        message = `👋 **Friendly review reminder**

This PR has been open for ${Math.floor(prAge / 24)} days without any reviews.

**PR Summary:**
- Author: @${pr.user.login}
- Created: ${new Date(pr.created_at).toLocaleDateString()}
- Changes: +${pr.additions} -${pr.deletions}

Please consider reviewing when you have time. Thank you! 🙏`;
      }
    } else {
      // Has reviews, check for requested changes
      const changesRequested = reviews.some(r => r.state === 'CHANGES_REQUESTED');
      const lastReview = reviews[reviews.length - 1];
      const daysSinceReview = Math.floor((now - new Date(lastReview.submitted_at)) / (1000 * 60 * 60 * 24));

      if (changesRequested && daysSinceReview > 3) {
        message = `🔄 **Review follow-up reminder**

This PR has requested changes from ${daysSinceReview} days ago.

@${pr.user.login}, please address the review feedback when possible.
Reviewers: Please re-review once changes are made.`;
      } else if (!changesRequested && daysSinceReview > 5) {
        message = `⏳ **Merge reminder**

This PR has been reviewed but hasn't been merged for ${daysSinceReview} days.

Last review: ${lastReview.state} by @${lastReview.user.login}

Please consider merging or provide additional feedback.`;
      }
    }

    // Post comment if we have a message
    if (message) {
      await github.rest.issues.createComment({
        owner,
        repo,
        issue_number: pr.number,
        body: message
      });
      console.log(`Posted reminder to PR #${pr.number}`);
    }
  }
};