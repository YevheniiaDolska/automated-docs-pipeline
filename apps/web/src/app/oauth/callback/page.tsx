"use client";

import { useEffect, useMemo } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { setToken } from "@/lib/api";

export default function OAuthCallbackPage() {
  const router = useRouter();
  const params = useSearchParams();
  const error = useMemo(() => params.get("error"), [params]);

  useEffect(() => {
    const token = params.get("access_token");
    if (token) {
      setToken(token);
      router.replace("/dashboard");
      return;
    }
    router.replace(`/login${error ? `?error=${encodeURIComponent(error)}` : ""}`);
  }, [error, params, router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <p className="text-sm text-slate-600">Completing sign in...</p>
    </div>
  );
}
