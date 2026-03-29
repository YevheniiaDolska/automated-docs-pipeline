"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { auth } from "@/lib/api";

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [ok, setOk] = useState(false);

  useEffect(() => {
    const token = typeof window !== "undefined" ? localStorage.getItem("veridoc_token") : null;
    if (!token) {
      router.replace("/login");
      return;
    }
    auth
      .me()
      .then(() => setOk(true))
      .catch(() => {
        localStorage.removeItem("veridoc_token");
        router.replace("/login");
      });
  }, [router]);

  if (!ok) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-muted">Authenticating...</p>
      </div>
    );
  }

  return <>{children}</>;
}
