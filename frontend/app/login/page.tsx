"use client";
import { signIn } from "next-auth/react";
import { useState } from "react";

export default function LoginPage() {
  const [email, setEmail] = useState("demo@cardvault.io");
  const [password, setPassword] = useState("password123");
  return (
    <main className="min-h-screen flex items-center justify-center">
      <form onSubmit={(e) => { e.preventDefault(); signIn("credentials", { email, password, callbackUrl: "/card" }); }} className="border p-6 rounded space-y-3 w-80">
        <h1 className="text-xl font-bold">Login</h1>
        <input value={email} onChange={(e) => setEmail(e.target.value)} className="w-full border p-2 rounded" placeholder="Email" />
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="w-full border p-2 rounded" placeholder="Password" />
        <button className="w-full bg-black text-white py-2 rounded">Sign in</button>
      </form>
    </main>
  );
}
