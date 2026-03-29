"use client";

import AppShell from "@/components/app-shell";

export default function ReferralTermsPage() {
  return (
    <AppShell>
    <div className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="text-2xl font-bold">Referral Terms</h1>
      <p className="mt-2 text-sm text-gray-600">
        Keep the Powered by VeriDoc badge enabled on higher plans to earn recurring
        referral commissions while both accounts stay on paid subscriptions.
      </p>

      <section className="mt-6 rounded border bg-white p-4 text-sm">
        <h2 className="text-base font-semibold">How recurring commissions work</h2>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-gray-700">
          <li>Your referral code is included in the badge link.</li>
          <li>When a referred customer buys a paid plan, attribution is stored.</li>
          <li>On each successful renewal payment, your commission accrues again.</li>
          <li>If payment is refunded, pending commission for that payment is reversed.</li>
        </ul>
      </section>

      <section className="mt-4 rounded border bg-white p-4 text-sm">
        <h2 className="text-base font-semibold">Badge policy by plan</h2>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-gray-700">
          <li>Free and cheapest paid plan: badge is mandatory, no commission.</li>
          <li>Higher paid plans: badge can be disabled, or kept enabled for commissions.</li>
        </ul>
      </section>

      <section className="mt-4 rounded border bg-white p-4 text-sm">
        <h2 className="text-base font-semibold">Payouts</h2>
        <p className="mt-2 text-gray-700">
          Payouts are calculated from accrued recurring commissions and are processed
          through your configured payout method when minimum threshold is reached.
        </p>
      </section>
    </div>
    </AppShell>
  );
}

