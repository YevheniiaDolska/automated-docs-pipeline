import { Suspense } from "react";
import OAuthCallbackClient from "./OAuthCallbackClient";

export const dynamic = "force-dynamic";

export default function OAuthCallbackPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <Suspense fallback={<p className="text-sm text-slate-600">Completing sign in...</p>}>
        <OAuthCallbackClient />
      </Suspense>
    </div>
  );
}
