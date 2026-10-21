"use client";
import { useState } from "react";

export function BuyButton({ cardId }: { cardId: string }) {
  const [loading, setLoading] = useState(false);
  async function buy() {
    setLoading(true);
    const sessionRes = await fetch("/api/auth/session");
    const session = await sessionRes.json();
    if (!session?.user) {
      window.location.href = "/register";
      return;
    }
    window.location.href = "/payment";
  }
  return (
    <button onClick={buy} disabled={loading} className="mt-2 px-3 py-1 bg-indigo-600 text-white rounded text-sm disabled:opacity-50">
      {loading ? "..." : "Buy Now"}
    </button>
  );
}
