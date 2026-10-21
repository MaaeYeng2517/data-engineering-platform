"use client";
import { useState } from "react";
import { signIn } from "next-auth/react";

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    await fetch("/api/register", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email, password, name }) });
    await signIn("credentials", { email, password, callbackUrl: "/payment" });
  }
  return (
    <main className="min-h-screen flex items-center justify-center">
      <form onSubmit={submit} className="border p-6 rounded space-y-3 w-80">
        <h1 className="text-xl font-bold">Register</h1>
        <input value={name} onChange={(e) => setName(e.target.value)} className="w-full border p-2 rounded" placeholder="Name" />
        <input value={email} onChange={(e) => setEmail(e.target.value)} className="w-full border p-2 rounded" placeholder="Email" />
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="w-full border p-2 rounded" placeholder="Password" />
        <button className="w-full bg-black text-white py-2 rounded">Sign up</button>
            <div className="flex flex-col gap-2 mt-2">
        <button type="button" onClick={() => (window as any).location="/api/auth/signin/google"} className="border p-2 rounded">Continue with Google</button>
        <button type="button" onClick={() => (window as any).location="/api/auth/signin/apple"} className="border p-2 rounded">Continue with Apple</button>
        <button type="button" onClick={() => (window as any).location="/api/auth/signin/facebook"} className="border p-2 rounded">Continue with Facebook</button>
      </div>
    </form>
    </main>
  );
}
