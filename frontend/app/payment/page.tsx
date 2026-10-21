export default function PaymentPage() {
  const connected = !!process.env.STRIPE_SECRET_KEY;
  return (
    <main className="p-8 max-w-xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Payment Methods</h1>
      {!connected && <p className="text-amber-600 mb-4">Stripe not connected. <a href="/payment" className="underline">Connect</a></p>}
      <ul className="space-y-2">
        <li className="border p-3 rounded">💳 Credit/Debit Card</li>
        <li className="border p-3 rounded">🏦 Bank Transfer (ACH)</li>
        <li className="border p-3 rounded">₿ Bitcoin / Crypto</li>
        <li className="border p-3 rounded">📱 PromptPay / Local</li>
      </ul>
      <a href="/card" className="mt-6 inline-block underline">Back to cards</a>
    </main>
  );
}
